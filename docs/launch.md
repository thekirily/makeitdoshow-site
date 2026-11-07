# Film 1: publication and remaining connections

The branch is a static GitHub Pages site. No server, paid dependency, new account, or Site hosting registration is needed. `main` remains the public branch, with the existing `CNAME` untouched. The branch is deliberately safe to preview: the supplied Gumroad records say every product is unpublished; no purchase or email-signup button sends someone to a draft.

## Current launch gates

1. The supplied tracking folder uses an older product's Umami property and explicitly says it is a separate account. No callable PostHog connector or project-local configuration was found. Do not reuse the other channel's project. Put the **existing Make It Do public capture key** and its ingest host in `data/site.json`. This is a write-only browser project token, never a personal PostHog API token. The owner was asked for the existing configuration's path. No secret is needed in chat.
2. Publish the already-created `free_sheet`, `free_cards`, and `youryear` Gumroad products through the existing product workflow, after fulfillment is ready. This task did not publish drafts, charge a card, order a proof, open an account, or change the supplier. Set the booklet to require a shipping address / physical delivery in Gumroad. The API in the supplied handback could not toggle this setting. The supplier decision now prefers Prodigi for the booklet, whereas the supplied order robot still uses Lulu; choose and prove the adapter before opening orders. This website does not submit print jobs.
3. Set `commerce_enabled` and `free_email_enabled` true only after those products work. Rebuild with `python3 scripts/build.py`; verify, review, and commit the generated changes. Preview text and product schema derive their availability from these flags. Before activating, update the “orders open with the film” wording, stock notes, and privacy shipping description to match the actual enabled service. No live sale, email delivery, shipping, or refund was tested here.
4. In the existing repository, give the conversion workflow access to `GUMROAD_ACCESS_TOKEN` as an Actions secret. The public project capture key/host may come from `data/site.json`, or repository variables `POSTHOG_PROJECT_KEY` and `POSTHOG_HOST`. The scheduled workflow runs only on `main`; it does not run on `launch`. No credentials are in this repository.

## Real acceptance checks before film upload

Use a genuine checkout verification through the existing product workflow; do not infer fulfillment from an HTTP 200. Confirm correct year, cover name, shipping-address collection, payment and tax amount, PDF receipt, intended print adapter, and delivery estimate. Verify the sign-up and order appear in Gumroad and then in PostHog as separate completed events. A `checkout_started` event is not an order. A `/thanks/` visit is not an order. Direct free PDF downloads are `sheet_downloaded`, not signups.

`python3 scripts/preflight.py` reads the live Gumroad API when the flags are enabled, checks publication, advertised prices, and physical-address collection, and never publishes anything. It stops when configuration is missing. It cannot prove print quality or fulfillment.

## Publication: one command, run by the owner

From the clean, committed `launch` checkout at film upload:

```bash
./scripts/publish.sh
```

The script checks the launch gates and static tests, fetches public `main`, and verifies it is included in this checkout. It then finds the open launch PR, verifies its head matches this checkout, marks it ready if needed, and merges through GitHub with a matching-head guard. It does not force-push, bypass branch rules, delete branches, publish products, or discard edits. The PR merge route supports the existing shell credential, which cannot introduce workflow files through a direct Git push. The agent did not run this command.

## Film doors: keep these addresses in the edit

- Spoken address: `makeitdoshow.com/01` (exact film/door attribution).
- Existing spoken alternative: `makeitdoshow.com/1953`, with the viewer substituting their birth year. It works; a visit without a referrer cannot establish whether it came from this film, a bookmark, a private message, or another source. Such visits remain direct/unattributed. Do not quietly relabel them as film01.
- QR: `https://makeitdoshow.com/01/?s=q` (the existing film-1 QR target remains compatible).
- Description: `https://makeitdoshow.com/01/?s=d`.
- Kitchen description: `https://makeitdoshow.com/01/?s=d&to=kitchen`.
- `/01/q/` and `/01/d/` also work, with attribution independent of query strings.

The existing narration does not need to change to make the free answer work. Use `/01` if exact spoken-door measurement is required. No analytics system can reconstruct an absent referrer with certainty.

## Google and AI discovery after publication

The sitemap is `https://makeitdoshow.com/sitemap.xml`. Submit it in the existing Search Console property if one is available, then inspect home, `/1953/`, `/your-year/`, and `/1950s-life/`. No new account is required by the code. Validate the public URLs in Google's Rich Results Test after publication. No claim of live indexing or rich-result eligibility is made from local JSON parsing.

Use Search Console for impressions/clicks and indexed pages. Use PostHog for landing pages, referred visits, year lookups, downloads, checkout starts, and verified conversions. AI referrers are a lower bound; many assistants and browsers do not send a referrer. Google AI Overviews traffic cannot reliably be separated from ordinary Google visits by this site. A crawlable page is eligible for consideration, not guaranteed a ranking or recommendation.

## Workflow permission during this build

The shell OAuth credential could push site files but could not introduce workflow files. The existing GitHub app could, and added both workflows directly to `launch`. No account permissions were changed. The verification workflow measures this branch without deployment; the conversion schedule is restricted to `main`. Future workflow edits need a credential with the appropriate permission or the same existing GitHub app.
