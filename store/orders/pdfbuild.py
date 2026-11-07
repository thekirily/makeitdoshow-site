"""Build the buyer's named cover, pair it with her year's interior, and preflight both against Lulu's spec.

The cover is the same design as the 1104 print file (`money-rung5-1104/scripts/print_html.py: cover`), carried
into this repo so the robot doesn't depend on a job folder. One change: the name line shrinks (22pt down to
16pt) to fit a long name instead of truncating it, and the build fails if it still doesn't fit.
"""
import hashlib, html, json, os, re, subprocess, tempfile
from .common import STORE, CATALOG, log_event
from . import personalise

PR = os.path.join(STORE, 'print')
FONTS = 'file://' + os.path.join(PR, 'fonts') + '/'
FRAME = 'file://' + os.path.join(PR, 'frames', 'kitchen-1955-c.jpg')
SPEC = CATALOG['products']['youryear']
# The faces the print files are designed in. Anything else in a PDF means a font failed to load and the browser fell back.
DESIGNED_FONTS = {'TableBookSans-Regular', 'TableBookSans-Bold', 'TableBookSans-Italic', 'SourceSerif4Roman-Regular',
                  'SourceSerif4Italic-Italic', 'CourierPrime-Regular', 'CourierPrime-Bold'}


def cover_html(y, name):
    nm = html.escape(name)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:SrcSerif;src:url('{FONTS}SourceSerif4-Var.ttf');font-weight:200 900}}
@font-face{{font-family:SrcSerif;src:url('{FONTS}SourceSerif4-VarItalic.ttf');font-style:italic;font-weight:200 900}}
@font-face{{font-family:Plain;src:url('{FONTS}tablebook-400.woff2')}}
@font-face{{font-family:Plain;src:url('{FONTS}tablebook-700.woff2');font-weight:700}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
@page{{size:17.25in 11.25in;margin:0}}
body{{margin:0;color:#1E1B18;font:400 16pt/1.42 SrcSerif;width:17.25in;height:11.25in;display:flex;background:#EFE6D2}}
.k{{font:700 14pt/1.2 Plain;letter-spacing:.12em;text-transform:uppercase;color:#B0392B}}
.src{{font:400 14pt/1.35 Plain;color:#6B655B}}
.half{{width:8.625in;height:11.25in;position:relative;overflow:hidden}}
.front{{background:#1E1B18;color:#EFE6D2}}
.front .img{{position:absolute;left:.125in;right:.125in;top:3.3in;height:5.1in;background:url('{FRAME}') center/cover}}
.front .yr{{position:absolute;left:.6in;top:.55in;font:800 150pt/.8 SrcSerif;font-variation-settings:"opsz" 60;letter-spacing:-.05em;color:#F4C430}}
.front .t{{position:absolute;left:.65in;top:2.45in;font:700 26pt/1 SrcSerif;letter-spacing:-.01em}}
.front .t i{{font-weight:400}}
.front .for{{position:absolute;left:.65in;bottom:1.45in;font:700 22pt/1.2 Plain;white-space:nowrap}}
.front .sub{{position:absolute;left:.65in;right:.65in;bottom:.7in;font:400 16pt/1.35 Plain;color:#cfc6b4}}
.back{{padding:.9in .8in}}
.back p{{font-size:16pt;max-width:6.3in}}
</style></head><body>
<div class="half back"><div class="k">Make It Do</div><p style="margin-top:14pt">Bread, eggs, milk, gas, a stamp and an hour's pay, as the government's own price agents wrote them down in {y}, beside real color film of the time. With the names in the hospital nursery that year, a recipe from the government's kitchen, and two pages for what it cost in your own house.</p>
<p class="src" style="position:absolute;bottom:.7in;left:.8in">From the film <i>Everyday Life in 1950s America, in Real Color Film</i>. Frames from <i>A Word to the Wives</i> (c. 1955) and <i>Shopping Can Be Fun</i> (1957), public domain.</p></div>
<div class="half front"><div class="yr">{y}</div><div class="t">Your Year, <i>in Color</i></div><div class="img"></div><div class="for" id="for">For {nm}, born {y}</div><div class="sub">What things cost the year you were born, from the government's own records</div></div>
</body></html>"""


# Type safe area: Lulu asks for 0.5 in from trim for text; the front half is 8.625in wide incl. 0.125 bleed.
SAFE_RIGHT_PX = (8.625 - 0.125 - 0.5) * 96


def build_cover(y, name, out_pdf, page=None):
    """Render the wrap cover with Chromium. Returns the font size used for the name line."""
    from playwright.sync_api import sync_playwright
    own = page is None
    if own:
        pw = sync_playwright().start(); br = pw.chromium.launch(); page = br.new_page()
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as t:
            t.write(cover_html(y, name)); tmp = t.name
        page.goto('file://' + tmp); page.wait_for_load_state('networkidle')
        page.evaluate('document.fonts.ready')
        size = 22
        while True:
            right = page.evaluate("(() => { const e = document.getElementById('for'); const r = e.getBoundingClientRect(); return r.right - e.parentElement.getBoundingClientRect().left; })()")
            if right <= SAFE_RIGHT_PX or size <= 16:
                break
            size -= 1
            page.evaluate(f"document.getElementById('for').style.fontSize = '{size}pt'")
        if right > SAFE_RIGHT_PX:
            raise personalise.Bad('That name is too long for the cover line.')
        page.pdf(path=out_pdf, width='17.25in', height='11.25in', print_background=True, prefer_css_page_size=True)
        os.unlink(tmp)
        return size
    finally:
        if own:
            br.close(); pw.stop()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def fonts_report(path):
    """pdffonts: every font must be embedded (Lulu rejects files with unembedded fonts)."""
    out = subprocess.run(['pdffonts', path], capture_output=True, text=True).stdout.splitlines()[2:]
    rows = []
    for line in out:
        parts = line.split()
        # name type ... emb sub uni object ID ; emb is 5th from the end
        if len(parts) >= 7:
            rows.append({'name': parts[0], 'emb': parts[-5], 'sub': parts[-4]})
    return rows


def preflight(kind, path, *, year, name=None):
    """Check the file the way Lulu's spec reads it. Returns a dict; 'ok' False means do not upload."""
    import fitz
    d = fitz.open(path)
    pts = lambda r: (round(r.width / 72, 3), round(r.height / 72, 3))
    rep = {'kind': kind, 'file': os.path.basename(path), 'sha256': sha256(path), 'bytes': os.path.getsize(path),
           'pages': d.page_count, 'page_in': sorted({pts(p.rect) for p in d}), 'fonts': fonts_report(path), 'problems': []}
    if kind == 'interior':
        if d.page_count != SPEC['interior_pages']:
            rep['problems'].append(f"interior has {d.page_count} pages, spec {SPEC['interior_pages']}")
        if rep['page_in'] != [tuple(SPEC['trim_in'])]:
            rep['problems'].append(f"interior page size {rep['page_in']} != trim {SPEC['trim_in']} (white-margin interior; Lulu adds bleed)")
        txt = d[0].get_text()
        if str(year) not in txt:
            rep['problems'].append(f'year {year} not found on interior page 1')
    else:
        if d.page_count != 1:
            rep['problems'].append(f'cover has {d.page_count} pages, expected one wrap')
        if rep['page_in'] != [tuple(SPEC['cover_in'])]:
            rep['problems'].append(f"cover size {rep['page_in']} != {SPEC['cover_in']} (17.25x11.25 in incl. 0.125 in bleed)")
        txt = re.sub(r'\s+', ' ', d[0].get_text())
        want = f'For {name}, born {year}'
        rep['name_line_found'] = want in txt
        if want not in txt:
            rep['problems'].append(f'cover text does not contain "{want}"')
    unemb = [f['name'] for f in rep['fonts'] if f['emb'] != 'yes']
    stray = sorted({f['name'].split('+')[-1] for f in rep['fonts']} - DESIGNED_FONTS)
    if stray:
        rep['problems'].append(f'fonts outside the design (a fallback was used): {stray}')
    if unemb:
        rep['problems'].append(f'unembedded fonts: {unemb}')
    rep['ok'] = not rep['problems']
    return rep


def proof_png(cover_pdf, out_png, front_only=True):
    """A picture of the cover as built, for the eye check (front half only by default)."""
    import fitz
    d = fitz.open(cover_pdf); p = d[0]
    clip = fitz.Rect(p.rect.width / 2, 0, p.rect.width, p.rect.height) if front_only else None
    p.get_pixmap(dpi=60, clip=clip).save(out_png)
    return out_png


def build_order_files(order, workdir):
    """For each line: the named cover (built) and the year's interior (shared file). Preflights both."""
    os.makedirs(workdir, exist_ok=True)
    results = []
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(); page = br.new_page()
        for i, line in enumerate(json.loads(order['lines']) if isinstance(order['lines'], str) else order['lines']):
            y, nm = personalise.clean_year(line['year']), personalise.clean_name(line['name'])   # checked again, after payment
            cpath = os.path.join(workdir, f"{order['id']}-{i + 1}-cover-{y}.pdf")
            size = build_cover(y, nm, cpath, page)
            ipath = personalise.interior_path(y)
            c = preflight('cover', cpath, year=y, name=nm); c['name_pt'] = size
            it = preflight('interior', ipath, year=y)
            results.append({'line': i + 1, 'year': y, 'name': nm, 'cover': c, 'interior': it, 'cover_path': cpath, 'interior_path': ipath})
            log_event('pdf.built', order_id=order['id'], line=i + 1, year=y, name=nm, cover_sha256=c['sha256'],
                      interior_sha256=it['sha256'], cover_ok=c['ok'], interior_ok=it['ok'], problems=c['problems'] + it['problems'])
        br.close()
    return results
