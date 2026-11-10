"""Génère le carrousel « cinq leçons… » de Silex Podcast.

Usage : python3 make.py   (depuis n'importe où)
Pour changer un texte ou une photo, modifie COVER / SLIDES / CTA puis relance.
Dans les leçons, **mots** = mots mis en couleur.
"""
import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
ACCENT = (255, 210, 63)


def font(name, size):
    path = subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout
    return ImageFont.truetype(path, size)


def photo(name, fx=0.5, fy=0.5, zoom=1.0):
    """Recadre la photo en 4:5 autour du point (fx, fy) puis la met en 1080x1350."""
    im = Image.open(os.path.join(HERE, 'photos', name + '.jpg')).convert('RGB')
    w, h = im.size
    if w / h > W / H:
        cw, ch = int(h * W / H), h
    else:
        cw, ch = w, int(w * H / W)
    cw, ch = int(cw / zoom), int(ch / zoom)
    x = min(max(int(fx * w - cw / 2), 0), w - cw)
    y = min(max(int(fy * h - ch / 2), 0), h - ch)
    return im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS).convert('RGBA')


def bottom_shade(im, start=0.5, full=0.8, alpha=235):
    """Dégradé sombre en bas de l'image (sert aussi à masquer le bas de la photo)."""
    g = Image.new('L', (1, H))
    for y in range(H):
        t = (y / H - start) / (full - start)
        g.putpixel((0, y), int(alpha * min(max(t, 0), 1)))
    black = Image.new('RGBA', (W, H), (8, 10, 14, 255))
    black.putalpha(g.resize((W, H)))
    im.alpha_composite(black)


def top_shade(im, end=0.42, alpha=130):
    g = Image.new('L', (1, H))
    for y in range(H):
        g.putpixel((0, y), int(alpha * max(0, 1 - y / (H * end))))
    black = Image.new('RGBA', (W, H), (8, 10, 14, 255))
    black.putalpha(g.resize((W, H)))
    im.alpha_composite(black)


def shadowed(base, draw_fn, blur, op):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(sh), (0, 0, 0, op))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    draw_fn(ImageDraw.Draw(base), None)


def text(base, xy, s, fnt, anchor='mm', blur=10, op=150, spacing=6, fill='white'):
    shadowed(base, lambda d, c: d.multiline_text(xy, s, font=fnt, fill=c or fill, anchor=anchor,
                                                 spacing=spacing, align='center'), blur, op)


def rich(base, y, s, fnt, maxw=840, lh=58, blur=12, op=190):
    """Texte centré multi-lignes, **mots** en couleur. Renvoie le y de fin."""
    words = []
    for i, part in enumerate(re.split(r'\*\*', s)):
        words += [(w, i % 2 == 1) for w in part.split(' ') if w]  # \u00a0 = espace insécable
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    sp = d.textlength(' ', font=fnt)
    lines, cur, cw = [], [], 0
    for w, hl in words:
        ww = d.textlength(w, font=fnt)
        if cur and cw + sp + ww > maxw and w[0] not in ',.)':
            lines.append((cur, cw))
            cur, cw = [], 0
        glue = bool(cur) and w[0] in ',.)'
        cw = cw + (sp if cur and not glue else 0) + ww
        cur.append((w, hl, ww, glue))
    lines.append((cur, cw))

    def draw(dr, c):
        yy = y
        for line, lw in lines:
            x = (W - lw) / 2
            for k, (w, hl, ww, glue) in enumerate(line):
                if k and not glue:
                    x += sp
                dr.text((x, yy), w, font=fnt, fill=c or (ACCENT if hl else 'white'), anchor='la')
                x += ww
            yy += lh
    shadowed(base, draw, blur, op)
    return y + lh * len(lines)


def cover(c):
    im = photo(c['photo'])
    text(im, (-28, 330), 'cinq', font('Inter Display:black', 330), anchor='ls', blur=16, op=120)
    text(im, (150, 470), 'leçons', font('Inter Display:extrabold', 150), anchor='ls', blur=12, op=120)
    text(im, (155, 560), "d'endurance réalistes", font('Inter Display:light', 64), anchor='ls', blur=10, op=160)
    bottom_shade(im, 0.55, 1.0, 170)
    y = 980
    for line in c['bottom']:
        text(im, (62, y), line, font('Inter Display:black', 62), anchor='ls', blur=12, op=150)
        y += 70
    text(im, (66, y + 10), c['small'], font('Inter Display:medium', 36), anchor='ls', blur=8, op=190)
    return im


def lesson(s):
    im = photo(s['photo'], s.get('fx', 0.5), s.get('fy', 0.5), s.get('zoom', 1.0))
    if s.get('bottom'):
        bottom_shade(im, s.get('shade_start', 0.45), s.get('shade_full', 0.72), 240)
    else:
        top_shade(im, *s.get('shade', (0.42, 130)))
    y = int(H * s.get('y', 0.10))
    text(im, (W // 2, y + 120), f"{s['n']}.", font('FreeSerif', 140), anchor='ms', blur=14, op=130)
    text(im, (W // 2, y + 190), s['name'], font('Inter Display:black', 62), anchor='ms', blur=12, op=170)
    text(im, (W // 2, y + 236), s['role'], font('Inter Display:medium', 32), anchor='ms', blur=8, op=190)
    rich(im, y + 275, s['text'], font('Inter:bold', 44))
    text(im, (W // 2, H - 60), s['credit'], font('Inter:semibold', 26), anchor='ms', blur=8, op=190)
    return im


def cta(c):
    im = photo(c['photo'])
    top_shade(im, end=0.62, alpha=215)
    y = int(H * 0.09)
    text(im, (W // 2, y), c['title'], font('Inter Display:black', 92), anchor='ma', blur=14, op=190)
    text(im, (W // 2, y + 112), c['sub'], font('Inter Display:bold', 52), anchor='ma', blur=12, op=190)
    yy = y + 250
    for line, hl in c['lines']:
        text(im, (W // 2, yy), line, font('Inter:bold', 46), anchor='ma', blur=10, op=200,
             fill=ACCENT if hl else 'white')
        yy += 62
    return im


COVER = {
    'photo': 'pointe-mont-blanc',
    'bottom': ['tirées de 36 invités,', 'dont un champion olympique'],
    'small': '(que la plupart des coureurs ignorent)',
}

# Les leçons marquées [À VALIDER] dans legende.md sont à confirmer avec ce que l'invité dit vraiment.
SLIDES = [
    {'photo': 'sortie-eau', 'fy': 0.0, 'n': 1, 'y': 0.02,
     'name': 'Kristian Blummenfelt', 'role': 'champion olympique de triathlon',
     'text': "À Tokyo, sa VO2max tournait autour de **85** : il gagne l'or. Avant Paris, elle était à **97** : il perd. « Le but, c'est de **gagner le jour de la course**. »",
     'credit': 'Épisode 10 · Silex Podcast'},
    {'photo': 'arche-utmb', 'fy': 0.6, 'n': 2, 'y': 0.06, 'shade': (0.55, 175),
     'name': 'Blaise Dubois', 'role': 'fondateur de La Clinique du Coureur',
     'text': "Pas le temps ? **«\u00a05\u00a0minutes, ça\u00a0compte.\u00a0»** Même en jean, c'est 450 appuis par jambe. Alors cours **un peu, tous les jours**.",
     'credit': 'Épisode 12 · Silex Podcast'},
    {'photo': 'velo-trio', 'fx': 0.62, 'n': 3, 'y': 0.03,
     'name': 'Guillaume Millet', 'role': 'chercheur, spécialiste de la fatigue',
     'text': "La fatigue ne se joue pas que dans les jambes. **Ton cerveau** décide souvent avant tes muscles.",
     'credit': 'Épisode 14 · Silex Podcast'},
    {'photo': 'velo-lyon', 'n': 4, 'y': 0.06,
     'name': 'Chloé Herbiet', 'role': "de sage-femme à championne d'Europe",
     'text': "**Un vrai boulot** n'empêche pas d'aller loin. Ta vie n'est pas un frein : c'est le cadre de ton entraînement.",
     'credit': 'Épisode 8 · Silex Podcast'},
    {'photo': 'avant-depart', 'fx': 0.53, 'fy': 0.55, 'zoom': 1.15, 'n': 5, 'bottom': True, 'y': 0.50,
     'shade_start': 0.40, 'shade_full': 0.62,
     'name': 'Dawa Sherpa', 'role': 'vainqueur du tout premier UTMB',
     'text': "Les pionniers n'attendaient pas d'être prêts. **Toi non plus** : la meilleure course est celle à laquelle tu t'inscris.",
     'credit': 'Épisode 35 · Silex Podcast'},
]

CTA = {
    'photo': 'tente',
    'title': 'Enregistre ce post',
    'sub': 'pour ta prochaine prépa',
    'lines': [("Commence par l'épisode avec", False), ('Kristian Blummenfelt', True), ('lien en bio', False)],
}

if __name__ == '__main__':
    out = os.path.join(HERE, 'slides')
    os.makedirs(out, exist_ok=True)
    slides = [cover(COVER)] + [lesson(s) for s in SLIDES] + [cta(CTA)]
    for i, s in enumerate(slides):
        s.convert('RGB').save(os.path.join(out, f'slide_{i + 1:02d}.jpg'), quality=93)
    prev = Image.new('RGB', (360 * 4, 450 * 2), 'white')
    for i, s in enumerate(slides):
        prev.paste(s.convert('RGB').resize((360, 450)), ((i % 4) * 360, (i // 4) * 450))
    prev.save(os.path.join(HERE, 'preview.jpg'))
    print('ok', len(slides))
