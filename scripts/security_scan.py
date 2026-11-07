#!/usr/bin/env python3
"""Equivalent header scan, plus per-template local CSP/SRI checks. No grade is invented."""
import concurrent.futures,json,os
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Meta(HTMLParser):
 def __init__(self,s):super().__init__();self.csp=None;self.remote=[];self.feed(s)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='meta' and a.get('http-equiv','').lower()=='content-security-policy':self.csp=a.get('content')
  if t=='script' and a.get('src','').startswith(('https://','//')):self.remote.append({'src':a['src'],'integrity':a.get('integrity')})
def inspect(item):
 name,path,device=item
 try:
  with urlopen(Request('https://makeitdoshow.com'+path,headers={'User-Agent':('Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/132.0 Mobile Safari/537.36' if device=='mobile' else 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/132.0 Safari/537.36')}),timeout=20) as r:
   h={k.lower():v for k,v in r.headers.items()};status=r.status;body=r.read().decode()
 except HTTPError as e:h={k.lower():v for k,v in e.headers.items()};status=e.code;body=e.read().decode(errors='replace')
 except Exception as e:return {'name':name,'device':device,'route':path,'error':str(e)}
 rel=path.lstrip('/') if path.endswith('.html') else path.lstrip('/')+'index.html';doc=Meta((ROOT/rel).read_text());live=Meta(body)
 return {'name':name,'device':device,'route':path,'live_status':status,'headers':h,'live_csp_meta':live.csp,'missing_headers':[k for k in ['strict-transport-security','content-security-policy','x-content-type-options','x-frame-options','referrer-policy','permissions-policy'] if k not in h],'branch_csp_meta':doc.csp,'branch_third_party_scripts':doc.remote,'branch_sri_pass':all(s['integrity'] for s in doc.remote)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:r=list(p.map(inspect,[(name,path,device) for name,path in json.loads((ROOT/'data/audit-templates.json').read_text()).items() for device in ['mobile','desktop']]))
out={'instrument':'urllib HTTPS GET, complete returned headers; Meta parser for staged HTML. Equivalent scan, not Mozilla Observatory grade.','results':r};(ROOT/'evidence/launch-1107/security.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'templates':len(r),'live_non_200':sum(x.get('live_status')!=200 for x in r),'branch_csp_pages':sum(bool(x.get('branch_csp_meta')) for x in r),'remote_scripts':sum(len(x.get('branch_third_party_scripts',[])) for x in r)},indent=2))
