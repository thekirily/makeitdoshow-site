#!/usr/bin/env python3
"""Build an isolated enabled signup fixture, verify native validation and POST without sending email."""
import json,os,subprocess,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
with tempfile.TemporaryDirectory(prefix='mid-signup-') as tmp:
 dest=Path(tmp)
 # Minimal isolated build inputs; never toggle the working tree or production config.
 import shutil
 for name in ['scripts','data','assets']:shutil.copytree(ROOT/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
 c=json.loads((dest/'data/site.json').read_text());c['email_capture'].update(enabled=True,form_action='https://fixture.sibforms.com/serve/fixture-not-live',double_opt_in_verified=True);(dest/'data/site.json').write_text(json.dumps(c))
 subprocess.run(['python3',str(dest/'scripts/build.py')],check=True,capture_output=True)
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':390,'height':844});posts=[]
  def local(route):
   from urllib.parse import urlsplit
   path=urlsplit(route.request.url).path.lstrip('/') or 'index.html';p=dest/path
   route.fulfill(path=p)
  ctx.route('https://makeitdoshow.com/**',local)
  def receive(route):posts.append({'method':route.request.method,'data':route.request.post_data});route.fulfill(status=200,content_type='text/html',body='Fixture provider: check your email. No email was sent.')
  ctx.route('https://fixture.sibforms.com/**',receive)
  page=ctx.new_page();page.goto('https://makeitdoshow.com/');form=page.locator('.email-signup')
  assert form.count()==1;checks.append('Enabled configuration renders signup')
  form.locator('button').click();assert not posts;checks.append('Empty email blocked by native validation')
  form.locator('[name=EMAIL]').fill('fixture@example.invalid');form.locator('button').click();assert not posts;checks.append('Separate marketing permission required')
  form.locator('[name=OPT_IN]').check();form.locator('button').focus();page.keyboard.press('Enter');page.wait_for_timeout(100)
  assert len(posts)==1 and posts[0]['method']=='POST' and 'EMAIL=fixture%40example.invalid' in posts[0]['data'];checks.append('One native POST reaches only the configured hosted Brevo endpoint')
  b.close()
 c['email_capture']['double_opt_in_verified']=False;(dest/'data/site.json').write_text(json.dumps(c));result=subprocess.run(['python3',str(dest/'scripts/build.py')],capture_output=True);assert result.returncode!=0;checks.append('Build refuses signup without DOI attestation')
assert not json.loads((ROOT/'data/site.json').read_text())['email_capture']['enabled'];checks.append('Production form remains off')
out={'checks':checks,'passed':len(checks),'scope':'Fixture POST intercepted. Provider double opt-in, email delivery and spam placement require an account and DNS verification.'};(ROOT/'evidence/launch-1107/signup-smoke.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
