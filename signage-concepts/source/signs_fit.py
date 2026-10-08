"""Final shopfront: each sign fitted inside its own border on 2 Gabriel Rd.

  barber inset panel (red)  -> black Cool Man, logo only
  corner square (blue)      -> Quick Fix repair mark
  right-hand fascia         -> Quick Fix Tech sign, content kept clear of the lamp pole

Renders the whole street-view capture, uncropped and unlabelled.

usage: python3 signs_fit.py <out_dir> <street_photo.jpg> <logo_dir> <quick-fix-flyer.jpg>
"""
from signlib import *
import qfparts as qp

OUT, PHOTO, LOGOS, FLYER_SRC = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)

RED_Q   = [(308, 350), (818, 290), (820, 484), (310, 505)]     # inside the barber panel's raised frame
BLUE_Q  = [(848, 290), (1010, 279), (1010, 472), (848, 476)]    # inside the corner square's frame
RIGHT_Q = [(1028, 264), (1820, 382), (1820, 547), (1028, 489)]  # right-hand fascia, corner to next shop
POLE_X  = (1727, 1771)
RED_WH, BLUE_WH, RIGHT_WH = (1920, 600), (600, 640), (3300, 600)
QBLUE = qp.QBLUE

CM = Image.open(os.path.join(LOGOS, "cool-man-logo-silver.png"))
CM = CM.crop((0, 0, CM.width, 344)); CM = CM.crop(CM.getbbox())          # no bottom "EST. 2019" row
P = qp.Parts(LOGOS, FLYER_SRC)

def brushed(w, h, base=(16, 16, 18)):
    rng = np.random.default_rng(7)
    streak = rng.normal(0, 4, (1, w)).repeat(h, 0) + rng.normal(0, 2, (h, w))
    a = np.clip(np.array(base)[None, None, :] + streak[..., None], 0, 255).astype(np.uint8)
    return ImageChops.multiply(Image.fromarray(a, "RGB").convert("RGBA"), vgrad(w, h, (255, 255, 255), (170, 170, 170)))

def white(w, h): return noise(vgrad(w, h, (252, 253, 255), (240, 243, 248)), 2)

def flat_x(px, quad, w, h):
    c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], quad)
    fx = lambda u: (c[0]*u + c[1]*h/2 + c[2]) / (c[6]*u + c[7]*h/2 + 1)
    lo, hi = 0, w
    for _ in range(40):
        m = (lo+hi)/2
        if fx(m) < px: lo = m
        else: hi = m
    return int(lo)

def barber():
    w, h = RED_WH; b = brushed(w, h)
    d = ImageDraw.Draw(b)
    for y in (22, h-26): d.line([(0, y), (w, y)], fill=(170, 172, 178), width=5)
    paste_c(b, qp.scale_fit(CM, w - 220, h - 110), (w/2, h/2))
    return b

def corner():
    """Small corner sign: repair mark, brand name, Same Day band."""
    w, h = BLUE_WH; t = white(w, h); d = ImageDraw.Draw(t)
    band_top = h - 150
    # one-line lockup: smaller mark, brand name as wide as the panel allows (slightly tightened)
    track = -0.025
    def line_w(f): return sum(d.textlength(ch, font=f) for ch in "QUICK FIX TECH") + track*f.size*13
    lo, hi = 10, 200
    while lo < hi:
        m = (lo+hi+1)//2
        if line_w(qp.mont(m, 900)) <= w - 34: lo = m
        else: hi = m-1
    f = qp.mont(lo, 900); cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    tw = line_w(f); x = (w - tw)/2
    rule_gap, rule_h = 14, 10
    mk_h = 230; gap = 30
    block = mk_h + gap + cap + rule_gap + rule_h
    top = (band_top - block)/2
    mk = qp.scale_fit(P.mark, w*0.6, mk_h); paste_c(t, mk, (w/2, top + mk_h/2))
    base = top + mk_h + gap + cap; x0 = x
    for word, col in (("QUICK ", qp.INK), ("FIX ", QBLUE), ("TECH", qp.INK)):
        for ch in word:
            d.text((x, base), ch, font=f, fill=col, anchor="ls"); x += d.textlength(ch, font=f) + track*f.size
    d.rounded_rectangle((x0 + 2, base + rule_gap, x0 + tw, base + rule_gap + rule_h), radius=5, fill=QBLUE)
    # same-day band
    d.rectangle((0, band_top, w, h), fill=QBLUE)
    fs = qp.mont_fit(["SAME DAY", "REPAIRS"], w - 90, 104, 900, 0.3)
    qp.text_block(d, ["SAME DAY", "REPAIRS"], fs, 0, band_top + (150 - qp.block_h(fs, 2, 0.3))/2, qp.WHITE, gap=0.3, align="c", width=w)
    return t

def tech():
    w, h = RIGHT_WH; t = white(w, h); d = ImageDraw.Draw(t)
    cw = flat_x(POLE_X[0] - 6, RIGHT_Q, w, h)            # usable width before the pole
    a1 = int(cw*0.355); b1 = int(cw*0.68); m = 34
    # zone A: brand, headline, icons
    P.brand(t, (m, 26, a1 - 10, 200))
    fh = qp.mont_fit(["WE REPAIR CELL PHONES"], a1 - m - 20, 58, 900, 0)
    cap = fh.getbbox("H")[3] - fh.getbbox("H")[1]; x = m + 6
    for word, col in (("WE REPAIR ", qp.INK), ("CELL PHONES", QBLUE)):
        d.text((x, 248 + cap), word, font=fh, fill=col, anchor="ls"); x += d.textlength(word, font=fh)
    d.line([(m, 342), (a1 - 10, 342)], fill=QBLUE, width=4)
    P.icon_row(t, (m, 356, a1 - 10, 566), labels=False, icon_h=124)
    # zone B: products
    pr = qp.scale_fit(P.products, b1 - a1 - 20, 560)
    qp.multiply_in(t, pr, (a1 + (b1 - a1 - pr.width)//2, 575 - pr.height))
    # zone C: same day + accessories
    P.same_day(t, (b1 + 10, 26, cw - 10, 258))
    P.accessories(t, (b1 + 10, 284, cw - 10, 572), head_h=76, cols=2)
    d.rectangle((0, h-14, w, h), fill=QBLUE)
    return t

def restore_pole(img, photo):
    msk = Image.new("L", photo.size, 0)
    ImageDraw.Draw(msk).rectangle((POLE_X[0], 200, POLE_X[1], 640), fill=255)
    out = img.convert("RGB"); out.paste(photo, (0, 0), msk.filter(ImageFilter.GaussianBlur(1.2))); return out

photo = Image.open(PHOTO).convert("RGB")
rb, cb, tb = barber(), corner(), tech()
img = place(photo, rb, RED_Q, light=1.0, warm=(1.03, 1.0, .96), texture=0.03)
img = place(img.convert("RGB"), cb, BLUE_Q, light=.97, warm=(1.03, 1.0, .96), texture=0.03)
img = place(img.convert("RGB"), tb, RIGHT_Q, light=.86, warm=(.95, .97, 1.03), texture=0.015)
img = restore_pole(img, photo)
img.save(os.path.join(OUT, "shopfront-final-full.jpg"), quality=93)

flat = Image.new("RGB", (RIGHT_WH[0], RED_WH[1] + RIGHT_WH[1] + 120), (240, 240, 240))
flat.paste(rb.convert("RGB"), (0, 0)); flat.paste(cb.convert("RGB"), (RED_WH[0] + 60, 0))
flat.paste(tb.convert("RGB"), (0, RED_WH[1] + 80))
flat.save(os.path.join(OUT, "shopfront-final-flat-artwork.png"))
print("ok")
