"""Local preview of the whole buyer path: site + order server on :8787 (same origin), PayPal stand-in on :8788.
python3 dev_preview.py /path/to/built/site   (SIMULATED PayPal; no real payment)"""
import os, sys, time, threading
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.update(SERVE_SITE=sys.argv[1], PAYPAL_API_BASE_URL='http://127.0.0.1:8788', PAYPAL_CLIENT_ID='fake', PAYPAL_CLIENT_SECRET='fake',
                  PAYPAL_WEBHOOK_ID='WH-FAKE', PUBLIC_BASE='http://127.0.0.1:8787', ORDER_DB=os.path.join(HERE, 'var', 'preview.sqlite'),
                  ORDER_LOG=os.path.join(HERE, 'var', 'preview-log.jsonl'))
from tests.fakes import FakePayPal
from orders.app import app, Quiet
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
class TS(ThreadingMixIn, WSGIServer): daemon_threads = True
FakePayPal(8788).start()
print('preview on http://127.0.0.1:8787/your-year/', flush=True)
make_server('127.0.0.1', 8787, app, server_class=TS, handler_class=Quiet).serve_forever()
