"""Brand Match, refined: Cool Man stops at the barber panel, the corner square carries the
Quick Fix repair logo, and the tech fascia uses product photos from the Quick Fix flyer.

usage: python3 signs_final.py <out_dir> <street_photo.jpg> <logo_dir>
"""
from signlib import *

OUT, PHOTO, LOGOS = sys.argv[1:4]
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
    logo = scale_h(CM, 470); paste_c(s, logo, (SPLIT/2, LH/2))
    f = font(INTER_B, 38); side = (SPLIT - logo.width)/4
    for x, lines in ((side, ["FADES", "BEARDS", "SHAVES"]), (SPLIT-side, ["WALK-INS", "WELCOME", "MON–SAT"])):
        for i, t in enumerate(lines): s.alpha_composite(silver_text(s.size, t, f, (x, 220+i*80)))
        for y in (172, 430): d.line([(x-95, y), (x+95, y)], fill=(150, 30, 40), width=4)
    # corner: repair logo
    cw = LW - SPLIT; cx = SPLIT + cw/2
    paste_c(s, scale_fit(QF_ICON, cw-120, 390), (cx, 245))
    lay = Image.new("RGBA", s.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    fq = fit("QUICK FIX", INTER_BL, cw-90, 76)
    wq = ld.textlength("QUICK ", font=fq); wf = ld.textlength("FIX", font=fq); x = cx-(wq+wf)/2
    ld.text((x, 530), "QUICK ", font=fq, fill=(14, 16, 22), anchor="ls"); ld.text((x+wq, 530), "FIX", font=fq, fill=QBLUE, anchor="ls")
    s.alpha_composite(lay)
    pole_stripes(s, (SPLIT-14, 0, SPLIT+14, LH), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=20, angle=.6)
    return s

def right_face():
    t = white(RW, RH)
    ImageDraw.Draw(t).rectangle((0, RH-18, RW, RH), fill=QBLUE)
    # logo block: logo, services, accessories photo strip
    lg = scale_h(QF, 250); t.alpha_composite(lg, (60, 36))
    sf = fit(SERVICES, INTER_B, lg.width-40, 44)
    t.alpha_composite(text_layer(t.size, SERVICES, sf, (60+lg.width/2, 322), (30, 34, 44, 255)))
    acc = scale_h(ACCESSORIES, 200); multiply_in(t, acc, (int(60+lg.width/2-acc.width/2), 362))
    # hero products
    pr = scale_h(PRODUCTS, 540); px = 60+lg.width+50
    multiply_in(t, pr, (px, 22))
    # same-day badge
    bd = scale_fit(BADGE, RW-(px+pr.width)-40, 420)
    t.alpha_composite(bd, (RW-bd.width-20, int((RH-bd.height)/2)))
    return t

photo = Image.open(PHOTO).convert("RGB")
lf, rf = left_face(), right_face()
img = place(photo, lf, LEFT_Q, light=1.0, warm=(1.03, 1.0, .96), texture=0.03)
img = place(img.convert("RGB"), rf, RIGHT_Q, light=.86, warm=(.95, .97, 1.03), texture=0.015)
img = label(img.convert("RGB").crop(CROP), "Brand Match — Cool Man panel, repair logo on the corner, product photos on Quick Fix")
img.save(os.path.join(OUT, "final-brand-match-products.jpg"), quality=92)
flat = Image.new("RGB", (RW, LH+RH+60), (240, 240, 240))
flat.paste(lf.convert("RGB"), (0, 0)); flat.paste(rf.convert("RGB"), (0, LH+60))
flat.save(os.path.join(OUT, "final-brand-match-products-flat-artwork.png"))
print("split", SPLIT)
