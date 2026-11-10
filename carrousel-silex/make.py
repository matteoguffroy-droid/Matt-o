"""Génère le carrousel « 5 leçons d'endurance réalistes tirées de 36 épisodes ».

Usage : python3 make.py   (depuis le dossier carrousel-silex)
Pour changer un texte ou une photo, modifie la liste SLIDES puis relance.
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350


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


def text(base, xy, s, fnt, anchor='mm', blur=10, op=150, spacing=6):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).multiline_text(xy, s, font=fnt, fill=(0, 0, 0, op), anchor=anchor, spacing=spacing, align='center')
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).multiline_text(xy, s, font=fnt, fill='white', anchor=anchor, spacing=spacing, align='center')


def wrap(s, fnt, maxw):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, cur = [], ''
    for word in s.split():
        t = (cur + ' ' + word).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return '\n'.join(lines)


def cover():
    im = photo('pointe-mont-blanc', 0.5, 0.5)
    text(im, (-28, 330), 'cinq', font('Inter Display:black', 330), anchor='ls', blur=16, op=120)
    text(im, (150, 470), 'leçons', font('Inter Display:extrabold', 150), anchor='ls', blur=12, op=120)
    text(im, (155, 560), "d'endurance réalistes", font('Inter Display:light', 64), anchor='ls', blur=10, op=160)
    text(im, (66, 1040), 'tirées de', font('Inter Display:light', 64), anchor='ls', blur=10, op=170)
    text(im, (60, 1180), '36 épisodes', font('Inter Display:black', 140), anchor='ls', blur=14, op=140)
    text(im, (66, 1250), '(que la plupart des coureurs ignorent)', font('Inter Display:medium', 36), anchor='ls', blur=8, op=190)
    return im


def lesson(name, fx, fy, n, body, credit, cy, zoom=1.0):
    im = photo(name, fx, fy, zoom)
    y = int(H * cy)
    text(im, (W // 2, y), f'{n}.', font('FreeSerif', 150), anchor='ms', blur=14, op=130)
    b = font('Inter:bold', 44)
    text(im, (W // 2, y + 30), wrap(body, b, 820), b, anchor='ma', blur=12, op=180, spacing=4)
    text(im, (W // 2, H - 70), credit, font('Inter:semibold', 26), anchor='ms', blur=8, op=190)
    return im


def cta():
    im = photo('tente', 0.5, 0.5)
    text(im, (W // 2, int(H * 0.22)), '36 épisodes.\n36 histoires d’endurance.', font('Inter Display:black', 74), anchor='mm', blur=14, op=170, spacing=10)
    text(im, (W // 2, int(H * 0.22) + 140), 'Écoute Silex Podcast\nlien en bio', font('Inter:bold', 42), anchor='ma', blur=10, op=180, spacing=8)
    return im


# (photo, centre x, centre y, n°, leçon, crédit, hauteur du texte en fraction de la slide)
SLIDES = [
    ('arche-utmb', 0.5, 0.6, 1,
     "Personne ne commence par l'ultra. On monte une marche, puis la suivante. Ton prochain objectif doit te faire un peu peur, pas te terrifier.",
     'Leçon tirée de l’ép. 34 · Alvin Alexandre', 0.19),
    ('avant-depart', 0.53, 0.55, 2,
     "Tenter un truc immense et ne pas le finir, ce n'est pas un échec. C'est ce qui te rend capable de tout le reste.",
     'Leçon tirée de l’épisode avec Fabien Leroux', 0.11, 1.15),
    ('velo-trio', 0.62, 0.5, 3,
     "L'endurance ne récompense pas les plus forts à 25 ans. Elle récompense ceux qui sont encore là à 45.",
     'Leçon tirée de l’ép. 22 · Ludovic Pommeret', 0.22),
    ('velo-lyon', 0.5, 0.5, 4,
     "Un vrai boulot n'empêche pas d'aller loin. Ta vie n'est pas un frein : c'est le cadre de ton entraînement.",
     'Leçon tirée de l’épisode avec Chloé Herbiet', 0.24),
    ('sortie-eau', 0.5, 0.0, 5,
     "Les pionniers n'attendaient pas d'être prêts. Toi non plus : la meilleure course est celle à laquelle tu t'inscris.",
     'Leçon tirée de l’ép. 35 · Dawa Sherpa', 0.12),
]

if __name__ == '__main__':
    out = os.path.join(HERE, 'slides')
    os.makedirs(out, exist_ok=True)
    slides = [cover()] + [lesson(*s) for s in SLIDES] + [cta()]
    for i, s in enumerate(slides):
        s.convert('RGB').save(os.path.join(out, f'slide_{i + 1:02d}.jpg'), quality=93)
    prev = Image.new('RGB', (360 * 4, 450 * 2), 'white')
    for i, s in enumerate(slides):
        prev.paste(s.convert('RGB').resize((360, 450)), ((i % 4) * 360, (i // 4) * 450))
    prev.save(os.path.join(HERE, 'preview.jpg'))
    print('ok', len(slides))
