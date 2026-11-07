#!/usr/bin/env python3
"""Read-only real-browser buyer path. Never submit signup or payment."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'evidence/launch-1107/buyer-path';out.mkdir(parents=True,exist_ok=True);rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox']);c=b.new_context(viewport={'width':390,'height':844},device_scale_factor=1);v=c.new_page()
 def visit(name,url,note):
  try:
   r=v.goto(url,wait_until='domcontentloaded',timeout=25000);v.wait_for_timeout(300);v.screenshot(path=out/(name+'.png'),full_page=True);rows.append({'step':name,'url':v.url,'status':r.status,'title':v.title(),'note':note,'body_excerpt':v.locator('body').inner_text()[:700]})
  except Exception as e:rows.append({'step':name,'url':url,'error':type(e).__name__+': '+str(e),'note':note})
 visit('01-youtube-channel','https://www.youtube.com/@makeitdo/videos','First-film URL/description is not supplied or published in this repo; channel is only a source inspection, not proof of an actual description link.')
 visit('02-live-film-door','https://makeitdoshow.com/01/?s=d&utm_source=youtube&utm_medium=description&utm_campaign=film01','Planned description destination. Public main is different from this PR.')
 visit('03-preview-film-door','http://127.0.0.1:8115/01/?s=d&utm_source=youtube&utm_medium=description&utm_campaign=film01','Local branch preview; not deployed.')
 v.locator('input[name=year]').fill('1953');v.locator('.year-form button').focus();v.keyboard.press('Enter');v.wait_for_url('**/1953/');v.screenshot(path=out/'04-preview-year.png',full_page=True)
 visit('05-preview-booklet','http://127.0.0.1:8115/your-year/?year=1953#order','No checkout button while commerce is disabled; selected year visible.')
 visit('06-gumroad-product','https://oldporchpress.gumroad.com/l/mid-your-year?wanted=true&variant=1953','Direct existing product URL for inspection only. Stop before any payment; public draft is unavailable.')
 visit('07-preview-thanks','http://127.0.0.1:8115/thanks/','Separate preview, not a successful return from a transaction and never proof of purchase.')
 visit('08-gumroad-owner-preview','https://app.gumroad.com/products','Read-only check for accessible owner product/receipt preview. No login, publication, or purchase attempted.')
 b.close()
(out/'results.json').write_text(json.dumps({'viewport':'390x844','steps':rows,'payment_submitted':False,'emails_sent':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
