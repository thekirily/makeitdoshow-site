"""The fulfilment loop. Run it on a schedule (every few minutes) or after each paid order.

paid -> building -> built -> validated -> submitting -> submitted -> (Lulu's own states) ; side states:
held (a person must look), submit_unknown (we sent it and never heard back), cancelled.

Rules that keep a book from printing wrong or twice:
  1. Only `paid` orders start, and only `paypal.settle()` can set `paid`, after reading PayPal's record.
  2. Each step claims its order with a compare-and-set; a second robot gets nothing.
  3. Name and year are checked again here, after payment, with the same rules as the page.
  4. Every file is preflighted locally and validated by Lulu before a job is created.
  5. Before creating a job we search Lulu for our external_id. A submission that timed out goes to
     `submit_unknown` and is settled by that search, never by sending again blind.
"""
import json, os, secrets, shutil, time
from .common import STORE, CATALOG, log_event, HTTPError
from . import ledger, pdfbuild

WORK = os.path.join(STORE, 'var', 'build')
FILES = os.path.join(STORE, 'var', 'files')
SPEC = CATALOG['products']['youryear']
UNKNOWN_GRACE = int(os.environ.get('UNKNOWN_GRACE_S', '600'))


def publish(path):
    """Put a file where Lulu can fetch it, under an unguessable path; removed after shipping.
    Production: swap for a private bucket's short-lived signed URL (R2/S3). Same interface."""
    tok = secrets.token_urlsafe(18)
    os.makedirs(os.path.join(FILES, tok), exist_ok=True)
    dst = os.path.join(FILES, tok, os.path.basename(path)); shutil.copyfile(path, dst)
    return f"{os.environ['PUBLIC_FILES_BASE'].rstrip('/')}/files/{tok}/{os.path.basename(path)}"


def contact():
    return os.environ.get('LULU_CONTACT_EMAIL', 'orders@makeitdoshow.com'), os.environ.get('LULU_CONTACT_PHONE', '')


def build(lulu, o):
    if not ledger.move(o['id'], 'paid', 'building', 'robot claimed'):
        return
    lines = json.loads(o['lines'])
    try:
        res = pdfbuild.build_order_files(o, os.path.join(WORK, o['id']))
    except Exception as e:   # includes personalise.Bad: data that passed the page but fails here is a person's job
        ledger.move(o['id'], 'building', 'held', f'build failed: {type(e).__name__}: {e}', note=str(e)); return
    bad = [p for r in res for p in r['cover']['problems'] + r['interior']['problems']]
    if bad:
        ledger.move(o['id'], 'building', 'held', 'preflight failed', note='; '.join(bad)); return
    for r in res:
        ledger.set_file(o['id'], r['line'], 'cover', path=r['cover_path'], sha256=r['cover']['sha256'], url=publish(r['cover_path']),
                        detail=json.dumps(r['cover']))
        ledger.set_file(o['id'], r['line'], 'interior', path=r['interior_path'], sha256=r['interior']['sha256'],
                        url=publish(r['interior_path']), detail=json.dumps(r['interior']))
    ledger.move(o['id'], 'building', 'built', 'files built, preflight passed')


PENDING = ('VALIDATING', 'NORMALIZING', None)
VALIDATION_GIVE_UP_S = int(os.environ.get('VALIDATION_GIVE_UP_S', '7200'))


def validate(lulu, o):
    """Non-blocking. Each file is posted to Lulu once; its validation id is kept and re-read on later passes.
    A slow normalisation leaves the order in `built`; only a Lulu error (or two hours without an answer) holds it."""
    sku, pages = SPEC['pod_package_id'], SPEC['interior_pages']
    errors, waiting = [], []
    for f in ledger.files(o['id']):
        if not f['validation_id']:
            v = (lulu.validate_interior(f['url'], sku, order_id=o['id']) if f['kind'] == 'interior'
                 else lulu.validate_cover(f['url'], sku, pages, order_id=o['id']))
            ledger.set_file(o['id'], f['line_no'], f['kind'], validation_id=str(v['id']), validation_status=v.get('status'))
            v = lulu.wait_validation(f['kind'], v['id'], order_id=o['id'], tries=6, every=5)
        elif f['validation_status'] in PENDING:
            v = lulu.get_validation(f['kind'], f['validation_id'], order_id=o['id'])
        else:
            v = {'status': f['validation_status'], 'errors': None, 'page_count': pages}
        ledger.set_file(o['id'], f['line_no'], f['kind'], validation_status=v.get('status'))
        if v.get('status') in PENDING:
            waiting.append(f"{f['kind']} {f['line_no']}")
        elif v.get('status') not in ('VALIDATED', 'NORMALIZED') or v.get('errors'):
            errors.append(f"{f['kind']} {f['line_no']}: {v.get('status')} {v.get('errors')}")
        elif f['kind'] == 'interior' and v.get('page_count') not in (None, '') and str(v.get('page_count')) != str(pages):
            errors.append(f"interior {f['line_no']}: Lulu counted {v.get('page_count')} pages")
    if errors:
        ledger.move(o['id'], 'built', 'held', 'Lulu validation failed', note='; '.join(errors))
    elif waiting:
        if time.time() - o['updated'] > VALIDATION_GIVE_UP_S:
            ledger.move(o['id'], 'built', 'held', 'Lulu validation still pending after the give-up time', note=', '.join(waiting))
        else:
            log_event('order.wait', order_id=o['id'], why='Lulu still normalising: ' + ', '.join(waiting))
    else:
        ledger.move(o['id'], 'built', 'validated', 'Lulu validated every file')


def submit(lulu, o, timeout=60):
    if not ledger.move(o['id'], 'validated', 'submitting', 'robot claimed for submission'):
        return
    existing = lulu.find_by_external_id(o['id'], order_id=o['id'])
    if existing:   # a previous attempt reached Lulu: adopt it, never send twice
        ledger.move(o['id'], 'submitting', 'submitted', 'found existing Lulu job', lulu_job_id=str(existing[0]['id']),
                    lulu_status=existing[0]['status']['name']); return
    fs = ledger.files(o['id'])
    lines = json.loads(o['lines'])
    covers = [f['url'] for f in fs if f['kind'] == 'cover']
    inters = [f['url'] for f in fs if f['kind'] == 'interior']
    ship = json.loads(o['ship'])
    email, phone = contact()
    ship = {k: v for k, v in ship.items() if v}
    ship.setdefault('phone_number', phone)
    try:
        j = lulu.create_job(o, lines, covers, inters, ship, email, SPEC['pod_package_id'], SPEC['shipping_level'], timeout=timeout)
    except HTTPError as e:
        if e.status >= 500:
            ledger.move(o['id'], 'submitting', 'submit_unknown', f'Lulu {e.status}: outcome unknown'); return
        ledger.move(o['id'], 'submitting', 'held', f'Lulu refused the job ({e.status})', note=json.dumps(e.body)[:900]); return
    except Exception as e:  # timeout, connection reset: Lulu may or may not have the job
        ledger.move(o['id'], 'submitting', 'submit_unknown', f'no answer from Lulu: {type(e).__name__}'); return
    ledger.move(o['id'], 'submitting', 'submitted', 'Lulu accepted the job', lulu_job_id=str(j['id']), lulu_status=j['status']['name'])


def reconcile_unknown(lulu, o):
    found = lulu.find_by_external_id(o['id'], order_id=o['id'])
    if found:
        ledger.move(o['id'], 'submit_unknown', 'submitted', 'reconciled: Lulu has the job', lulu_job_id=str(found[0]['id']),
                    lulu_status=found[0]['status']['name'])
    elif time.time() - o['updated'] > UNKNOWN_GRACE:
        ledger.move(o['id'], 'submit_unknown', 'validated', f'reconciled: Lulu has no job after {UNKNOWN_GRACE}s; safe to send')
    else:
        log_event('order.wait', order_id=o['id'], why='submit_unknown inside grace period; not resending')


def poll(lulu, o):
    j = lulu.job(o['lulu_job_id'], order_id=o['id'])
    st = j['status']['name']
    if st != o['lulu_status']:
        ledger.move(o['id'], 'submitted', 'submitted', f'Lulu status {o["lulu_status"]} -> {st}', lulu_status=st)
    if st in ('REJECTED', 'CANCELED'):
        log_event('order.alert', order_id=o['id'], why=f'Lulu {st}: {j["status"].get("message")}')
    return j


def run_once(lulu):
    """One pass. A failure on one order is logged and left in its state for the next pass; it never stops the others."""
    for state, step in (('paid', build), ('built', validate), ('submit_unknown', reconcile_unknown),
                        ('validated', submit), ('submitted', poll)):
        for o in ledger.in_state(state):
            try:
                step(lulu, o)
            except Exception as e:
                log_event('order.step_error', order_id=o['id'], step=step.__name__, error=f'{type(e).__name__}: {str(e)[:300]}')
