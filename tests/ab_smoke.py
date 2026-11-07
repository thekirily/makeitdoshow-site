#!/usr/bin/env python3
"""Exercise real flag, capture, consent, checkout and sync code with network-isolated fixtures."""
import importlib.util,json,os,time
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];BASE=os.environ.get('PREVIEW_URL','http://127.0.0.1:8115');ORIGIN='https://makeitdoshow.com'
spec=importlib.util.spec_from_file_location('sales',ROOT/'scripts/sync_sales.py');sales=importlib.util.module_from_spec(spec);spec.loader.exec_module(sales)
checks=[]
def check(label,value):
 if not value:raise AssertionError(label)
 checks.append(label)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox'])
 for variant in ['control','variant','generic-campaign','timeout','error','declined','dnt','gpc','storage-denied','unconfigured']:
  context=browser.new_context(viewport={'width':390,'height':844});events=[];flag_requests=[];checkouts=[];errors=[]
  consent='no' if variant=='declined' else 'yes'
  context.add_init_script(f"localStorage.setItem('mid_analytics_consent','{consent}');")
  if variant in ['dnt','gpc']:context.add_init_script('Object.defineProperty(navigator,'+json.dumps('doNotTrack' if variant=='dnt' else 'globalPrivacyControl')+',{get:()=>'+('"1"' if variant=='dnt' else 'true')+'});')
  if variant=='storage-denied':context.add_init_script('Object.defineProperty(window,"sessionStorage",{get(){throw Error("denied")}});Object.defineProperty(window,"localStorage",{get(){throw Error("denied")}});')
  def serve(route):
   u=urlsplit(route.request.url);r=context.request.get(BASE+u.path+('?' + u.query if u.query else ''))
   if 'text/html' not in r.headers.get('content-type',''):route.fulfill(response=r);return
   body=r.text();start=body.index('<script id="site-config"');start=body.index('>',start)+1;end=body.index('</script>',start);cfg=json.loads(body[start:end])
   cfg['posthog_project_key']='' if variant=='unconfigured' else 'phc_fixture_never_sent'
   cfg['experiment']={'enabled':u.path=='/','key':'launch-presentation-v1','variants':{'control':{},'variant':{'headline':'Fixture alternative headline','price':'$49','hero':{'src':'kitchen-1955-c.webp','alt':'Fixture kitchen image'}}}}
   body=body[:start]+json.dumps(cfg)+body[end:]
   if cfg['experiment']['enabled']:body=body.replace('<script defer src="/assets/experiments.js">','<script src="/assets/experiments.js">')
   # Same-origin JS and specific ingest host remain enforced. Production config JSON hashes do not apply to intercepted fixtures.
   body=body.replace("connect-src &#x27;self&#x27;",'connect-src https://us.i.posthog.com')
   if u.path=='/your-year/':body=body.replace('</main>','<a id="fixture-buy" href="https://oldporchpress.gumroad.com/l/mid-your-year?wanted=true" data-checkout="youryear" data-year="1953">Fixture checkout</a></main>')
   route.fulfill(status=200,content_type='text/html',body=body)
  context.route(ORIGIN+'/**',serve)
  def flags(route):
   flag_requests.append(json.loads(route.request.post_data))
   if variant=='timeout':time.sleep(.4)
   if variant=='error':route.fulfill(status=503,body='unavailable');return
   route.fulfill(status=200,content_type='application/json',body=json.dumps({'requestId':'fixture','flags':{'launch-presentation-v1':{'enabled':True,'variant':variant if variant in ['control','variant'] else 'control'}}}))
  context.route('https://us.i.posthog.com/flags**',flags)
  def capture(route):events.append(json.loads(route.request.post_data));route.fulfill(status=200,content_type='application/json',body='{"status":1}')
  context.route('https://us.i.posthog.com/i/**',capture)
  def checkout(route):checkouts.append(route.request.url);route.fulfill(status=200,content_type='text/html',body='Fixture checkout receiver; no payment service contacted')
  context.route('https://oldporchpress.gumroad.com/**',checkout)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(ORIGIN+('/year/?utm_source=newsletter&utm_medium=email&utm_campaign=autumn&utm_content=launch_link' if variant=='generic-campaign' else '/01/?s=d&utm_source=youtube&utm_medium=description&utm_campaign=film01&utm_content=description_link&email=private@example.invalid'));page.wait_for_timeout(50)
  page.goto(ORIGIN+'/');page.wait_for_timeout(500)
  blocked=variant in ['declined','dnt','gpc','storage-denied','unconfigured']
  if blocked:
   check(variant+' no analytics or flags',not events and not flag_requests)
   if variant!='storage-denied':check(variant+' no visit stored',page.evaluate('sessionStorage.getItem("mid_visit")') is None)
  elif variant in ['control','variant','generic-campaign']:
   expected='Fixture alternative headline' if variant=='variant' else 'The past was'
   check(variant+' renders',expected in page.locator('[data-ab-slot=headline]').inner_text())
   check(variant+' exposed once',len([e for e in events if e['event']=='experiment_exposed'])==1)
   check(variant+' PostHog exposure once',len([e for e in events if e['event']=='$feature_flag_called'])==1)
   check(variant+' hold below 300ms',page.evaluate('window.midExperiment.hold_ms')<300)
  else:
   check(variant+' original visible, no late swap', 'The past was' in page.locator('h1').inner_text() and not page.evaluate('document.documentElement.classList.contains("ab-pending")'))
   check(variant+' no false exposure',not any(e['event']=='experiment_exposed' for e in events))
  page.goto(ORIGIN+'/your-year/?year=1946');page.locator('#fixture-buy').click();page.wait_for_timeout(100)
  params={k:v[-1] for k,v in parse_qs(urlsplit(checkouts[-1]).query).items()}
  check(variant+' selected product year',params.get('mid_year')=='1946')
  if not blocked:
   check(variant+' one CTA and checkout start',len([e for e in events if e['event']=='cta_clicked'])==1 and len([e for e in events if e['event']=='checkout_started'])==1)
   check(variant+' one pageview per navigation',len([e for e in events if e['event']=='$pageview'])==3)
   if variant=='generic-campaign':
    check('Generic campaign survives without becoming a film',params.get('utm_campaign')=='autumn' and params.get('utm_source')=='newsletter' and params.get('utm_medium')=='email' and params.get('mid_film')=='none')
   else:check(variant+' door and campaign survive',params.get('utm_campaign')=='film01' and params.get('utm_medium')=='description' and params.get('utm_content')=='description_link')
   check(variant+' no PII in capture','private@example.invalid' not in json.dumps(events))
  else:check(variant+' checkout omits tracking identity',params.get('mid_analytics')=='no' and 'mid_visit' not in params)
  sale={'id':'fixture-'+variant,'product_id':sales.PRODUCTS['youryear']['id'],'created_at':'2026-11-07T00:00:00Z','price':4900,'currency':'usd','url_params':params}
  converted=sales.events_for_sale(sale)
  check(variant+' sync honors permission',bool(converted)!=blocked)
  if not blocked:
   check(variant+' paid conversion deterministic',converted==sales.events_for_sale(sale) and converted[0]['event']=='order_paid')
   check(variant+' sale joins browser',converted[0]['properties']['distinct_id']==params['mid_visit'])
   if variant in ['control','variant']:check(variant+' experiment reaches conversion',converted[0]['properties']['$feature/launch-presentation-v1']==variant)
   free=sales.events_for_sale({**sale,'product_id':sales.PRODUCTS['free_sheet']['id'],'price':0})
   check(variant+' verified free signup',len(free)==1 and free[0]['event']=='signup_completed')
  page.goto(ORIGIN+'/thanks/?amount=99999');page.wait_for_timeout(50)
  check(variant+' thank-you never mints sale',not any(e['event'] in ['order_paid','signup_completed'] for e in events))
  if not blocked:
   page.goto(ORIGIN+'/privacy.html');page.locator('#analytics-toggle').click();page.wait_for_timeout(50);count=len(events)
   check(variant+' withdrawal clears storage',page.evaluate('sessionStorage.getItem("mid_visit")') is None)
   page.goto(ORIGIN+'/1953/');page.wait_for_timeout(50);check(variant+' withdrawal stops events',len(events)==count)
  check(variant+' no script exceptions',not errors)
  context.close()
 # First-time visitor: opt-in is needed and decline works by keyboard.
 c=browser.new_context();seen=[]
 def real_local(route):
  r=c.request.get(BASE+urlsplit(route.request.url).path)
  if 'html' not in r.headers['content-type']:route.fulfill(response=r);return
  body=r.text().replace('"posthog_project_key": ""','"posthog_project_key": "phc_fixture_never_sent"').replace("connect-src &#x27;self&#x27;",'connect-src https://us.i.posthog.com')
  route.fulfill(status=200,content_type=r.headers['content-type'],body=body)
 c.route(ORIGIN+'/**',real_local);c.route('https://us.i.posthog.com/**',lambda r:(seen.append(r.request.url),r.fulfill(status=200,body='{"status":1}')))
 v=c.new_page();v.goto(ORIGIN+'/01/?s=q');v.wait_for_timeout(50);check('first visit no capture or storage',not seen and v.evaluate('sessionStorage.length')==0)
 v.locator('[data-consent=yes]').focus();v.keyboard.press('Enter');v.wait_for_timeout(50);check('keyboard consent starts analytics',len(seen)==2)
 browser.close()
out={'checks':checks,'passed':len(checks),'scope':'Real Chrome; all PostHog and Gumroad traffic intercepted; authenticated-sale fixtures, no real signup or payment.'}
(ROOT/'evidence/launch-1107/ab-smoke.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
