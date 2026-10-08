"""Brand Match signage fitted to the owner's marked-up zones on 2 Gabriel Rd.

  red    -> Cool Man barber sign (left inset panel)
  blue   -> Quick Fix Tech logo (square corner panel)
  yellow -> one continuous right-hand sign, split: barber (purple part) | tech (rest)

usage: python3 signs_layout.py <out_dir> <street_photo.jpg> <logo_dir>
"""
from signlib import *

OUT, PHOTO, LOGOS = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
CROP = (0, 105, 2112, 1030)

RED_Q    = [(308, 350), (818, 290), (820, 484), (310, 505)]
BLUE_Q   = [(848, 290), (1010, 279), (1010, 472), (848, 476)]
YELLOW_Q = [(1028, 264), (1820, 382), (1820, 547), (1028, 489)]
POLE_X   = (1727, 1771)                       # street-light pole in front of the yellow sign
RED_WH, BLUE_WH, YEL_WH = (1920, 600), (600, 640), (3300, 600)

CM = Image.open(os.path.join(LOGOS, "cool-man-logo-silver.png"))
QF = Image.open(os.path.join(LOGOS, "quick-fix-tech-logo.png"))
BADGE = Image.open(os.path.join(LOGOS, "quick-fix-same-day-badge.png"))
QF_ICON = QF.crop((0, 0, 192, QF.height))
QBLUE = (26, 110, 232)
SILVER = (170, 172, 178)
SERVICES = "PHONES · LAPTOPS · PS5 · XBOX · SPEAKERS · ACCESSORIES"

def scale_h(im, h):
    return im.resize((round(im.width*h/im.height), h), Image.LANCZOS)

def scale_fit(im, w, h):
    k = min(w/im.width, h/im.height)
    return im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)

def brushed(w, h, base=(16, 16, 18)):
    rng = np.random.default_rng(7)
    streak = rng.normal(0, 4, (1, w)).repeat(h, 0) + rng.normal(0, 2, (h, w))
    a = np.clip(np.array(base)[None, None, :] + streak[..., None], 0, 255).astype(np.uint8)
    return ImageChops.multiply(Image.fromarray(a, "RGB").convert("RGBA"), vgrad(w, h, (255, 255, 255), (170, 170, 170)))

def white_panel(w, h):
    return noise(vgrad(w, h, (252, 253, 255), (236, 240, 246)), 3)

def silver_text(size, s, f, center, tracking=6):
    t = text_layer(size, s, f, center, (255, 255, 255, 255), tracking)
    g = vgrad(size[0], size[1], (236, 238, 242), (150, 154, 162)); g.putalpha(t.split()[3]); return g

def trims(img, color=SILVER):
    d = ImageDraw.Draw(img); w, h = img.size
    for y in (24, h-28): d.line([(0, y), (w, y)], fill=color, width=5)

# ---------- red: main barber sign ----------
def red_sign():
    w, h = RED_WH
    b = brushed(w, h); trims(b)
    logo = scale_h(CM, 480); paste_c(b, logo, (w/2, h/2))
    f = font(INTER_B, 38); side = (w - logo.width)/4
    for x, lines in ((side, ["FADES", "BEARDS", "SHAVES"]), (w-side, ["WALK-INS", "WELCOME", "MON–SAT"])):
        for i, s in enumerate(lines):
            b.alpha_composite(silver_text(b.size, s, f, (x, 220+i*80), tracking=8))
        d = ImageDraw.Draw(b)
        d.line([(x-95, 172), (x+95, 172)], fill=(150, 30, 40), width=4)
        d.line([(x-95, 430), (x+95, 430)], fill=(150, 30, 40), width=4)
    return b

# ---------- blue: tech logo panel ----------
def blue_sign():
    w, h = BLUE_WH
    t = white_panel(w, h)
    ImageDraw.Draw(t).rectangle((0, 0, w-1, h-1), outline=QBLUE, width=18)
    ic = scale_h(QF_ICON, 360); paste_c(t, ic, (w/2, 225))
    lay = Image.new("RGBA", t.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = fit("QUICK FIX", INTER_BL, w-110, 80)
    wq = d.textlength("QUICK ", font=f); wf = d.textlength("FIX", font=f); x = (w-(wq+wf))/2
    d.text((x, 520), "QUICK ", font=f, fill=(14, 16, 22), anchor="ls"); d.text((x+wq, 520), "FIX", font=f, fill=QBLUE, anchor="ls")
    t.alpha_composite(lay)
    t.alpha_composite(text_layer(t.size, "TECH", font(INTER_BL, 50), (w/2, 573), (14, 16, 22, 255), tracking=22))
    return t

# ---------- yellow: one sign, barber | tech ----------
def split_for_photo_x(px):
    """flat x on the yellow artwork that lands on photo x=px (keeps the split where it was drawn)."""
    w, h = YEL_WH
    c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], YELLOW_Q)          # flat -> photo
    def fx(u):
        v = h/2; den = c[6]*u + c[7]*v + 1; return (c[0]*u + c[1]*v + c[2]) / den
    lo, hi = 0, w
    for _ in range(40):
        m = (lo+hi)/2
        if fx(m) < px: lo = m
        else: hi = m
    return int(lo)

def yellow_sign(split):
    w, h = YEL_WH
    s = Image.new("RGBA", (w, h))
    s.paste(brushed(split, h), (0, 0))
    s.paste(white_panel(w-split, h), (split, 0))
    d = ImageDraw.Draw(s)
    d.rectangle((split, h-18, w, h), fill=QBLUE)
    cap = split_for_photo_x(POLE_X[0] - 4)                           # keep artwork clear of the lamp pole
    d.rectangle((cap, 0, w, h), fill=QBLUE)
    trims(s)                                                        # one continuous trim ties both halves together
    pole_stripes(s, (split-14, 0, split+14, h), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=20, angle=.6)
    # barber half
    logo = scale_fit(CM, split-140, 480); paste_c(s, logo, (split/2, h/2))
    # tech half
    tw = cap - split; x0 = split + 60
    bd = scale_h(BADGE, 440) if tw > 1700 else None
    room = tw - 120 - (bd.width + 40 if bd else 0)
    lg = scale_fit(QF, room, 360)
    sf = fit(SERVICES, INTER_B, lg.width-60, 56)
    block = lg.height + 40 + 56; top = (h - block)/2
    s.alpha_composite(lg, (x0, int(top)))
    s.alpha_composite(text_layer(s.size, SERVICES, sf, (x0+lg.width/2, top+lg.height+40+28), (30, 34, 44, 255)))
    if bd: s.alpha_composite(bd, (cap-bd.width-30, int((h-bd.height)/2)))
    return s

def restore_pole(img, photo):
    m = Image.new("L", photo.size, 0)
    ImageDraw.Draw(m).rectangle((POLE_X[0], 200, POLE_X[1], 640), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    out = img.convert("RGB"); out.paste(photo, (0, 0), m); return out

photo = Image.open(PHOTO).convert("RGB")
split_drawn = split_for_photo_x(1512)
VARIANTS = [
    ("as-marked", "As marked — barber in the purple zone, tech the rest, tech logo in the corner square", split_drawn),
    ("barber-shrunk", "Barber shrunk — smaller barber section, more room for the tech store", int(YEL_WH[0]*0.34)),
]
print("split as drawn:", split_drawn, "of", YEL_WH[0])
red, blue = red_sign(), blue_sign()
for i, (slug, title, split) in enumerate(VARIANTS, 1):
    yel = yellow_sign(split)
    img = place(photo, red, RED_Q, light=1.0, warm=(1.03, 1.0, .96))
    img = place(img.convert("RGB"), blue, BLUE_Q, light=.97, warm=(1.03, 1.0, .96))
    img = place(img.convert("RGB"), yel, YELLOW_Q, light=.82, warm=(.94, .97, 1.04), texture=0.015)
    img = restore_pole(img, photo)
    img = label(img.crop(CROP), title)
    p = os.path.join(OUT, f"layout-{i}-{slug}.jpg"); img.save(p, quality=90); print(p)
    flat = Image.new("RGB", (YEL_WH[0], RED_WH[1]+YEL_WH[1]+120), (240, 240, 240))
    flat.paste(red.convert("RGB"), (0, 0)); flat.paste(blue.convert("RGB"), (RED_WH[0]+60, 0))
    flat.paste(yel.convert("RGB"), (0, RED_WH[1]+80))
    flat.save(os.path.join(OUT, f"layout-{i}-{slug}-flat-artwork.png"))
