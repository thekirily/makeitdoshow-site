# Make It Do — launch branch

Work is on `launch`. The public `main` branch and GitHub Pages publishing source are unchanged. The newer public-main commit that makes each channel sell under its own name is included.

## Built

A shared film-world design using the actual color footage, warm paper, large type, readable self-hosted fonts, and green controls. The site includes the home, 46 year pages (1930–1975), a year directory, a $49 booklet page with a four-page real sample, a gift page, a sourced 1950s-life article, recipe cards, sources/method, about, privacy, terms, film doors, thanks, and 404. There are 64 HTML routes and 57 sitemap entries.

The free answer appears before any signup. Every sheet is a direct PDF download without an email or card. The supplied 1949 PDF was blank; it was rebuilt from the checked year data. Most sheets have two pages; 1949 and 1970 have three. Download labels use measured page counts. All 46 now contain text and their year, with approximately 14-point minimum type. All 41 source booklet interiors have 20 pages and readable text; a print proof was not ordered.

Prices, baby names, recipes, and film dates retain their sources. Reference prices are dated rather than called live “today” prices. The 1971–1975 pages are explicitly partial and have no booklet offer. Unsupported delivery and unconditional refund promises were removed. Privacy and terms retain the existing YouTube API disclosure and contact address.

Search work includes full static answers, semantic tables, primary-source links, distinct titles/descriptions, canonical URLs, social cards, sitemap, and matching Organization, WebPage, Breadcrumb, Article, Dataset, and Product markup. Product availability is closed while the drafts are unpublished. Google's [AI guidance](https://developers.google.com/search/docs/appearance/ai-features) does not require a separate AI-SEO markup layer; this work follows crawlability, readable evidence, and useful content. No indexing, ranking, or AI citation is promised.

## Counting and launch gates

The film doors preserve the existing QR target: `/01/?s=q`; description is `/01/?s=d`; an exact spoken door is `/01/`. `/01/q/` and `/01/d/` also work. A direct `/1953/` visit cannot prove it came from the film, so it stays unattributed. First-touch film and door survive internal navigation. The code honors analytics opt-out, DNT, and GPC, and excludes personal details from event payloads.

Completed signups and orders come from authenticated Gumroad sales, never a thank-you URL. A free download is not called a signup, and a checkout click is not called an order. The server importer supports pagination, deterministic event UUIDs, and separate refunds; a scheduled workflow can run on `main` after configuration. Six unit tests and intercepted browser requests cover these distinctions.

**Not live:** the supplied Gumroad products are drafts, the existing Make It Do PostHog public key/host has not been located, and real fulfillment must be confirmed. The supplied tracking folder uses an older product's Umami property, which was not reused. Repository secret/variable listings were empty. Checkout and email signup remain closed; free downloads work now. The supplier decision prefers Prodigi for the booklet while the supplied robot uses Lulu; the site does not pretend that adapter is proven. Details: [launch gates](docs/launch.md) and [tracking](docs/tracking.md).

## Verification and screenshots

Static verification passed: 1,964 internal references, all 46 year downloads, canonical routes, and parsed JSON-LD. There are 312 passing browser checks at 320, 390, 768, 1440, and 1920 pixels, including year lookup, invalid input, working without storage or JavaScript, attribution, checkout parameters, and privacy choices. This is not a human usability study or Google's live Rich Results Test.

| View | Home | Year page | Booklet |
|---|---|---|---|
| Phone, 390 px | [Screenshot](evidence/screenshots/home-phone.png) | [1953](evidence/screenshots/year-1953-phone.png) | [Booklet](evidence/screenshots/booklet-phone.png) |
| Desktop, 1440 px | [Screenshot](evidence/screenshots/home-desktop.png) | [1953](evidence/screenshots/year-1953-desktop.png) | [Booklet](evidence/screenshots/booklet-desktop.png) |
| TV, 1920 px | [Screenshot](evidence/screenshots/home-tv.png) | [1953](evidence/screenshots/year-1953-tv.png) | [Booklet](evidence/screenshots/booklet-tv.png) |

Lighthouse 13.6.0 passed on a separate free GitHub Actions runner. **Accessibility, best practices, and SEO scored 100 for every audited view.**

| View | Performance | LCP | Total blocking time |
|---|---:|---:|---:|
| Home · mobile | 97 | 1.53 s | 100 ms |
| Home · desktop | 100 | 0.38 s | 0 ms |
| 1953 prices · mobile | 100 | 0.90 s | 2 ms |
| Booklet · mobile | 99 | 2.03 s | 11 ms |
| Gifts · mobile | 100 | 0.90 s | 0 ms |
| 1950s life · mobile | 100 | 0.95 s | 0 ms |

[Successful CI run](https://github.com/thekirily/makeitdoshow-site/actions/runs/42072944731) · [Machine-readable summary](evidence/lighthouse/summary.json) · [Raw reports](evidence/lighthouse/ci-current). A prior separate-runner pass scored 99–100 performance and is also retained in `ci/`; the current pass scored 97–100. The source fingerprint matches the delivered site. These are simulated lab checks against a local HTTP server, not live CDN or field measurements. PostHog and commerce are disabled in the measured build.

The shared eight-core local host had load averages up to 29 and unstable results: home-mobile scores 58, 91, and 84; booklet-mobile 71, 98, and 94. Those raw runs remain under `run-1`, `run-2`, and `run-3`, with [local medians](evidence/lighthouse/local-summary.json). The separate-runner result is reported with its own environment, rather than selecting the best local score.

## What would prove this wrong

- Older viewers cannot find their free year or read the controls without help. Automated accessibility 100 does not settle that.
- After ordering opens and attribution is verified, fewer than 20% of 500 qualified film visits download a sheet, or fewer than 1% place a $49 order. Those are test thresholds, not current results; exclude closed-checkout and partial-year visits.
- A real Gumroad transaction loses its year/door, a PostHog count disagrees with known sales after refunds, or a print job uses the wrong name/year. Do not infer success from fixtures.
- Indexed year pages receive no relevant non-brand impressions after eight weeks, or search visitors leave without using the answer. Check indexing and intent before producing more pages.
- A clean-device or live measurement repeatedly shows mobile LCP over 2.5 seconds, or the delivered booklet does not look like the sample.

## With more time

Observe several 55–80-year-old viewers using a phone and a TV address, plus adult children buying a gift. Verify the existing checkout → PDF → selected print adapter → receipt chain with a real accepted order through the product workflow. Use a physical proof for photography only after it exists. Extend the food series beyond 1970 from checked records; do not manufacture missing data. Review Search Console and actual referral/conversion data before changing price or adding keyword pages. Live analytics, fulfillment, print quality, and indexing remain unverified.

## The one command that publishes

From a clean, committed `launch` checkout, the owner runs this at film upload:

```bash
./scripts/publish.sh
```

It checks the launch gates, verifies the live Gumroad products when enabled, runs static checks, fetches `main`, and merges the reviewed launch PR with a matching-head guard. It does not force-push or overwrite concurrent edits. It uses GitHub’s PR merge route because the existing shell credential cannot introduce workflow files through a direct push. It currently refuses publication because the configuration and product gates above remain unresolved. The agent did not run it. No account was opened and no money was spent.
