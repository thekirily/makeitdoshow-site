# Read-only buyer path, 390 × 844 phone — November 7

Real Chrome navigations and screenshots are retained in [buyer-path](../evidence/launch-1107/buyer-path/); `results.json` lists exact URLs, status, titles and excerpts. No form signup, login, payment, purchase, product publication or message send occurred.

| Step / seam | Observed evidence | Result / owner gap |
|---|---|---|
| YouTube → description | Visited the channel's videos page. No final first-film watch URL or approved description is supplied in this repo. The test uses the documented planned description destination. | Actual published-description click **unverified**; a channel visit is not that evidence. Owner must test final shortened/redirected URL and QR scan, too. |
| Description destination → public site | `https://makeitdoshow.com/01/?s=d&utm_source=youtube&utm_medium=description&utm_campaign=film01` returned 404. | **FAIL**, public main differs from launch. Keep final film upload gated on owner publication and live path verification. |
| Film door → year | Local branch preview loads the film door and keyboard year entry reaches `/1953/`; free PDF is accessible. | Preview **PASS**, not a live-site result. Film title/creative may change; verify the final promise matches this destination. |
| Year → paid offer | Local booklet page shows the chosen year, price/tax/shipping explanation and closed-order notice. | Preview is usable; checkout deliberately unavailable until owner resolves the product. |
| Make It Do → Old Porch Press / Gumroad | Existing `oldporchpress.gumroad.com/l/mid-your-year?wanted=true&variant=1953` returned Gumroad's 404. | **FAIL / blocked at product**, before a payment form could be inspected. Brand/domain/person changes at this seam; confirm displayed seller, support, price, year, name and shipping once public. |
| Checkout → thank-you | Opened local `/thanks/` separately. It says a visit alone does not confirm purchase; the smoke test proves it cannot mint revenue. | **Not a real checkout return**. Owner must inspect real return configuration. |
| Receipt / delivery email | Read-only access to `app.gumroad.com/products` redirected to login. No authenticated product Receipt tab or delivery email was accessible. | **UNVERIFIED**. Inspect Gumroad's actual Receipt tab, custom message, download button, file and sender, then seed inbox rendering. Do not use generic vendor documentation as a screenshot of this product. |
| Follow-up / printing | No configured actual follow-up/receipt sequence in this repo. The handback names an unresolved print adapter/supplier seam. | **UNVERIFIED**. Owner decides follow-up purpose, sender, timing and suppression, and verifies print fulfillment. No invented welcome message or delivery promise was added. |

Visible changes of look/person: YouTube app/chrome → custom warm-paper site → Old Porch Press Gumroad domain and Gumroad-hosted checkout → Gumroad receipt/download environment → support Gmail → chosen printer/shipping service. The final film's identity and actual email/checkout presentation remain unavailable. The desired promise continuity cannot be signed off across these hidden seams.
