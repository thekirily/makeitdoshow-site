# Launch audit — 2026-11-07

**Launch is blocked.** This PR hardens the static launch branch. Live public main still returns 404 for the film door and most launch routes; the existing draft Gumroad product also returns 404. PostHog is unconfigured; actual checkout, receipt/delivery/follow-up and inbox placement remain unverified. No publication, DNS change, account signup, purchase or experiment start occurred.

## Scope and reproducibility

Baseline is an isolated git archive of launch at b878192. Final Lighthouse uses a frozen HTML/assets/robots snapshot with a source hash in its summary. There are 19 existing templates × phone/desktop and one new accessibility template × both devices. Full-year variants include 1953, pre-minimum-wage 1930, and partial-year 1975. Film q/d paths share the door template. All 46 years, aliases and orphan pages are separately checked by static/link/budget tools. There are now **65 HTML routes and 58 sitemap entries**.

Lighthouse 13.6.0, Chrome, one serial run per template/device, default simulated throttling, local HTTP. These are shared-host lab numbers, **not field or production-CDN measurements**. Load, timestamp and environment are retained. PostHog, capture and experiments are disabled in speed measurements. Final enabled configurations and assets need their own acceptance check.

Raw JSON is retained losslessly as .json.gz; use gzip -dc to inspect it. Summary JSON retains failed-audit details. Diagnostic runs remain separate: an initial CSP/robots interaction was fixed with same-origin connections; another run predates the final UTM correction. The final matrix does not select the best score. An incomplete after matrix remains UNMEASURED until all 40 rows exist.

## Lighthouse before → after

Targets: P/A/BP/SEO each ≥95; LCP <2.000s, CLS <0.0500, TBT <150ms. Score order is performance/accessibility/best-practices/SEO. Metric order is LCP seconds / CLS / TBT milliseconds. PASS requires all seven literal targets, including on noindex pages.

| Template | Device | Before scores | Before LCP / CLS / TBT | Before | After scores | After LCP / CLS / TBT | After |
|---|---|---|---|---|---|---|---|
| home | mobile | 93 / 100 / 100 / 100 | 0.907 / 0.0000 / 320.0 | FAIL performance, tbt_ms | 96 / 100 / 100 / 100 | 0.902 / 0.0000 / 244.0 | FAIL tbt_ms |
| home | desktop | 100 / 100 / 100 / 100 | 0.365 / 0.0001 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.383 / 0.0001 / 0.0 | PASS |
| directory | mobile | 99 / 100 / 100 / 100 | 0.902 / 0.0000 / 99.5 | PASS | 100 / 100 / 100 / 100 | 0.903 / 0.0000 / 56.2 | PASS |
| directory | desktop | 100 / 100 / 100 / 100 | 0.242 / 0.0001 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.285 / 0.0001 / 0.0 | PASS |
| year-full | mobile | 100 / 100 / 100 / 100 | 1.024 / 0.0104 / 29.5 | PASS | 100 / 100 / 100 / 100 | 1.053 / 0.0104 / 0.0 | PASS |
| year-full | desktop | 100 / 100 / 100 / 100 | 0.405 / 0.0002 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.442 / 0.0002 / 0.0 | PASS |
| year-pre-wage | mobile | 100 / 100 / 100 / 100 | 0.955 / 0.0000 / 35.0 | PASS | 100 / 100 / 100 / 100 | 1.054 / 0.0105 / 1.0 | PASS |
| year-pre-wage | desktop | 100 / 100 / 100 / 100 | 0.408 / 0.0002 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.405 / 0.0002 / 0.0 | PASS |
| year-partial | mobile | 100 / 100 / 100 / 100 | 0.903 / 0.0095 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.903 / 0.0095 / 5.2 | PASS |
| year-partial | desktop | 100 / 100 / 100 / 100 | 0.365 / 0.0102 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.364 / 0.0102 / 3.7 | PASS |
| booklet | mobile | 98 / 100 / 100 / 100 | 1.803 / 0.0000 / 150.0 | FAIL tbt_ms | 98 / 100 / 100 / 100 | 1.877 / 0.0000 / 159.0 | FAIL tbt_ms |
| booklet | desktop | 100 / 100 / 100 / 100 | 0.408 / 0.0001 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.424 / 0.0001 / 7.0 | PASS |
| gifts | mobile | 99 / 100 / 100 / 100 | 0.903 / 0.0000 / 109.5 | PASS | 100 / 100 / 100 / 100 | 0.905 / 0.0000 / 58.0 | PASS |
| gifts | desktop | 100 / 100 / 100 / 100 | 0.246 / 0.0001 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.243 / 0.0001 / 0.0 | PASS |
| article | mobile | 98 / 100 / 100 / 100 | 0.902 / 0.0004 / 179.0 | FAIL tbt_ms | 98 / 100 / 100 / 100 | 0.903 / 0.0004 / 153.0 | FAIL tbt_ms |
| article | desktop | 100 / 100 / 100 / 100 | 0.366 / 0.0005 / 0.0 | PASS | 100 / 100 / 100 / 100 | 0.403 / 0.0005 / 0.0 | PASS |
| recipes | mobile | 100 / 100 / 100 / 100 | 1.243 / 0.0000 / 65.5 | PASS | 99 / 100 / 100 / 100 | 1.553 / 0.0068 / 0.5 | PASS |
| recipes | desktop | 100 / 100 / 100 / 100 | 0.444 / 0.0004 / 0.0 | PASS | — | — | UNMEASURED |
| sources | mobile | 100 / 100 / 100 / 100 | 0.903 / 0.0000 / 86.0 | PASS | — | — | UNMEASURED |
| sources | desktop | 100 / 100 / 100 / 100 | 0.243 / 0.0001 / 0.0 | PASS | — | — | UNMEASURED |
| about | mobile | 100 / 100 / 100 / 100 | 0.902 / 0.0003 / 0.0 | PASS | — | — | UNMEASURED |
| about | desktop | 100 / 100 / 100 / 100 | 0.242 / 0.0005 / 0.0 | PASS | — | — | UNMEASURED |
| privacy | mobile | 100 / 100 / 100 / 100 | 0.902 / 0.0000 / 0.0 | PASS | — | — | UNMEASURED |
| privacy | desktop | 100 / 100 / 100 / 100 | 0.242 / 0.0001 / 0.0 | PASS | — | — | UNMEASURED |
| terms | mobile | 100 / 100 / 100 / 100 | 0.902 / 0.0000 / 0.0 | PASS | — | — | UNMEASURED |
| terms | desktop | 100 / 100 / 100 / 100 | 0.243 / 0.0006 / 0.0 | PASS | — | — | UNMEASURED |
| family | mobile | 100 / 100 / 100 / 100 | 0.902 / 0.0000 / 0.0 | PASS | — | — | UNMEASURED |
| family | desktop | 100 / 100 / 100 / 100 | 0.244 / 0.0001 / 0.0 | PASS | — | — | UNMEASURED |
| thanks | mobile | 100 / 100 / 100 / 66 | 0.902 / 0.0002 / 0.0 | FAIL seo | — | — | UNMEASURED |
| thanks | desktop | 100 / 100 / 100 / 66 | 0.300 / 0.0001 / 5.0 | FAIL seo | — | — | UNMEASURED |
| missing | mobile | 99 / 100 / 100 / 66 | 0.903 / 0.0002 / 119.0 | FAIL seo | — | — | UNMEASURED |
| missing | desktop | 100 / 100 / 100 / 66 | 0.242 / 0.0001 / 0.0 | FAIL seo | — | — | UNMEASURED |
| door | mobile | 100 / 100 / 100 / 66 | 0.903 / 0.0001 / 66.1 | FAIL seo | — | — | UNMEASURED |
| door | desktop | 100 / 100 / 100 / 66 | 0.243 / 0.0003 / 0.0 | FAIL seo | — | — | UNMEASURED |
| privacy-alias | mobile | 100 / 100 / 100 / 66 | 0.902 / 0.0003 / 0.0 | FAIL seo | — | — | UNMEASURED |
| privacy-alias | desktop | 100 / 100 / 100 / 66 | 0.243 / 0.0001 / 0.0 | FAIL seo | — | — | UNMEASURED |
| terms-alias | mobile | 100 / 100 / 100 / 66 | 0.902 / 0.0003 / 0.0 | FAIL seo | — | — | UNMEASURED |
| terms-alias | desktop | 100 / 100 / 100 / 66 | 0.243 / 0.0001 / 0.0 | FAIL seo | — | — | UNMEASURED |
| accessibility | mobile | — | — | UNMEASURED | — | — | UNMEASURED |
| accessibility | desktop | — | — | UNMEASURED | — | — | UNMEASURED |

[Baseline outputs](evidence/launch-1107/before-lighthouse/) · [Final outputs](evidence/launch-1107/after-lighthouse/). Accessibility has no baseline.

| Criterion | Before output | After output | After verdict |
|---|---|---|---|
| performance | min 93; 1/38 fail | min 96; 0/17 fail | UNMEASURED |
| accessibility | min 100; 0/38 fail | min 100; 0/17 fail | UNMEASURED |
| best-practices | min 100; 0/38 fail | min 100; 0/17 fail | UNMEASURED |
| seo | min 66; 10/38 fail | min 100; 0/17 fail | UNMEASURED |
| lcp_ms | max 1802.7506; 0/38 fail | max 1877.3759; 0/17 fail | UNMEASURED |
| cls | max 0.0104; 0/38 fail | max 0.0105; 0/17 fail | UNMEASURED |
| tbt_ms | max 320; 3/38 fail | max 244; 3/17 fail | UNMEASURED |

Intentional noindex doors, aliases, thanks and 404 retain low SEO scores: **literal-target FAIL**. Their SEO-only CI exception is explicit; no other metric is relaxed. Shared-host blocking-time failures remain FAIL. A separate runner, when available, is reported separately.

## All other requested checks

| Check | Before evidence | After instrument/output | Verdict / practical limit |
|---|---|---|---|
| Headers on every template, phone/desktop | Public main has no requested response security headers | security.json: 40 HTTPS GETs, full headers and mobile/desktop UAs; staged CSP/SRI parser checks | **PARTIAL / FAIL for unavailable headers**, equivalent scan, no invented Observatory grade |
| HTTPS / TLS | Root HTTP→HTTPS redirect 301 | live-health.json: root/privacy 200; chain and hostname verified; certificate expires 2027-02-04, ~88 days left | **PASS when measured**, not proof launch routes are live |
| CSP meta | Absent | Generated on all 65 pages: default none; self scripts/styles/images/fonts; exact JSON hashes; same-origin connections plus configured regional ingest; exact Brevo form origin only when enabled; base/object none | **PASS staged**, no unsafe-inline/eval; zero HTTP-browser CSP violations |
| SRI | No third-party scripts | Zero third-party scripts, fonts self-hosted | **PASS / N/A** |
| Secrets, including history | Gitleaks 8.30.1: 8 starting commits, no leaks | Redacted all-ref history log/report retained; final commit scan recorded at delivery | **PASS scanned scope**, no arbitrary future-secret guarantee |
| Internal links/assets/fragments | Original static verifier previously reported 1,964 references; baseline linkinator raw output retained | 2,178 static references, 65 HTML pages, all 46 year PDFs; linkinator all routes, both UAs, CSS and fragments | **PASS staged internal**, canonical same-site URLs explicitly mapped to preview; public failures separately retained |
| External links | One USPS historical-rate PDF URL 404 | Fixed to official HTML source; full all-route linkinator output retained | **NOT an anonymous all-links PASS**: Google account permissions is authenticated (401). Public same-site canonical/social destinations remain 404 until publication |
| Nu valid HTML | One figure-content-order error and one headingless-wrapper warning | 65 files, zero syntax errors; file-origin CSP warnings retained | **PASS syntax**; file:// warnings do not establish a runtime policy failure. HTTP-origin Nu attempt refused local host and was not counted as validation |
| Schema.org | Local JSON parsing; no fresh baseline live test claimed | Live code submissions for all 20 templates: zero errors, zero warnings; localized raw output and screenshot | **PASS schema**, not rich-result eligibility |
| Google Rich Results | Previously untested | Real Chrome code submission rejected: Something went wrong / Log in and try again; screenshot retained | **UNVERIFIED**, not substituted by JSON parsing or Lighthouse |
| Axe serious/critical | Zero in 38 existing views | Zero in all 40 final views | **PASS automated scope**, not all WCAG criteria |
| Keyboard | Baseline traversal retained | 40 final tab/Enter/skip/focus scans; year selection and consent via keyboard | **PASS checked flows**, no screen-reader/user study |
| 200% readable/reflow | 15/38 existing views overflowed | 40 final views: no page overflow or clipped-text detection; 390→195 and 1440→720 CSS viewport, double device pixel ratio | **PASS geometry/readability proxy**, not a human study. Price tables scroll in a keyboard-focusable region |
| Pageview / CTA / checkout once | No generic CTA event | Smoke counts one pageview per navigation, CTA and checkout start per click, with correct year and ID | **PASS intercepted wiring**; checkout click does not prove the off-site page opened |
| Signup / paid sale | Importer accepted sale with unknown analytics consent | Authenticated-sale fixtures: free→signup_completed; paid→order_paid; deterministic UUIDs, test/other products excluded, refunds separate | **PASS fixtures; production UNVERIFIED**, no actual sale or ingest proof |
| UTM / film door | Generic campaign tags lost/overwritten | Newsletter UTMs stay separate from film/door; browser→checkout→importer regression check | **PASS smoke**; no pre-consent cross-page attribution is persisted |
| Opt-out | Stopped browser events, retained visit storage; server could still count sale | Missing/declined consent, DNT/GPC, denied storage and withdrawal checked; stored visit removed; importer requires permission | **PASS checked paths**; later erasure of already-imported records needs an owner process |
| A/B ready, no test started | Absent | Three home slots; PostHog flags API; 250ms fail-open deadline; both variants, exposure, conversion, timeout/error and consent smoke-tested | **PASS fixture readiness**, disabled; final variants still need review |
| Uptime / certificate / alert | No 15-minute monitor | Scheduled :07/:22/:37/:52 HTTPS/TLS check; warning at 21 days; deduplicated failure issue and recovery closure; failing-path probe returns false | **CONFIGURED, NOT ACTIVE here**; default main and notification settings are owner gates; Actions scheduling is best effort |
| Page weight | No enforced every-route budget | 65 routes; limits raw 550KB, gzip estimate 400KB, JS 30KB, 24 requests; includes lazy images/fonts | **PASS**, actual maxima below |
| Email capture / deliverability | No selected independent DOI vendor or authenticated sender proof | Three free services compared; Brevo form six fixture checks; off by default; DNS observed read-only | **PARTIAL / BLOCKED** by account-generated DNS, sender, DOI and seed inbox checks |
| Legal / rights / statement | Policies existed with consent/controller/retention/refund/rights gaps | LEGAL.md checks actual behavior with primary sources; 104-file hash/license inventory; accessibility statement linked | **CHECKLIST COMPLETE, LEGAL CLEARANCE OPEN** |
| Buyer / delivery / follow-up | Draft commerce closed | Phone Chrome: live door 404, local path works, Gumroad product 404, owner preview redirects to login; separate thanks preview | **FAIL / UNVERIFIED beyond observed seams**, screenshots retained |

GitHub Pages cannot expose arbitrary custom headers here. HSTS, anti-framing, nosniff, Permissions-Policy and response CSP require host/edge support. Meta CSP cannot implement frame-ancestors. A supported referrer-policy meta is included. Owner must accept the limits or arrange an approved host/edge change; no DNS/host mutation occurred. References: [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP), [frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).

## Instrument totals

- before-browser.json: 38 views; 0 serious/critical axe issues; 15 zoom overflows; 0 CSP violations.
- after-browser.json: 40 views; 0 serious/critical axe issues; 0 zoom overflows; 0 CSP violations.
- after-links-all.json mobile: 65 routes, 362 references, 1 failures: https://myaccount.google.com/permissions HTTP 401.
- after-links-all.json desktop: 65 routes, 362 references, 1 failures: https://myaccount.google.com/permissions HTTP 401.
- ci-internal-links-all.json mobile: 65 routes, 1521 references, 0 failures.
- ci-internal-links-all.json desktop: 65 routes, 1521 references, 0 failures.
- before-weight.json: 64 routes; maxima total_raw_bytes=249252, total_gzip_bytes=224321, javascript_raw_bytes=7540, requests=11.
- after-weight.json: 65 routes; maxima total_raw_bytes=259913, total_gzip_bytes=227893, javascript_raw_bytes=15056, requests=12.
- ab-smoke.json: 119 passing checks.
- signup-smoke.json: 6 passing checks.
- functional.json: 309 passing checks.
- Nu 26.11.4 (70ae341): 0 errors, 295 retained file-origin messages.


[Raw evidence](evidence/launch-1107/) includes headers, DNS, link scans, baseline consent failures, browser checks, Nu, Gitleaks, npm audit, rights metadata and screenshots. Development-only tooling has zero npm-audit vulnerabilities with the committed lockfile/overrides at audit time. No npm runtime is shipped.

## Reproduce / owner acceptance

README.md lists pinned setup and commands. Run browser_qa.py, page_budget.py, validate_html.py, and check_links.mjs with preview port 8115; run launch_measure.py serially afterward and assert_lighthouse.py against its summary. CI retains raw artifacts. Use a separate runner for speed checks when available.

[Experiment operation](docs/experiments.md), [email/DNS](DNS-FOR-OWNER.md), [buyer seams](docs/buyer-path-1107.md), [legal checklist](LEGAL.md), [premortem](PREMORTEM.md), [handback](handback-1107.md). Actual ingestion, authenticated checkout/receipt, fulfillment, inbox placement, Google acceptance and final film links are still owner gates.

## PR / independent CI

PR and final CI status are recorded in handback-1107.md. Local failures remain visible even if a separate runner passes. No merge or deployment occurred.
