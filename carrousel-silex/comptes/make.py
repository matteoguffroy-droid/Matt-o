"""Carrousel « 5 comptes à suivre si tu aimes courir ».

Même direction artistique que le carrousel « cinq leçons » : on réutilise ses
polices, ses photos et ses fonctions de mise en page (../make.py).

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et comptes-a-suivre.pdf
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make import H, W, SANS, SERIF, Image, ImageDraw, cta, draw_text, font, photo, wrap  # noqa: E402


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
    y = int(H * s['y'])
    draw_text(im, (W // 2, y), f"{s['n']}.", font(SERIF, 168), anchor='ms')
    draw_text(im, (W // 2, y + 26), s['name'], font(SANS[700], 58), anchor='ma')
    body = font(SANS[600], 39)
    draw_text(im, (W // 2, y + 112), wrap(s['text'], body, 740), body, anchor='ma', spacing=4)
    return im


COVER = {'photo': 'arche-utmb', 'fy': 0.6, 'top': 330, 'small': '(testés et approuvés au micro de Silex)'}

# Descriptions tirées des interviews du podcast (voir ../conseils-*.md).
ACCOUNTS = [
    {'photo': 'trail-foret', 'n': 1, 'y': 0.16, 'name': 'La Clinique du Coureur',
     'text': "Blaise Dubois et son équipe démontent les idées reçues sur les blessures, les chaussures et les étirements. Toujours avec la science derrière."},
    {'photo': 'velo-trio', 'fx': 0.62, 'n': 2, 'y': 0.12, 'name': 'Guillaume Millet',
     'text': "Chercheur spécialiste de la fatigue et auteur de livres sur l'ultra-trail. Il t'explique ce qui se passe vraiment dans ton corps quand tu coinces."},
    {'photo': 'sortie-eau', 'fy': 0.0, 'n': 3, 'y': 0.15, 'name': 'Chloé Herbiet',
     'text': "Sage-femme devenue championne d'Europe de semi-marathon. Une des plus belles histoires de l'athlé belge."},
    {'photo': 'pointe-mont-blanc', 'n': 4, 'y': 0.12, 'name': 'Zinzin Reporter',
     'text': "L'homme derrière la caméra des plus grandes courses de trail. Ses vidéos te font vivre l'ultra de l'intérieur."},
    {'photo': 'tente', 'n': 5, 'y': 0.12, 'name': 'Dawa Sherpa',
     'text': "Vainqueur du tout premier UTMB, trois fois aux JO en ski de fond, et une association pour les enfants et les aînés au Népal."},
]

CTA = {
    'photo': 'avant-depart', 'fx': 0.31, 'fy': 0.43, 'zoom': 1.6, 'y': 0.06,
    'title': 'Et pour les écouter\nen vrai',
    'text': "Ils sont tous passés sur Silex Podcast. Lien en bio.",
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
