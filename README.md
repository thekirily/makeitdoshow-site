# Make It Do

Static GitHub Pages site for makeitdoshow.com. Work is on `launch`; `main` is public.

Build and inspect locally (Python 3.12+, no build dependencies):

```bash
python3 scripts/build.py
python3 scripts/verify.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8115 --bind 127.0.0.1
```

Open http://127.0.0.1:8115. Content/data inputs are in `scripts/build.py` and `data/`; generated HTML is committed for GitHub Pages. Shared assets are in `assets/`. No runtime package install is required.

Browser QA requires the existing Python Playwright install and Chrome. `python3 scripts/browser_qa.py` verifies responsive layouts and attribution with intercepted test endpoints and saves screenshots. `python3 scripts/measure.py` runs Lighthouse 13.6.0 via npm, serially, and saves the raw reports. Run those independently so the browsers do not compete during speed measurements. `python3 scripts/verify_pdfs.py` additionally checks printable content and measured page counts with the existing PyMuPDF installation. `scripts/render_sheet.py 1949` reproduces the repaired sheet; do not regenerate other years unless their sources change.

Read [handback.md](handback.md), [launch details](docs/launch.md), [tracking](docs/tracking.md), and [search/design evidence](docs/search-and-evidence.md). The owner's publication command is `./scripts/publish.sh`. It deliberately stops while the existing PostHog configuration and Gumroad/fulfillment launch gates remain unresolved.
