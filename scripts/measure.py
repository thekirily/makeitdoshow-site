#!/usr/bin/env python3
"""Run Lighthouse serially to avoid browser contention; save raw reports and summary."""
import json,os,subprocess,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=os.environ.get('PREVIEW_URL','http://127.0.0.1:8115')
matrix=[('home-mobile','/','mobile'),('home-desktop','/','desktop'),('year-1953-mobile','/1953/','mobile'),('booklet-mobile','/your-year/','mobile'),('gifts-mobile','/gifts/','mobile'),('life-mobile','/1950s-life/','mobile')]
def fingerprint():
 paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and (p.suffix=='.html' and 'evidence' not in p.parts or p.parts[len(ROOT.parts)] in {'assets','data','downloads'}))
 return hashlib.sha256(''.join(str(p.relative_to(ROOT))+':'+hashlib.sha256(p.read_bytes()).hexdigest()+'\n' for p in paths).encode()).hexdigest()
source_fingerprint=fingerprint()
parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*');parser.add_argument('--directory',default='evidence/lighthouse');args=parser.parse_args()
output=ROOT/args.directory;output.mkdir(parents=True,exist_ok=True)
summary=[]
for name,path,device in matrix:
 if args.only and name not in args.only:continue
 load_start=os.getloadavg()
 cmd=['npm','exec','--yes','--package=lighthouse@13.6.0','--','lighthouse',base+path,'--chrome-flags=--headless --no-sandbox','--output=json','--output=html','--output-path='+str(output/name),'--only-categories=performance,accessibility,best-practices,seo','--quiet']
 if device=='desktop':cmd.append('--preset=desktop')
 result=subprocess.run(cmd,cwd=ROOT,env={**os.environ,'CHROME_PATH':os.environ.get('CHROME_PATH','/usr/bin/google-chrome')},check=True)
 d=json.loads((output/f'{name}.report.json').read_text())
 a=d['audits'];item={'name':name,'load_average_start':load_start,'load_average_end':os.getloadavg(),'page':path,'device':device,'scores':{k:round(v['score']*100) for k,v in d['categories'].items()},'FCP_ms':round(a['first-contentful-paint']['numericValue']),'LCP_ms':round(a['largest-contentful-paint']['numericValue']),'TBT_ms':round(a['total-blocking-time']['numericValue']),'CLS':round(a['cumulative-layout-shift']['numericValue'],4),'transfer_bytes':a['total-byte-weight']['numericValue'],'lighthouse_version':d['lighthouseVersion'],'fetch_time':d['fetchTime'],'environment':d['environment'],'config':d['configSettings']}
 summary.append(item);print(name,item['scores'], 'LCP',item['LCP_ms'],flush=True)
assert fingerprint()==source_fingerprint, 'Site changed during measurement; rerun on a stable build.'
(output/'summary.json').write_text(json.dumps({'source_sha256':source_fingerprint,'scope':'Local HTTP preview, default Lighthouse simulated mobile/desktop throttling. Not a live CDN or field measurement. Commerce and PostHog disabled in measured build.','results':summary},indent=2)+'\n')
