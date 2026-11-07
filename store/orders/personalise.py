"""What a buyer may put on a cover, checked before she pays (the page) and again before anything prints (the robot).

The same function runs in both places, so a name that would print wrong can't be paid for, and a tampered
order can't slip past the robot.
"""
import os, re, unicodedata
from .common import CATALOG, STORE

FONT = os.path.join(STORE, 'print', 'fonts', 'tablebook-700.woff2')   # the face the cover's name line is set in
INTERIORS = os.environ.get('INTERIOR_DIR', os.path.join(STORE, 'var', 'interiors'))
Y0, Y1 = CATALOG['years']
NAME_MAX = CATALOG['name_max']
_cmap = None


def _glyphs():
    global _cmap
    if _cmap is None:
        from fontTools.ttLib import TTFont
        _cmap = set(TTFont(FONT).getBestCmap())
    return _cmap


ALLOWED = re.compile(r"^[^\W\d_]+(?:[ '’.\-][^\W\d_]*)*\.?$")   # letters, joined by single space/apostrophe/period/hyphen


class Bad(ValueError):
    """A message written for the buyer, shown beside the field."""


def clean_name(raw):
    if raw is None:
        raise Bad('Please write the name for the cover.')
    s = unicodedata.normalize('NFC', str(raw)).strip()
    s = re.sub(r'\s+', ' ', s).replace("'", '’')          # typewriter apostrophe -> the printed one
    if not s:
        raise Bad('Please write the name for the cover.')
    if len(s) > NAME_MAX:
        raise Bad(f'The cover has room for {NAME_MAX} letters. Try a first name, or a shorter form.')
    if any(unicodedata.category(ch)[0] == 'C' for ch in s):
        raise Bad('That name has a character we can’t print.')
    if not ALLOWED.match(s):
        raise Bad('Letters only, please, with spaces, hyphens or apostrophes between them.')
    missing = sorted({ch for ch in s if ord(ch) not in _glyphs()})
    if missing:
        raise Bad('Our cover type doesn’t have ' + ' '.join(missing) + '. Could you write it without that letter?')
    return s


def clean_year(raw):
    try:
        y = int(str(raw).strip())
    except (TypeError, ValueError):
        raise Bad('Please choose a year.')
    if not Y0 <= y <= Y1:
        raise Bad(f'We have every year from {Y0} to {Y1}. {y} isn’t printed yet.')
    if not os.path.exists(interior_path(y)):
        raise Bad(f'{y} isn’t ready to print yet.')
    return y


def interior_path(y):
    return os.path.join(INTERIORS, f'your-year-{y}-interior.pdf')


def clean_lines(lines, max_lines):
    if not isinstance(lines, list) or not lines:
        raise Bad('Please choose a year and a name.')
    if len(lines) > max_lines:
        raise Bad(f'Up to {max_lines} booklets in one envelope.')
    return [{'year': clean_year(l.get('year')), 'name': clean_name(l.get('name'))} for l in lines]


def price_cents(product, n_lines):
    p = CATALOG['products'][product]
    return p['price_cents'] + p['extra_copy_cents'] * (n_lines - 1)
