#!/usr/bin/env python3
"""Read-only HTTPS health and independent TLS validity probe. Nonzero triggers Actions alert."""
import argparse, concurrent.futures, datetime as dt, json, socket, ssl, sys, time
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
p=argparse.ArgumentParser();p.add_argument('--origin',default='https://makeitdoshow.com');p.add_argument('--output',default='monitor-result.json');a=p.parse_args()
host=urlsplit(a.origin).hostname
checks=[]
def http(path):
 for attempt in range(2):
  try:
   start=time.monotonic()
   with urlopen(Request(a.origin+path,headers={'User-Agent':'MakeItDoHealth/1.0'}),timeout=20) as r:
    data=r.read(1_000_000);headers=dict(r.headers);elapsed=time.monotonic()-start
    return {'kind':'http','path':path,'status':r.status,'url':r.url,'seconds':round(elapsed,3),'bytes':len(data),'headers':headers,'pass':r.status==200 and r.url.startswith('https://'+host+'/') and bool(data) and elapsed<15}
  except Exception as e: error=type(e).__name__+': '+str(e)
 return {'kind':'http','path':path,'pass':False,'error':error}
# Public-main-compatible probes; film/checkout health is separately gated before publication.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: checks+=list(pool.map(http,['/','/privacy.html']))
try:
 with socket.create_connection((host,443),timeout=15) as sock:
  with ssl.create_default_context().wrap_socket(sock,server_hostname=host) as tls:
   cert=tls.getpeercert();expires=dt.datetime.fromtimestamp(ssl.cert_time_to_seconds(cert['notAfter']),dt.timezone.utc)
   remaining=(expires-dt.datetime.now(dt.timezone.utc)).total_seconds()/86400
   checks.append({'kind':'certificate','host':host,'expires':expires.isoformat(),'days_remaining':round(remaining,2),'pass':remaining>21})
except Exception as e: checks.append({'kind':'certificate','pass':False,'error':type(e).__name__+': '+str(e)})
out={'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'origin':a.origin,'pass':all(c['pass'] for c in checks),'checks':checks}
from pathlib import Path
Path(a.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));sys.exit(not out['pass'])
