"""Carrousel « 5 comptes à suivre si tu aimes courir ».

Même direction artistique que le carrousel « cinq leçons » (polices, photos et
fonctions de mise en page de ../make.py), avec la structure des posts
« comptes à suivre » : @ bien visible, nombre d'abonnés et « pourquoi le suivre ? ».

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et comptes-a-suivre.pdf
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make import H, W, SANS, SERIF, Image, cta, draw_text, font, photo, wrap  # noqa: E402


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


def account(s):
    im = photo(s['photo'], s.get('fx', 0.5), s.get('fy', 0.5), s.get('zoom', 1.0))
    y = int(H * s.get('y', 0.17))
    draw_text(im, (W // 2, y), f"{s['n']}.", font(SERIF, 168), anchor='ms')
    draw_text(im, (W // 2, y + 30), '@' + s['handle'], font(SANS[700], 58), anchor='ma')
    yy = y + 110
    if s.get('meta'):
        draw_text(im, (W // 2, yy), s['meta'], font(SANS[500], 30), anchor='ma')
        yy += 62
    draw_text(im, (W // 2, yy), 'Pourquoi le suivre ?', font(SANS[400], 34), anchor='ma')
    body = font(SANS[600], 40)
    draw_text(im, (W // 2, yy + 54), wrap(s['text'], body, 760), body, anchor='ma', spacing=4)
    return im


COVER = {'photo': 'arche-utmb', 'fy': 0.6, 'top': 330, 'small': '(que je suis vraiment, promis)'}

# Descriptions tirées des publications publiques des comptes (novembre 2026).
# papacanca.io et mustapha.salmi_ : comptes non lisibles depuis la session, textes à fournir.
ACCOUNTS = [
    {'photo': 'pointe-mont-blanc', 'n': 1, 'handle': 'lesgenouxdanslegif', 'meta': '182 k abonnés',
     'text': "Le trail raconté avec humour, des lives de course et leur revue Point de Côté : 192 pages, zéro pub."},
    {'photo': 'tente', 'n': 2, 'handle': 'simon.dugue', 'meta': '29 k abonnés',
     'text': "Ses photos et ses films de l'UTMB, de la Diagonale des Fous ou du Tor des Géants sont de vraies œuvres."},
    {'photo': 'sortie-eau', 'fy': 0.0, 'n': 3, 'handle': 'maxime_lopes', 'meta': '18,9 k abonnés',
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
