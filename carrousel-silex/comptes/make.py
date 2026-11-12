"""Carrousel « 5 comptes à suivre si tu aimes courir ».

Même direction artistique que le carrousel « cinq leçons » (polices, photos et
fonctions de mise en page de ../make.py), avec la structure des posts
« comptes à suivre » : @ bien visible, photo de profil, aperçu du compte et
« pourquoi le suivre ? ».

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et comptes-a-suivre.pdf
Les images des comptes (photo de profil 0.jpg, publications 1.jpg…) sont dans
accounts/<compte>/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make import H, W, SANS, SERIF, Image, ImageDraw, ImageFilter, cta, draw_text, font, photo, wrap  # noqa: E402


def cover(c):
    im = photo(c['photo'], c.get('fx', 0.5), c.get('fy', 0.5))
    x0, y = 92, c.get('top', 330)
    draw_text(im, (-24, y), 'cinq', font(SANS[800], 318), anchor='ls')
    y += 150
    draw_text(im, (x0, y), 'comptes', font(SANS[700], 150), anchor='ls')
    y += 92
    draw_text(im, (x0 + 6, y), 'à suivre si tu aimes', font(SANS[400], 54), anchor='ls')
    y += 140
    draw_text(im, (x0, y), 'courir', font(SANS[800], 150), anchor='ls')
    y += 62
    draw_text(im, (x0 + 6, y), c['small'], font(SANS[500], 36), anchor='ls')
    return im


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


def shadow_paste(base, img, xy, blur=18, op=120):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * op // 255)
    block = Image.new('RGBA', img.size, (0, 0, 0, 255))
    block.putalpha(a)
    sh.paste(block, (xy[0], xy[1] + 8), block)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(img, xy)


def avatar(acc, d):
    p = os.path.join(HERE, 'accounts', acc['handle'], '0.jpg')
    if os.path.exists(p):
        pic = fit(Image.open(p).convert('RGB'), d, d)
    else:  # pas de photo de profil récupérée : initiale sur fond orange
        pic = Image.new('RGB', (d, d), (232, 89, 12))
        ImageDraw.Draw(pic).text((d // 2, d // 2), acc['handle'][0].upper(), font=font(SANS[800], d // 2),
                                 fill='white', anchor='mm')
    m = Image.new('L', (d, d), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    ring = Image.new('RGBA', (d + 12, d + 12), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, d + 11, d + 11), fill='white')
    pic = pic.convert('RGBA')
    pic.putalpha(m)
    ring.alpha_composite(pic, (6, 6))
    return ring


def account(s):
    im = photo(s['photo'], s.get('fx', 0.5), s.get('fy', 0.5), s.get('zoom', 1.0))
    draw_text(im, (W // 2, 158), f"{s['n']}.", font(SERIF, 130), anchor='ms')
    av = avatar(s, 156)
    shadow_paste(im, av, (W // 2 - av.width // 2, 186))
    draw_text(im, (W // 2, 372), '@' + s['handle'], font(SANS[700], 52), anchor='ma')
    if s.get('meta'):
        draw_text(im, (W // 2, 436), s['meta'], font(SANS[500], 28), anchor='ma')
    draw_text(im, (W // 2, 506), 'Pourquoi le suivre ?', font(SANS[400], 32), anchor='ma')
    body = font(SANS[600], 38)
    draw_text(im, (W // 2, 556), wrap(s['text'], body, 760), body, anchor='ma', spacing=4)
    # aperçu du compte : 3 publications, comme sur les posts d'inspiration
    posts = s.get('posts', [])
    if posts:
        tw, th, gap = 296, 370, 22
        n = len(posts[:3])
        x = (W - (n * tw + (n - 1) * gap)) // 2
        for i in posts[:3]:
            img = fit(Image.open(os.path.join(HERE, 'accounts', s['handle'], f'{i}.jpg')).convert('RGB'), tw, th)
            card = rounded(img, 26)
            shadow_paste(im, card, (x, H - th - 70))
            x += tw + gap
    return im


COVER = {'photo': 'arche-utmb', 'fy': 0.6, 'top': 330, 'small': '(que je suis vraiment, promis)'}

# Descriptions tirées des publications publiques des comptes (novembre 2026).
# papacanca.io et mustapha.salmi_ : comptes non lisibles depuis la session, textes à fournir.
ACCOUNTS = [
    {'photo': 'pointe-mont-blanc', 'n': 1, 'handle': 'lesgenouxdanslegif', 'meta': '182 k abonnés', 'posts': [1, 2, 3],
     'text': "Le trail raconté avec humour, des lives de course et leur revue Point de Côté : 192 pages, zéro pub."},
    {'photo': 'tente', 'n': 2, 'handle': 'simon.dugue', 'meta': '29 k abonnés', 'posts': [1, 2, 4],
     'text': "Ses photos et ses films de l'UTMB, de la Diagonale des Fous ou du Tor des Géants sont de vraies œuvres."},
    {'photo': 'sortie-eau', 'fy': 0.0, 'n': 3, 'handle': 'maxime_lopes', 'meta': '18,9 k abonnés', 'posts': [1, 4],
     'text': "Marathonien en 2h20, il partage ses prépas et ses chronos, et anime le podcast Runwise."},
    {'photo': 'velo-trio', 'fx': 0.62, 'n': 4, 'handle': 'papacanca.io', 'meta': '',
     'text': "TEXTE À COMPLÉTER"},
    {'photo': 'velo-lyon', 'n': 5, 'handle': 'mustapha.salmi_', 'meta': '',
     'text': "TEXTE À COMPLÉTER"},
]

CTA = {
    'photo': 'avant-depart', 'fx': 0.31, 'fy': 0.43, 'zoom': 1.6, 'y': 0.06,
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
