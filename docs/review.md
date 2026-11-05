# Review the launch branch

Start with [home on phone](../evidence/screenshots/home-phone.png), [desktop](../evidence/screenshots/home-desktop.png), and [TV width](../evidence/screenshots/home-tv.png). First-screen captures are adjacent with `-first` in the filename. Then compare the year page and booklet page at those same three widths.

| Item | Evidence |
|---|---|
| Complete static site | 64 HTML routes; 57 in the sitemap |
| Historic year coverage | 46 pages and 46 large-print free PDFs, 1930–1975 |
| Paid-year coverage | 1930–1970 only |
| Real sample | Four-page PDF excerpt, with three interior-page previews |
| Shared atmosphere | Existing color film, warm paper, green controls, large type, self-hosted readable fonts |
| Metadata | Canonical URLs, unique descriptions, Open Graph, sitemap, matching JSON-LD |
| Local speed | Six separate-runner Lighthouse JSON/HTML reports plus retained local variability |
| Browser behavior | 312 assertions at widths 320, 390, 768, 1440, and 1920 |
| Conversion correctness | Six unit tests plus intercepted browser capture and checkout tests |
| Public state | `main` remains untouched by this work; Pages still serves it |

Reproduce static verification with `python3 scripts/verify.py` and `python3 -m unittest discover -s tests -v`. For browser QA, run a local server on 8115 and `python3 scripts/browser_qa.py`. Run Lighthouse separately with `python3 scripts/measure.py` to avoid concurrent browser contention.

Do not interpret automated accessibility 100 as a human usability study. Screen reader and keyboard behavior are supported structurally, and forms were exercised, but this task did not recruit older viewers or test a screen reader at couch distance.

The existing product drafts and missing analytics configuration are external launch gates. They do not prevent reviewing the free experience, source accuracy, visual system, or code. Details are in [launch.md](launch.md).

A direct PDF content audit found the supplied 1949 free sheet blank (861 bytes). It was rebuilt here from `data/years.json`, with dates and large print. The 1970 original has three pages, so download labels now use measured page counts rather than a blanket two-page claim. All 41 original paid booklet interiors were also checked: each has 20 pages and extractable text. These checks do not establish print quality.

The separate-runner CI passed with performance 99–100 and accessibility 100 on all six audited views. See `evidence/lighthouse/summary.json` and `ci/` for the reports; the measured source hash matches the site. No public deployment was performed.
