# Counting without inventing conversions

The implementation is `assets/site.js` plus `scripts/sync_sales.py`. The previous tracking folder was inspected for its film door convention, not copied as a working analytics connection. Its old Umami project belongs to a different product and is not loaded here.

## Visit attribution

`/01/` establishes film01 / typed; `s=q` establishes QR; `s=d` description; `s=p` pinned; `s=e` endscreen. `/01/q/` and `/01/d/` are query-free alternatives. Admitted `utm_campaign=filmNN` and `utm_medium` pairs also establish explicit film attribution. A new explicit door replaces a different door; internal links preserve it. A random UUID and the attribution live in sessionStorage, with a 30-minute inactivity limit. A refresh of the same film door keeps the same visit. New tabs can have separate visits; this is not a unique-human count.

A direct `/1953/` or bare-domain visit remains `film=none, door=direct`. Search and known assistant referrers are categorized only when present. Google AI answers and ordinary Google search share the Google referrer. We do not guess that a direct visitor watched the latest film. The old script made that guess; it has been removed.

## Events

| Event | Evidence |
|---|---|
| `visit_started` | New anonymous browser visit with film/door when known |
| `$pageview` | A page rendered with JavaScript and analytics enabled |
| `year_selected` | Valid year submitted |
| `book_year_selected` | A booklet year selected |
| `sheet_downloaded` | Free PDF link clicked; it is not proof of successful saving/printing |
| `sample_opened` | Sample PDF link clicked |
| `signup_started` | Free Gumroad checkout link clicked, once enabled |
| `checkout_started` | Paid Gumroad checkout link clicked, once enabled |
| `signup_completed` | Verified free-sheet/cards transaction from Gumroad API |
| `order_paid` | Verified known-product Gumroad sale, excluding tests |
| `order_refunded` | Verified refund reported separately from gross orders |

`/thanks/` never emits an order or signup event. An arbitrary visitor cannot mint revenue by adding URL parameters. The sales importer is an authenticated read from Gumroad, not a public webhook accepting unsigned claims.

Checkout links use Gumroad's documented `wanted=true&variant=YEAR`, carry film, door, the random visit ID, and year, and return those in Gumroad `url_params`. No name/email/address is inserted into analytics or checkout URLs by this site. Confirm preservation against a real transaction before launch; the existing fulfillment report uses the same `url_params` field. Non-JavaScript checkout still works with the static default year, which must be confirmed at Gumroad; browser attribution is absent in that case.

## Confirmed conversions

The Actions workflow polls the last 30 days every half hour on `main` (schedule delivery is not guaranteed). It handles pagination and ignores all product IDs outside the provided Make It Do product map. It sends a deterministic UUID per sale/event to PostHog so repeat imports can be deduplicated there. Report gross orders and refunds separately; revenue is in the sale's currency, never summed across currencies. A zero-dollar discount on a paid product remains an order, not a lead. Chargeback/dispute accounting and multiple partial-refund revisions need a fuller financial ledger; this is an acquisition funnel, not the accounting system.

Dry run an already-downloaded sales JSON with `python3 scripts/sync_sales.py --input /private/path/sales.json`. The output is aggregate counts only; do not commit customer exports. `--send` requires the existing public project capture key and uses PostHog's batch endpoint. Do not use a personal API token in browser files. A real API read takes `GUMROAD_ACCESS_TOKEN` from the environment, never arguments or logs.

## Privacy and coverage

Explicit anonymous events only: no downloaded SDK, autocapture, replay, heatmaps, email identification, advertising cookies, or cross-site identity. Full query strings and referrer paths are excluded. Honor Do Not Track, Global Privacy Control, and the opt-out on `/privacy.html`. Blocked storage does not break lookup. Blocking analytics does not block navigation or downloads. Counts are incomplete for opt-outs, ad blockers, network loss, and JavaScript-disabled visits. “Every visit” is not a technically honest guarantee on a static privacy-respecting site.

Create a funnel in the existing PostHog project: visit → year selection → download/sample → checkout start → order paid. Break down by `film` and `door`, and inspect `none/direct` separately. For marketing, gross and net revenue per 1,000 film views matter more than clicks alone. Set a free-tier usage limit in the existing project to prevent paid overage; no paid plan is needed by this code.

## Implementation gap flagged

There was no project-local playbook or working connection for verified Gumroad-to-PostHog conversions. This bridge was built from the providers' primary documentation and tested with fixtures. Real end-to-end verification is still required. There is no `missions/_evolution_queue.yaml` in this repo; no external knowledge library was modified.

Primary references read live November 5, 2026:

- https://posthog.com/docs/api
- https://posthog.com/tutorials/api-capture-events
- https://gumroad.com/help/article/270-url-parameters
- https://gumroad.com/api

## November 7 consent and experiments correction (supersedes opt-out-only behavior above)

Analytics now require explicit permission before storing attribution, evaluating flags,
or sending events. DNT/GPC override it. With no public project key, no visit ID is stored.
Only consented checkout URLs carry `mid_visit`, campaign/door and experiment parameters.
The server importer accepts only `mid_analytics=yes`; historical/unknown and declined
sales stay in Gumroad. Existing fixture sales were updated to carry permission.
This changes the denominator: neither raw visitors nor all purchases can be inferred
from PostHog. Report consented visits and reconcile against Gumroad totals.
UTM source, medium, campaign and content slug values survive navigation; email-like,
long or malformed values are rejected. Do not put personal data in campaign tags.
`cta_clicked` records one intentional main-content action click. `checkout_started`
is still a click, not proof the off-site page loaded. Optional Brevo forms emit only
`signup_started`; confirmed Brevo DOI is read in Brevo, not inferred from a return page.
See [experiments](experiments.md) for flag/exposure/conversion setup. This PR starts no test.
