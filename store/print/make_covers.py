"""Round 2: cover fronts for the live preview (name left blank, 'FOR' and 'BORN year' printed), the flat hero and the
two-booklet shelf picture, all rasterised from the real print template. Prints the name box position for the overlay."""
import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orders import pdfbuild
import fitz
from PIL import Image, ImageFilter, ImageDraw
from playwright.sync_api import sync_playwright
OUT = os.path.join(os.path.dirname(pdfbuild.STORE), 'assets', 'img', 'shop')
B = 0.125 * 72
def front(pdf, dpi):
    p = fitz.open(pdf)[0]; pix = p.get_pixmap(dpi=dpi, clip=fitz.Rect(p.rect.width / 2, B, p.rect.width - B, p.rect.height - B))
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
with sync_playwright() as pw:
    br = pw.chromium.launch(); pg = br.new_page()
    for y in range(1930, 1971):
        html = pdfbuild.cover_html(y, ' ')
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as t: t.write(html)
        pg.goto('file://' + t.name); pg.wait_for_load_state('networkidle')
        if y == 1953:
            box = pg.evaluate("(() => { const h = document.querySelector('.front').getBoundingClientRect(); const r = document.getElementById('for').getBoundingClientRect(); return {left: (r.left - h.left) / 96, top: (r.top - h.top) / 96 - 0.125, height: r.height / 96}; })()")
        pg.pdf(path='/tmp/blank.pdf', width='17.25in', height='11.25in', print_background=True, prefer_css_page_size=True)
        front('/tmp/blank.pdf', 110).resize((600, 776), Image.LANCZOS).save(os.path.join(OUT, f'cover-{y}.webp'), quality=82)
    br.close()
def staged(covers, w, h):
    bg = Image.new('RGB', (w, h), (232, 226, 212)); n = len(covers)
    cw = int(w * (0.42 if n == 1 else 0.36)); ch = int(cw * 11 / 8.5)
    for i, c in enumerate(covers):
        x = (w - cw) // 2 if n == 1 else int(w * (0.12 + 0.40 * i)); yy = (h - ch) // 2 + (0 if n == 1 else (-30 if i == 0 else 30))
        sh = Image.new('L', (cw + 80, ch + 80), 0); ImageDraw.Draw(sh).rectangle([40, 40, cw + 40, ch + 40], fill=120)
        bg.paste((70, 60, 45), (x - 28, yy - 22), sh.filter(ImageFilter.GaussianBlur(22)))
        bg.paste(c.resize((cw, ch), Image.LANCZOS), (x, yy))
    return bg
pdfbuild.build_cover(1953, 'Margaret', '/tmp/m53.pdf'); pdfbuild.build_cover(1951, 'Walter O’Neill', '/tmp/w51.pdf')
m, w = front('/tmp/m53.pdf', 150), front('/tmp/w51.pdf', 150)
for name, im in (('cover_hero', staged([m], 1600, 1067)), ('cover_pair', staged([m, w], 1600, 1067))):
    for wd in (1600, 800, 560):
        im.resize((wd, int(1067 * wd / 1600)), Image.LANCZOS).save(os.path.join(OUT, f'{name}-{wd}.webp'), quality=80)
print(json.dumps(box))
