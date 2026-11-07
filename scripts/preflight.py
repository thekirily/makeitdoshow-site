#!/usr/bin/env python3
"""Read-only film-launch gate. No product publishing, test purchase, or print job."""
import json,os,sys
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'data/site.json').read_text());p=json.loads((ROOT/'data/gumroad-products.json').read_text())['makeitdo']
problems=[]
if not c['posthog_project_key']:problems.append('The existing Make It Do PostHog public project key has not been configured in data/site.json.')
if not c['commerce_enabled']:problems.append('Printed ordering is disabled. Publish the existing Gumroad draft and verify fulfillment before enabling commerce.')
if not c['free_email_enabled']:problems.append('Gumroad email delivery is disabled. Publish the free sheet/cards drafts before enabling it.')
if c['commerce_enabled'] or c['free_email_enabled']:
 token=os.environ.get('GUMROAD_ACCESS_TOKEN')
 if not token:problems.append('GUMROAD_ACCESS_TOKEN is required in the environment for read-only product verification. Do not paste it into chat or commit it.')
 else:
  for key in (['youryear'] if c['commerce_enabled'] else [])+(['free_sheet','free_cards'] if c['free_email_enabled'] else []):
   try:
    request=Request('https://api.gumroad.com/v2/products/'+p[key]['id'],headers={'Authorization':'Bearer '+token,'User-Agent':'MakeItDoLaunch/1.0'})
    with urlopen(request,timeout=20) as response:data=json.load(response)
    product=data.get('product',{})
    if not data.get('success') or not product.get('published'):problems.append(f'{key}: Gumroad has not confirmed the product is published.')
    if int(product.get('price',-1))!=int(p[key]['price']*100):problems.append(f'{key}: live price differs from the advertised price.')
    if key=='youryear' and not product.get('require_shipping'):problems.append('Your Year must collect a shipping address and be configured as a physical product in Gumroad.')
   except Exception as e:problems.append(f'{key}: read-only Gumroad verification failed ({type(e).__name__}); nothing was published.')
if problems:
 print('FILM LAUNCH IS BLOCKED:\n'+'\n'.join('- '+x for x in problems));sys.exit(1)
print('Public configuration and live Gumroad product checks passed. Fulfillment and analytics delivery still need the real acceptance checks in docs/launch.md.')
