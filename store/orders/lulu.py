"""Lulu Print API client.

Env: LULU_ENV=sandbox|production, LULU_CLIENT_KEY, LULU_CLIENT_SECRET, LULU_CONTACT_PHONE (Lulu refuses a job
without a phone on the account or the address), LULU_CONTACT_EMAIL.

Guard: creating a print job against production requires LULU_ALLOW_LIVE_PRINT=yes-print-and-charge. Nothing in
this repo sets it; the owner sets it when he goes live. Quotes, cover dimensions and file validation are free,
read-only calls and are allowed on either server.
"""
import base64, os, time
from .common import http, HTTPError, log_event

SERVERS = {'sandbox': 'https://api.sandbox.lulu.com', 'production': 'https://api.lulu.com'}


class LiveRefused(RuntimeError):
    pass


class Lulu:
    def __init__(self, env=None, key=None, secret=None):
        self.env = env or os.environ.get('LULU_ENV', 'sandbox')
        self.base = os.environ.get('LULU_API_BASE_URL') or SERVERS[self.env]
        self.key = key or os.environ['LULU_CLIENT_KEY']
        self.secret = secret or os.environ['LULU_CLIENT_SECRET']
        self._tok, self._exp = None, 0

    def _token(self):
        if not self._tok or time.time() > self._exp - 60:
            basic = base64.b64encode(f'{self.key}:{self.secret}'.encode()).decode()
            r = http('POST', self.base + '/auth/realms/glasstree/protocol/openid-connect/token',
                     headers={'Authorization': 'Basic ' + basic}, form={'grant_type': 'client_credentials'}, tag=f'lulu.{self.env}.token')
            self._tok, self._exp = r['access_token'], time.time() + int(r.get('expires_in', 300))
        return self._tok

    def call(self, method, path, body=None, order_id=None, timeout=60):
        if method == 'POST' and path.rstrip('/') == '/print-jobs' and self.env != 'sandbox' \
                and os.environ.get('LULU_ALLOW_LIVE_PRINT') != 'yes-print-and-charge':
            log_event('lulu.live_refused', order_id=order_id, path=path)
            raise LiveRefused('live print job refused: LULU_ALLOW_LIVE_PRINT not set')
        return http(method, self.base + path, headers={'Authorization': 'Bearer ' + self._token(), 'Cache-Control': 'no-cache'},
                    json_body=body, tag=f'lulu.{self.env}{path.split("?")[0]}', order_id=order_id, timeout=timeout)

    # --- free, read-only ------------------------------------------------------------------------------
    def quote(self, sku, pages, qty, address, level='MAIL', lines=None):
        items = lines or [{'pod_package_id': sku, 'page_count': pages, 'quantity': qty}]
        return self.call('POST', '/print-job-cost-calculations/', {'line_items': items, 'shipping_address': address, 'shipping_option': level})

    def shipping_options(self, sku, pages, qty, address):
        return self.call('POST', '/shipping-options/', {'line_items': [{'pod_package_id': sku, 'page_count': pages, 'quantity': qty}],
                                                         'shipping_address': address})

    def cover_dimensions(self, sku, pages):
        return self.call('POST', '/cover-dimensions/', {'pod_package_id': sku, 'interior_page_count': pages, 'unit': 'pt'})

    def validate_interior(self, url, sku, order_id=None):
        return self.call('POST', '/validate-interior/', {'source_url': url, 'pod_package_id': sku}, order_id=order_id)

    def validate_cover(self, url, sku, pages, order_id=None):
        return self.call('POST', '/validate-cover/', {'source_url': url, 'pod_package_id': sku, 'interior_page_count': pages}, order_id=order_id)

    def get_validation(self, kind, vid, order_id=None):
        return self.call('GET', f'/validate-{kind}/{vid}/', order_id=order_id)

    def wait_validation(self, kind, vid, order_id=None, tries=40, every=6):
        for _ in range(tries):
            r = self.call('GET', f'/validate-{kind}/{vid}/', order_id=order_id)
            if r.get('status') not in ('VALIDATING', 'NORMALIZING', None):
                return r
            time.sleep(every)
        return r

    # --- print jobs ------------------------------------------------------------------------------------
    def find_by_external_id(self, external_id, order_id=None):
        """Lulu's list endpoint searches external_id; used to settle a submission whose answer never came back."""
        r = self.call('GET', f'/print-jobs/?search={external_id}&page_size=20', order_id=order_id)
        return [j for j in r.get('results', []) if j.get('external_id') == external_id]

    def create_job(self, order, lines, cover_urls, interior_urls, address, contact_email, sku, level, timeout=60):
        body = {
            'external_id': order['id'],
            'contact_email': contact_email,
            'shipping_level': level,
            'shipping_address': address,
            'line_items': [{
                'external_id': f"{order['id']}-{i + 1}",
                'title': f"Your Year, in Color: {l['year']}, for {l['name']}",
                'quantity': 1,
                'printable_normalization': {'pod_package_id': sku, 'cover': {'source_url': cover_urls[i]},
                                            'interior': {'source_url': interior_urls[i]}},
            } for i, l in enumerate(lines)],
        }
        return self.call('POST', '/print-jobs/', body, order_id=order['id'], timeout=timeout)

    def job(self, job_id, order_id=None):
        return self.call('GET', f'/print-jobs/{job_id}/', order_id=order_id)
