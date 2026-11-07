#!/usr/bin/env python3
"""Read verified Gumroad sales; emit pseudonymous PostHog events. Never a web endpoint.
Default is a JSON summary only. --send requires existing environment configuration.
No customer PII is logged or sent; deterministic event UUIDs make re-runs idempotent.
"""
import argparse, datetime as dt, hashlib, json, os, re, sys, uuid
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = json.loads((ROOT/'data/gumroad-products.json').read_text())['makeitdo']
BY_ID = {v['id']: k for k,v in PRODUCTS.items()}
NAMESPACE = uuid.UUID('c31523bb-a214-4ee5-9cf9-62e97ca3916b')
DOORS = {'qr','typed','description','pinned','endscreen','search','direct','ai_referral','referral'}

def parameters(value):
 if isinstance(value,dict): return {k:str(v) for k,v in value.items() if isinstance(v,(str,int,float))}
 if isinstance(value,str): return {k:v[-1] for k,v in parse_qs(value.lstrip('?')).items()}
 return {}

def events_for_sale(sale):
 product = BY_ID.get(sale.get('product_id'))
 if not product or sale.get('test') or sale.get('is_test') or not sale.get('id') or not sale.get('created_at'): return []
 params=parameters(sale.get('url_params'))
 # Browser analytics permission is separate from purchase consent. Unknown/declined stays in Gumroad only.
 if params.get('mid_analytics') != 'yes': return []
 film=params.get('mid_film',params.get('utm_campaign','none'))
 if not re.fullmatch(r'film\d{2}',film): film='none'
 door=params.get('mid_door',params.get('utm_medium','direct'))
 if door not in DOORS: door='direct'
 # Only admitted random visit IDs join browser events; no customer ID or email is used.
 visit=params.get('mid_visit','')
 if not re.fullmatch(r'[0-9a-fA-F-]{36}',visit): visit='sale-'+hashlib.sha256(str(sale['id']).encode()).hexdigest()[:24]
 amount=int(sale.get('price',0))/100
 currency=str(sale.get('currency','usd')).upper()
 if not re.fullmatch('[A-Z]{3}',currency): return []
 props={'distinct_id':visit,'$process_person_profile':False,'film':film,'door':door,'product':product,'currency':currency,'amount':amount,'attribution': 'checkout_url_params' if film!='none' else 'unattributed'}
 for key in ['utm_source','utm_medium','utm_campaign','utm_content']:
  if re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',params.get(key,'')): props[key]=params[key]
 year=params.get('mid_year','')
 if re.fullmatch(r'19\d{2}',year) and 1930<=int(year)<=1975: props['year']=year
 experiment=params.get('mid_experiment',''); variant=params.get('mid_variant','')
 if re.fullmatch(r'[a-z0-9-]{1,80}',experiment) and variant in {'control','variant'}:
  props.update({'experiment':experiment,'variant':variant,'$feature/'+experiment:variant})
 # Never let a zero-price discount on a paid product masquerade as a lead signup.
 event='signup_completed' if product in {'free_sheet','free_cards'} else 'order_paid'
 if event=='order_paid': props.update({'revenue':amount,'$revenue':amount})
 def one(name,timestamp,extra=None):
  return {'uuid':str(uuid.uuid5(NAMESPACE,str(sale['id'])+':'+name)), 'event':name,'timestamp':timestamp,'properties':{**props,**(extra or {})}}
 events=[one(event,sale['created_at'])]
 # Gross sale and refund are separate facts. Net reporting subtracts refunds.
 if sale.get('refunded') or sale.get('partially_refunded'):
  refund_cents=sale.get('amount_refunded_in_currency')
  refund=amount if sale.get('refunded') else float(refund_cents or 0)/100
  if refund: events.append(one('order_refunded',sale.get('refunded_at') or sale['created_at'],{'amount':refund,'refund_timestamp_known':bool(sale.get('refunded_at')),'revenue':-refund,'$revenue':-refund}))
 return events

def fetch_sales(token,days):
 after=(dt.date.today()-dt.timedelta(days=days)).isoformat()
 page=None; seen=set(); out=[]
 for _ in range(1000):
  params={'after':after}
  if page: params['page_key']=page
  # Bearer token stays in request headers, never in a URL or a log.
  req=Request('https://api.gumroad.com/v2/sales?'+urlencode(params),headers={'Authorization':'Bearer '+token,'User-Agent':'MakeItDoAnalytics/1.0'})
  with urlopen(req,timeout=30) as response: data=json.load(response)
  if not data.get('success'): raise RuntimeError('Gumroad did not confirm a successful read')
  out.extend(data.get('sales',[])); page=data.get('next_page_key')
  if not page: return out
  if page in seen: raise RuntimeError('Gumroad repeated a pagination cursor')
  seen.add(page)
 raise RuntimeError('Gumroad pagination limit exceeded')

def send_events(events,host,key):
 parsed=urlparse(host)
 if parsed.scheme!='https' or parsed.hostname not in {'us.i.posthog.com','eu.i.posthog.com'}: raise ValueError('Use the correct PostHog cloud ingest host')
 for offset in range(0,len(events),100):
  body=json.dumps({'api_key':key,'batch':events[offset:offset+100]}).encode()
  req=Request(host.rstrip('/')+'/batch/',data=body,headers={'Content-Type':'application/json'})
  with urlopen(req,timeout=30) as response:
   result=json.load(response)
   if isinstance(result,dict) and result.get('status') not in (None,1,'Ok'): raise RuntimeError('PostHog did not acknowledge the batch')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path);parser.add_argument('--send',action='store_true');parser.add_argument('--days',type=int,default=30)
 args=parser.parse_args()
 if args.input:
  data=json.loads(args.input.read_text()); sales=data.get('sales',[]) if isinstance(data,dict) else data
 else:
  token=os.environ.get('GUMROAD_ACCESS_TOKEN')
  if not token: sys.exit('Missing GUMROAD_ACCESS_TOKEN in environment; no requests sent.')
  sales=fetch_sales(token,args.days)
 events=[event for sale in sales for event in events_for_sale(sale)]
 if args.send:
  c=json.loads((ROOT/'data/site.json').read_text())
  key=os.environ.get('POSTHOG_PROJECT_KEY') or c['posthog_project_key']
  host=os.environ.get('POSTHOG_HOST') or c['posthog_host']
  if not key: sys.exit('Missing PostHog public project key; nothing sent.')
  send_events(events,host,key)
 counts={}
 for e in events:
  p=e['properties']; k=(p['film'],p['door'],p['product'],e['event'],p['currency'])
  if k not in counts: counts[k]={'count':0,'amount':0}
  counts[k]['count']+=1; counts[k]['amount']+=p['amount']
 print(json.dumps({'sent':bool(args.send),'events':len(events),'counts':[dict(zip(['film','door','product','event','currency'],k),**v) for k,v in sorted(counts.items())]},indent=2))
if __name__=='__main__': main()
