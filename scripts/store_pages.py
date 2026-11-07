"""The store: /your-year/ (the product page), /shop/ (the shelf), /shop/thanks/ (after payment).
Called from build.py with its helpers. Every claim on these pages has a source in the store-1108 acceptance table.
Store pictures are made from the real print files (store/print/make_previews.py) or rendered from them at true size
(store-look-1104); nothing is a mockup template."""
import json
from html import escape as esc
from decimal import Decimal, ROUND_HALF_UP

CAT = None


def mins(price, wage):
    return int(Decimal(str(price / wage * 60)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def cents(v):
    return f'{round(v * 100)}¢' if v < 1 else f'${v:,.2f}'


def year_facts(Y):
    """One true line per year, the same arithmetic the booklet prints on its paycheck page."""
    out = {}
    for y in range(1930, 1971):
        d = Y[str(y)]; k = {r['key']: r for r in d['rows']}
        eggs, wage = k['E194'], k.get('minwage')
        f = {'eggs': cents(eggs['then'])}
        if wage and wage.get('then'):
            f['then'] = mins(eggs['then'], wage['then']); f['now'] = mins(eggs['now'], wage['now']); f['wage'] = cents(wage['then'])
        f['girl'], f['boy'] = d['names']['girls'][0], d['names']['boys'][0]
        out[y] = f
    return out


def pic(src, alt, w, h, cls='', lazy=True, sizes='(max-width: 800px) 100vw, 60vw', srcset=None):
    ss = f' srcset="{srcset}" sizes="{sizes}"' if srcset else ''
    return (f'<img src="/assets/img/shop/{src}"{ss} alt="{esc(alt)}" width="{w}" height="{h}" class="{cls}" '
            + ('loading="lazy"' if lazy else 'fetchpriority="high"') + ' decoding="async">')


def render(name, alt, lazy=True, cls=''):
    return pic(f'{name}-1600.webp', alt, 1600, 1067, cls, lazy, srcset=(f'/assets/img/shop/{name}-560.webp 560w, ' if name == 'yy_hero' else '') + f'/assets/img/shop/{name}-800.webp 800w, /assets/img/shop/{name}-1600.webp 1600w')


def build(page, a, crumbs, Y, C, CATALOG):
    facts = year_facts(Y)
    live = bool(C.get('commerce_enabled')) and C.get('orders_api') is not None
    api = C.get('orders_api') or ''
    spec = CATALOG['products']['youryear']
    opts = '<option value="">Choose a year</option>' + ''.join(f'<option value="{y}">{y}</option>' for y in range(1970, 1929, -1))
    honest = ('<p class="shop-note">Pictures: the booklet rendered from its actual print files at true size, and its real pages. '
              'No printed copy has been photographed yet.</p>')

    def line_fields(n, hidden=False):
        return (f'<fieldset class="shop-line" id="line{n}"{" hidden" if hidden else ""}><legend>{"Her" if n == 1 else "The second"} booklet</legend>'
                f'<label for="{"book-year" if n == 1 else "year2"}">Year she was born</label><select id="{"book-year" if n == 1 else "year2"}" name="year{n}" {"required" if n == 1 else ""} data-line="{n}">{opts}</select>'
                f'<label for="name{n}">Name for the cover</label><input id="name{n}" name="name{n}" maxlength="24" autocomplete="off" '
                f'{"required" if n == 1 else ""} data-line="{n}" placeholder="Margaret" aria-describedby="hint{n}">'
                f'<p class="shop-hint" id="hint{n}">It prints as “For Margaret, born 1953”. Up to 24 letters.</p></fieldset>')

    buy = (f'<form class="shop-buy" id="order" method="post" action="{api}/api/checkout" data-facts=\'{esc(json.dumps(facts))}\'>'
           '<input type="hidden" name="product" value="youryear">'
           + line_fields(1) +
           '<div class="shop-preview" aria-live="polite"><div class="shop-cover">'
           + pic('cover-1953.webp', 'The front cover of the booklet, with the year and the name you choose', 600, 776, 'shop-cover-img', lazy=True, sizes='300px') +
           '<p class="shop-cover-name" id="covername" aria-hidden="true">For Margaret, born 1953</p></div>'
           '<div><p class="shop-nameline" id="nameline">For Margaret, born 1953</p>'
           '<p class="shop-preview-cap">The cover as it will print, and its name line enlarged. Type a name and choose a year to see hers.</p></div></div>'
           '<p class="shop-fact" id="fact"></p>'
           '<details class="shop-second" id="second"><summary>Add another year in the same envelope <b>+$29</b></summary>'
           '<p class="small">Her husband’s year, the year they married, a sister’s. Each booklet has its own year and name.</p>'
           + line_fields(2) + '</details>'
           + (f'<button class="button shop-pay" type="submit" id="pay">Continue to payment · <span id="total">$49</span></button>'
              if live else '<p class="availability"><span class="status-dot" aria-hidden="true"></span> Orders open soon. No payment is being taken yet.</p>') +
           '<ul class="shop-assure">'
           '<li><b>Pay by card</b> on PayPal’s secure page, usually as a guest, with no account to open. You enter the mailing address there.</li>'
           '<li><b>About 2½ weeks to her door.</b> Printed after you pay, then U.S. Mail: our printer quotes 11–13 business days in all.</li>'
           '<li><b>Shipping to any U.S. address is included.</b> Send it straight to her.</li></ul>'
           '</form>')

    hero = ('<section class="shop-hero"><div class="shop-head"><p class="eyebrow">Printed to order · one name on the cover</p>'
            '<h1>Your Year,<br><span class="acc">in Color.</span></h1>'
            '<p class="lede">Her birth year, as the government recorded it. Her name on the cover.</p>'
            '<p class="shop-price"><span>$49</span> U.S. shipping included</p></div>'
            '<div class="shop-gallery">'
            '<figure class="shop-main">' + render('yy_hero', 'The 1953 booklet on a kitchen table: the cover reads “For Margaret, born 1953”; beside it, the booklet open at “Was it really cheaper?”', lazy=False) +
            '<figcaption>The 1953 edition, named for Margaret. 8½ × 11 inches, the size of a letter.</figcaption></figure>'
            '<div class="shop-thumbs">'
            '<figure>' + pic('page-1953-05.webp', 'Page 5: Was it really cheaper? Minutes of work at the minimum wage for each grocery, 1953 and today', 680, 880, sizes='200px') + '<figcaption>Page 5</figcaption></figure>'
            '<figure>' + pic('page-1953-07.webp', 'Page 7: the names on the cribs in 1953, Mary first with 64,389', 680, 880, sizes='200px') + '<figcaption>Page 7</figcaption></figure>'
            '<figure>' + pic('page-1953-13.webp', 'Page 13: What it cost in our house, a page of blank lines beside the government’s prices', 680, 880, sizes='200px') + '<figcaption>Page 13</figcaption></figure>'
            '</div>' + honest + '</div>'
            '<div class="shop-panel">' + buy + '</div></section>')

    grey = ('<section class="section shop-grey"><div class="shop-grey-copy"><p class="eyebrow">What’s inside</p>'
            '<h2>It was written down in grey.<br><span class="acc">Here it is again, in color.</span></h2>'
            '<p>Every year, the government’s price agents walked into grocery stores in dozens of American cities and wrote down what bread, eggs and coffee cost. '
            'Those numbers sat in grey tables for decades. The booklet sets them beside real color film from the time, and adds the fairer measure: how long it took to earn them.</p>'
            '<p class="shop-big" id="bigfact"><span>56 minutes</span> of work at the minimum wage bought a dozen eggs in 1953. <em>Today, 35.</em></p>'
            '<p class="small">From the booklet’s paycheck page. The minimum covered only some jobs in 1953: a yardstick, not everybody’s pay. Sources are printed on pages 18–19.</p></div>'
            '<figure class="shop-page">' + pic('page-1953-02.webp', 'Page 2: what the groceries cost in 1953 beside today, from the government record', 680, 880, sizes='(max-width: 800px) 90vw, 40vw') +
            '<figcaption>Page 2 of the 1953 edition, as it prints.</figcaption></figure></section>')

    leaf = ('<section class="section shop-leaf" id="inside"><div class="shop-leaf-head"><p class="eyebrow">All twenty pages</p><h2>Leaf through the 1953 edition.</h2>'
            '<p>The prices, the paycheck, the names in the nursery, two recipes from the government’s 1950 kitchen, and real color film. Every year is its own edition, with its own numbers.</p></div>'
            '<figure><video class="shop-video" muted loop playsinline preload="none" data-poster="/assets/img/shop/leaf-1953-poster.webp" width="1100" height="740" '
            'aria-label="The twenty pages of the 1953 booklet, spread by spread"><source src="/assets/img/shop/leaf-1953.mp4" type="video/mp4"></video>'
            '<figcaption>The real pages, in order. It plays without sound.</figcaption></figure></section>')

    hers = ('<section class="section shop-hers"><figure>' + pic('page-1953-17.webp', 'Page 17: A letter to the grandchildren, begun with a price', 680, 880, sizes='(max-width: 800px) 90vw, 30vw') +
            '<figcaption>Page 17</figcaption></figure><div><p class="eyebrow">The pages left for her</p>'
            '<h2>The government wrote down the average.<br><span class="acc">She knows the real one.</span></h2>'
            '<p>Four pages are hers to fill: what it really cost in your house, the questions to ask, what she remembers, and a letter to the grandchildren that starts with a price: '
            '<i>“When I was born, a loaf of bread cost…”</i></p>'
            '<p>Give it at the table and ask the first question. The answers end up in the book.</p></div></section>')

    arrives = ('<section class="section shop-arrives"><div><p class="eyebrow">Exactly what arrives</p><h2>One booklet, made for one person.</h2></div>'
               '<dl class="shop-spec">'
               '<div><dt>Pages</dt><dd>20, in full color. Large type: 16-point text, nothing smaller than 14</dd></div>'
               '<div><dt>Size</dt><dd>8½ × 11 inches, the size of a letter</dd></div>'
               '<div><dt>Binding</dt><dd>Saddle-stitched: folded and stapled at the spine, like a good program</dd></div>'
               '<div><dt>Paper</dt><dd>80 lb coated white, with a matte cover</dd></div>'
               '<div><dt>On the cover</dt><dd>Her year, and “For [her name], born [year]”</dd></div>'
               '<div><dt>Printed by</dt><dd>Lulu, the print-on-demand house, after you order</dd></div>'
               '<div><dt>Delivery</dt><dd>U.S. Mail, about 2½ weeks in all; U.S. addresses only</dd></div>'
               '<div><dt>Price</dt><dd>$49, shipping included. Another year in the same envelope, $29</dd></div>'
               '</dl></section>')

    faq = ('<section class="section reading shop-faq"><h2>Before you order</h2>'
           '<details><summary>Can it go straight to her?</summary><p>Yes. Enter her mailing address on the payment page. Shipping to any U.S. address is included. There is no gift wrap.</p></details>'
           '<details><summary>Do I need a PayPal account?</summary><p>Usually not. The payment page opens on a card form, so most people pay by debit or credit card as a guest. PayPal decides case by case when it asks for an account; if you already have one, you can use it.</p></details>'
           '<details><summary>Will it arrive in time?</summary><p>Allow about 2½ weeks. Our printer’s own estimate for U.S. Mail is 11–13 business days from order to door. If you need it sooner, write to us before you order.</p></details>'
           '<details><summary>What if the name is wrong?</summary><p>The cover prints exactly as the preview above shows, so check the spelling there. If something arrives wrong because of us, write to ' + a('mailto:' + C['contact'], C['contact']) + ' and we will make it right.</p></details>'
           '<details><summary>Is this the same as the free sheet?</summary><p>No. The free sheet is a page of prices to print at home. The booklet is twenty printed pages with film, names, recipes, the paycheck page and the pages left for her.</p></details>'
           '<details><summary>Which years can I choose?</summary><p>Every year from 1930 to 1970. Years before 1938, when there was no federal minimum wage, show the prices without the minutes-of-work comparison.</p></details>'
           '</section>')

    close = ('<section class="section shop-close"><h2>The last page is hers.</h2>'
             '<p class="lede">Start with a price. The rest is what she remembers.</p>' + a('#order', 'Choose her year', 'button') + '</section>')

    schema = [{'@type': 'Product', 'name': 'Your Year, in Color', 'description': spec['spec'] + '. Personalized with one name and birth year, 1930–1970.',
               'image': C['origin'] + '/assets/img/shop/yy_hero-1600.webp', 'brand': {'@type': 'Brand', 'name': 'Make It Do'},
               'offers': {'@type': 'Offer', 'price': '49.00', 'priceCurrency': 'USD', 'availability': 'https://schema.org/' + ('InStock' if live else 'PreOrder'),
                          'shippingDetails': {'@type': 'OfferShippingDetails', 'shippingRate': {'@type': 'MonetaryAmount', 'value': '0', 'currency': 'USD'},
                                              'shippingDestination': {'@type': 'DefinedRegion', 'addressCountry': 'US'}}}}]
    page('/your-year/', 'Your Year, in Color: a birth-year booklet with her name on the cover',
         'The year she was born, as the government wrote it down: 20 printed pages, 8½ × 11, with her name on the cover. $49 with U.S. shipping.',
         crumbs([('Shop', '/shop/'), ('Your Year, in Color', None)]) + hero + grey + leaf + hers + arrives + faq + close,
         kind='ItemPage', schema=schema, scripts=('/assets/store.js',))

    def label(img_html, title, medium, dims, price, href, status=''):
        return (f'<article class="shop-item"><a href="{href}" class="shop-item-pic">{img_html}</a><div class="shop-label">'
                f'<h2 class="shop-label-title">{a(href, title)}</h2><p class="shop-medium">{medium}</p><p class="shop-dims">{dims}</p><p class="shop-cost">{price}</p>{status}</div></article>')

    shelf = (crumbs([('Shop', None)]) +
             '<section class="page-intro shop-intro"><p class="eyebrow">The Make It Do shop</p><h1>Things to keep,<br><span class="acc">printed one at a time.</span></h1>'
             '<p class="lede">Each one is printed for the person it’s for, from the same government records and real color film as the films.</p></section>'
             '<section class="shop-shelf">'
             + label(render('yy_hero', 'The Your Year booklet for 1953, closed beside an open copy'), 'Your Year, in Color',
                     'Printed booklet, saddle-stitched. Her name and birth year on the cover; 1930–1970.', '20 pages · 8½ × 11 in', '$49, U.S. shipping included', '/your-year/')
             + label(render('other_hero', 'Two booklets, 1953 for Margaret and 1951 for Walter'), 'Another year, same envelope',
                     'A second booklet with its own year and name, added to the same order.', '20 pages · 8½ × 11 in', '+$29', '/your-year/#second')
             + label(render('family_hero', 'The Family Years hardcover, open, with two closed copies'), 'The Family Years',
                     'Hardcover with up to eight family years in one book; three copies, one for each household.', '8½ × 11 in · casewrap',
                     '$249 for three', 'mailto:' + C['contact'] + '?subject=The%20Family%20Years',
                     '<p class="shop-status">Not on sale yet: it opens once its first printed proof passes. Write to us to be told.</p>')
             + label(pic('sheet-1953-p1.webp', 'Page 1 of the free 1953 price sheet', 680, 880, sizes='(max-width: 800px) 90vw, 30vw'), 'The year sheet',
                     'What things cost the year you were born, to print at home. 1930–1975.', '2-page PDF · large print', 'Free, no email needed', '/year/')
             + '</section>' + honest)
    page('/shop/', 'The shop: printed keepsakes from the year they were born',
         'Your Year, in Color, a 20-page booklet with her name on the cover ($49 with U.S. shipping); another year in the same envelope; the free year sheet.', shelf)

    thanks = (crumbs([('Shop', '/shop/'), ('Your order', None)]) +
              '<section class="page-intro reading shop-thanks" id="thanks" data-api="' + api + '"><p class="eyebrow">Thank you</p><h1>Your order is in.</h1>'
              '<p class="lede" id="thanks-line">We’re checking the payment with PayPal. Nothing prints until it clears.</p>'
              '<p>PayPal emails your receipt. Your order number is <b id="thanks-id">shown on your receipt</b>. Questions: ' + a('mailto:' + C['contact'], C['contact']) + '.</p></section>')
    page('/shop/thanks/', 'Your order', 'Your Make It Do order.', thanks, noindex=True, scripts=('/assets/store.js',))
