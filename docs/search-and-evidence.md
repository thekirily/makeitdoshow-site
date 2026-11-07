# Search, AI discovery, and the design evidence

## What was implemented

The site serves complete static HTML at stable URLs, including a distinct answer, semantic price table, source links, dated comparisons, names, and a free PDF for each available year. Prices are visible without JavaScript or signup. The main discovery paths are `/year/`, `/1930/`–`/1975/`, `/1950s-life/`, `/gifts/`, `/your-year/`, and `/kitchen/`. These are linked through ordinary anchors, with a sitemap, canonical URLs, social previews, page descriptions, and a helpful static 404.

Structured data is limited to what the page actually shows: Organization, WebSite, WebPage, BreadcrumbList, an Article on the 1950s-life page, Dataset information on year pages, and a Product/Offer on the booklet page. The offer says OutOfStock while checkout is closed. No invented review, rating, aggregate count, event, or FAQ rich-result claim is present. The data JSON is public and linked through Dataset distribution; that is a convenience for reuse, not a guarantee of AI citation.

Google's AI-features guidance says the usual SEO practices apply and does not require special AI markup or files. Accordingly, this implementation concentrates on readable answers, primary sources, ordinary crawlable links, dated claims, and matching structured data. There is no hidden “AI answer,” keyword doorway farm, or promise that a model will recommend the site.

Primary documentation read live November 5, 2026:

- [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- [General structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)
- [Product snippet structured data](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)

The local checks parse JSON-LD and crawl internal links. They are not Google's Rich Results Test, and local Lighthouse SEO is not proof of indexing or rankings. After owner publication, use Search Console and Google's public validators on the real URLs. Assistant referral counts are incomplete; absent referrers cannot be reconstructed.

## Material actually inspected

- Existing `money-rung5-1104/site` year, kitchen, film door, and client code; `MONEY.md`, the handback, `TYPE.md`, `data/years.json`, `data/recipes.json`, `data/gumroad_ids.json`, free PDFs, booklet interior, and sample cover.
- `suppliers-1104/SETUP.md`, including its final Prodigi decision and the remaining cloth/Lulu exception. The site avoids a printer promise until the fulfillment adapter is confirmed.
- `product-oldamerica-1103/tracking/README.md`, links CSV, and the old first-touch convention. It uses an older Umami account, not the requested PostHog connection. It also attributed direct visits to the latest film and counted a thank-you URL as a purchase. Those assumptions were not retained.
- `brand-flows-1104/found.md`, Storyworth's captured landing page and first purchase wizard, and Vermont Country Store's actual product page. The borrowed hypotheses are a clear tangible offer, readable inclusions, a visible full price, and gift details at checkout. There are no borrowed awards, ratings, counts, subscriptions, sale timers, or customer quotes.
- The 79-page collection's page inventory, relevant screen readings, and the Storyworth, Artifact Uprising, Townsends, and Tasting History examples. Those show ways to carry a film's atmosphere into a real object, expose the interior, and answer format and gift questions. They are observations, not proof that these layouts will convert this audience.

## Deliberate corrections to the old build

- Kept Make It Do as the selling brand, preserving the newer public-main commit rather than restoring Old Porch Press as the visible seller.
- Replaced preview alerts and a full-site preview banner with a working direct free download and accurate local product availability.
- Did not promise 7–10-day print delivery. The supplier material did not support it.
- Did not promise an unconditional 30-day refund; the handback called that an owner decision. The existing damaged/wrong-order support commitment remains.
- Kept large-print sheets (mostly two pages), 20-page booklet, and 5-by-8 recipe cards, using the latest TYPE findings rather than the earlier 16-page / 4-by-6 descriptions.
- Kept 1971–1975 partial and did not sell a booklet for a year outside the verified food table.
- Identified archival film frames by their actual 1955/1957 dates even when beside a different birth year. The film is not a household survey.
- Separated direct downloads, started signups, completed signups, checkout starts, and confirmed orders.

A direct PDF content audit found the supplied 1949 free sheet blank (861 bytes). It was rebuilt here from `data/years.json`, with dates and large print. The 1970 original has three pages, so download labels now use measured page counts rather than a blanket two-page claim. All 41 original paid booklet interiors were also checked: each has 20 pages and extractable text. These checks do not establish print quality.
