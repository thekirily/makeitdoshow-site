"""Store pictures made from the real print files (no mockups): name-free cover fronts for the live preview,
real interior pages, and the frames of the leaf-through loop. Usage: python3 -m print.make_previews (from store/)."""
import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orders import pdfbuild, personalise
import fitz
from PIL import Image
OUT = os.path.join(os.path.dirname(pdfbuild.STORE), 'assets', 'img', 'shop'); os.makedirs(OUT, exist_ok=True)
from playwright.sync_api import sync_playwright

def front_png(pdf, dpi=110):
    d = fitz.open(pdf); p = d[0]
    # the front half, trimmed of its 0.125in bleed so it shows the cut page
    b = 0.125 * 72
    clip = fitz.Rect(p.rect.width / 2, b, p.rect.width - b, p.rect.height - b)
    pix = p.get_pixmap(dpi=dpi, clip=clip); return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

with sync_playwright() as pw:
    br = pw.chromium.launch(); pg = br.new_page()
    for y in range(1930, 1971):
        html = pdfbuild.cover_html(y, 'X').replace('<div class="for" id="for">For X, born %d</div>' % y, '')
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as t:
            t.write(html)
        pg.goto('file://' + t.name); pg.wait_for_load_state('networkidle')
        pdf = f'/tmp/blank-{y}.pdf'
        pg.pdf(path=pdf, width='17.25in', height='11.25in', print_background=True, prefer_css_page_size=True)
        front_png(pdf).resize((600, 776), Image.LANCZOS).save(os.path.join(OUT, f'cover-{y}.webp'), quality=82)
    br.close()
d = fitz.open(personalise.interior_path(1953))
for n in (1, 2, 5, 7, 13, 14, 17):
    pix = d[n - 1].get_pixmap(dpi=110)
    Image.frombytes('RGB', (pix.width, pix.height), pix.samples).resize((850, 1100), Image.LANCZOS).save(os.path.join(OUT, f'page-1953-{n:02d}.webp'), quality=84)
os.makedirs('/tmp/leaf', exist_ok=True)
for n in range(20):
    pix = d[n].get_pixmap(dpi=80)
    Image.frombytes('RGB', (pix.width, pix.height), pix.samples).resize((680, 880), Image.LANCZOS).save(f'/tmp/leaf/p{n:02d}.png')
print('ok', len(os.listdir(OUT)))
