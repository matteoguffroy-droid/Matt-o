"""Carrousel « Ces 5 comptes que j'adore suivre — édition course à pied ».

Polices et typographie du carrousel « cinq leçons » (../make.py), structure
des posts « comptes à suivre » : fond uni tramé, numéro, photo de profil,
@ en pastille, « pourquoi le suivre ? » et aperçu de publications du compte.

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et comptes-a-suivre.pdf
Images des comptes : accounts/<compte>/0.jpg (photo de profil), 1.jpg… (publications).
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make import H, W, SANS, SERIF, Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, font, photo, wrap  # noqa: E402

# Charte Silex Podcast (relevée sur les miniatures YouTube)
BG = (27, 75, 75)           # vert canard
LIGHT = (39, 98, 96)        # halo plus clair en haut
ACCENT = (252, 144, 76)     # orange Silex
SOFT = (196, 222, 218)      # texte secondaire
DEEP = (11, 36, 37)         # vert canard profond (bas des slides)
SELECT = (236, 222, 150)    # surlignage façon sélection iOS
SELECT_KNOB = (246, 232, 170, 255)


def background(seed=0):
    """Fond premium : dégradé vert canard, courbes de niveau façon carte de trail, halo orange et grain."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = yy / H
    top, bottom = np.array(LIGHT, np.float32), np.array(DEEP, np.float32)
    img = top[None, None, :] * (1 - t[..., None]) + bottom[None, None, :] * t[..., None]
    # halo orange très discret, dans un coin qui change d'une slide à l'autre
    cx, cy = (W * 0.95, H * 0.95) if seed % 2 == 0 else (W * 0.05, H * 0.9)
    glow = np.exp(-(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.45)) ** 2))
    img += glow[..., None] * (np.array(ACCENT, np.float32) - img) * 0.16
    # courbes de niveau : champ lisse aléatoire, puis lignes à intervalles réguliers
    field = Image.fromarray((rng.random((9, 7)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    f = np.asarray(field.filter(ImageFilter.GaussianBlur(60)), np.float32) / 255
    f = (f - f.min()) / (f.max() - f.min() + 1e-6) * 16
    dist = np.abs(f - np.round(f))
    grad = np.hypot(*np.gradient(f)) + 1e-6
    line = np.clip(1 - dist / (grad * 1.6), 0, 1)
    img = img * (1 - line[..., None] * 0.10) + 255 * line[..., None] * 0.10
    # vignette et grain argentique
    v = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2)
    img *= (1 - v * 0.55)[..., None]
    img += rng.normal(0, 6, (H, W, 1))
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


def ios_font(size, weight='Medium'):
    path = subprocess.run(['fc-match', '-f', '%{file}', f'Inter:{weight.lower()}'], capture_output=True, text=True).stdout
    return ImageFont.truetype(path, size)


def selection(im, box):
    """Effet « texte sélectionné » d'iOS : surlignage, poignées et menu Copier / Tout sélectionner."""
    x0, y0, x1, y1 = box
    hl = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.rectangle(box, fill=SELECT + (105,))
    knob = SELECT_KNOB
    d.rectangle((x0 - 3, y0, x0 + 3, y1), fill=knob)
    d.rectangle((x1 - 3, y0, x1 + 3, y1), fill=knob)
    d.ellipse((x0 - 14, y0 - 26, x0 + 14, y0 + 2), fill=knob)
    d.ellipse((x1 - 14, y1 - 2, x1 + 14, y1 + 26), fill=knob)
    im.alpha_composite(hl)
    # menu contextuel au-dessus
    f = ios_font(38)
    items = ['Copier', 'Tout sélectionner', 'Rechercher']
    pad, h = 30, 82
    widths = [ImageDraw.Draw(im).textlength(t, font=f) + 2 * pad for t in items] + [62]
    mw = sum(widths)
    mx = min(max((x0 + x1) / 2 - mw / 2, 30), W - 30 - mw)
    my = y0 - 44 - h
    menu = Image.new('RGBA', im.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(menu)
    md.rounded_rectangle((mx, my, mx + mw, my + h), h / 2, fill=(255, 255, 255, 250))
    tx = (x0 + x1) / 2
    md.polygon([(tx - 18, my + h - 1), (tx + 18, my + h - 1), (tx, my + h + 18)], fill=(255, 255, 255, 250))
    x = mx
    for i, (t, w) in enumerate(zip(items + ['>'], widths)):
        if i:
            md.line((x, my + 14, x, my + h - 14), fill=(0, 0, 0, 40), width=2)
        if t == '>':
            md.line([(x + 24, my + 28), (x + 38, my + h / 2), (x + 24, my + h - 28)], fill=(20, 20, 20), width=4, joint='curve')
        else:
            md.text((x + w / 2, my + h / 2), t, font=f, fill=(20, 20, 20), anchor='mm')
        x += w
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((mx, my + 8, mx + mw, my + h + 8), h / 2, fill=(0, 0, 0, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(menu)


def runs(im, cy, parts, select=None):
    """Ligne centrée faite de morceaux (texte, police, couleur). select = index du morceau à « sélectionner »."""
    d = ImageDraw.Draw(im)
    widths = [d.textlength(t, font=f) for t, f, _ in parts]
    total = sum(widths)
    x = (W - total) / 2
    pos = []
    for (t, f, col), w in zip(parts, widths):
        pos.append(x)
        x += w
    if select is not None:
        t, f, _ = parts[select]
        bb = d.textbbox((pos[select], cy), t, font=f, anchor='lm')
        selection(im, (bb[0] - 10, cy - f.size * 0.46, bb[2] + 10, cy + f.size * 0.5))
    for (t, f, col), x in zip(parts, pos):
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, cy), t, font=f, fill=(0, 0, 0, 150), anchor='lm')
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).text((x, cy), t, font=f, fill=col, anchor='lm')
    return (W - total) / 2, (W + total) / 2, pos


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
    if 'shift' in c:
        # photo calée en largeur et remontée de `shift` pixels ; le bas est complété par le fond texturé
        im = background(0)
        ph = Image.open(os.path.join(os.path.dirname(HERE), 'photos', c['photo'] + '.jpg')).convert('RGB')
        ph = ph.resize((W, int(ph.height * W / ph.width)), Image.LANCZOS)
        ph = ImageEnhance.Brightness(ph).enhance(0.9).convert('RGBA')
        fade = Image.new('L', (1, ph.height))
        for yy in range(ph.height):
            fade.putpixel((0, yy), 255 if yy < ph.height - 160 else int(255 * (ph.height - yy) / 160))
        ph.putalpha(fade.resize(ph.size))
        im.alpha_composite(ph, (0, c['shift']))
    else:
        im = photo(c['photo'], c.get('fx', 0.5), c.get('fy', 0.5), c.get('zoom', 1.0))
    # léger voile à la couleur Silex, puis dégradé vert canard vers le bas pour le titre
    im.alpha_composite(Image.new('RGBA', (W, H), BG + (38,)))
    g = Image.new('L', (1, H))
    for y in range(H):
        t = (y / H - 0.5) / 0.3
        g.putpixel((0, y), int(225 * min(max(t, 0), 1)))
    shade = Image.new('RGBA', (W, H), BG + (255,))
    shade.putalpha(g.resize((W, H)))
    im.alpha_composite(shade)
    size = c.get('size', 122)
    big, reg = font(SANS[800], size), font(SANS[400], size)
    y = int(H * c.get('y', 0.555))
    lh = int(size * 1.05)
    x0, x1, _ = runs(im, y, [('Ces ', reg, 'white'), ('5 comptes', big, 'white')], select=1)
    st = insta_sticker(104)
    im.alpha_composite(st, (int(x1 - 30), int(y - size * 1.3)))
    runs(im, y + lh, [("que j'", reg, 'white'), ('adore', big, ACCENT)])
    runs(im, y + 2 * lh, [('suivre', big, ACCENT)])
    # pastille « édition course à pied »
    d = ImageDraw.Draw(im)
    f1, f2 = font(SANS[400], 46), font(SANS[700], 46)
    w1, w2 = d.textlength(c['pill'][0], font=f1), d.textlength(c['pill'][1], font=f2)
    pw, ph, py = w1 + w2 + 70, 86, y + 2 * lh + int(size * 0.75)
    px = (W - pw) / 2
    d.rounded_rectangle((px, py, px + pw, py + ph), ph / 2, fill=BG, outline=(255, 255, 255), width=3)
    d.text((px + 35, py + ph / 2), c['pill'][0], font=f1, fill='white', anchor='lm')
    d.text((px + 35 + w1, py + ph / 2), c['pill'][1], font=f2, fill='white', anchor='lm')
    return im


def account(s):
    im = background(s['n'])
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
    im = background(7)
    text(im, (W // 2, H // 2 - 150), c['title'], font(SANS[800], 96), anchor='ma', spacing=10)
    body = font(SANS[600], 42)
    text(im, (W // 2, H // 2 + 110), wrap(c['text'], body, 820), body, anchor='ma')
    return im


COVER = {'photo': 'trail-foret', 'shift': -460, 'y': 0.72, 'size': 100, 'pill': ('édition ', 'course à pied')}

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
