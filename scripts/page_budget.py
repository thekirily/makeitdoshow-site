#!/usr/bin/env python3
"""Enforce every HTML route's complete local page weight, including lazy images and fonts."""
import gzip, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
LIMITS={'total_raw_bytes':550_000,'total_gzip_bytes':400_000,'javascript_raw_bytes':30_000,'requests':24}
class Assets(HTMLParser):
 def __init__(self,text): super().__init__();self.urls=set();self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in {'img','script'} and a.get('src'):self.urls.add(a['src'])
  if tag=='link' and a.get('rel') in {'stylesheet','preload','icon'}:self.urls.add(a['href'])
def pages(root=ROOT):
 return sorted(p for p in root.rglob('*.html') if not {'evidence','node_modules','.git'} & set(p.relative_to(root).parts))
def budget(root=ROOT):
 results=[]
 for page in pages(root):
  files={page};external=[];pending=list(Assets(page.read_text()).urls)
  while pending:
   url=pending.pop();u=urlsplit(url)
   if u.netloc:external.append(url);continue
   p=root/u.path.lstrip('/') if u.path.startswith('/') else page.parent/u.path
   if not p.is_file() or p in files:continue
   files.add(p)
   if p.suffix=='.css':pending+=re.findall(r'url\([\'"]?([^\)\'\"]+)',p.read_text())
  vals={'total_raw_bytes':sum(p.stat().st_size for p in files),'total_gzip_bytes':sum(len(gzip.compress(p.read_bytes(),mtime=0)) for p in files),'javascript_raw_bytes':sum(p.stat().st_size for p in files if p.suffix=='.js'),'requests':len(files)}
  failures=[k for k,v in vals.items() if v>LIMITS[k]]+(['unbudgeted_external_assets'] if external else [])
  results.append({'route':'/'+str(page.relative_to(root)).removesuffix('index.html'),**vals,'failures':failures})
 return {'limits':LIMITS,'scope':'Complete HTML + CSS + JS + fonts + icons + all images, including lazy images. PDFs are separate downloads. Gzip estimate, not CDN transfer measurement.','results':results}
if __name__=='__main__':
 d=budget();target=ROOT/'evidence/launch-1107/after-weight.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(d,indent=2)+'\n');bad=[r for r in d['results'] if r['failures']];print(json.dumps({'routes':len(d['results']),'failures':bad,'maximums':{k:max(r[k] for r in d['results']) for k in LIMITS}},indent=2));sys.exit(bool(bad))
