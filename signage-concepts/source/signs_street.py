"""Brand Match, refined: Cool Man stops at the barber panel, the corner square carries the
Quick Fix repair logo, and the tech fascia uses product photos from the Quick Fix flyer.

usage: python3 signs_street.py <out_dir> <street_photo.jpg> <logo_dir> <quick-fix-flyer.jpg>
"""
from signlib import *
import qfparts as qp

OUT, PHOTO, LOGOS = sys.argv[1:4]
FLYER_SRC = sys.argv[4]                 # original Quick Fix flyer (for the icon row)
os.makedirs(OUT, exist_ok=True)
CROP = (0, 105, 2112, 1030)

LW, LH = 2600, 600            # left face: barber | repair logo (corner square)
RW, RH = 3400, 600            # right face: tech
CORNER_PX = 834               # photo x where the barber inset panel ends and the corner square begins
QBLUE = (26, 110, 232)
SERVICES = "PHONES · LAPTOPS · PS5 · XBOX · SPEAKERS · ACCESSORIES"

def L(n): return Image.open(os.path.join(LOGOS, n))
CM, QF, BADGE = L("cool-man-logo-silver.png"), L("quick-fix-tech-logo.png"), L("quick-fix-same-day-badge.png")
QF_ICON = QF.crop((0, 0, 192, QF.height))

flyer = Image.open(os.path.join(LOGOS, "quick-fix-tech-flyer-no-tv.jpg")).convert("RGB")
PRODUCTS = flyer.crop((752, 252, 1598, 604))
ImageDraw.Draw(PRODUCTS).rectangle((0, 572-252, 935-752, 604-252), fill=(255, 255, 255))   # icon-row bits
ACCESSORIES = flyer.crop((374, 718, 1238, 882))

def clean_white(im, fade=36):
    """Lift the flyer's off-white backdrop to pure white and fade the crop edges, so no box shows after multiply."""
    a = np.array(im).astype(np.float32)
    a = np.clip(a*255/236, 0, 255)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, w-1-xx, yy, h-1-yy]).astype(np.float32)
    k = np.clip(edge/fade, 0, 1)[..., None]
    a = a*k + 255*(1-k)
    return Image.fromarray(a.astype(np.uint8))
PRODUCTS, ACCESSORIES = clean_white(PRODUCTS), clean_white(ACCESSORIES, 18)

# service icons from the flyer's icon row (labels and the TV icon left out)
_orig = np.array(Image.open(FLYER_SRC).convert("RGB")).astype(np.float32)
ICON_X = [(60, 101), (330, 371), (442, 520), (579, 656), (717, 779), (838, 926), (1005, 1067)]  # phone, speaker, laptop, PS5, Xbox, controller, radio
def icon(x0, x1, y0=561, y1=636):
    c = _orig[y0:y1, x0-4:x1+4]
    al = np.clip((c[..., 2] - c[..., 0] - 40) / 80, 0, 1)
    out = np.zeros(c.shape[:2] + (4,), np.uint8); out[..., :3] = QBLUE; out[..., 3] = (al*255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")
ICONS = [icon(x0, x1, 566 if x0 == 838 else 561) for x0, x1 in ICON_X]

def scale_h(im, h): return im.resize((round(im.width*h/im.height), h), Image.LANCZOS)
def scale_fit(im, w, h):
    k = min(w/im.width, h/im.height); return im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)

def brushed(w, h, base=(16, 16, 18)):
    rng = np.random.default_rng(7)
    streak = rng.normal(0, 4, (1, w)).repeat(h, 0) + rng.normal(0, 2, (h, w))
    a = np.clip(np.array(base)[None, None, :] + streak[..., None], 0, 255).astype(np.uint8)
    return ImageChops.multiply(Image.fromarray(a, "RGB").convert("RGBA"), vgrad(w, h, (255, 255, 255), (170, 170, 170)))

def white(w, h): return noise(vgrad(w, h, (252, 253, 255), (240, 243, 248)), 2)

def silver_text(size, s, f, center, tracking=8):
    t = text_layer(size, s, f, center, (255, 255, 255, 255), tracking)
    g = vgrad(size[0], size[1], (236, 238, 242), (150, 154, 162)); g.putalpha(t.split()[3]); return g

def multiply_in(img, photo, xy):
    """Drop a white-background product photo onto a light panel: multiply makes its white vanish."""
    x, y = xy; box = (x, y, x+photo.width, y+photo.height)
    region = img.crop(box).convert("RGB")
    img.paste(ImageChops.multiply(region, photo.convert("RGB")).convert("RGBA"), box[:2])

def flat_x_for_photo_x(px, quad, w, h):
    c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], quad)
    fx = lambda u: (c[0]*u + c[1]*h/2 + c[2]) / (c[6]*u + c[7]*h/2 + 1)
    lo, hi = 0, w
    for _ in range(40):
        m = (lo+hi)/2
        if fx(m) < px: lo = m
        else: hi = m
    return int(lo)

SPLIT = flat_x_for_photo_x(CORNER_PX, LEFT_Q, LW, LH)

def left_face():
    s = Image.new("RGBA", (LW, LH))
    s.paste(brushed(SPLIT, LH), (0, 0)); s.paste(white(LW-SPLIT, LH), (SPLIT, 0))
    d = ImageDraw.Draw(s)
    for y in (24, LH-28): d.line([(0, y), (SPLIT, y)], fill=(170, 172, 178), width=5)
    d.rectangle((SPLIT, LH-18, LW, LH), fill=QBLUE)
    # barber
    # Cool Man logo without the bottom "EST. 2019" row and its gold lines; no side text
    cm = CM.crop((0, 0, CM.width, 344)); cm = cm.crop(cm.getbbox())
    logo = scale_fit(cm, SPLIT - 260, 500); paste_c(s, logo, (SPLIT/2, LH/2))
    # corner slot: small repair logo only
    cw = LW - SPLIT; cx = SPLIT + cw/2
    paste_c(s, scale_fit(QF_ICON, cw*0.62, LH*0.62), (cx, LH/2 - 6))
    pole_stripes(s, (SPLIT-14, 0, SPLIT+14, LH), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=20, angle=.6)
    return s

def right_face():
    """The compact Quick Fix sign re-laid for the long, shallow fascia."""
    P = qp.Parts(LOGOS, FLYER_SRC)
    t = white(RW, RH); d = ImageDraw.Draw(t)
    P.brand(t, (40, 26, 1180, 216))
    fh = qp.mont_fit(["WE REPAIR CELL PHONES"], 1120, 64, 900, 0)
    cap = fh.getbbox("H")[3] - fh.getbbox("H")[1]; x = 48
    for word, col in (("WE REPAIR ", qp.INK), ("CELL PHONES", QBLUE)):
        d.text((x, 262 + cap), word, font=fh, fill=col, anchor="ls"); x += d.textlength(word, font=fh)
    d.line([(40, 362), (1180, 362)], fill=QBLUE, width=4)
    P.icon_row(t, (40, 378, 1180, 566), labels=False, icon_h=130)
    pr = qp.scale_fit(P.products, 1120, 560); qp.multiply_in(t, pr, (1210 + (1120 - pr.width)//2, 575 - pr.height))
    P.same_day(t, (2370, 26, 3370, 262), sub=True)
    P.accessories(t, (2370, 290, 3370, 572), head_h=78, cols=2)
    d.rectangle((0, RH-14, RW, RH), fill=QBLUE)
    return t

photo = Image.open(PHOTO).convert("RGB")
lf, rf = left_face(), right_face()
img = place(photo, lf, LEFT_Q, light=1.0, warm=(1.03, 1.0, .96), texture=0.03)
img = place(img.convert("RGB"), rf, RIGHT_Q, light=.86, warm=(.95, .97, 1.03), texture=0.015)
img = label(img.convert("RGB").crop(CROP), "Brand Match — black Cool Man, repair logo in the corner slot, new Quick Fix Tech sign")
img.save(os.path.join(OUT, "street-brand-match-compact.jpg"), quality=92)
flat = Image.new("RGB", (RW, LH+RH+60), (240, 240, 240))
flat.paste(lf.convert("RGB"), (0, 0)); flat.paste(rf.convert("RGB"), (0, LH+60))
flat.save(os.path.join(OUT, "street-brand-match-compact-flat-artwork.png"))
print("split", SPLIT)
