import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
YT = sys.argv[1]; OUT = sys.argv[2]
W, H = 1080, 1350
F = '/usr/share/fonts'
def font(name, size):
    import subprocess
    p = subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout
    return ImageFont.truetype(p, size)

def prep(vid, box, patches=()):
    im = Image.open(os.path.join(YT, vid + '.jpg')).convert('RGB')
    for (x0, y0, x1, y1) in patches:
        bl = im.filter(ImageFilter.GaussianBlur(70))
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rectangle((x0, y0, x1, y1), fill=255)
        im = Image.composite(bl, im, m.filter(ImageFilter.GaussianBlur(10)))
    im = im.crop(box).resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return im

def shadow_text(base, xy, text, fnt, anchor='mm', fill='white', blur=10, op=150, spacing=6, align='center'):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.multiline_text(xy, text, font=fnt, fill=(0, 0, 0, op), anchor=anchor, spacing=spacing, align=align)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh)
    ImageDraw.Draw(base).multiline_text(xy, text, font=fnt, fill=fill, anchor=anchor, spacing=spacing, align=align)

def wrap(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return '\n'.join(lines)

def lesson(vid, box, patches, n, text, name, cy=0.42):
    cy = CY.get(n, cy)
    im = prep(vid, box, patches).convert('RGBA')
    num = font('FreeSerif', 150)
    body = font('Inter:bold', 44)
    y = int(H * cy)
    shadow_text(im, (W // 2, y), f'{n}.', num, anchor='ms', blur=14, op=120)
    shadow_text(im, (W // 2, y + 30), wrap(text, body, 820), body, anchor='ma', blur=12, op=170, spacing=4)
    small = font('Inter:semibold', 26)
    shadow_text(im, (W // 2, H - 70), name, small, anchor='ms', blur=8, op=170)
    return im.convert('RGB')

slides = []
CY = {3: 0.60, 4: 0.60}
# Cover
im = prep('snLmCv__04Q', (80, 0, 620, 675), [(20, 20, 230, 150)]).convert('RGBA')
grad = Image.new('L', (1, H)); [grad.putpixel((0, y), int(110 * max(0, 1 - y / (H * 0.6)))) for y in range(H)]
im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 0)] * 3 + [grad.resize((W, H))]))
big = font('Inter Display:black', 330); mid = font('Inter Display:extrabold', 150); thin = font('Inter Display:light', 64); big2 = font('Inter Display:black', 140)
shadow_text(im, (-28, 360), 'cinq', big, anchor='ls', blur=16, op=110)
shadow_text(im, (150, 500), 'leçons', mid, anchor='ls', blur=12, op=110)
shadow_text(im, (155, 590), "d'endurance réalistes", thin, anchor='ls', blur=10, op=150)
shadow_text(im, (66, 1040), 'tirées de', thin, anchor='ls', blur=10, op=150)
shadow_text(im, (60, 1180), '36 épisodes', big2, anchor='ls', blur=14, op=110)
shadow_text(im, (66, 1250), '(que la plupart des coureurs ignorent)', font('Inter Display:medium', 36), anchor='ls', blur=8, op=170)
slides.append(im.convert('RGB'))

L = [
 ('snLmCv__04Q', None, None, 1, "Personne ne commence par l'ultra. On monte une marche, puis la suivante. Ton prochain objectif doit te faire un peu peur, pas te terrifier.", 'Alvin Alexandre · Ép. 34'),
 ('Ck4ki_VoahQ', (704, 0, 1280, 720), [(950, 15, 1280, 200)], 2, "Tenter un truc immense et ne pas le finir, ce n'est pas un échec. C'est ce qui te rend capable de tout le reste.", 'Fabien Leroux · Traverser l’Atlantique à la nage'),
 ('HGiAxVZLmOM', (60, 190, 484, 720), [], 3, "L'endurance ne récompense pas les plus forts à 25 ans. Elle récompense ceux qui sont encore là à 45.", 'Ludovic Pommeret · Ép. 22'),
 ('y4b_PniAoAY', (0, 190, 424, 720), [(380, 160, 440, 350)], 4, "Un vrai boulot n'empêche pas d'aller loin. Ta vie n'est pas un frein : c'est le cadre de ton entraînement.", 'Chloé Herbiet · De sage-femme à championne'),
 ('biaEUki94-g', (100, 0, 676, 720), [], 5, "Les pionniers n'attendaient pas d'être prêts. Toi non plus : la meilleure course est celle à laquelle tu t'inscris.", 'Dawa Sherpa · Ép. 35'),
]
# lesson 1 reuses Alvin with a different (tighter) crop than the cover
L[0] = ('snLmCv__04Q', (190, 60, 640, 622), [], *L[0][3:])
for vid, box, patches, n, text, name in L:
    slides.append(lesson(vid, box, patches, n, text, name))

# CTA
im = prep('wtGT7vQqZVQ', (0, 0, 576, 720)).convert('RGBA')
shadow_text(im, (W // 2, int(H * 0.60)), '36 épisodes.\n36 histoires d’endurance.', font('Inter Display:black', 74), anchor='mm', blur=14, op=160, spacing=10)
shadow_text(im, (W // 2, int(H * 0.60) + 150), 'Écoute Silex Podcast\nlien en bio', font('Inter:bold', 42), anchor='ma', blur=10, op=170, spacing=8)
slides.append(im.convert('RGB'))

os.makedirs(OUT, exist_ok=True)
for i, s in enumerate(slides):
    s.save(os.path.join(OUT, f'slide_{i+1:02d}.jpg'), quality=93)
prev = Image.new('RGB', (360 * 4, 450 * 2), 'white')
for i, s in enumerate(slides):
    prev.paste(s.resize((360, 450)), ((i % 4) * 360, (i // 4) * 450))
prev.save(os.path.join(OUT, '..', 'preview.jpg'))
print('done', len(slides))
