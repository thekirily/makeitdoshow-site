# Launch legal checklist — reviewed 2026-11-07

This is an evidence-based checklist, **not legal advice or a legal clearance**. PASS means a narrowly described implementation check passed. OPEN means an owner/legal decision or external evidence is missing. Apply the final offer and actual markets before publication. The present public `main` site differs from this branch; branch fixes have not reached visitors.

## Privacy, analytics and email

| Status | Check against the actual site | Owner gap / required decision |
|---|---|---|
| FIXED | The previous code wrote `mid_visit` to sessionStorage even with analytics unconfigured, and could capture on configuration without prior consent. The new code waits for explicit analytics permission before writing/reading attribution or sending events/flag requests. Separate Allow/Decline controls; free content works either way. | Approve global opt-in as the baseline. Do not switch it to implicit consent to recover missing counts. |
| PASS, tested | Missing consent, opt-out, DNT, GPC and denied storage stop analytics. Withdrawal removes visit attribution. Marketing permission is separate. Raw email, full URL queries, names, address and payment fields are excluded from browser events. | Maintain the same rule in every added SDK, email tracker and vendor integration. |
| PASS, tested | Server Gumroad import now requires `mid_analytics=yes`. Unknown/declined transactions remain in Gumroad; they do not become PostHog events. This closes a prior mismatch where browser opt-out did not stop later server sales analytics. | A withdrawal after leaving checkout cannot recall an already-imported event automatically. Establish an erasure/request procedure and how consent evidence is retained. URL parameters are an operational signal, not an auditable consent ledger. |
| OPEN — GDPR/UK GDPR notice | Privacy describes session/local storage, PostHog paths/film/door, pseudonymous sale events, provider IP exposure, hosting, printers and email. New text covers consent, experiments and optional Brevo DOI. | Publish the controller's legal identity/address, lawful basis by purpose, actual processors, exact retention periods, transfer safeguards, rights/complaint route and any required EU/UK representative. The contact Gmail alone does not settle these obligations. Confirm who controls each of the three named brands. |
| OPEN — processors/transfers | US PostHog ingest is the default; project key is empty. Brevo is off. GitHub hosts; Gumroad is merchant of record. | Choose actual PostHog region and retention (including IP/GeoIP settings), enter DPAs/transfer documents, review subprocessors and configure least privilege. Do not claim data residency or anonymity solely because names are excluded. |
| OPEN — EU device storage | SessionStorage for analytics is still device storage, even without cookies. This patch uses prior consent globally, including experiments. | Review applicability and local exemptions with counsel; do not assume a national aggregate-statistics exemption covers a third-party pseudonymous conversion funnel. Essential preference storage only remembers the person's choice. |
| OPEN — UK | Uses the same opt-in baseline; no reliance on an analytics exemption. | UK rules are changing under the Data (Use and Access) Act. Assess the current applicable exception/conditions before any relaxation. |
| OPEN — CCPA/CPRA | No ads, selling/sharing integration, sensitive form capture or cross-site profiles found; GPC additionally disables optional analytics. | Determine business/household/revenue applicability and vendor contractual status. If applicable, complete notice-at-collection, access/delete/correct, opt-out, retention and request-verification procedures. Current adjusted revenue threshold is $26.625m, with other applicability tests; small traffic alone is not the whole test. |
| OPEN — email | The off-by-default Brevo form requires an unticked marketing checkbox and a provider DOI attestation; no key or remote JS is shipped. Six fixture checks pass. | Select the account and sender, verify DOI on the provider, choose message purpose/frequency, include sender/postal address/unsubscribe, sign the DPA, set retention and test suppression. Disable provider open/click tracking unless reviewed and disclosed. No real email or DOI has been tested. |

Primary sources: [GDPR, especially Arts 3, 6, 7, 12–22, 28 and 44](https://eur-lex.europa.eu/eli/reg/2016/679/oj); [EU cookie guidance](https://europa.eu/youreurope/business/growing/digitalising/online-privacy/index_en.htm); [Irish DPC analytics consent](https://www.dataprotection.ie/en/faqs/cookies/do-i-need-consent-analytics-cookies); [ICO storage technologies](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-storage-and-access-technologies/); [ICO consent update](https://ico.org.uk/consent); [California AG CCPA/CPRA](https://oag.ca.gov/privacy/ccpa); [CPPA adjusted thresholds](https://privacy.ca.gov/laws-and-regulations/monetary-thresholds-in-the-ccpa/); [FTC CAN-SPAM](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business). These support the checklist, not a conclusion about this owner's legal status.

## Terms, refund and buyer obligations

| Status | Site / vendor comparison | Owner gap |
|---|---|---|
| PASS, limited | Terms identify Gumroad as merchant of record; payment/tax/receipts are handled there. No card collection here. Gumroad's current supplier terms confirm its reseller/MoR role. | Confirm actual seller/support identity shown at checkout and on receipts; domain is still `oldporchpress.gumroad.com` while the site says Make It Do. |
| OPEN — refunds | Site offers help for wrong/damaged goods and refers to applicable checkout terms. Gumroad lets sellers set their own refund policies; the site does **not** thereby acquire a complete refund policy. | Decide a precise policy for print, personalization, PDF access, cancellation, defects and statutory rights; set it on Gumroad and match site wording. Do not add a blanket no-refund policy or an unsupported unconditional promise. |
| OPEN — consumer rights | Digital + personalized physical delivery may have different withdrawal rules. Gumroad's buyer/refund rules include jurisdiction-dependent rights. | Decide service countries and have counsel review mandatory consumer rights, digital-content consent/acknowledgment and personalized-goods exceptions where applicable. U.S.-only shipping does not by itself prove all viewers/buyers are U.S. residents. |
| OPEN — delivery | Current copy states $49 including U.S. shipping plus checkout tax, a PDF and print booklet; no guaranteed arrival date. Commerce is closed. | Verify final product, address/name fields, tax/currency/PPP/discount behavior, shipping charge, digital file, print adapter, support SLA and realistic timing. This task did not change any offer or choose a printer. |

Sources: [Gumroad terms](https://gumroad.com/terms), [refund policy](https://gumroad.com/help/article/51-what-is-gumroads-refund-policy), [buyer purchase flow](https://gumroad.com/help/article/282-how-do-purchases-work-for-my-customers.html), [receipt information](https://gumroad.com/help/article/204-get-to-know-your-gumroad-receipt). These pages cannot establish the unpublished products' actual configured terms or receipt contents; the owner preview remains necessary.

## FTC disclosures and claims

- [x] No testimonials, ratings, affiliate links, sponsorship badges or invented reviews were found in the staged site. It presents the booklet as its own product and labels covers as digital previews. Historical promotional footage is identified as such.
- [ ] Owner: confirm and clearly disclose any sponsor, affiliate or material relationship in the final film, spoken endorsement, YouTube description and landing page where relevant. A site footer alone may not make a film disclosure clear.
- [ ] Owner: identify the studio/brand relationship clearly at the Gumroad seam. Do not imply archival actors endorse a new product.
- [ ] Owner: substantiate final price, included shipping, large-print specifications and digital/physical delivery claims before opening orders. Check every proposed experiment against the real checkout amount.

Source: [FTC endorsement guides Q&A](https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking), [disclosures for social media](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers). The final first film/description is unavailable, so no disclosure clearance is possible for it.

## Asset rights, including every delivered file

The row-by-row inventory is [asset-licenses.csv](evidence/launch-1107/asset-licenses.csv): **104 files**, SHA-256, asserted source, license basis and remaining gap. It covers all 52 WebP files, three WOFF2 files, the SVG favicon and 48 PDF downloads. There is no embedded video/audio or third-party script in these pages. Dormant small-image variants are included as well as used images.

| Asset family | Evidence found | Result |
|---|---|---|
| `kitchen-1955-*` | Repository credits *A Word to the Wives* (1955); Archive metadata gives a Public Domain Mark URL. Metadata retained as `rights-Wordtoth1955.json`. | Source assertion verified, not independent copyright/publicity clearance. Owner confirm frame provenance and intended commercial use. |
| `cars-1957-*`, `market-1957-*` | Repository credits *Shopping Can Be Fun* (1957); same Archive public-domain metadata, retained as `rights-Shopping1957.json`. | Same owner check; do not assume all files on Archive.org are public domain. |
| `book-1930.webp`–`book-1970.webp`, `sample-*.webp` | Supplied project cover/layout and actual sample-page renders; repository describes archival film/federal records. | OPEN: no per-frame extraction log or authorship/assignment document for supplied design files. Confirm layouts, all component images and any embedded fonts. |
| Three website fonts | Adjacent `tablebook-OFL.txt` and `sourceserif4-OFL.txt`. Binary metadata retains original copyrights; families renamed TableBook Sans and Porch Serif. Source reserved family name is not used for the derivative. Metadata saved in `font-metadata.json`. | PASS for supplied license presence/renaming; keep notices alongside redistribution. No font is sold on its own. |
| Free year sheets, recipe cards, booklet sample | Federal historical data / USDA text plus project layouts. All 46 year sheets remain direct downloads. | Government-origin facts/text do not grant rights to third-party design elements. Owner confirm PDF layouts and embedded font/image licensing; no new rights were invented. |
| `favicon.svg` | Simple project brand graphic, no external reference. | Owner confirm studio ownership/permission and brand rights. |

Sources: [1955 Archive item](https://archive.org/details/Wordtoth1955), [1957 Archive item](https://archive.org/details/Shopping1957), [USDA book](https://archive.org/details/familyfarefoodma00unit), [17 USC 105](https://www.copyright.gov/title17/92chap1.html#105), [OFL official conditions](https://openfontlicense.org/open-font-license-official-text/). Public-domain marking is evidence, not a warranty or model release; final film music and footage outside this repository require their own clearance.

## Accessibility

- [x] Added `/accessibility/` and linked it from every footer. It states a WCAG 2.2 AA goal, support contact, review date and limits; it does not claim certification.
- [x] Axe-core reports zero serious/critical issues on all 20 templates at phone and desktop widths. Keyboard tab/Enter, visible focus and 200% equivalent reflow are instrumented. Narrow-layout defects were corrected. See `LAUNCH-AUDIT.md` for raw evidence and scope.
- [ ] Owner: arrange assistive-technology and human reading checks, especially for the intended older audience and tagged PDFs. Extractable PDF text is not proof of correct reading order or PDF accessibility.
- [ ] Owner: verify Gumroad checkout, receipt/download and follow-up accessibility; public drafts return 404 and the owner preview requires authentication. No blanket statement of end-to-end conformance is warranted.

Reference: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/), especially keyboard, resize text, reflow and focus. The final launch decision must account for the open items in this checklist.
