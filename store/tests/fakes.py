"""Stand-ins for the two services we couldn't open accounts on. SIMULATED, and labelled so in every log line.

FakePayPal  — Orders v2 + webhook verification, shapes from developer.paypal.com/docs/api/orders/v2 and
              /api/webhooks/v1 (#verify-webhook-signature). The buyer's approval on PayPal's hosted page is
              stood in for by POST /_test/approve/<id>.
FakeLuluJobs — POST/GET /print-jobs/ shaped from Lulu's OpenAPI (api.lulu.com/api-docs/openapi-specs/
              openapi_public.yml, saved in research/lulu/spec.yml). `hang` mode accepts the job, then answers
              after the client has timed out: the dangerous case.
"""
import json, re, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VALID_SIG = 'fixture-signature-that-paypal-verifies'


class _H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        try:
            return json.loads(raw or b'{}')
        except ValueError:
            return {'_form': raw.decode()}

    def send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)


class FakePayPal:
    def __init__(self, port):
        self.orders, self.by_req, self.port = {}, {}, port
        fake = self

        class H(_H):
            def do_POST(self):
                b = self.body(); p = self.path; rid = self.headers.get('PayPal-Request-Id')
                if p == '/v1/oauth2/token':
                    return self.send(200, {'access_token': 'fake-' + uuid.uuid4().hex, 'token_type': 'Bearer', 'expires_in': 32400, '_simulated': True})
                if rid and rid in fake.by_req:   # PayPal idempotency: same request id, same answer
                    return self.send(*fake.by_req[rid])
                if p == '/v2/checkout/orders':
                    oid = uuid.uuid4().hex[:17].upper()
                    pu = b['purchase_units'][0]
                    fake.orders[oid] = {'id': oid, 'intent': 'CAPTURE', 'status': 'PAYER_ACTION_REQUIRED', 'purchase_units': [
                        {**pu, 'payee': {'merchant_id': 'FAKEMERCHANT01', 'email_address': 'seller@example.com'}}],
                        'payment_source': b.get('payment_source'), '_simulated': True}
                    ans = (200, {'id': oid, 'status': 'PAYER_ACTION_REQUIRED', 'payment_source': {'paypal': {}},
                                 'links': [{'href': f'http://127.0.0.1:{fake.port}/checkoutnow?token={oid}', 'rel': 'payer-action', 'method': 'GET'},
                                           {'href': f'/v2/checkout/orders/{oid}', 'rel': 'self', 'method': 'GET'}], '_simulated': True})
                    if rid:
                        fake.by_req[rid] = ans
                    return self.send(*ans)
                m = re.fullmatch(r'/v2/checkout/orders/(\w+)/capture', p)
                if m:
                    o = fake.orders.get(m.group(1))
                    if not o:
                        return self.send(404, {'name': 'RESOURCE_NOT_FOUND'})
                    if o['status'] == 'COMPLETED':
                        return self.send(422, {'name': 'UNPROCESSABLE_ENTITY', 'details': [{'issue': 'ORDER_ALREADY_CAPTURED'}]})
                    if o['status'] != 'APPROVED':
                        return self.send(422, {'name': 'UNPROCESSABLE_ENTITY', 'details': [{'issue': 'ORDER_NOT_APPROVED'}]})
                    sc = o['_scenario']; pu = o['purchase_units'][0]
                    value = pu['amount']['value'] if sc.get('outcome') != 'wrong_amount' else '1.00'
                    cap = {'id': 'CAP' + uuid.uuid4().hex[:14].upper(), 'status': 'PENDING' if sc.get('outcome') == 'pending' else 'COMPLETED',
                           'amount': {'currency_code': 'USD', 'value': value}, 'custom_id': pu['custom_id'], 'invoice_id': pu['invoice_id'],
                           'final_capture': True, 'seller_protection': {'status': 'ELIGIBLE'}}
                    if cap['status'] == 'PENDING':
                        cap['status_details'] = {'reason': 'PENDING_REVIEW'}
                    o['status'] = 'COMPLETED'
                    pu['payments'] = {'captures': [cap]}
                    pu['shipping'] = sc['shipping']
                    o['payer'] = sc['payer']
                    ans = (201, o)
                    if rid:
                        fake.by_req[rid] = ans
                    return self.send(*ans)
                if p == '/v1/notifications/verify-webhook-signature':
                    ok = b.get('transmission_sig') == VALID_SIG and b.get('webhook_id')
                    return self.send(200, {'verification_status': 'SUCCESS' if ok else 'FAILURE', '_simulated': True})
                m = re.fullmatch(r'/_test/approve/(\w+)', p)
                if m:   # stands in for the buyer paying on PayPal's hosted page
                    o = fake.orders[m.group(1)]; o['status'] = 'APPROVED'; o['_scenario'] = b
                    return self.send(200, {'approved': m.group(1)})
                self.send(404, {'name': 'NOT_FOUND', 'path': p})

            def do_GET(self):
                m = re.fullmatch(r'/v2/checkout/orders/(\w+)', self.path)
                if m and m.group(1) in fake.orders:
                    return self.send(200, fake.orders[m.group(1)])
                if self.path.startswith('/checkoutnow'):
                    page = (b'<!doctype html><meta charset=utf-8><title>SIMULATED PayPal</title><body style="font:16px system-ui;'
                            b'max-width:420px;margin:40px auto"><p style="background:#ffe9a8;padding:8px">SIMULATED: stands in for PayPal\'s '
                            b'hosted guest checkout (no PayPal sandbox account available to this job).</p><h2>Pay with debit or credit card</h2>'
                            b'<p>Card number, expiry, CVV, billing and shipping address are entered here, on PayPal, never on makeitdoshow.com.</p></body>')
                    self.send_response(200); self.send_header('Content-Type', 'text/html'); self.end_headers(); return self.wfile.write(page)
                self.send(404, {'name': 'RESOURCE_NOT_FOUND'})

        self.srv = ThreadingHTTPServer(('127.0.0.1', port), H)

    def start(self):
        threading.Thread(target=self.srv.serve_forever, daemon=True).start(); return self

    def stop(self):
        self.srv.shutdown()


class FakeLuluJobs:
    def __init__(self, port):
        self.jobs, self.validations, self.mode, self.port = {}, {}, 'normal', port
        fake = self

        class H(_H):
            def do_POST(self):
                if self.path.startswith('/auth/'):
                    return self.send(200, {'access_token': 'fake', 'expires_in': 3600, '_simulated': True})
                m = re.fullmatch(r'/validate-(interior|cover)/', self.path)
                if m:
                    b = self.body(); vid = len(fake.validations) + 1
                    fake.validations[vid] = {'id': vid, 'source_url': b['source_url'], 'status': 'VALIDATED' if m.group(1) == 'interior' else 'NORMALIZED',
                                             'page_count': 20 if m.group(1) == 'interior' else None, 'errors': [], '_simulated': True}
                    return self.send(201, {**fake.validations[vid], 'status': 'VALIDATING' if m.group(1) == 'interior' else 'NORMALIZING'})
                if self.path == '/print-jobs/':
                    b = self.body(); mode = fake.mode
                    if mode == 'drop':   # the connection dies before Lulu records anything
                        time.sleep(3); self.close_connection = True; return
                    jid = 100000 + len(fake.jobs) + 1
                    now = time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())
                    job = {'id': jid, 'external_id': b.get('external_id'), 'order_id': None, 'date_created': now,
                           'status': {'name': 'CREATED', 'message': 'Print-Job created', 'changed': now},
                           'contact_email': b.get('contact_email'), 'shipping_level': b.get('shipping_level'),
                           'shipping_address': b.get('shipping_address'),
                           'line_items': [{'id': jid * 10 + i, 'external_id': li.get('external_id'), 'title': li.get('title'), 'quantity': li.get('quantity'),
                                           'pod_package_id': li['printable_normalization']['pod_package_id'],
                                           'status': {'name': 'CREATED', 'messages': {}},
                                           'printable_normalization': li['printable_normalization']} for i, li in enumerate(b.get('line_items', []))],
                           'costs': None, 'estimated_shipping_dates': None, '_simulated': True}
                    fake.jobs[jid] = job
                    if mode == 'hang':   # Lulu has it, but the answer arrives after the client gave up
                        time.sleep(4)
                    return self.send(201, job)
                self.send(404, {'detail': 'Not found.'})

            def do_GET(self):
                m = re.fullmatch(r'/validate-(?:interior|cover)/(\d+)/', self.path)
                if m:
                    return self.send(200, fake.validations[int(m.group(1))])
                m = re.fullmatch(r'/print-jobs/\?search=([^&]+).*', self.path)
                if m:
                    res = [j for j in fake.jobs.values() if m.group(1) in (j['external_id'] or '')]
                    return self.send(200, {'count': len(res), 'next': None, 'previous': None, 'results': res, '_simulated': True})
                m = re.fullmatch(r'/print-jobs/(\d+)/', self.path)
                if m and int(m.group(1)) in fake.jobs:
                    j = fake.jobs[int(m.group(1))]
                    if j['status']['name'] == 'CREATED':   # sandbox jobs wait for payment with a test card
                        j['status'] = {'name': 'UNPAID', 'message': 'Print-Job can be paid', 'changed': j['date_created']}
                    return self.send(200, j)
                self.send(404, {'detail': 'Not found.'})

        self.srv = ThreadingHTTPServer(('127.0.0.1', port), H)

    def start(self):
        threading.Thread(target=self.srv.serve_forever, daemon=True).start(); return self

    def stop(self):
        self.srv.shutdown()
