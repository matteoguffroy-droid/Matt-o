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
from make import H, W, SANS, SERIF, Image, ImageDraw, ImageFilter, font, wrap  # noqa: E402

BG = (16, 23, 42)          # bleu nuit
DOT = (255, 255, 255, 18)  # trame de points discrète
ACCENT = (232, 89, 12)     # orange (pastille du @)
SOFT = (196, 204, 222)     # texte secondaire


def background():
    im = Image.new('RGBA', (W, H), BG + (255,))
    dots = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dots)
    for y in range(18, H, 36):
        for x in range(18, W, 36):
            d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=DOT)
    im.alpha_composite(dots)
    return im


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
    im = background()
    x0, y = 92, 360
    text(im, (-24, y), 'cinq', font(SANS[800], 318), anchor='ls')
    y += 182
    text(im, (x0, y), 'comptes', font(SANS[700], 150), anchor='ls')
    y += 92
    text(im, (x0 + 6, y), 'à suivre si tu aimes', font(SANS[400], 54), anchor='ls')
    y += 140
    text(im, (x0, y), 'courir', font(SANS[800], 150), anchor='ls')
    y += 62
    text(im, (x0 + 6, y), c['small'], font(SANS[500], 36), fill=SOFT, anchor='ls')
    # les 5 photos de profil en rang, qui se chevauchent légèrement
    d, step = 150, 128
    x = (W - (step * (len(ACCOUNTS) - 1) + d + 12)) // 2
    for a in ACCOUNTS:
        av = avatar(a['handle'], d)
        shadow_paste(im, av, (x, H - 300))
        x += step
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


COVER = {'small': '(que je suis vraiment, promis)'}

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
