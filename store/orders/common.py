"""Shared config, logging and HTTP for the order robot.

Every outbound and inbound HTTP exchange goes through `http()` / `log_event()` so the order walk has a
complete, redacted record. Secrets never reach the log: Authorization headers, tokens, client secrets,
API keys and webhook signatures are replaced before writing.
"""
import json, os, re, time, uuid, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.dirname(HERE)
CATALOG = json.load(open(os.path.join(STORE, 'catalog.json')))
UA = 'makeitdo-orders/1.0 (+https://makeitdoshow.com)'  # Cloudflare in front of Lulu refuses Python's default UA

LOG_PATH = os.environ.get('ORDER_LOG', os.path.join(STORE, 'var', 'order-log.jsonl'))

SECRET_KEYS = re.compile(r'(authorization|access_token|refresh_token|client_secret|secret|api_?key|password|signature|transmission_sig|cert_url|id_token)', re.I)
BEARER = re.compile(r'(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+')


def redact(obj):
    if isinstance(obj, dict):
        return {k: ('[REDACTED]' if SECRET_KEYS.search(str(k)) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    if isinstance(obj, str):
        s = BEARER.sub(r'\1 [REDACTED]', obj)
        # email addresses: keep the domain, hide the person
        return re.sub(r'([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@', r'\1***@', s)
    return obj


def log_event(kind, **fields):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    rec = {'t': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + 'Z', 'kind': kind, **redact(fields)}
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(rec, default=str) + '\n')
    return rec


class HTTPError(Exception):
    def __init__(self, status, body):
        super().__init__(f'HTTP {status}: {str(body)[:300]}')
        self.status, self.body = status, body


def http(method, url, *, headers=None, json_body=None, form=None, timeout=60, tag='', order_id=None):
    """One logged HTTP call. Raises HTTPError for >=400, TimeoutError/URLError for transport failures."""
    h = {'User-Agent': UA, 'Accept': 'application/json', **(headers or {})}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode(); h['Content-Type'] = 'application/json'
    elif form is not None:
        data = urllib.parse.urlencode(form).encode(); h['Content-Type'] = 'application/x-www-form-urlencoded'
    rid = uuid.uuid4().hex[:10]
    log_event('http.request', rid=rid, tag=tag, order_id=order_id, method=method, url=url, headers=h,
              body=json_body if json_body is not None else (form or None))
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode() or '{}'
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace'); status = e.code
    except Exception as e:  # timeout, refused, DNS
        log_event('http.error', rid=rid, tag=tag, order_id=order_id, error=f'{type(e).__name__}: {e}', ms=int((time.time() - t0) * 1000))
        raise
    try:
        body = json.loads(raw)
    except ValueError:
        body = {'_raw': raw[:2000]}
    log_event('http.response', rid=rid, tag=tag, order_id=order_id, status=status, ms=int((time.time() - t0) * 1000), body=body)
    if status >= 400:
        raise HTTPError(status, body)
    return body


import urllib.parse  # noqa: E402  (used by http form encoding)
