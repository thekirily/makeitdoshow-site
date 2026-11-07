#!/usr/bin/env python3
"""Nu syntax validation of every shipped HTML file. CSP runtime is checked separately in Chrome."""
import argparse,json,subprocess,sys
from page_budget import ROOT,pages
p=argparse.ArgumentParser();p.add_argument('--jar',required=True);a=p.parse_args()
r=subprocess.run(['java','-jar',a.jar,'--format','json',*[str(p) for p in pages()]],capture_output=True,text=True)
d=json.loads(r.stderr or r.stdout);d['scope_note']='File-based HTML validation. Nu emits same-origin CSP resource warnings against file:// URLs. Real HTTP browser CSP violations are checked separately; no CSP directive is relaxed for file://.'
(ROOT/'evidence/launch-1107/after-nu.json').write_text(json.dumps(d,indent=2)+'\n');errors=[m for m in d['messages'] if m['type'] in ['error','non-document-error']];print(json.dumps({'version':d['version'],'pages':len(pages()),'errors':len(errors),'warnings':len(d['messages'])-len(errors),'error_details':errors},indent=2));sys.exit(bool(errors) or bool(r.returncode))
