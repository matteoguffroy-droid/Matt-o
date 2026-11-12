"""Carrousel « 5 comptes à suivre si tu aimes courir ».

Polices et typographie du carrousel « cinq leçons » (../make.py), structure
des posts « comptes à suivre » : fond uni tramé, numéro, photo de profil,
@ en pastille, « pourquoi le suivre ? » et aperçu de publications du compte.

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et comptes-a-suivre.pdf
Images des comptes : accounts/<compte>/0.jpg (photo de profil), 1.jpg… (publications).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make import H, W, SANS, SERIF, Image, ImageDraw, ImageFilter, ImageFont, font, photo, wrap  # noqa: E402

# Charte Silex Podcast (relevée sur les miniatures YouTube)
BG = (27, 75, 75)           # vert canard
LIGHT = (39, 98, 96)        # halo plus clair en haut
DOT = (255, 255, 255, 16)   # trame de points discrète
ACCENT = (252, 144, 76)     # orange Silex
SOFT = (196, 222, 218)      # texte secondaire
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'


def background():
    im = Image.new('RGBA', (W, H), BG + (255,))
    # halo doux en haut de la slide
    halo = Image.new('L', (W, H), 0)
    ImageDraw.Draw(halo).ellipse((-W * 0.3, -H * 0.45, W * 1.3, H * 0.55), fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new('RGBA', (W, H), LIGHT + (255,)), im, halo)
    dots = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dots)
    for y in range(18, H, 36):
        for x in range(18, W, 36):
            d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=DOT)
    im.alpha_composite(dots)
    return im


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    c = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(c).text((10, 10), ch, font=f, embedded_color=True)
    c = c.crop(c.getbbox())
    return c.resize((int(c.width * size / c.height), size), Image.LANCZOS)


def runs(im, cy, parts, gap=0):
    """Ligne centrée faite de morceaux : (texte, police, couleur) ou ('emoji', caractère, taille)."""
    d = ImageDraw.Draw(im)
    items = []
    for p in parts:
        if p[0] == 'emoji':
            e = emoji(p[1], p[2])
            items.append(('e', e, e.width))
        else:
            items.append(('t', p, d.textlength(p[0], font=p[1])))
    total = sum(w for _, _, w in items) + gap * (len(items) - 1)
    x = (W - total) / 2
    for kind, it, w in items:
        if kind == 'e':
            im.alpha_composite(it, (int(x), int(cy - it.height / 2)))
        else:
            txt, f, col = it
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((x, cy), txt, font=f, fill=(0, 0, 0, 150), anchor='lm')
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
            ImageDraw.Draw(im).text((x, cy), txt, font=f, fill=col, anchor='lm')
        x += w + gap
    return (W - total) / 2, (W + total) / 2


def insta_sticker(size, angle=-10):
    """Petit logo d'appareil photo façon Instagram, dessiné (dégradé orange-rose-violet)."""
    g = Image.new('RGBA', (size, size))
    gd = ImageDraw.Draw(g)
    c0, c1, c2 = (254, 176, 64), (232, 38, 112), (140, 54, 214)
    for i in range(size * 2):
        t = i / (size * 2)
        col = tuple(int(c0[k] + (c1[k] - c0[k]) * t * 2) if t < .5 else int(c1[k] + (c2[k] - c1[k]) * (t - .5) * 2) for k in range(3))
        gd.line((i, 0, 0, i), fill=col + (255,), width=2)
    m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), size // 4, fill=255)
    g.putalpha(m)
    d = ImageDraw.Draw(g)
    s = size
    d.rounded_rectangle((s * .2, s * .2, s * .8, s * .8), s * .18, outline='white', width=max(3, s // 14))
    d.ellipse((s * .36, s * .36, s * .64, s * .64), outline='white', width=max(3, s // 14))
    d.ellipse((s * .66, s * .28, s * .72, s * .34), fill='white')
    framed = Image.new('RGBA', (size + 10, size + 10), (0, 0, 0, 0))
    framed.alpha_composite(g, (5, 5))
    return framed.rotate(angle, resample=Image.BICUBIC, expand=True)


def text(im, xy, s, fnt, fill='white', anchor='la', spacing=4, align='center'):
    ImageDraw.Draw(im).multiline_text(xy, s, font=fnt, fill=fill, anchor=anchor, spacing=spacing, align=align)


def fit(img, w, h):
    """Recadre une image au centre pour remplir w x h."""
    iw, ih = img.size
    s = max(w / iw, h / ih)
    img = img.resize((int(iw * s + 1), int(ih * s + 1)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def rounded(img, r):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255)
    out = img.convert('RGBA')
    out.putalpha(m)
    return out


def shadow_paste(base, img, xy, blur=18, op=150):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    block = Image.new('RGBA', img.size, (0, 0, 0, 255))
    block.putalpha(img.split()[3].point(lambda v: v * op // 255))
    sh.paste(block, (xy[0], xy[1] + 10), block)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(img, xy)


def avatar(handle, d):
    p = os.path.join(HERE, 'accounts', handle, '0.jpg')
    if os.path.exists(p):
        pic = fit(Image.open(p).convert('RGB'), d, d)
    else:  # pas de photo de profil : initiale sur fond orange
        pic = Image.new('RGB', (d, d), ACCENT)
        ImageDraw.Draw(pic).text((d // 2, d // 2), handle[0].upper(), font=font(SANS[800], d // 2),
                                 fill='white', anchor='mm')
    m = Image.new('L', (d, d), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    ring = Image.new('RGBA', (d + 12, d + 12), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, d + 11, d + 11), fill='white')
    pic = pic.convert('RGBA')
    pic.putalpha(m)
    ring.alpha_composite(pic, (6, 6))
    return ring


def chip(im, cx, y, label):
    f = font(SANS[700], 46)
    w = ImageDraw.Draw(im).textlength(label, font=f)
    x0, x1 = cx - w / 2 - 30, cx + w / 2 + 30
    ImageDraw.Draw(im).rounded_rectangle((x0, y, x1, y + 80), 40, fill=ACCENT)
    text(im, (cx, y + 40), label, f, anchor='mm')


def cover(c):
    """Première slide inspirée du post « Ces 6 comptes que j'adore suivre » : ta photo + titre."""
    im = photo(c['photo'], c.get('fx', 0.5), c.get('fy', 0.5), c.get('zoom', 1.0))
    # léger voile à la couleur Silex, puis dégradé vert canard vers le bas pour le titre
    im.alpha_composite(Image.new('RGBA', (W, H), BG + (38,)))
    g = Image.new('L', (1, H))
    for y in range(H):
        t = (y / H - 0.36) / 0.36
        g.putpixel((0, y), int(225 * min(max(t, 0), 1)))
    shade = Image.new('RGBA', (W, H), BG + (255,))
    shade.putalpha(g.resize((W, H)))
    im.alpha_composite(shade)
    big, reg = font(SANS[800], 122), font(SANS[400], 122)
    y = int(H * 0.555)
    x0, x1 = runs(im, y, [('Ces ', reg, 'white'), ('5 comptes', big, 'white')])
    st = insta_sticker(104)
    im.alpha_composite(st, (int(x1 - 70), int(y - 150)))
    runs(im, y + 128, [("que j'", reg, 'white'), ('adore', big, ACCENT)])
    runs(im, y + 256, [('emoji', '\U0001F440', 84), ('suivre', big, ACCENT), ('emoji', '\U0001F3C3', 112)], gap=14)
    # pastille « si tu aimes courir »
    d = ImageDraw.Draw(im)
    f1, f2 = font(SANS[400], 46), font(SANS[700], 46)
    w1, w2 = d.textlength('si tu aimes ', font=f1), d.textlength('courir', font=f2)
    pw, ph, py = w1 + w2 + 70, 86, y + 350
    px = (W - pw) / 2
    d.rounded_rectangle((px, py, px + pw, py + ph), ph / 2, fill=BG, outline=(255, 255, 255), width=3)
    d.text((px + 35, py + ph / 2), 'si tu aimes ', font=f1, fill='white', anchor='lm')
    d.text((px + 35 + w1, py + ph / 2), 'courir', font=f2, fill='white', anchor='lm')
    return im


def account(s):
    im = background()
    text(im, (W // 2, 150), f"{s['n']}.", font(SERIF, 130), anchor='ms')
    av = avatar(s['handle'], 156)
    shadow_paste(im, av, (W // 2 - av.width // 2, 180))
    chip(im, W // 2, 362, '@' + s['handle'])
    y = 470
    if s.get('meta'):
        text(im, (W // 2, y), s['meta'], font(SANS[500], 30), fill=SOFT, anchor='ma')
        y += 60
    text(im, (W // 2, y), 'Pourquoi le suivre ?', font(SANS[400], 34), fill=SOFT, anchor='ma')
    body = font(SANS[600], 40)
    text(im, (W // 2, y + 52), wrap(s['text'], body, 800), body, anchor='ma')
    posts = s.get('posts', [])
    if posts:
        tw, th, gap = 296, 370, 22
        n = len(posts[:3])
        x = (W - (n * tw + (n - 1) * gap)) // 2
        for i in posts[:3]:
            img = fit(Image.open(os.path.join(HERE, 'accounts', s['handle'], f'{i}.jpg')).convert('RGB'), tw, th)
            shadow_paste(im, rounded(img, 26), (x, H - th - 80))
            x += tw + gap
    return im


def cta(c):
    im = background()
    text(im, (W // 2, H // 2 - 150), c['title'], font(SANS[800], 96), anchor='ma', spacing=10)
    body = font(SANS[600], 42)
    text(im, (W // 2, H // 2 + 110), wrap(c['text'], body, 820), body, anchor='ma')
    return im


COVER = {'photo': 'sortie-eau', 'fy': 1.0}

# Descriptions tirées des publications publiques des comptes (novembre 2026).
# papacanca.io et mustapha.salmi_ : comptes non lisibles depuis la session, textes à fournir.
ACCOUNTS = [
    {'n': 1, 'handle': 'lesgenouxdanslegif', 'meta': '182 k abonnés', 'posts': [1, 2, 3],
     'text': "Le trail raconté avec humour, des lives de course et leur revue Point de Côté : 192 pages, zéro pub."},
    {'n': 2, 'handle': 'simon.dugue', 'meta': '29 k abonnés', 'posts': [1, 2, 4],
     'text': "Ses photos et ses films de l'UTMB, de la Diagonale des Fous ou du Tor des Géants sont de vraies œuvres."},
    {'n': 3, 'handle': 'maxime_lopes', 'meta': '18,9 k abonnés', 'posts': [1, 4],
     'text': "Marathonien en 2h20, il partage ses prépas et ses chronos, et anime le podcast Runwise."},
    {'n': 4, 'handle': 'papacanca.io', 'meta': '',
     'text': "TEXTE À COMPLÉTER"},
    {'n': 5, 'handle': 'mustapha.salmi_', 'meta': '',
     'text': "TEXTE À COMPLÉTER"},
]

CTA = {
    'title': 'Et toi, tu suis\nqui ?',
    'text': "Donne tes pépites en commentaire. Les interviews, c'est sur Silex Podcast (lien en bio).",
}

if __name__ == '__main__':
    out = os.path.join(HERE, 'slides')
    os.makedirs(out, exist_ok=True)
    slides = [cover(COVER)] + [account(a) for a in ACCOUNTS] + [cta(CTA)]
    slides = [s.convert('RGB') for s in slides]
    for i, s in enumerate(slides):
        s.save(os.path.join(out, f'slide_{i + 1:02d}.jpg'), quality=93)
    slides[0].save(os.path.join(HERE, 'comptes-a-suivre.pdf'), save_all=True,
                   append_images=slides[1:], resolution=150)
    pad, tw, th = 24, 360, 450
    prev = Image.new('RGB', (pad + 4 * (tw + pad), pad + 2 * (th + pad)), (245, 245, 245))
    for i, s in enumerate(slides):
        prev.paste(s.resize((tw, th)), (pad + (i % 4) * (tw + pad), pad + (i // 4) * (th + pad)))
    prev.save(os.path.join(HERE, 'preview.jpg'), quality=92)
    print('ok', len(slides))
