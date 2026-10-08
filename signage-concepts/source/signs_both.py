"""Variations with both shops on both faces of the corner.

usage: python3 signs_both.py <out_dir> <street_photo.jpg> <logo_dir> <quick-fix-flyer.jpg>
"""
from signlib import *
import qfparts as qp

OUT, PHOTO, LOGOS, FLYER_SRC = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)

RED_Q   = [(308, 350), (818, 290), (820, 484), (310, 505)]
BLUE_Q  = [(848, 290), (1010, 279), (1010, 472), (848, 476)]
RIGHT_Q = [(1028, 264), (1820, 382), (1820, 547), (1028, 489)]
POLE_X  = (1727, 1771)
RED_WH, BLUE_WH, RIGHT_WH = (1920, 600), (600, 640), (3300, 600)
QBLUE, INK = qp.QBLUE, qp.INK

CM = Image.open(os.path.join(LOGOS, "cool-man-logo-silver.png"))
CM = CM.crop((0, 0, CM.width, 344)); CM = CM.crop(CM.getbbox())
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

# ---------- section renderers (each returns an RGBA panel w x h) ----------
def cool_man(w, h):
    b = brushed(w, h); d = ImageDraw.Draw(b)
    for y in (22, h-26): d.line([(0, y), (w, y)], fill=(170, 172, 178), width=5)
    paste_c(b, qp.scale_fit(CM, w - min(220, w*0.12), h - 110), (w/2, h/2))
    return b

def qf_badge(w, h):
    """Compact Quick Fix sign: mark, one-line name, Same Day band (the corner-square design)."""
    t = white(w, h); d = ImageDraw.Draw(t)
    band = int(h*0.234); band_top = h - band
    track = -0.025
    lw = lambda f: sum(d.textlength(ch, font=f) for ch in "QUICK FIX TECH") + track*f.size*13
    lo, hi = 10, 400
    while lo < hi:
        m = (lo+hi+1)//2
        if lw(qp.mont(m, 900)) <= w - 34 and m <= h*0.16: lo = m
        else: hi = m-1
    f = qp.mont(lo, 900); cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    base = band_top - 30; x = (w - lw(f))/2
    mk_top, mk_bot = 20, base - cap - 26
    paste_c(t, qp.scale_fit(P.mark, w*0.8, mk_bot - mk_top), (w/2, (mk_top + mk_bot)/2))
    for word, col in (("QUICK ", INK), ("FIX ", QBLUE), ("TECH", INK)):
        for ch in word:
            d.text((x, base), ch, font=f, fill=col, anchor="ls"); x += d.textlength(ch, font=f) + track*f.size
    d.rectangle((0, band_top, w, h), fill=QBLUE)
    fs = qp.mont_fit(["SAME DAY", "REPAIRS"], w - 90, band*0.7, 900, 0.3)
    qp.text_block(d, ["SAME DAY", "REPAIRS"], fs, 0, band_top + (band - qp.block_h(fs, 2, 0.3))/2, qp.WHITE, gap=0.3, align="c", width=w)
    return t

def qf_wide(w, h):
    """Quick Fix fascia section; full layout when wide, a two-row layout when narrower."""
    t = white(w, h); d = ImageDraw.Draw(t); m = 34
    if w >= 2500:
        a1 = int(w*0.36); b1 = int(w*0.69)
        P.brand(t, (m, 26, a1 - 10, 200))
        fh = qp.mont_fit(["WE REPAIR CELL PHONES"], a1 - m - 20, 58, 900, 0)
        cap = fh.getbbox("H")[3] - fh.getbbox("H")[1]; x = m + 6
        for word, col in (("WE REPAIR ", INK), ("CELL PHONES", QBLUE)):
            d.text((x, 248 + cap), word, font=fh, fill=col, anchor="ls"); x += d.textlength(word, font=fh)
        d.line([(m, 342), (a1 - 10, 342)], fill=QBLUE, width=4)
        P.icon_row(t, (m, 356, a1 - 10, 566), labels=False, icon_h=124)
        pr = qp.scale_fit(P.products, b1 - a1 - 20, 560)
        qp.multiply_in(t, pr, (a1 + (b1 - a1 - pr.width)//2, 575 - pr.height))
        P.same_day(t, (b1 + 10, 26, w - 20, 258))
        P.accessories(t, (b1 + 10, 284, w - 20, 572), head_h=76, cols=2)
        return t
    # narrow: brand + Same Day on top, icons + products below
    split = int(w*0.6)
    P.brand(t, (m, 30, split - 20, 220))
    P.same_day(t, (split + 10, 30, w - 30, 220))
    d.line([(m, 250), (w - 30, 250)], fill=QBLUE, width=4)
    P.icon_row(t, (m, 268, split - 20, 570), labels=False, icon_h=int(min(130, (split - m)/6*0.7)))
    pr = qp.scale_fit(P.products, w - split - 40, 310)
    qp.multiply_in(t, pr, (split + 10 + (w - split - 40 - pr.width)//2, 575 - pr.height))
    return t

def strip(t, x0, x1):
    ImageDraw.Draw(t).rectangle((x0, t.height - 14, x1, t.height), fill=QBLUE)

def compose(w, h, segments, usable=None):
    """segments: [(kind, fraction)] across the usable width; anything past it continues the last background."""
    usable = usable or w
    out = Image.new("RGBA", (w, h)); x = 0
    for i, (kind, frac) in enumerate(segments):
        sw = int(round(usable*frac)) if i < len(segments) - 1 else usable - x
        if kind == "cm": seg = cool_man(sw, h)
        elif kind == "qf": seg = qf_wide(sw, h); strip(seg, 0, sw)
        else: seg = qf_badge(sw, h)
        out.paste(seg, (x, 0)); x += sw
    if usable < w:
        last = segments[-1][0]
        tail = brushed(w - usable, h) if last == "cm" else white(w - usable, h)
        if last == "cm":
            d = ImageDraw.Draw(tail)
            for y in (22, h-26): d.line([(0, y), (tail.width, y)], fill=(170, 172, 178), width=5)
        else: strip(tail, 0, tail.width)
        out.paste(tail, (usable, 0))
    return out

def restore_pole(img, photo):
    msk = Image.new("L", photo.size, 0)
    ImageDraw.Draw(msk).rectangle((POLE_X[0], 200, POLE_X[1], 640), fill=255)
    out = img.convert("RGB"); out.paste(photo, (0, 0), msk.filter(ImageFilter.GaussianBlur(1.2))); return out

CW = flat_x(POLE_X[0] - 6, RIGHT_Q, *RIGHT_WH)
VARIANTS = [
    ("barber-at-corner", "Barber at the corner — Cool Man wraps round, then Quick Fix",
     [("cm", 1.0)], [("cm", 0.30), ("qf", 0.70)]),
    ("tech-at-corner", "Tech at the corner — Quick Fix wraps round, Cool Man at the far end",
     [("cm", 1.0)], [("qf", 0.70), ("cm", 0.30)]),
    ("half-and-half", "Half and half — right fascia split evenly",
     [("cm", 1.0)], [("cm", 0.5), ("qf", 0.5)]),
    ("alternating", "Alternating — Quick Fix, Cool Man, corner, Quick Fix, Cool Man",
     [("badge", 0.34), ("cm", 0.66)], [("qf", 0.64), ("cm", 0.36)]),
]

photo = Image.open(PHOTO).convert("RGB")
corner = qf_badge(*BLUE_WH)
paths = []
for i, (slug, title, left_segs, right_segs) in enumerate(VARIANTS, 1):
    lf = compose(*RED_WH, left_segs)
    rf = compose(*RIGHT_WH, right_segs, usable=CW)
    img = place(photo, lf, RED_Q, light=1.0, warm=(1.03, 1.0, .96), texture=0.03)
    img = place(img.convert("RGB"), corner, BLUE_Q, light=.97, warm=(1.03, 1.0, .96), texture=0.03)
    img = place(img.convert("RGB"), rf, RIGHT_Q, light=.86, warm=(.95, .97, 1.03), texture=0.015)
    img = restore_pole(img, photo)
    p = os.path.join(OUT, f"both-{i}-{slug}.jpg"); img.save(p, quality=92); paths.append((p, title))
    flat = Image.new("RGB", (RIGHT_WH[0], RED_WH[1] + RIGHT_WH[1] + 120), (240, 240, 240))
    flat.paste(lf.convert("RGB"), (0, 0)); flat.paste(corner.convert("RGB"), (RED_WH[0] + 60, 0))
    flat.paste(rf.convert("RGB"), (0, RED_WH[1] + 80))
    flat.save(os.path.join(OUT, f"both-{i}-{slug}-flat-artwork.png"))
    print(p)

tiles = [Image.open(p).crop((260, 230, 1880, 560)).resize((1100, 224)) for p, _ in paths]
sheet = Image.new("RGB", (2*1100+30, 2*(224+60)+10), (18, 18, 20)); d = ImageDraw.Draw(sheet); f = font(INTER_B, 32)
for k, (t, (_, title)) in enumerate(zip(tiles, paths)):
    x = 10 + (k % 2)*1110; y = 10 + (k//2)*(224+60)
    sheet.paste(t, (x, y)); d.text((x+6, y+232), f"{k+1}. {title.split(' — ')[0]}", font=f, fill=(240, 240, 240))
sheet.save(os.path.join(OUT, "both-sides-overview.jpg"), quality=90)
