# The store's order robot (store-1108)

The pages (`/your-year/`, `/shop/`, `/shop/thanks/`) are static and built by `scripts/build.py` → `scripts/store_pages.py`.
They take no payment and hold no secrets. With `commerce_enabled: false` in `data/site.json` (the state in this branch), the buy
button is replaced by "Orders open soon".

This folder is the small server that takes the order, sends the buyer to the payment page, checks the payment with the
processor itself, builds her named cover and sends the job to Lulu.

```
buyer ── /your-year/ form (year, name) ──► POST /api/checkout ─► our order MID-yymmdd-XXXXXXXX (name/year stay here)
      ◄── 303 to PayPal (custom_id = our id; card form first) ◄─┘
PayPal ── return ──► /api/paypal/return ─► capture ─► GET order from PayPal ─► exact match? ─► state "paid"
PayPal ── webhook ─► verified by PayPal's verify-webhook-signature ─► same check (dedup by event id, capture id UNIQUE)
robot  ── paid → build cover (Chromium) + preflight → public file URL → Lulu validate (non-blocking)
          → search Lulu for our external_id → create job → read status
```

Fallback checkout: Payhip, with `metadata[order_id]` on the checkout link (`orders/payhip.py`). It is weaker, and the docstring says why.

## Run the walk (no cost)
```
cd store && python3 walk.py --lulu-validate live     # real Lulu file validation (read-only), stand-ins for PayPal + Lulu jobs
cd store && python3 walk.py --lulu-validate fake     # fully offline
LULU_ENV=sandbox LULU_CLIENT_KEY=… LULU_CLIENT_SECRET=… python3 walk.py --lulu-jobs sandbox   # once a sandbox account exists
python3 dev_preview.py /path/to/commerce-on/build    # the whole buyer path in a browser, PayPal simulated
```
`walk.py` needs `var/interiors/your-year-YYYY-interior.pdf` (41 files, 26 MB, not in git; symlink the folder) and
`../../tools/bin/cloudflared` for the public file URL.

## Environment (production)
| var | what |
|---|---|
| `PAYPAL_ENV=live`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | REST app on the owner's PayPal Business account |
| `PAYPAL_WEBHOOK_ID`, `PAYPAL_MERCHANT_ID` | webhook for `PAYMENT.CAPTURE.*`; payee check |
| `PUBLIC_BASE` | `https://makeitdoshow.com` (serve `/api/*` on the same origin as the site) |
| `LULU_ENV=production`, `LULU_CLIENT_KEY`, `LULU_CLIENT_SECRET` | print account with a funding card |
| `LULU_ALLOW_LIVE_PRINT=yes-print-and-charge` | **required to create a real print job**; nothing here sets it |
| `LULU_CONTACT_EMAIL`, `LULU_CONTACT_PHONE` | Lulu refuses a job without a phone |
| `PUBLIC_FILES_BASE` | where Lulu fetches the PDFs. Replace `fulfil.publish()` with private-bucket signed URLs before real names |
| `INTERIOR_DIR`, `ORDER_DB`, `ORDER_LOG` | interiors, SQLite ledger, redacted JSONL log |

Run `python3 -m orders.app 8787` behind the site's domain at `/api/*`, and run `orders.fulfil.run_once()` every few minutes.
The host needs Python 3.12, Playwright Chromium, PyMuPDF, fontTools and poppler-utils (`pdffonts`).
