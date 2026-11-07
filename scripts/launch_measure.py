#!/usr/bin/env python3
"""One serial Lighthouse run per template/device; strict launch budgets, retained output."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8115');p.add_argument('--output',required=True);p.add_argument('--site-root',type=Path,default=ROOT);a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
def fingerprint():
 files=sorted(p for p in a.site_root.rglob('*') if p.is_file() and not {'evidence','node_modules','.git','.playwright-mcp'} & set(p.relative_to(a.site_root).parts) and (p.suffix=='.html' or 'assets' in p.relative_to(a.site_root).parts or p.name=='robots.txt'))
 return hashlib.sha256(''.join(str(p.relative_to(a.site_root))+':'+hashlib.sha256(p.read_bytes()).hexdigest()+'\n' for p in files).encode()).hexdigest()
source_sha256=fingerprint()
results=[]
for name,route in json.loads((ROOT/'data/audit-templates.json').read_text()).items():
 for device in ['mobile','desktop']:
  label=name+'-'+device
  cmd=[str(ROOT/'node_modules/.bin/lighthouse'),a.base+route,'--chrome-flags=--headless --no-sandbox','--output=json','--output-path='+str(out/(label+'.json')),'--only-categories=performance,accessibility,best-practices,seo','--quiet']
  if device=='desktop':cmd+=['--preset=desktop']
  started=time.time();load=os.getloadavg()
  run=subprocess.run(cmd,env={**os.environ,'CHROME_PATH':os.environ.get('CHROME_PATH','/usr/bin/google-chrome')},capture_output=True,text=True)
  if run.returncode:
   results.append({'name':name,'device':device,'error':run.stderr[-2000:]});print(label,'ERROR',flush=True)
  else:
   d=json.loads((out/(label+'.json')).read_text());aud=d['audits']
   scores={k:round(v['score']*100) for k,v in d['categories'].items()}
   vals={k:aud[id]['numericValue'] for k,id in [('lcp_ms','largest-contentful-paint'),('cls','cumulative-layout-shift'),('tbt_ms','total-blocking-time'),('bytes','total-byte-weight')]}
   failures=[k for k,v in scores.items() if v<95]+[k for k,limit in [('lcp_ms',2000),('cls',.05),('tbt_ms',150)] if vals[k]>=limit]
   results.append({'name':name,'route':route,'device':device,'scores':scores,**vals,'failures':failures,'load':load,'seconds':round(time.time()-started,1),'version':d['lighthouseVersion'],'fetch_time':d['fetchTime'],'failed_audits':{k:{'title':v['title'],'score':v['score'],'details':v.get('details')} for k,v in aud.items() if v.get('score') is not None and v['score']<1 and v.get('scoreDisplayMode') not in ['informative','notApplicable']}})
   print(label,scores,{k:round(v,3) for k,v in vals.items()},'FAIL '+','.join(failures) if failures else 'PASS',flush=True)
  (out/'summary.json').write_text(json.dumps({'source_sha256':source_sha256,'scope':'Local HTTP preview, one run per template/device, simulated throttling; NOT field data.', 'results':results},indent=2)+'\n')

assert fingerprint()==source_sha256, "Measured source changed; results are not a stable-build measurement."
