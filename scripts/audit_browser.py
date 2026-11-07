#!/usr/bin/env python3
"""Axe, keyboard traversal and 200% zoom-equivalent checks on every template and device."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8115');p.add_argument('--output',default='evidence/launch-1107/after-browser.json');a=p.parse_args()
axe=(ROOT/'node_modules/axe-core/axe.min.js').read_text();results=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox'])
 for name,path in json.loads((ROOT/'data/audit-templates.json').read_text()).items():
  for device,w in [('mobile',390),('desktop',1440)]:
   context=b.new_context(viewport={'width':w,'height':900});page=context.new_page();errors=[];violations=[]
   page.on('pageerror',lambda e: errors.append(str(e)))
   page.add_init_script('window.cspViolations=[];document.addEventListener("securitypolicyviolation",e=>window.cspViolations.push({directive:e.violatedDirective,uri:e.blockedURI}));')
   response=page.goto(a.base+path)
   if response.status!=200:
    results.append({'template':name,'device':device,'unavailable':response.status});context.close();continue
   page.evaluate('document.fonts.ready');page.evaluate(axe)
   scan=page.evaluate('async () => await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa","best-practice"]}})')
   # Native focus traversal, with the first skip link actually activated by Enter.
   page.keyboard.press('Tab');first=page.evaluate('document.activeElement.getAttribute("href")')
   page.keyboard.press('Enter');skip=page.evaluate('location.hash==="#main"')
   focusable=page.locator('a[href],button:not([disabled]),input:not([type=hidden]),select,textarea').count();seen=set();bad=[]
   for _ in range(focusable+3):
    page.keyboard.press('Tab')
    f=page.evaluate('''() => {const e=document.activeElement;if(!e||e===document.body)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {key:e.tagName+':'+(e.id||e.getAttribute('href')||e.textContent.trim()),width:r.width,height:r.height,outline:s.outlineStyle,visibility:s.visibility};}''')
    if f:
     seen.add(f['key'])
     if f['width']<=0 or f['height']<=0 or f['visibility']=='hidden' or f['outline']=='none':bad.append(f)
   # CSS zoom uses the same doubled rendering/reflow goal; not a human reading or screen-reader study.
   page.context.new_cdp_session(page).send('Emulation.setDeviceMetricsOverride',{'width':w//2,'height':450,'deviceScaleFactor':2,'mobile':False});page.wait_for_timeout(50)
   zoom=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth+1, bodyFont:getComputedStyle(document.body).fontSize, zoom:getComputedStyle(document.documentElement).zoom, clippedText:[...document.querySelectorAll('p,h1,h2,label,button')].filter(e=>e.scrollHeight>e.clientHeight+2&&['hidden','clip'].includes(getComputedStyle(e).overflowY)).map(e=>e.textContent.slice(0,80))})''')
   result={'template':name,'path':path,'device':device,'status':response.status,'axe_version':scan['testEngine']['version'],'axe_violations':scan['violations'],'serious_critical':sum(v['impact'] in ['serious','critical'] for v in scan['violations']),'keyboard':{'skip_first':first=='#main','skip_activated':skip,'unique_focus_targets':len(seen),'bad_focus':bad},'zoom_200':zoom,'page_errors':errors,'csp_violations':page.evaluate('window.cspViolations')}
   results.append(result);print(name,device,'axe serious/critical',result['serious_critical'],'zoom overflow',zoom['overflow'],flush=True)
   Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps({'scope':'All templates at 390/1440px; Chrome axe-core, keyboard traversal and 200% equivalent (half CSS viewport, double device pixel ratio) reflow.','results':results},indent=2)+'\n')
   context.close()
 b.close()
Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps({'scope':'All templates at 390/1440px; real Chrome. Keyboard tab/Enter, 200% equivalent (half CSS viewport, double device pixel ratio) reflow. Automated readability proxy; no human/screen-reader certification.','results':results},indent=2)+'\n')
raise SystemExit(any(r['serious_critical'] or r['page_errors'] or r['csp_violations'] or not r['keyboard']['skip_activated'] or r['keyboard']['bad_focus'] or r['zoom_200']['overflow'] or r['zoom_200']['clippedText'] for r in results if not r.get('unavailable')))
