#!/usr/bin/env python3
"""Local browser verification. Requires Playwright and installed Chrome."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8115')
results=[]
def check(label,value):
 if not value:raise AssertionError(label)
 results.append(label)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox'])
 context=b.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 # Representative layouts at smallest phone, phone, tablet, desktop, and TV widths.
 routes=['/','/year/','/1953/','/1930/','/1975/','/your-year/','/gifts/','/1950s-life/','/kitchen/','/sources/','/privacy.html','/terms.html','/thanks/','/01/']
 for width in [320,390,768,1440,1920]:
  page.set_viewport_size({'width':width,'height':844 if width<1000 else 1080})
  for route in routes:
   response=page.goto(BASE+route,wait_until='load');page.locator('h1').wait_for()
   check(f'HTTP 200 {width} {route}',response.status==200)
   check(f'No horizontal overflow {width} {route}',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
   check(f'One H1 {width} {route}',page.locator('h1').count()==1)
   check(f'Images load {width} {route}',page.evaluate('Array.from(document.images).filter(i=>i.loading!=="lazy").every(i=>i.complete&&i.naturalWidth>0)'))
 check('No browser JavaScript exceptions',not errors)
 # Year validation and two-digit shorthand.
 page.goto(BASE+'/year/');page.locator('input[name=year]').fill('53');page.locator('.year-form button').click();page.wait_for_url('**/1953/')
 check('53 resolves to 1953',page.url.endswith('/1953/'))
 page.goto(BASE+'/year/');page.locator('input[name=year]').fill('1929');page.locator('.year-form button').click()
 check('Out-of-range year has inline error',page.locator('.form-error').is_visible())
 # Reloading a door should not invent a new conversion. Attribution survives a year lookup.
 for url,door in [('/01/','typed'),('/01/?s=q','qr'),('/01/?s=d','description'),('/01/q/','qr'),('/01/d/','description')]:
  page.goto(BASE+url)
  v=page.evaluate('JSON.parse(sessionStorage.getItem("mid_visit"))')
  check('Film door '+url,v['film']=='film01' and v['door']==door)
  page.locator('input[name=year]').fill('1946');page.locator('.year-form button').click();page.wait_for_url('**/1946/')
  after=page.evaluate('JSON.parse(sessionStorage.getItem("mid_visit"))')
  check('Door persists to year '+url,after['id']==v['id'] and after['door']==door)
 # Legacy chapter destination accepts only the kitchen.
 page.goto(BASE+'/01/?s=d&to=kitchen');page.wait_for_url('**/kitchen/')
 check('Kitchen description preserves attribution',page.evaluate('JSON.parse(sessionStorage.getItem("mid_visit")).door')=='description')
 page.goto(BASE+'/01/?to=//example.invalid');check('Untrusted destination stays local',page.url.startswith(BASE+'/01/'))
 # Direct year URL is intentionally not attributed to film 1.
 fresh=b.new_context();direct=fresh.new_page();direct.goto(BASE+'/1953/')
 v=direct.evaluate('JSON.parse(sessionStorage.getItem("mid_visit"))')
 check('Direct year is not falsely credited to a film',v['film']=='none' and v['door']=='direct')
 direct.goto(BASE+'/your-year/?year=1946#order');check('Gift birth year carried to selection',direct.locator('#book-year').input_value()=='1946')
 # Free download is an actual PDF, not a placeholder signup or a disabled button.
 response=context.request.get(BASE+'/downloads/what-things-cost-1953.pdf')
 check('Year PDF is downloadable',response.status==200 and response.body().startswith(b'%PDF'))
 check('Checkout is safely closed for draft products',page.locator('[data-checkout]').count()==0)
 # Opt-out and storage-denied resilience.
 direct.goto(BASE+'/privacy.html');direct.locator('#analytics-toggle').click()
 check('Privacy opt-out stored',direct.evaluate('localStorage.getItem("mid_analytics_off")')=='1')
 limited=b.new_context();limited.add_init_script('Object.defineProperty(window,"sessionStorage",{get(){throw new Error("denied")}});Object.defineProperty(window,"localStorage",{get(){throw new Error("denied")}});')
 blocked=limited.new_page();blocked.goto(BASE+'/');blocked.locator('input[name=year]').fill('1954');blocked.locator('.year-form button').click();blocked.wait_for_url('**/1954/');check('Lookup works with storage unavailable',True)
 # All answers and source links are usable with JavaScript disabled.
 nojs=b.new_context(java_script_enabled=False);static=nojs.new_page();static.goto(BASE+'/1953/')
 check('Prices available without JS','69.8¢' in static.locator('.price-table').inner_text())
 check('Free PDF available without JS',static.locator('a[data-download]').count()==1)
 static.goto(BASE+'/year/');check('46 year links available without JS',static.locator('.year-links a').count()==46)
 # Exercise production capture and checkout wiring using intercepted fake endpoints.
 # Requests never reach the live PostHog project or Gumroad.
 simulated=b.new_context();captured=[];checkouts=[]
 def serve_site(route):
  from urllib.parse import urlsplit
  u=urlsplit(route.request.url);response=context.request.get(BASE+u.path+('?' + u.query if u.query else ''))
  if 'text/html' in response.headers.get('content-type',''):
   body=response.text().replace('"posthog_project_key": ""','"posthog_project_key": "phc_fixture_never_sent"')
   if u.path=='/your-year/':body=body.replace('</main>','<a id="fixture-buy" href="https://oldporchpress.gumroad.com/l/mid-your-year?wanted=true&amp;variant=1953" data-checkout="youryear" data-year="1953">Fixture checkout</a></main>')
   route.fulfill(status=response.status,content_type='text/html',body=body)
  else:route.fulfill(response=response)
 simulated.route('https://makeitdoshow.com/**',serve_site)
 def receive_event(route):
  captured.append(json.loads(route.request.post_data));route.fulfill(status=200,content_type='application/json',body='{"status":1}')
 simulated.route('https://us.i.posthog.com/**',receive_event)
 def receive_checkout(route):
  checkouts.append(route.request.url);route.fulfill(status=200,content_type='text/html',body='Fixture receiver')
 simulated.route('https://oldporchpress.gumroad.com/**',receive_checkout)
 live=simulated.new_page();live.goto('https://makeitdoshow.com/01/?s=q&email=never-log@example.invalid');live.wait_for_timeout(100)
 first_visit=live.evaluate('JSON.parse(sessionStorage.getItem("mid_visit")).id')
 live.reload();live.wait_for_timeout(100)
 check('Refreshing a film door retains the visit',live.evaluate('JSON.parse(sessionStorage.getItem("mid_visit")).id')==first_visit)
 check('One visit_started across a door refresh',len([e for e in captured if e['event']=='visit_started'])==1)
 live.goto('https://makeitdoshow.com/your-year/?year=1946');live.locator('#fixture-buy').click();live.wait_for_timeout(100)
 from urllib.parse import parse_qs,urlsplit
 params=parse_qs(urlsplit(checkouts[-1]).query)
 check('Checkout carries film, QR door and selected year',params['utm_campaign']==['film01'] and params['utm_medium']==['qr'] and params['variant']==['1946'] and params['mid_year']==['1946'])
 check('Checkout carries anonymous visit identity',params['mid_visit']==[first_visit])
 check('Capture excludes query PII', 'never-log@example.invalid' not in json.dumps(captured))
 check('Checkout capture is a start, never a paid order',any(e['event']=='checkout_started' for e in captured) and not any(e['event']=='order_paid' for e in captured))
 live.goto('https://makeitdoshow.com/thanks/?amount=99999&product=youryear');live.wait_for_timeout(100)
 check('Thanks URL cannot mint revenue',not any(e['event']=='order_paid' for e in captured))
 live.goto('https://makeitdoshow.com/privacy.html');live.locator('#analytics-toggle').click();count=len(captured);live.goto('https://makeitdoshow.com/1953/');live.wait_for_timeout(100)
 check('Opt-out prevents further capture',len(captured)==count)
 # Retained visual evidence. Full-page and viewport captures for the owner.
 shot=b.new_context(device_scale_factor=1);view=shot.new_page()
 for label,w,h in [('phone',390,844),('desktop',1440,1000),('tv',1920,1080)]:
  view.set_viewport_size({'width':w,'height':h})
  for slug,route in [('home','/'),('year-1953','/1953/'),('booklet','/your-year/')]:
   view.goto(BASE+route,wait_until='networkidle');view.evaluate('document.fonts.ready');view.evaluate('async () => { await Promise.all(Array.from(document.images).map(i => {i.loading="eager";return i.decode().catch(()=>{});})); }');view.screenshot(path=str(ROOT/f'evidence/screenshots/{slug}-{label}.png'),full_page=True)
   if slug=='home':view.screenshot(path=str(ROOT/f'evidence/screenshots/home-{label}-first.png'))
 b.close()
(ROOT/'evidence/browser-checks.json').write_text(json.dumps({'checks_passed':len(results),'checks':results,'screenshots':'evidence/screenshots/','browser':'Installed Google Chrome, headless, device scale 1','widths':[320,390,768,1440,1920]},indent=2)+'\n')
print(f'{len(results)} browser checks passed; phone, desktop and TV screenshots saved.')
