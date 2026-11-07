"""PayPal Orders v2: the checkout that carries our order to the payment and back.

How the year and name reach the printer: they never travel through PayPal. The buyer types them on our page;
we store them under our order id; PayPal's order carries that id in `custom_id` and `invoice_id`. When the
money comes back, we ask PayPal itself what was paid (never the browser, never the webhook body alone), and
only an exact match moves the order to `paid`.

Guest cards: the order asks PayPal for `landing_page: GUEST_CHECKOUT`, which opens on the card form. Whether
PayPal offers it to a given buyer is PayPal's risk decision (see research/CHECKOUT-ROUTE.md).

Env: PAYPAL_ENV=sandbox|live, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_WEBHOOK_ID, PAYPAL_MERCHANT_ID
(optional, checked against the payee), PUBLIC_BASE (https://makeitdoshow.com), PAYPAL_API_BASE_URL (tests).
"""
import base64, os, time
from decimal import Decimal
from .common import http, HTTPError, log_event, CATALOG
from . import ledger

SERVERS = {'sandbox': 'https://api-m.sandbox.paypal.com', 'live': 'https://api-m.paypal.com'}
_tok = {}


def base():
    return os.environ.get('PAYPAL_API_BASE_URL') or SERVERS[os.environ.get('PAYPAL_ENV', 'sandbox')]


def token():
    if _tok.get('exp', 0) < time.time() + 60:
        basic = base64.b64encode(f"{os.environ['PAYPAL_CLIENT_ID']}:{os.environ['PAYPAL_CLIENT_SECRET']}".encode()).decode()
        r = http('POST', base() + '/v1/oauth2/token', headers={'Authorization': 'Basic ' + basic},
                 form={'grant_type': 'client_credentials'}, tag='paypal.token')
        _tok.update(v=r['access_token'], exp=time.time() + int(r.get('expires_in', 300)))
    return _tok['v']


def call(method, path, body=None, request_id=None, order_id=None, timeout=60):
    h = {'Authorization': 'Bearer ' + token()}
    if request_id:
        h['PayPal-Request-Id'] = request_id   # PayPal's own idempotency: a repeated create/capture returns the first result
    return http(method, base() + path, headers=h, json_body=body, tag='paypal' + path.split('?')[0], order_id=order_id, timeout=timeout)


def usd(cents):
    return f'{Decimal(cents) / 100:.2f}'


def create(order):
    """Create the PayPal order for one of ours. Returns the URL to send the buyer to."""
    p = CATALOG['products'][order['product']]
    lines = order['lines']
    items = [{'name': f"{p['title']}, {l['year']}"[:127], 'description': f"For {l['name']}, born {l['year']}"[:127],
              'sku': f"YY-{l['year']}", 'quantity': '1', 'category': 'PHYSICAL_GOODS',
              'unit_amount': {'currency_code': 'USD', 'value': usd(p['price_cents'] if i == 0 else p['extra_copy_cents'])}}
             for i, l in enumerate(lines)]
    pub = os.environ.get('PUBLIC_BASE', 'http://127.0.0.1:8115')
    body = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'reference_id': order['id'], 'custom_id': order['id'], 'invoice_id': order['id'],
            'description': 'Make It Do: printed booklet, mailed',
            'amount': {'currency_code': 'USD', 'value': usd(order['total_cents']),
                       'breakdown': {'item_total': {'currency_code': 'USD', 'value': usd(order['total_cents'])}}},
            'items': items,
        }],
        'payment_source': {'paypal': {'experience_context': {
            'brand_name': 'Make It Do', 'locale': 'en-US', 'landing_page': 'GUEST_CHECKOUT',
            'shipping_preference': 'GET_FROM_FILE', 'user_action': 'PAY_NOW',
            'return_url': f"{pub}/api/paypal/return", 'cancel_url': f"{pub}/api/paypal/cancel?order={order['id']}"}}},
    }
    r = call('POST', '/v2/checkout/orders', body, request_id='create-' + order['id'], order_id=order['id'])
    approve = next(l['href'] for l in r.get('links', []) if l.get('rel') in ('payer-action', 'approve'))
    ledger.move(order['id'], 'created', 'awaiting_payment', 'PayPal order created', processor='paypal', processor_order_id=r['id'])
    return approve


def capture(pp_order_id):
    """Called when the buyer comes back from PayPal. Idempotent: a second capture of the same order returns
    PayPal's first answer (same PayPal-Request-Id) or 422 ORDER_ALREADY_CAPTURED; either way we then settle
    from PayPal's record."""
    o = ledger.by_processor_order(pp_order_id)
    if not o:
        log_event('paypal.capture_unknown_order', pp_order_id=pp_order_id)
        return None
    try:
        call('POST', f'/v2/checkout/orders/{pp_order_id}/capture', {}, request_id='capture-' + o['id'], order_id=o['id'])
    except HTTPError as e:
        issue = str(e.body)
        if 'ORDER_ALREADY_CAPTURED' not in issue:
            log_event('paypal.capture_failed', order_id=o['id'], status=e.status)
            return settle(pp_order_id, source='return')   # still read PayPal's record; it decides
    return settle(pp_order_id, source='return')


def _first_capture(pp):
    pu = (pp.get('purchase_units') or [{}])[0]
    caps = ((pu.get('payments') or {}).get('captures') or [])
    return pu, (caps[0] if caps else None)


def settle(pp_order_id, source):
    """The one place an order becomes `paid`. Reads PayPal's own record and checks it against ours."""
    o = ledger.by_processor_order(pp_order_id)
    if not o:
        log_event('paypal.settle_unknown_order', pp_order_id=pp_order_id, source=source)
        return None
    pp = call('GET', f'/v2/checkout/orders/{pp_order_id}', order_id=o['id'])
    pu, cap = _first_capture(pp)
    if not cap:   # nobody has paid: leave the order exactly as it was (a hand-typed return URL can't poison it)
        log_event('paypal.not_paid_yet', order_id=o['id'], source=source, pp_status=pp.get('status'))
        return ledger.get(o['id'])
    why = []
    if pp.get('status') != 'COMPLETED':
        why.append(f"order status {pp.get('status')}")
    if not cap:
        why.append('no capture')
    else:
        if cap.get('status') != 'COMPLETED':
            why.append(f"capture status {cap.get('status')} ({(cap.get('status_details') or {}).get('reason', '')})")
        amt = cap.get('amount') or {}
        if amt.get('currency_code') != 'USD' or amt.get('value') != usd(o['total_cents']):
            why.append(f"amount {amt} != {usd(o['total_cents'])} USD")
        if cap.get('custom_id', pu.get('custom_id')) != o['id']:
            why.append('custom_id mismatch')
    merchant = os.environ.get('PAYPAL_MERCHANT_ID')
    if merchant and (pu.get('payee') or {}).get('merchant_id') != merchant:
        why.append('payee is not our merchant account')
    ship = pu.get('shipping') or {}
    a = ship.get('address') or {}
    if a.get('country_code') not in CATALOG['ship_to']:
        why.append(f"ships to {a.get('country_code')!r}, outside {CATALOG['ship_to']}")
    if why:
        # Not paid in a way we can print. PENDING (eCheck, review) waits for the webhook; everything else waits for a person.
        pending = cap and cap.get('status') == 'PENDING' and len(why) == 1
        ledger.move(o['id'], ('awaiting_payment', 'created'), 'payment_pending' if pending else 'held',
                    f'{source}: not printable: ' + '; '.join(why), note='; '.join(why))
        return ledger.get(o['id'])
    addr = {'name': (ship.get('name') or {}).get('full_name', ''), 'street1': a.get('address_line_1', ''),
            'street2': a.get('address_line_2', ''), 'city': a.get('admin_area_2', ''), 'state_code': a.get('admin_area_1', ''),
            'postcode': a.get('postal_code', ''), 'country_code': a.get('country_code', ''),
            'phone_number': ((pp.get('payer') or {}).get('phone') or {}).get('phone_number', {}).get('national_number', '')}
    ledger.move(o['id'], ('awaiting_payment', 'payment_pending'), 'paid', f'{source}: PayPal record verified',
                capture_id=cap['id'], paid_cents=o['total_cents'], ship=addr, email=(pp.get('payer') or {}).get('email_address'))
    return ledger.get(o['id'])


def webhook(headers, raw_body, event):
    """PayPal webhook: verify with PayPal, dedupe by event id, then settle from PayPal's record."""
    need = {'auth_algo': 'PAYPAL-AUTH-ALGO', 'cert_url': 'PAYPAL-CERT-URL', 'transmission_id': 'PAYPAL-TRANSMISSION-ID',
            'transmission_sig': 'PAYPAL-TRANSMISSION-SIG', 'transmission_time': 'PAYPAL-TRANSMISSION-TIME'}
    hdr = {k.upper(): v for k, v in headers.items()}
    if any(h not in hdr for h in need.values()):
        log_event('paypal.webhook_rejected', why='missing signature headers', event_id=event.get('id'))
        return 400, 'missing signature headers'
    v = call('POST', '/v1/notifications/verify-webhook-signature',
             {**{k: hdr[h] for k, h in need.items()}, 'webhook_id': os.environ['PAYPAL_WEBHOOK_ID'], 'webhook_event': event})
    if v.get('verification_status') != 'SUCCESS':
        log_event('paypal.webhook_rejected', why='signature not verified by PayPal', event_id=event.get('id'))
        return 400, 'not verified'
    if not ledger.seen_event('paypal', event['id'], event.get('event_type')):
        log_event('paypal.webhook_duplicate', event_id=event['id'])
        return 200, 'duplicate ignored'
    et = event.get('event_type')
    res = event.get('resource') or {}
    if et in ('PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.CAPTURE.PENDING', 'CHECKOUT.ORDER.COMPLETED'):
        pp_order = ((res.get('supplementary_data') or {}).get('related_ids') or {}).get('order_id') or res.get('id')
        settle(pp_order, source='webhook:' + et)
    elif et in ('PAYMENT.CAPTURE.REFUNDED', 'PAYMENT.CAPTURE.REVERSED', 'PAYMENT.CAPTURE.DENIED'):
        pp_order = ((res.get('supplementary_data') or {}).get('related_ids') or {}).get('order_id')
        o = ledger.by_processor_order(pp_order) if pp_order else None
        if o:   # stop it if it hasn't gone to the printer; if it has, a person decides (Lulu can cancel only while unpaid)
            ledger.move(o['id'], ('paid', 'built', 'validated', 'payment_pending', 'awaiting_payment'), 'cancelled', 'webhook:' + et)
            if o['state'] in ('submitting', 'submitted', 'submit_unknown'):
                log_event('order.alert', order_id=o['id'], why=f'{et} after submission to Lulu: cancel the Lulu job if still unpaid')
    return 200, 'ok'
