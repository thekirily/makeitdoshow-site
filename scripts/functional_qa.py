#!/usr/bin/env python3
"""Functional site checks without analytics permission, across all supported layouts."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8115');checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox']);c=b.new_context();v=c.new_page();errors=[];v.on('pageerror',lambda e:errors.append(str(e)))
 for w in [320,390,768,1440,1920]:
  v.set_viewport_size({'width':w,'height':900})
  for name,path in json.loads((ROOT/'data/audit-templates.json').read_text()).items():
   r=v.goto(BASE+path)
   check(f'HTTP 200 {name} {w}',r.status==200);check(f'One heading {name} {w}',v.locator('h1').count()==1);check(f'No page overflow {name} {w}',v.evaluate('document.documentElement.scrollWidth<=innerWidth'))
 v.goto(BASE+'/year/');v.locator('input[name=year]').fill('53');v.locator('input[name=year]').press('Enter');v.wait_for_url('**/1953/');check('Keyboard year shorthand works',True)
 v.goto(BASE+'/year/');v.locator('input[name=year]').fill('1929');v.locator('.year-form button').click();check('Invalid year has visible error',v.locator('.form-error').is_visible())
 v.goto(BASE+'/01/?to=//example.invalid');check('Untrusted redirect stays local',v.url.startswith(BASE+'/01/'))
 check('Unconfigured analytics has no stored visit',v.evaluate('sessionStorage.getItem("mid_visit")') is None)
 r=c.request.get(BASE+'/downloads/what-things-cost-1953.pdf');check('Free sheet is an actual downloadable PDF',r.status==200 and r.body().startswith(b'%PDF'))
 c2=b.new_context(java_script_enabled=False);s=c2.new_page();s.goto(BASE+'/1953/');check('Prices and downloads without JavaScript',s.locator('.price-table').count()==1 and s.locator('[data-download]').count()==1);s.goto(BASE+'/year/');check('All 46 years available without JavaScript',s.locator('.year-links a').count()==46)
 c3=b.new_context();c3.add_init_script('Object.defineProperty(window,"sessionStorage",{get(){throw Error("denied")}});Object.defineProperty(window,"localStorage",{get(){throw Error("denied")}});');s=c3.new_page();s.goto(BASE+'/year/');s.locator('input[name=year]').fill('1954');s.locator('.year-form button').click();s.wait_for_url('**/1954/');check('Year lookup with denied storage',True)
 check('No browser exceptions',not errors);b.close()
out={'passed':len(checks),'checks':checks};(ROOT/'evidence/launch-1107/functional.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':len(checks)},indent=2))
