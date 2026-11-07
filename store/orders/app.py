"""The store's small server. Run: python3 -m orders.app (from store/). Standard-library WSGI, no framework.

POST /api/checkout          {product, lines:[{year,name}]}  -> {order_id, approve_url}   (or 422 {field, message})
GET  /api/paypal/return     ?token=<PayPal order id>         -> capture, verify, 303 to /thanks/?order=
GET  /api/paypal/cancel     ?order=                          -> 303 back to the product page
POST /api/paypal/webhook    PayPal event (verified with PayPal before use)
POST /api/payhip/webhook    Payhip event (recorded, never printable: see payhip.py)
GET  /api/order/<id>        {state, lines} for the thank-you page (no address, no email)
GET  /files/<token>/<name>  print files for Lulu to fetch
"""
import json, os, re, sys
from wsgiref.simple_server import make_server, WSGIRequestHandler
from .common import CATALOG, log_event, STORE
from . import ledger, personalise, paypal, payhip

ALLOW_ORIGIN = os.environ.get('SITE_ORIGIN', 'http://127.0.0.1:8115')
FILES = os.path.join(STORE, 'var', 'files')
_DELIVERY = None


def respond(start, status, body=None, headers=(), ctype='application/json'):
    data = body if isinstance(body, bytes) else json.dumps(body or {}).encode()
    start(status, [('Content-Type', ctype), ('Access-Control-Allow-Origin', ALLOW_ORIGIN),
                   ('Access-Control-Allow-Headers', 'Content-Type'), ('Cache-Control', 'no-store'), *headers])
    return [data]


def app(env, start):
    path, method = env.get('PATH_INFO', ''), env['REQUEST_METHOD']
    qs = dict(p.split('=', 1) for p in env.get('QUERY_STRING', '').split('&') if '=' in p)
    raw = env['wsgi.input'].read(int(env.get('CONTENT_LENGTH') or 0)) if method == 'POST' else b''
    if method == 'OPTIONS':
        return respond(start, '204 No Content')
    log_event('http.inbound', method=method, path=path, query=qs, body=raw[:4000].decode(errors='replace') if raw else None)

    if path == '/api/checkout' and method == 'POST':
        form_post = 'application/x-www-form-urlencoded' in env.get('CONTENT_TYPE', '')
        if form_post:   # the page's plain HTML form: works with JavaScript off
            from urllib.parse import parse_qs, quote
            f = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            lines = [{'year': f.get(f'year{i}'), 'name': f.get(f'name{i}', '')} for i in (1, 2, 3) if f.get(f'year{i}') or f.get(f'name{i}', '').strip()]
            req = {'product': f.get('product'), 'lines': lines or [{}], 'processor': f.get('processor')}
            try:
                lines = personalise.clean_lines(req['lines'], CATALOG['products'].get(req['product'] or '', {}).get('max_lines', 1))
            except personalise.Bad as e:
                return respond(start, '303 See Other', b'', [('Location', os.environ.get('SITE_BASE', '') + '/your-year/?error=' + quote(str(e)) + '#order')])
            total = personalise.price_cents(req['product'], len(lines))
            oid = ledger.new_order(req['product'], lines, total)
            o = ledger.get(oid) | {'lines': lines}
            url = payhip.checkout_url(o) if req.get('processor') == 'payhip' else paypal.create(o)
            return respond(start, '303 See Other', b'', [('Location', url)])
        try:
            req = json.loads(raw or b'{}')
            product = req.get('product')
            if product not in CATALOG['products']:
                return respond(start, '422 Unprocessable Entity', {'field': 'product', 'message': 'Unknown product.'})
            lines = personalise.clean_lines(req.get('lines'), CATALOG['products'][product]['max_lines'])
        except personalise.Bad as e:
            return respond(start, '422 Unprocessable Entity', {'message': str(e)})
        except ValueError:
            return respond(start, '400 Bad Request', {'message': 'Bad request.'})
        total = personalise.price_cents(product, len(lines))   # the server sets the price; the page can't
        oid = ledger.new_order(product, lines, total)
        o = ledger.get(oid) | {'lines': lines}
        url = payhip.checkout_url(o) if req.get('processor') == 'payhip' else paypal.create(o)
        return respond(start, '200 OK', {'order_id': oid, 'approve_url': url, 'total_cents': total})

    if path == '/api/paypal/return':
        o = paypal.capture(qs.get('token', ''))
        dest = f"/shop/thanks/?order={o['id']}" if o else '/shop/thanks/?order=unknown'
        return respond(start, '303 See Other', b'', [('Location', os.environ.get('SITE_BASE', '') + dest)])

    if path == '/api/paypal/cancel':
        oid = qs.get('order', '')
        log_event('checkout.cancelled', order_id=oid)
        return respond(start, '303 See Other', b'', [('Location', os.environ.get('SITE_BASE', '') + '/shop/your-year/?cancelled=1')])

    if path == '/api/paypal/webhook' and method == 'POST':
        hdrs = {k[5:].replace('_', '-'): v for k, v in env.items() if k.startswith('HTTP_')}
        code, msg = paypal.webhook(hdrs, raw, json.loads(raw))
        return respond(start, f'{code} {"OK" if code == 200 else "Bad Request"}', {'result': msg})

    if path == '/api/payhip/webhook' and method == 'POST':
        code, msg = payhip.webhook(json.loads(raw))
        return respond(start, f'{code} {"OK" if code == 200 else "Bad Request"}', {'result': msg})

    if path == '/api/delivery':   # Lulu's own estimate for MAIL to a mid-country address, cached; read-only call
        import time as _t, datetime as _d
        global _DELIVERY
        if not _DELIVERY or _t.time() - _DELIVERY[0] > 6 * 3600:
            try:
                from .lulu import Lulu
                spec = CATALOG['products']['youryear']
                opts = Lulu().shipping_options(spec['pod_package_id'], spec['interior_pages'], 1,
                       {'city': 'Columbus', 'country_code': 'US', 'postcode': '43215', 'state_code': 'OH', 'street1': '101 N High St', 'phone_number': '6145550100'})
                o = next(x for x in opts if x['level'] == spec['shipping_level'])
                lo, hi = _d.date.fromisoformat(o['min_delivery_date'][:10]), _d.date.fromisoformat(o['max_delivery_date'][:10])
                today = _d.date.today(); xmas = _d.date(today.year, 12, 24)
                cutoff = xmas - (hi - today)
                _DELIVERY = (_t.time(), {'from': lo.isoformat(), 'to': hi.isoformat(), 'christmas_cutoff': cutoff.isoformat() if today <= cutoff <= xmas else None,
                                         'source': 'Lulu shipping-options, ' + spec['shipping_level'], 'as_of': today.isoformat()})
            except Exception as e:
                log_event('delivery.unavailable', error=f'{type(e).__name__}: {e}')
                return respond(start, '503 Service Unavailable', {'message': 'estimate unavailable'})
        return respond(start, '200 OK', _DELIVERY[1])

    m = re.fullmatch(r'/api/order/(MID-[0-9]{6}-[0-9A-F]{8})', path)
    if m:
        o = ledger.get(m.group(1))
        if not o:
            return respond(start, '404 Not Found', {'message': 'No such order.'})
        return respond(start, '200 OK', {'order_id': o['id'], 'state': o['state'], 'lines': json.loads(o['lines']),
                                         'total_cents': o['total_cents'], 'lulu_status': o['lulu_status']})

    m = re.fullmatch(r'/files/([A-Za-z0-9_-]{20,})/([A-Za-z0-9._-]+\.pdf)', path)
    if m and method in ('GET', 'HEAD'):
        f = os.path.join(FILES, m.group(1), m.group(2))
        if os.path.isfile(f):
            log_event('file.fetched', file=m.group(2), ua=env.get('HTTP_USER_AGENT', ''))
            return respond(start, '200 OK', open(f, 'rb').read() if method == 'GET' else b'', ctype='application/pdf')
    site = os.environ.get('SERVE_SITE')   # local preview only: serve the static site on the same origin as /api
    if site and method == 'GET':
        rel = path.lstrip('/')
        f = os.path.realpath(os.path.join(site, rel, 'index.html' if path.endswith('/') else ''))
        if f.startswith(os.path.realpath(site)) and os.path.isfile(f):
            import mimetypes
            return respond(start, '200 OK', open(f, 'rb').read(), ctype=mimetypes.guess_type(f)[0] or 'application/octet-stream')
    return respond(start, '404 Not Found', {'message': 'Not found.'})


class Quiet(WSGIRequestHandler):
    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f'orders app on 127.0.0.1:{port}', flush=True)
    make_server('127.0.0.1', port, app, handler_class=Quiet).serve_forever()
