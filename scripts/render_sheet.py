#!/usr/bin/env python3
"""Repair a free sheet from the checked data. Requires Playwright + installed Chrome.
Only the years named on the command line are written. No network request is needed.
"""
from pathlib import Path
from html import escape
from decimal import Decimal,ROUND_HALF_UP
import base64,json,os,sys,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
YEARS=json.loads((ROOT/'data/years.json').read_text())
def font(name):return base64.b64encode((ROOT/'assets/fonts'/name).read_bytes()).decode()
def price(v):
 if v is None:return '—'
 p=Decimal(str(v)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
 return str(int(p*100))+'¢' if p<1 else f'${p:,.2f}'
def render(year,page):
 d=YEARS[str(year)]
 rows=''
 for r in d['rows']:
  label='A pound of white bread' if r['key']=='E188' else r['label']
  ref='2026' if r['key'] in {'minwage','postage_first_class_letter'} else '2025'
  rows+=f'<tr><th>{escape(label)}<small>{escape(r["unit"])}</small></th><td>{price(r["then"])}</td><td>{price(r["now"])}<small>{ref if r["now"] is not None else "Not compared"}</small></td><td>________</td></tr>'
 names=d['names'];ns=''
 if names:ns='<h2>The names in the nursery</h2><p>Girls: '+', '.join(names['girls'][:5])+'.<br>Boys: '+', '.join(names['boys'][:5])+'.</p>'
 sources=list(dict.fromkeys(re.sub(r', series E \d+$','',r['src']) for r in d['rows']))
 html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
 @font-face{{font-family:Table;src:url(data:font/woff2;base64,{font('tablebook-400.woff2')})}}@font-face{{font-family:Porch;src:url(data:font/woff2;base64,{font('sourceserif4-display.woff2')})}}
 @page{{size:Letter;margin:.55in}}*{{box-sizing:border-box}}body{{margin:0;font:16pt/1.3 Table,Arial,sans-serif;color:#252b25}}h1,h2{{font-family:Porch,Georgia,serif;font-weight:550;line-height:1.15}}h1{{font-size:24pt;margin:6pt 0}}.sheet-head{{display:flex;align-items:flex-end;justify-content:space-between;gap:14pt;margin-bottom:15pt;padding-bottom:10pt;border-bottom:2pt solid #234638}}.sheet-head>div:first-child{{max-width:340pt}}h2{{font-size:22pt}}.year{{font:65pt/1 Porch;color:#234638;margin:0}}.kicker{{font-size:14pt;letter-spacing:.05em}}table{{border-collapse:collapse;width:100%;font-size:16pt}}th,td{{text-align:left;padding:3pt 5pt;border-bottom:1px solid #cecbbd;vertical-align:top}}thead th{{font-size:14pt;background:#e9ecdf}}tbody th{{font-weight:400;width:40%}}td{{white-space:nowrap}}small{{font-size:14pt;display:block;line-height:1.3;margin-top:2pt}}tr{{break-inside:avoid}}.sources{{break-before:page}}.sources p,.sources li{{font-size:14pt;line-height:1.3;margin:6pt 0}}.sources h2{{font-size:20pt;margin:12pt 0 8pt}}li{{margin:6pt 0}}a{{color:#234638}}
 </style><title>{year} · What things cost</title></head><body><header class="sheet-head"><div><div class="kicker">MAKE IT DO · FREE SHEET</div><h1>What things cost the year you were born</h1></div><div class="year">{year}</div></header><table><thead><tr><th>The everyday things</th><th>{year}</th><th>Reference</th><th>In our house</th></tr></thead><tbody>{rows}</tbody></table><section class="sources">{ns}<h2>Read the dates beside the prices</h2><p>The reference food and gas figures are the supplied BLS 2025 averages. The stamp and federal wage figures are dated 2026. These are not live prices. Milk then was home-delivered; the reference is store-bought. Prices are rounded to the nearest cent. Original averages can include tenths of a cent.</p><p>$1 in {year} had approximately the buying power of ${d['multiplier']} in 2025, using CPI-U. A general price index is not a family budget.</p><h2>Where the numbers come from</h2><ul>{''.join('<li>'+escape(s)+'</li>' for s in sources)}</ul><p>Reference prices: BLS Average Price Data, 2025 monthly means; USPS Forever stamp, November 2026; DOL federal minimum wage. Names: SSA national birth-year data. Full linked records and exact series: <a href="https://makeitdoshow.com/{year}/#sources">makeitdoshow.com/{year}</a>.</p><p>From <cite>Everyday Life in 1950s America, in Real Color Film</cite> · Make It Do</p></section></body></html>'''
 page.set_content(html);page.evaluate('document.fonts.ready');page.pdf(path=str(ROOT/f'downloads/what-things-cost-{year}.pdf'),prefer_css_page_size=True,print_background=True)
if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox']);page=b.new_page()
  for value in sys.argv[1:]:
   if value not in YEARS:raise SystemExit('Choose 1930–1975.')
   render(int(value),page);print('Rendered',value)
  b.close()
