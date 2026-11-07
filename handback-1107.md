# Launch-standard handback — 2026-11-07

This branch hardens shared infrastructure and records launch blockers. It does **not** make the first-film buyer path launch-ready. Offer/product copy, price and final creative were not rewritten; checkout, email capture and experiments stay closed/off.

Branch `launch-standard-1107` starts at `launch` commit `b878192`. The pre-existing untracked `BRIEF-launch-standard-1107.md` was preserved. No merge, publication, DNS change, account signup, product publication, purchase, paid service or email send occurred.

## Fixed

- Prior-consent analytics instead of unconditional visit storage; DNT/GPC/opt-out and denied-storage behavior; withdrawal removes attribution. The Gumroad importer now requires checkout analytics permission as well, including for completed free signups.
- Campaign slugs and film/door survive consented navigation; generic CTA clicks are counted once; experiment assignments join authenticated paid/free conversions. Thank-you URLs cannot create sales.
- A PostHog flag bootstrap, headline/hero/price slots and 250ms fail-open hold. Both variants and timeout/failure are exercised by `tests/ab_smoke`. No flag/test was created or started.
- Off-by-default Brevo native signup form with separate marketing checkbox, hosted double confirmation, host/config validation and six intercepted submission checks. No API key or remote script ships to the browser.
- Generated CSP on all 65 HTML routes, exact JSON script hashes, no inline/eval exception, local asset sources and configured vendor origins only. No third-party scripts, so third-party SRI is vacuously satisfied.
- Enlarged-text reflow defects in navigation, forms, grids and the year selector; keyboard-accessible horizontally scrollable price tables; reduced-motion preference retained. New accessibility statement and footer link.
- Invalid figure structure, a headingless recipe wrapper, and the broken USPS historical-rate source URL.
- PR CI, strict Lighthouse gates (with explicit noindex-only SEO exception), complete every-route page-weight budget, Nu HTML, history secret scan, axe/keyboard/zoom, functional/browser, A/B and signup smoke checks.
- A 15-minute scheduled HTTPS/TLS probe with 21-day expiry warning, deduplicated alert issue and recovery closure. This remains inactive as a schedule until it reaches default `main`; configuration is not an active monitor.

## Evidence and remaining failures

Read [LAUNCH-AUDIT.md](LAUNCH-AUDIT.md) for before/after numbers, raw outputs, every literal-target failure and test limits; [LEGAL.md](LEGAL.md) for sourced legal gaps; [DNS-FOR-OWNER.md](DNS-FOR-OWNER.md) for the provider comparison and DNS blocker; [PREMORTEM.md](PREMORTEM.md) for ten ranked failure cases. [Buyer path](docs/buyer-path-1107.md) links phone screenshots and exact observed seams. Final measurement/CI status is recorded in the audit when available.

## Every owner decision / external acceptance gate

1. **Final film and offer:** decide creative/product and approved claims; provide the actual description/watch URL, QR and spoken destination. Recheck identity and promise continuity. Publication remains the owner's action.
2. **Live route cutover:** current public main returns 404 for most launch routes. Merge/release through the existing owner workflow only after acceptance. PR-to-launch does not update public main.
3. **Commerce and fulfillment:** publish final Gumroad products only after proving year, cover name, shipping address, tax/currency/discounts, charged amount, file delivery, print supplier/adapter, duplicate handling and realistic timing. Decide final refund/cancellation/defect policy and seller/support identity. Draft products are public 404s today.
4. **Actual receipt / follow-up:** authenticated Gumroad Receipt tab, checkout up to payment and delivery email could not be inspected. Decide custom receipt/download wording, support sender, transactional vs marketing follow-up, timing, unsubscribe/suppression and print updates. A local thank-you preview is not a completed buyer path.
5. **Analytics:** configure the existing Make It Do public key and region, server Gumroad secret, free usage limit, retention/IP settings and ingestion checks. Verify real browser-to-confirmed-sale attribution after configuring. This PR's endpoint tests are intercepted fixtures. Consent reduces coverage; reconcile with Gumroad, never describe it as every visitor.
6. **Privacy/legal:** choose controller/legal identity/address, lawful bases, jurisdictions, processor/DPA/transfer arrangements, retention periods, complaint/right-request process, CCPA/CPRA applicability and consent evidence/withdrawal procedure. Review final FTC disclosures and consumer rights with qualified advice.
7. **Email account and DNS:** select/open Brevo Free or a reviewed alternative, choose authenticated From and receiving Reply-To, get the actual generated domain-verification/DKIM records, and have the DNS operator apply them. Only known generic values are exact now; account-specific DNS is explicitly incomplete. Verify DOI, sender, postal address, unsubscribe and seed inbox headers before enabling the form. No automatic confirmed-Brevo→PostHog bridge is claimed.
8. **Asset rights:** confirm supplied layouts/PDFs, frame extraction/derivative provenance, brand ownership and final film footage/music rights. Per-file inventory and source metadata are retained; archive marking is not a warranty.
9. **Accessibility:** arrange human/assistive-technology/PDF checks and accessible alternatives, and check Gumroad/email. Automated passes do not certify all WCAG criteria or end-to-end accessibility.
10. **Monitoring/security/CI:** make workflows available on default main without bypassing the publication limit, watch alert issues/Actions failures, and decide whether best-effort GitHub scheduling is sufficient. Accept or arrange an edge/host change for headers GitHub Pages cannot set (HSTS, anti-framing, nosniff, permissions policy). No host/DNS move happened.
11. **Validation:** Google's live Rich Results Test rejected submission with an authentication error. Complete that acceptance check with an accessible session/final URLs. Intentional noindex routes retain SEO scores below the literal all-page target. Public canonical/social URLs become valid only after owner publication. Authenticated account-management links require login, so anonymous zero-broken-link certification is unavailable.
12. **Experiment start:** approve one hypothesis/slot, actual variants/assets and a metric/sample rule; configure and enable a flag only after privacy and ingestion checks. [docs/experiments.md](docs/experiments.md) explains operation. Start none is still respected.

## Procedure gap

The repo had individual tools but no single launch-standard playbook or evidence matrix for this scope. This pass compiled the repeatable checks, disabled integrations and owner gates into the scripts/workflows/docs above. There is no local `missions/_evolution_queue.yaml`; Alexandria and other projects were not mutated.
