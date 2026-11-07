#!/usr/bin/env python3
"""The order walk: buy -> order data -> named file -> Lulu file validation -> print job -> status, plus the
dangerous cases. Writes everything to OUT (default ../../order-walk).

Which parts are real:
  REAL       our store server, ledger, name/year rules, the PDF build and local preflight, the public file URL
             (Cloudflare quick tunnel), Lulu's file validation (production API, read-only validation endpoints)
  SIMULATED  PayPal (FakePayPal, shaped from PayPal's docs) and Lulu print-job create/read (FakeLuluJobs, shaped
             from Lulu's OpenAPI), because no PayPal or Lulu *sandbox* account could be opened by this job.
With LULU_ENV=sandbox and sandbox keys in the environment, `--lulu-jobs sandbox` sends jobs to Lulu's sandbox instead.

Usage: python3 walk.py [--out DIR] [--lulu-validate live|fake] [--lulu-jobs fake|sandbox]
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, threading, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.join(HERE, '..', '..', 'order-walk'))
ap.add_argument('--lulu-validate', default='live', choices=['live', 'fake'])
ap.add_argument('--lulu-jobs', default='fake', choices=['fake', 'sandbox'])
ap.add_argument('--tunnel', default=os.path.join(HERE, '..', '..', 'tools', 'bin', 'cloudflared'))
A = ap.parse_args()
OUT = os.path.abspath(A.out)
shutil.rmtree(os.path.join(HERE, 'var', 'files'), ignore_errors=True)
for f in ('orders.sqlite', 'order-log.jsonl'):
    if os.path.exists(os.path.join(HERE, 'var', f)):
        os.remove(os.path.join(HERE, 'var', f))
os.makedirs(OUT, exist_ok=True)

APP, PP, LJ = 8797, 8798, 8799
os.environ.update(PAYPAL_API_BASE_URL=f'http://127.0.0.1:{PP}', PAYPAL_CLIENT_ID='fake', PAYPAL_CLIENT_SECRET='fake',
                  PAYPAL_WEBHOOK_ID='WH-FAKE', PAYPAL_MERCHANT_ID='FAKEMERCHANT01', PUBLIC_BASE=f'http://127.0.0.1:{APP}',
                  PAYHIP_API_KEY='fake-payhip-key', LULU_CONTACT_EMAIL='orders@makeitdoshow.com',
                  LULU_CONTACT_PHONE='+1 614 555 0100', UNKNOWN_GRACE_S='2')

from orders import ledger, fulfil, lulu as lulu_mod, common, pdfbuild   # noqa: E402
from orders.app import app                                              # noqa: E402
from tests.fakes import FakePayPal, FakeLuluJobs, VALID_SIG              # noqa: E402
from wsgiref.simple_server import make_server                            # noqa: E402
from orders.app import Quiet                                             # noqa: E402

RESULTS = []


def check(name, cond, detail=''):
    RESULTS.append({'check': name, 'pass': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (f' — {detail}' if detail else ''), flush=True)


def req(method, path, body=None, headers=None, base=f'http://127.0.0.1:{APP}'):
    r = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                               headers={'Content-Type': 'application/json', **(headers or {})})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(NoRedirect)
    try:
        with op.open(r, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


# --- servers ----------------------------------------------------------------------------------------------
srv = make_server('127.0.0.1', APP, app, handler_class=Quiet)
threading.Thread(target=srv.serve_forever, daemon=True).start()
pp = FakePayPal(PP).start()
lj = FakeLuluJobs(LJ).start()

public = None
if A.lulu_validate == 'live':
    tl = open(os.path.join(OUT, 'tunnel.log'), 'w')
    tun = subprocess.Popen([A.tunnel, 'tunnel', '--no-autoupdate', '--url', f'http://127.0.0.1:{APP}'], stdout=tl, stderr=subprocess.STDOUT)
    for _ in range(60):
        time.sleep(1)
        m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', open(tl.name).read())
        if m:
            public = m.group(0); break
    check('public file URL (Cloudflare quick tunnel) is up', public, public or 'no tunnel')
    time.sleep(8)
os.environ['PUBLIC_FILES_BASE'] = public or f'http://127.0.0.1:{APP}'


class SplitLulu:
    """File validation on Lulu for real (read-only); print jobs on the stand-in or the sandbox."""
    def __init__(self):
        if A.lulu_validate == 'live':
            env = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/.local/share/agent-tools/secrets/lulu.env')) if '=' in l)
            self.v = lulu_mod.Lulu(env='production', key=env['LULU_CLIENT_KEY'], secret=env['LULU_CLIENT_SECRET'])
        if A.lulu_jobs == 'sandbox':
            self.j = lulu_mod.Lulu(env='sandbox')
        else:
            os.environ['LULU_API_BASE_URL'] = f'http://127.0.0.1:{LJ}'
            self.j = lulu_mod.Lulu(env='sandbox', key='fake', secret='fake')
            del os.environ['LULU_API_BASE_URL']
        if A.lulu_validate != 'live':
            self.v = self.j

    def __getattr__(self, k):
        return getattr(self.v if k.startswith('validate') or k in ('wait_validation', 'get_validation') else self.j, k)


LULU = SplitLulu()
SHIP = {'name': {'full_name': 'Margaret Test'}, 'address': {'address_line_1': '101 N High St', 'admin_area_2': 'Columbus',
        'admin_area_1': 'OH', 'postal_code': '43215', 'country_code': 'US'}}
PAYER = {'email_address': 'carol.test@example.com', 'name': {'given_name': 'Carol', 'surname': 'Test'}}


def buy(lines, outcome='completed', approve=True):
    st, h, b = req('POST', '/api/checkout', {'product': 'youryear', 'lines': lines})
    if st != 200:
        return st, json.loads(b), None
    r = json.loads(b)
    pp_id = re.search(r'token=(\w+)', r['approve_url']).group(1)
    if approve:
        req('POST', f'/_test/approve/{pp_id}', {'outcome': outcome, 'shipping': SHIP, 'payer': PAYER}, base=f'http://127.0.0.1:{PP}')
    return st, r, pp_id


def webhook_event(pp_id, cap_id, etype='PAYMENT.CAPTURE.COMPLETED', eid=None):
    return {'id': eid or 'WH-' + cap_id, 'event_type': etype, 'resource_type': 'capture',
            'resource': {'id': cap_id, 'status': 'COMPLETED', 'supplementary_data': {'related_ids': {'order_id': pp_id}}}}


def sig(valid=True):
    return {'PAYPAL-AUTH-ALGO': 'SHA256withRSA', 'PAYPAL-CERT-URL': 'https://api.paypal.com/v1/notifications/certs/CERT-fixture',
            'PAYPAL-TRANSMISSION-ID': 'tx-' + str(time.time()), 'PAYPAL-TRANSMISSION-TIME': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'PAYPAL-TRANSMISSION-SIG': VALID_SIG if valid else 'forged'}


def jobs_for(oid):
    return [j for j in lj.jobs.values() if j['external_id'] == oid] if A.lulu_jobs == 'fake' else LULU.j.find_by_external_id(oid)


records = {}


def settle_validation(oid, limit=900):
    t0 = time.time()
    while ledger.get(oid)['state'] == 'built' and time.time() - t0 < limit:
        fulfil.validate(LULU, ledger.get(oid))
        if ledger.get(oid)['state'] == 'built':
            time.sleep(15)


def run_until(oid, states=('submitted', 'held'), limit=900):
    t0 = time.time()
    while ledger.get(oid)['state'] not in states and time.time() - t0 < limit:
        fulfil.run_once(LULU)
        if ledger.get(oid)['state'] not in states:
            time.sleep(15)

# ===== 1. The happy path, two booklets in one envelope ======================================================
print('\n== 1. happy path')
st, r, pp1 = buy([{'year': 1953, 'name': 'Margaret'}, {'year': 1951, 'name': "Walter O'Neill"}])
oid = r['order_id']
check('checkout accepted and priced by the server', st == 200 and r['total_cents'] == 4900 + 2900, f"{oid} total {r['total_cents']}")
check('nothing paid before the buyer returns', ledger.get(oid)['state'] == 'awaiting_payment')
fulfil.run_once(LULU)
check('robot does nothing for an unpaid order', ledger.get(oid)['state'] == 'awaiting_payment' and not jobs_for(oid))
st, h, _ = req('GET', f'/api/paypal/return?token={pp1}')
check('return from PayPal: capture verified, order paid', ledger.get(oid)['state'] == 'paid', f"303 -> {h.get('Location')}")
run_until(oid)
o = ledger.get(oid)
check('files built, Lulu validated, job created', o['state'] == 'submitted' and o['lulu_job_id'], f"state {o['state']} job {o['lulu_job_id']} note {o['note']}")
for _ in range(2):
    fulfil.run_once(LULU)
o = ledger.get(oid)
check('status read back from the print job', o['lulu_status'] in ('UNPAID', 'CREATED', 'PRODUCTION_DELAYED'), o['lulu_status'])
records['happy'] = oid

# ===== 2. Same payment event twice (return twice + webhook twice + a fresh webhook id for the same capture) ==
print('\n== 2. duplicate payment events')
cap = ledger.get(oid)['capture_id']
for _ in range(2):
    req('GET', f'/api/paypal/return?token={pp1}')
ev = webhook_event(pp1, cap)
s1 = req('POST', '/api/paypal/webhook', ev, sig())
s2 = req('POST', '/api/paypal/webhook', ev, sig())
s3 = req('POST', '/api/paypal/webhook', webhook_event(pp1, cap, eid='WH-different-id-same-capture'), sig())
fulfil.run_once(LULU)
check('re-delivered webhook recognised as duplicate', b'duplicate' in s2[2], s2[2].decode())
check('one order, one print job after 2 returns + 3 webhooks', len(jobs_for(oid)) == 1, f'{len(jobs_for(oid))} job(s)')

# ===== 3. Payment not verified =====================================================================
print('\n== 3. unverified payment')
st, r3, pp3 = buy([{'year': 1960, 'name': 'Dorothy'}], approve=False)
o3 = r3['order_id']
s = req('POST', '/api/paypal/webhook', webhook_event(pp3, 'CAPFORGED'), sig(valid=False))
check('forged webhook (bad signature) rejected', s[0] == 400, s[2].decode())
req('GET', f'/api/paypal/return?token={pp3}')   # buyer never approved: someone hits the return URL by hand
fulfil.run_once(LULU)
check('return URL without an approved payment does not pay the order', ledger.get(o3)['state'] != 'paid' and not jobs_for(o3), ledger.get(o3)['state'])
st, r4, pp4 = buy([{'year': 1947, 'name': 'Ruth'}], outcome='pending')
req('GET', f'/api/paypal/return?token={pp4}')
fulfil.run_once(LULU)
check('capture PENDING (eCheck/review) waits; nothing prints', ledger.get(r4['order_id'])['state'] == 'payment_pending' and not jobs_for(r4['order_id']), ledger.get(r4['order_id'])['state'])
st, r5, pp5 = buy([{'year': 1958, 'name': 'Joan'}], outcome='wrong_amount')
req('GET', f'/api/paypal/return?token={pp5}')
fulfil.run_once(LULU)
check('captured amount differs from the order: held, not printed', ledger.get(r5['order_id'])['state'] == 'held' and not jobs_for(r5['order_id']), ledger.get(r5['order_id'])['note'])
ph = {'id': 'ZGjVj5x4GN-unlinked', 'email': 'johndoe@example.com', 'currency': 'USD', 'price': 4900, 'items': [{'product_id': '2804256', 'quantity': '1', 'has_variant': True}],
      'payment_type': 'card', 'type': 'paid', 'date': int(time.time())}
import hashlib as _h
s_bad = req('POST', '/api/payhip/webhook', {**ph, 'signature': 'nope'})
s_ok = req('POST', '/api/payhip/webhook', {**ph, 'signature': _h.sha256(b'fake-payhip-key').hexdigest()})
check('Payhip paid webhook (documented shape) is recorded but never printable', s_bad[0] == 400 and b'needs a person' in s_ok[2], s_ok[2].decode())

# ===== 4. Bad personalisation =======================================================================
print('\n== 4. bad personalisation')
for lines, why in [([{'year': 1953, 'name': ''}], 'empty name'), ([{'year': 1953, 'name': '   '}], 'blank name'),
                   ([{'year': 1929, 'name': 'Ann'}], 'year 1929'), ([{'year': 1975, 'name': 'Ann'}], 'year 1975 (sheet only)'),
                   ([{'year': 'nineteen', 'name': 'Ann'}], 'year not a number'), ([{'year': 1953, 'name': 'Ann 🎂'}], 'emoji'),
                   ([{'year': 1953, 'name': 'Ĉarlo'}], 'glyph not in the cover type'),
                   ([{'year': 1953, 'name': 'Maximiliana Bartholomew Jr'}], 'name over 24'),
                   ([{'year': 1953, 'name': 'A'}] * 4, 'four booklets in one envelope')]:
    st, b, _ = buy(lines)
    check(f'refused before payment: {why}', st == 422, b.get('message') if isinstance(b, dict) else b)
st, r6, pp6 = buy([{'year': 1955, 'name': 'Betty'}])
req('GET', f'/api/paypal/return?token={pp6}')
with ledger.connect() as c:   # someone edits the ledger after payment
    c.execute('UPDATE orders SET lines=? WHERE id=?', (json.dumps([{'year': 1999, 'name': ''}]), r6['order_id']))
fulfil.run_once(LULU)
check('order tampered after payment is held at build, not printed', ledger.get(r6['order_id'])['state'] == 'held' and not jobs_for(r6['order_id']), ledger.get(r6['order_id'])['note'])

# ===== 5. Timeout mid-submission ======================================================================
print('\n== 5. timeout mid-submission')
if A.lulu_jobs == 'fake':
    st, r7, pp7 = buy([{'year': 1949, 'name': 'Evelyn'}])
    req('GET', f'/api/paypal/return?token={pp7}')
    o7 = r7['order_id']
    fulfil.build(LULU, ledger.get(o7)); settle_validation(o7)
    lj.mode = 'hang'                                   # Lulu takes the job, answers after we gave up
    fulfil.submit(LULU, ledger.get(o7), timeout=1)
    lj.mode = 'normal'
    check('no answer from Lulu -> submit_unknown, not resent', ledger.get(o7)['state'] == 'submit_unknown', ledger.get(o7)['state'])
    time.sleep(1)
    fulfil.run_once(LULU)
    check('reconciled by external_id: adopts the job Lulu already has; one job only',
          ledger.get(o7)['state'] == 'submitted' and len(jobs_for(o7)) == 1, f"{ledger.get(o7)['state']}, {len(jobs_for(o7))} job(s)")
    st, r8, pp8 = buy([{'year': 1966, 'name': 'Linda'}])
    req('GET', f'/api/paypal/return?token={pp8}')
    o8 = r8['order_id']
    fulfil.build(LULU, ledger.get(o8)); settle_validation(o8)
    lj.mode = 'drop'                                   # connection dies before Lulu records anything
    fulfil.submit(LULU, ledger.get(o8), timeout=1)
    lj.mode = 'normal'
    fulfil.run_once(LULU)
    check('inside the grace period: still waiting, nothing resent', ledger.get(o8)['state'] == 'submit_unknown' and not jobs_for(o8), ledger.get(o8)['state'])
    time.sleep(3)
    fulfil.run_once(LULU); fulfil.run_once(LULU)
    check('after the grace period with no Lulu job: sent once', ledger.get(o8)['state'] == 'submitted' and len(jobs_for(o8)) == 1, f"{len(jobs_for(o8))} job(s)")
    records['timeout_adopted'], records['timeout_resent'] = o7, o8

# ===== 6. The Payhip route (metadata carries our order id) ==============================================
print('\n== 6. Payhip route')
st, _hd, b = req('POST', '/api/checkout', {'product': 'youryear', 'processor': 'payhip', 'lines': [{'year': 1962, 'name': 'Patricia'}]})
r9 = json.loads(b); o9 = r9['order_id']
check('Payhip checkout link carries our order id as metadata', f'metadata[order_id]={o9}' in r9['approve_url'], r9['approve_url'])
key = _h.sha256(b'fake-payhip-key').hexdigest()
addr = {'name': 'Patricia Test', 'line1': '101 N High St', 'city': 'Columbus', 'state_code': 'OH', 'zipcode': '43215', 'country_code': 'US'}
ev9 = {'id': 'PH-' + o9, 'email': 'pat.test@example.com', 'currency': 'USD', 'price': 4900, 'type': 'paid', 'signature': key,
       'items': [{'product_id': '2804256', 'quantity': '1'}], 'metadata': {'order_id': o9}, 'shipping_address': addr}
req('POST', '/api/payhip/webhook', {**ev9, 'signature': 'forged'})
check('Payhip event with the wrong secret does not pay', ledger.get(o9)['state'] == 'awaiting_payment')
req('POST', '/api/payhip/webhook', ev9); req('POST', '/api/payhip/webhook', ev9)
run_until(o9)
check('Payhip paid event (shape from docs + metadata) -> named file -> one job', ledger.get(o9)['state'] == 'submitted' and len(jobs_for(o9)) == 1,
      f"{ledger.get(o9)['state']}, {len(jobs_for(o9))} job(s)")
st, _hd, b = req('POST', '/api/checkout', {'product': 'youryear', 'processor': 'payhip', 'lines': [{'year': 1940, 'name': 'Helen'}]})
o10 = json.loads(b)['order_id']
req('POST', '/api/payhip/webhook', {**ev9, 'id': 'PH-' + o10, 'metadata': {'order_id': o10}, 'shipping_address': None})
fulfil.run_once(LULU)
check('Payhip event without a shipping address is held, not printed', ledger.get(o10)['state'] == 'held' and not jobs_for(o10), ledger.get(o10)['note'])
records['payhip'] = o9

# ===== write the record ============================================================================
os.makedirs(os.path.join(OUT, 'pdfs'), exist_ok=True); os.makedirs(os.path.join(OUT, 'proofs'), exist_ok=True)
table = []
with ledger.connect() as c:
    allo = [dict(x) for x in c.execute('SELECT * FROM orders ORDER BY created')]
for o in allo:
    fs = ledger.files(o['id'])
    for i, l in enumerate(json.loads(o['lines'])):
        cov = next((f for f in fs if f['kind'] == 'cover' and f['line_no'] == i + 1), None)
        inn = next((f for f in fs if f['kind'] == 'interior' and f['line_no'] == i + 1), None)
        if cov and cov['path'] and os.path.exists(cov['path']):
            shutil.copy(cov['path'], os.path.join(OUT, 'pdfs'))
            pdfbuild.proof_png(cov['path'], os.path.join(OUT, 'proofs', os.path.basename(cov['path']).replace('.pdf', '-front.png')))
        table.append({'order_id': o['id'], 'state': o['state'], 'sku': 'youryear / 0850X1100FCPRESS080CW444MXX', 'line': i + 1,
                      'year': l.get('year'), 'name': l.get('name'), 'print_spec': common.CATALOG['products']['youryear']['spec'],
                      'cover_sha256': cov and cov['sha256'], 'interior_sha256': inn and inn['sha256'],
                      'lulu_cover_validation': cov and f"{cov['validation_id']} {cov['validation_status']}",
                      'lulu_interior_validation': inn and f"{inn['validation_id']} {inn['validation_status']}",
                      'cover_preflight': cov and json.loads(cov['detail']) if cov and cov['detail'] else None,
                      'job_id': o['lulu_job_id'], 'job_status_read_back': o['lulu_status'], 'note': o['note'],
                      'history': [f"{h['frm']}->{h['too']}: {h['why']}" for h in ledger.history(o['id'])]})
json.dump({'simulated': ['PayPal (FakePayPal)', 'Lulu print-job create/read (FakeLuluJobs)' if A.lulu_jobs == 'fake' else None],
           'real': ['store server', 'ledger', 'personalisation rules', 'PDF build + preflight', 'public file URL',
                    'Lulu file validation (production, read-only)' if A.lulu_validate == 'live' else None],
           'checks': RESULTS, 'orders': table}, open(os.path.join(OUT, 'walk-record.json'), 'w'), indent=1, default=str)
shutil.copy(common.LOG_PATH, os.path.join(OUT, 'order-log.redacted.jsonl'))
print(f"\n{sum(r['pass'] for r in RESULTS)}/{len(RESULTS)} checks passed; record in {OUT}")
if A.lulu_validate == 'live':
    tun.terminate()
srv.shutdown(); pp.stop(); lj.stop()
