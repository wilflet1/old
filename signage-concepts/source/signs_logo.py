"""Corner signage built from the real Cool Man + Quick Fix Tech logos.

usage: python3 signs_logo.py <out_dir> <street_photo.jpg> <logo_dir>
"""
from signlib import *

OUT, PHOTO, LOGOS = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
CROP = (0, 105, 2112, 1030)

CM = Image.open(os.path.join(LOGOS, "cool-man-logo-silver.png"))
QF = Image.open(os.path.join(LOGOS, "quick-fix-tech-logo.png"))
QF_W = Image.open(os.path.join(LOGOS, "quick-fix-tech-logo-white.png"))
BADGE = Image.open(os.path.join(LOGOS, "quick-fix-same-day-badge.png"))
SERVICES = "PHONES  ·  LAPTOPS  ·  PS5  ·  XBOX  ·  SPEAKERS  ·  ACCESSORIES"
QBLUE = (26, 110, 232)

def scale_h(im, h):
    return im.resize((round(im.width*h/im.height), h), Image.LANCZOS)

def all_white(im):
    a = np.array(im).copy(); a[..., :3] = 255; return Image.fromarray(a, "RGBA")

def brushed(w, h, base=(16, 16, 18)):
    rng = np.random.default_rng(7)
    streak = rng.normal(0, 4, (1, w)).repeat(h, 0) + rng.normal(0, 2, (h, w))
    a = np.clip(np.array(base)[None, None, :] + streak[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB").convert("RGBA")
    shade = vgrad(w, h, (255, 255, 255), (170, 170, 170))
    return ImageChops.multiply(im, shade)

def silver_text(size, s, f, center, tracking=6):
    t = text_layer(size, s, f, center, (255, 255, 255, 255), tracking)
    g = vgrad(size[0], size[1], (236, 238, 242), (150, 154, 162)); g.putalpha(t.split()[3]); return g

def barber_face(stripes):
    b = brushed(LW, LH)
    if stripes:
        pole_stripes(b, (0, 0, LW, 34), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=34)
        pole_stripes(b, (0, LH-34, LW, LH), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=34)
    else:
        d = ImageDraw.Draw(b)
        for y in (26, LH-30): d.line([(0, y), (LW, y)], fill=(170, 172, 178), width=5)
    logo = scale_h(CM, 500); paste_c(b, logo, (LW/2, LH/2))
    f = font(INTER_B, 44)
    for x, lines in ((250, ["FADES", "BEARDS", "SHAVES"]), (LW-250, ["WALK-INS", "WELCOME", "MON–SAT"])):
        for i, s in enumerate(lines):
            b.alpha_composite(silver_text(b.size, s, f, (x, 210+i*90), tracking=10))
        ImageDraw.Draw(b).line([(x-110, 165), (x+110, 165)], fill=(150, 30, 40), width=4)
        ImageDraw.Draw(b).line([(x-110, 435), (x+110, 435)], fill=(150, 30, 40), width=4)
    return b

def tech_white():
    t = noise(vgrad(RW, RH, (252, 253, 255), (236, 240, 246)), 3)
    lg = scale_h(QF, 360); t.alpha_composite(lg, (70, 40))
    t.alpha_composite(text_layer(t.size, SERVICES, fit(SERVICES, INTER_B, lg.width-120, 60), (70+lg.width/2, 500), (30, 34, 44, 255)))
    bd = scale_h(BADGE, 520); t.alpha_composite(bd, (RW-bd.width-10, 40))
    ImageDraw.Draw(t).rectangle((0, RH-18, RW, RH), fill=QBLUE)
    return t

def tech_dark():
    t = brushed(RW, RH, (14, 18, 26))
    circuit(t, (40, 130, 255), n=22, alpha=40)
    lg = scale_h(QF_W, 360); t.alpha_composite(lg, (70, 40))
    t.alpha_composite(text_layer(t.size, SERVICES, fit(SERVICES, INTER_B, lg.width-120, 60), (70+lg.width/2, 500), (200, 210, 225, 255)))
    bd = scale_h(BADGE, 520); t.alpha_composite(bd, (RW-bd.width-10, 40))
    d = ImageDraw.Draw(t)
    for y in (26, RH-30): d.line([(0, y), (RW, y)], fill=QBLUE, width=5)
    return t

def tech_blue():
    t = noise(vgrad(RW, RH, (34, 120, 240), (18, 92, 214)), 3)
    lg = scale_h(all_white(QF), 360); t.alpha_composite(lg, (70, 40))
    t.alpha_composite(text_layer(t.size, SERVICES, fit(SERVICES, INTER_B, lg.width-120, 60), (70+lg.width/2, 500), (255, 255, 255, 235)))
    d = ImageDraw.Draw(t)
    x0 = 2060; d.line([(x0-40, 70), (x0-40, RH-70)], fill=(255, 255, 255, 120), width=4)
    t.alpha_composite(text_layer(t.size, "SAME DAY", font(INTER_BL, 120), (x0+350, 180), (255, 255, 255, 255)))
    t.alpha_composite(text_layer(t.size, "REPAIRS", font(INTER_BL, 120), (x0+350, 315), (255, 255, 255, 255)))
    t.alpha_composite(text_layer(t.size, "IN TODAY · BACK TODAY", font(INTER_B, 44), (x0+350, 440), (190, 220, 255, 255), tracking=4))
    return t

CONCEPTS = [
    ("brand-match", "Brand Match — chrome Cool Man on black, Quick Fix Tech on its own white", lambda: (barber_face(False), tech_white())),
    ("after-dark", "After Dark — both shops on black, chrome barber + white/blue tech", lambda: (barber_face(False), tech_dark())),
    ("pole-and-blue", "Pole & Blue — barber-pole trims, solid Quick Fix blue tech fascia", lambda: (barber_face(True), tech_blue())),
]

photo = Image.open(PHOTO).convert("RGB")
paths = []
for i, (slug, title, make) in enumerate(CONCEPTS, 1):
    bf, tf = make()
    img = place(photo, bf, LEFT_Q, light=1.0, warm=(1.03, 1.0, .96))
    img = place(img.convert("RGB"), tf, RIGHT_Q, light=.82, warm=(.94, .97, 1.04))
    img = label(img.convert("RGB").crop(CROP), title)
    p = os.path.join(OUT, f"logo-concept-{i}-{slug}.jpg"); img.save(p, quality=90); paths.append(p)
    flat = Image.new("RGB", (RW, LH+RH+60), (240, 240, 240))
    flat.paste(bf.convert("RGB"), (0, 0)); flat.paste(tf.convert("RGB"), (0, LH+60))
    flat.save(os.path.join(OUT, f"logo-concept-{i}-{slug}-flat-artwork.png"))
    print(p)
