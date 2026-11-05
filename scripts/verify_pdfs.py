#!/usr/bin/env python3
"""Content-check all free sheets. Optional QA dependencies: PyMuPDF."""
from pathlib import Path
import collections,json
import fitz
ROOT=Path(__file__).resolve().parents[1]
counts={};blank=[];minsize=100;word_counts={}
for f in sorted((ROOT/'downloads').glob('what-things-cost-*.pdf')):
 year=f.stem[-4:];doc=fitz.open(f);counts[year]=len(doc);text=''.join(p.get_text() for p in doc);word_counts[year]=len(text.split())
 if year not in text or len(text.strip())<200:blank.append(year)
 for page in doc:
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     if span['text'].strip():minsize=min(minsize,span['size'])
(ROOT/'data/sheet-pages.json').write_text(json.dumps(counts,indent=2)+'\n')
summary={'year_sheets':len(counts),'pages_by_year':counts,'page_count_distribution':dict(collections.Counter(counts.values())),'blank_or_missing_year_sheets':blank,'minimum_text_pt':round(minsize,2),'word_counts':word_counts,'recipe_card_pages':len(fitz.open(ROOT/'downloads/make-it-do-1950-recipe-cards.pdf')),'sample_pages':len(fitz.open(ROOT/'downloads/your-year-1953-sample.pdf')),'repaired':'1949: original supplied PDF was 861 bytes and had no text; rebuilt locally from the checked year data.'}
(ROOT/'evidence/pdf-checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in {'pages_by_year','word_counts'}},indent=2))
assert len(counts)==46 and not blank and minsize>=13.95
