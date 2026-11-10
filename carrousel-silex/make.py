"""Génère le carrousel « cinq leçons d'endurance réalistes » de Silex Podcast.

Style calqué sur le carrousel de référence : photo plein cadre, grand numéro
à empattements, texte court en sans-serif arrondie, ombre légère, rien d'autre.

Usage : python3 make.py
Sortie : slides/slide_01.jpg … slide_07.jpg, preview.jpg et carrousel-silex.pdf
Pour changer un texte ou une photo, modifie COVER / SLIDES / CTA puis relance.
"""
import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350


def font(name, size):
    return ImageFont.truetype(os.path.join(HERE, 'fonts', name + '.ttf'), size)


SERIF = 'PlayfairDisplay_400Regular'
SANS = {400: 'Poppins_400Regular', 500: 'Poppins_500Medium', 600: 'Poppins_600SemiBold',
        700: 'Poppins_700Bold', 800: 'Poppins_800ExtraBold'}


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
    im = im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
    return ImageEnhance.Brightness(im).enhance(0.9).convert('RGBA')  # très léger assombrissement


def draw_text(base, xy, s, fnt, anchor='la', blur=6, op=190, spacing=0, align='center'):
    """Texte blanc avec une ombre douce, comme sur la référence."""
    for b, o in ((blur * 4, int(op * 0.55)), (blur, op)):  # halo large + ombre serrée
        sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).multiline_text(xy, s, font=fnt, fill=(0, 0, 0, o), anchor=anchor,
                                          spacing=spacing, align=align)
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(b)))
    ImageDraw.Draw(base).multiline_text(xy, s, font=fnt, fill='white', anchor=anchor,
                                        spacing=spacing, align=align)


def wrap(s, fnt, maxw):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, cur = [], ''
    for word in s.split(' '):
        t = (cur + ' ' + word).strip()
        if not cur or d.textlength(t, font=fnt) <= maxw or word[0] in '»,.':
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return '\n'.join(lines)


def cover(c):
    im = photo(c['photo'], c.get('fx', 0.5), c.get('fy', 0.5))
    x0, y = 92, c.get('top', 330)
    draw_text(im, (-24, y), 'cinq', font(SANS[800], 318), anchor='ls')
    y += 150
    draw_text(im, (x0, y), 'leçons', font(SANS[700], 150), anchor='ls')
    y += 92
    draw_text(im, (x0 + 6, y), c['middle'], font(SANS[400], 54), anchor='ls')
    y += 158
    draw_text(im, (x0, y), c['big'], font(SANS[800], 150), anchor='ls')
    y += 62
    draw_text(im, (x0 + 6, y), c['small'], font(SANS[500], 36), anchor='ls')
    return im


def lesson(s):
    im = photo(s['photo'], s.get('fx', 0.5), s.get('fy', 0.5), s.get('zoom', 1.0))
    y = int(H * s['y'])
    draw_text(im, (W // 2, y), f"{s['n']}.", font(SERIF, 168), anchor='ms')
    body = font(SANS[600], 39)
    keep = s['text'].replace('« ', '«\u00a0').replace(' »', '\u00a0»')  # guillemets collés au mot
    txt = wrap(keep, body, s.get('maxw', 740))
    draw_text(im, (W // 2, y + 24), txt, body, anchor='ma', spacing=4)
    bottom = ImageDraw.Draw(im).multiline_textbbox((W // 2, y + 24), txt, font=body, anchor='ma',
                                                   spacing=4)[3]
    draw_text(im, (W // 2, bottom + 28), s['who'], font(SANS[500], 28), anchor='ma')
    return im


def cta(c):
    im = photo(c['photo'], c.get('fx', 0.5), c.get('fy', 0.5), c.get('zoom', 1.0))
    y = int(H * c['y'])
    draw_text(im, (W // 2, y), c['title'], font(SANS[700], 64), anchor='ma', spacing=6)
    body = font(SANS[600], 40)
    draw_text(im, (W // 2, y + 190), wrap(c['text'], body, 720), body, anchor='ma', spacing=4)
    return im


COVER = {
    'photo': 'pointe-mont-blanc', 'top': 330,
    'middle': "d'endurance réalistes tirées de",
    'big': '36 invités',
    'small': '(dont un champion olympique)',
}

SLIDES = [
    {'photo': 'sortie-eau', 'fy': 0.0, 'n': 1, 'y': 0.22,
     'text': "À Tokyo, sa VO2max tournait autour de 85 : il gagne l'or. Avant Paris, elle était à 97 : il perd. « Le but, c'est de gagner le jour de la course. »",
     'who': 'Kristian Blummenfelt, champion olympique'},
    {'photo': 'arche-utmb', 'fy': 0.6, 'n': 2, 'y': 0.21,
     'text': "Pas le temps ? « 5 minutes, ça compte. » Même en jean, c'est 450 appuis par jambe. Alors cours un peu, tous les jours.",
     'who': 'Blaise Dubois, La Clinique du Coureur'},
    {'photo': 'velo-trio', 'fx': 0.62, 'n': 3, 'y': 0.16,
     'text': "« La récupération fait partie de l'entraînement. » Dormir, bien manger, te reposer : pas besoin du dernier complément à la mode.",
     'who': 'Guillaume Millet, spécialiste de la fatigue'},
    {'photo': 'velo-lyon', 'n': 4, 'y': 0.18,
     'text': "Le plus important, c'est la base : du volume, en aisance, pas à fond. « Si on est en aisance, le lendemain, on a envie d'y retourner. »",
     'who': "Chloé Herbiet, championne d'Europe de semi"},
    {'photo': 'tente', 'n': 5, 'y': 0.18,
     'text': "« Il faut aimer, et le faire pour soi-même. » Si tu passes ton temps à te comparer, un jour ou l'autre, ça ne tiendra plus.",
     'who': 'Dawa Sherpa, vainqueur du premier UTMB'},
]

# Photo en combinaison : recadrage serré qui s'arrête au buste.
CTA = {
    'photo': 'avant-depart', 'fx': 0.31, 'fy': 0.43, 'zoom': 1.6, 'y': 0.06,
    'title': 'Enregistre ce post\npour ta prochaine prépa',
    'text': "Commence par l'épisode avec Kristian Blummenfelt. Lien en bio.",
}

if __name__ == '__main__':
    out = os.path.join(HERE, 'slides')
    os.makedirs(out, exist_ok=True)
    slides = [cover(COVER)] + [lesson(s) for s in SLIDES] + [cta(CTA)]
    slides = [s.convert('RGB') for s in slides]
    for i, s in enumerate(slides):
        s.save(os.path.join(out, f'slide_{i + 1:02d}.jpg'), quality=93)
    slides[0].save(os.path.join(HERE, 'carrousel-silex.pdf'), save_all=True,
                   append_images=slides[1:], resolution=150)
    pad, tw, th = 24, 360, 450
    prev = Image.new('RGB', (pad + 4 * (tw + pad), pad + 2 * (th + pad)), (245, 245, 245))
    for i, s in enumerate(slides):
        prev.paste(s.resize((tw, th)), (pad + (i % 4) * (tw + pad), pad + (i // 4) * (th + pad)))
    prev.save(os.path.join(HERE, 'preview.jpg'), quality=92)
    print('ok', len(slides))
