"""Payhip, the fallback checkout. Built to Payhip's documented webhook (help.payhip.com/article/115, updated
2026-09-29) and checkout-link metadata (article/126, updated 2026-07-21: "set some metadata on the checkout page
link, which is then passed through to your webhooks payload").

How the name and year reach the printer: they stay with us, under our order id. The buyer is sent to
`payhip.com/buy?link=<KEY>&metadata[order_id]=<our id>`; the paid webhook brings our id back.

What's weaker than the PayPal route, from Payhip's own docs:
  * `signature` is sha256(apiKey): a fixed shared secret sent with every event, not a signature of the body.
    It proves the sender knows our key; it can't prove the body wasn't changed or replayed.
  * There is no orders API, so we can't ask Payhip to confirm a sale the way we ask PayPal.
  * The shipping-address fields are documented only indirectly (Payhip's Printful-via-Pabbly guide, 2024);
    a 100%-off test order must confirm their names before this route is switched on. Until a payload carries
    a complete US address, the order is held for a person, never printed.
Env: PAYHIP_API_KEY, PAYHIP_LINK_1 / _2 / _3 (checkout-link keys for one, two, three booklets).
"""
import hashlib, hmac, os
from .common import log_event, CATALOG
from . import ledger


def checkout_url(order):
    key = os.environ.get(f"PAYHIP_LINK_{len(order['lines'])}", 'LINKKEY')
    ledger.move(order['id'], 'created', 'awaiting_payment', 'Payhip checkout link issued', processor='payhip', processor_order_id='payhip:' + order['id'])
    return f"https://payhip.com/buy?link={key}&metadata[order_id]={order['id']}"


def _address(ev):
    a = ev.get('shipping_address') or ev.get('shipping') or {}
    if not isinstance(a, dict):
        return None
    g = lambda *ks: next((str(a[k]).strip() for k in ks if a.get(k)), '')
    addr = {'name': g('name', 'full_name'), 'street1': g('line1', 'address_line_1', 'address1'), 'street2': g('line2', 'address_line_2', 'address2'),
            'city': g('city'), 'state_code': g('state_code', 'state'), 'postcode': g('zipcode', 'zip', 'postal_code', 'postcode'),
            'country_code': g('country_code', 'country')}
    need = ('name', 'street1', 'city', 'state_code', 'postcode', 'country_code')
    return addr if all(addr[k] for k in need) else None


def webhook(event):
    want = hashlib.sha256(os.environ.get('PAYHIP_API_KEY', '').encode()).hexdigest()
    if not os.environ.get('PAYHIP_API_KEY') or not hmac.compare_digest(str(event.get('signature', '')), want):
        log_event('payhip.webhook_rejected', why='signature != sha256(api key)', event_id=event.get('id'))
        return 400, 'bad signature'
    if event.get('type') != 'paid':
        return 200, 'ignored'
    if not ledger.seen_event('payhip', str(event.get('id')), 'paid'):
        log_event('payhip.webhook_duplicate', event_id=event.get('id'))
        return 200, 'duplicate ignored'
    oid = (event.get('metadata') or {}).get('order_id')
    o = ledger.get(oid) if oid else None
    if not o:
        log_event('payhip.sale_unlinked', event_id=event.get('id'), why='no metadata.order_id we know: a person must match it by hand')
        return 200, 'recorded; needs a person'
    why = []
    if event.get('currency') != 'USD':
        why.append(f"currency {event.get('currency')}")
    if int(event.get('price') or 0) < o['total_cents']:      # Payhip may add US sales tax on top, never less
        why.append(f"paid {event.get('price')} < {o['total_cents']} cents")
    addr = _address(event)
    if not addr:
        why.append('no complete shipping address in the payload')
    elif addr['country_code'] not in CATALOG['ship_to'] + ['United States']:
        why.append(f"ships to {addr['country_code']}")
    if why:
        ledger.move(o['id'], 'awaiting_payment', 'held', 'payhip: not printable: ' + '; '.join(why), note='; '.join(why))
        return 200, 'recorded; held'
    addr['country_code'] = 'US'
    ledger.move(o['id'], 'awaiting_payment', 'paid', 'payhip: paid webhook matched our order (static-secret auth)',
                capture_id='payhip:' + str(event['id']), paid_cents=int(event['price']), ship=addr, email=event.get('email'))
    return 200, 'ok'
