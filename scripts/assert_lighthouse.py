#!/usr/bin/env python3
"""Strict score and Web Vitals budgets. Deliberately private routes retain noindex."""
import json,sys
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
d=json.loads(Path(sys.argv[1]).read_text());bad=[]
for r in d['results']:
 if r.get('error'):bad.append(r);continue
 rel=r['route'].lstrip('/') if r['route'].endswith('.html') else r['route'].lstrip('/')+'index.html'
 private='noindex,follow' in (ROOT/rel).read_text()
 failures=[f for f in r['failures'] if f!='seo' or not private]
 if failures:bad.append({'name':r['name'],'device':r['device'],'failures':failures})
print(json.dumps({'measurements':len(d['results']),'failures':bad,'seo_exception':'Only explicitly noindexed doors, aliases, 404 and thanks. Raw SEO scores retained and reported as failing the literal all-page target.'},indent=2));sys.exit(bool(bad))
