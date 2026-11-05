#!/usr/bin/env python3
"""Check static routes, fragment targets, canonical URLs, and crawlable content."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.ids=set();self.h1=0;self.schema=[];self.canonical=[];self.noindex=False;self._json=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.add(a['id'])
  if tag=='h1':self.h1+=1
  if tag in {'a','link'} and a.get('href'):self.links.append(a['href'])
  if tag in {'img','script'} and a.get('src'):self.links.append(a['src'])
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
  if tag=='meta' and a.get('name')=='robots' and 'noindex' in a.get('content',''):self.noindex=True
  if tag=='script' and a.get('type')=='application/ld+json':self._json=True
 def handle_data(self,data):
  if self._json:self.schema.append(json.loads(data))
 def handle_endtag(self,tag):
  if tag=='script':self._json=False

def main():
 docs={p:Document(p.read_text()) for p in ROOT.rglob('*.html') if 'evidence' not in p.parts and '.git' not in p.parts}
 errors=[];links=0
 for p,d in docs.items():
  if d.h1!=1:errors.append(f'{p}: {d.h1} H1s')
  if len(d.canonical)!=1:errors.append(f'{p}: missing or duplicated canonical')
  if not d.schema:errors.append(f'{p}: no JSON-LD')
  for link in d.links:
   u=urlsplit(link)
   if u.scheme or u.netloc:continue
   path=ROOT/unquote(u.path.lstrip('/')) if u.path.startswith('/') else p.parent/unquote(u.path)
   if not u.path:path=p
   elif path.is_dir():path=path/'index.html'
   if not path.exists():errors.append(f'{p.relative_to(ROOT)}: missing {link}')
   elif u.fragment and path.suffix=='.html' and u.fragment not in docs[path].ids:errors.append(f'{p.relative_to(ROOT)}: missing anchor {link}')
   links+=1
 urls=[e.text for e in ET.parse(ROOT/'sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
 if len(urls)!=len(set(urls)):errors.append('Duplicate sitemap URL')
 for url in urls:
  suffix=urlsplit(url).path
  p=ROOT/((suffix.lstrip('/')+'index.html') if suffix.endswith('/') else suffix.lstrip('/'))
  if p not in docs or docs[p].noindex:errors.append('Missing or noindexed sitemap URL '+url)
 for y in range(1930,1976):
  if not (ROOT/str(y)/'index.html').exists() or not (ROOT/'downloads'/f'what-things-cost-{y}.pdf').exists():errors.append(f'Missing year or download {y}')
 result={'html_pages':len(docs),'internal_links_checked':links,'sitemap_urls':len(urls),'free_year_pdfs':46,'errors':errors}
 (ROOT/'evidence/static-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
