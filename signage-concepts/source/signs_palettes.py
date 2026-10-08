"""Colour-scheme variants of the marked-up layout (barber shrunk).

usage: python3 signs_palettes.py <out_dir> <street_photo.jpg> <logo_dir>
"""
from signlib import *

OUT, PHOTO, LOGOS = sys.argv[1:4]
FIRST = int(sys.argv[4]) if len(sys.argv) > 4 else 1
os.makedirs(OUT, exist_ok=True)
CROP = (0, 105, 2112, 1030)

RED_Q    = [(308, 350), (818, 290), (820, 484), (310, 505)]
BLUE_Q   = [(848, 290), (1010, 279), (1010, 472), (848, 476)]
YELLOW_Q = [(1028, 264), (1820, 382), (1820, 547), (1028, 489)]
POLE_X   = (1727, 1771)
RED_WH, BLUE_WH, YEL_WH = (1920, 600), (600, 640), (3300, 600)
SPLIT = int(YEL_WH[0]*0.34)
SERVICES = "PHONES · LAPTOPS · PS5 · XBOX · SPEAKERS · ACCESSORIES"
QBLUE = (26, 110, 232)

def L(n): return Image.open(os.path.join(LOGOS, n))
CM, QF, QF_W, BADGE = L("cool-man-logo-silver.png"), L("quick-fix-tech-logo.png"), L("quick-fix-tech-logo-white.png"), L("quick-fix-same-day-badge.png")

def all_white(im):
    a = np.array(im).copy(); a[..., :3] = 255; return Image.fromarray(a, "RGBA")

def gunmetal(logo):
    a = np.array(logo).astype(np.float32); rgb = a[..., :3]
    sat = rgb.max(2) - rgb.min(2); neutral = (1 - np.clip((sat-30)/50, 0, 1))[..., None]
    v = rgb.mean(2, keepdims=True)
    dark = np.clip(255 - v*0.92, 0, 255)*np.array([0.30, 0.31, 0.34]) + 8
    gold = (rgb[..., 0] > rgb[..., 2]+40) & (rgb[..., 1] > rgb[..., 2]+15)
    out = rgb*(1-neutral) + dark*neutral; out[gold] = rgb[gold]*0.72
    a[..., :3] = out; a[..., 3] = np.clip(a[..., 3]*1.15, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")

def white_chrome(logo):
    """Brighter chrome for red panels: silver lifted towards white, red rule turned white, gold kept."""
    a = np.array(logo).astype(np.float32); rgb = a[..., :3]
    sat = rgb.max(2) - rgb.min(2); neutral = (1 - np.clip((sat-30)/50, 0, 1))[..., None]
    red = ((rgb[..., 0] > rgb[..., 1]+50) & (rgb[..., 0] > rgb[..., 2]+50))[..., None]
    v = rgb.mean(2, keepdims=True); lifted = 255 - (255 - v)*0.35
    out = rgb*(1-neutral) + lifted*neutral
    out = np.where(red, 250, out)
    a[..., :3] = out; a[..., 3] = np.clip(a[..., 3]*1.25, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")

CM_LOGO = {"silver": CM, "gunmetal": gunmetal(CM), "white": white_chrome(CM)}
QF_LOGO = {"colour": QF, "white": QF_W, "allwhite": all_white(QF)}

def scale_h(im, h): return im.resize((round(im.width*h/im.height), h), Image.LANCZOS)
def scale_fit(im, w, h):
    k = min(w/im.width, h/im.height); return im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)

def panel(w, h, col, brushed=True):
    """Flat colour panel; dark colours get a subtle brushed-metal grain, light ones a gentle sheen."""
    lum = sum(col)/3
    if brushed and lum < 110:
        rng = np.random.default_rng(7)
        streak = rng.normal(0, 4, (1, w)).repeat(h, 0) + rng.normal(0, 2, (h, w))
        a = np.clip(np.array(col)[None, None, :] + streak[..., None], 0, 255).astype(np.uint8)
        return ImageChops.multiply(Image.fromarray(a, "RGB").convert("RGBA"), vgrad(w, h, (255, 255, 255), (185, 185, 185)))
    top = tuple(min(255, c+8) for c in col); bot = tuple(max(0, c-12) for c in col)
    return noise(vgrad(w, h, top, bot), 3)

def ink_text(size, s, f, center, col, tracking=8, silver=False):
    t = text_layer(size, s, f, center, (255, 255, 255, 255), tracking)
    if silver:
        g = vgrad(size[0], size[1], (236, 238, 242), (150, 154, 162)); g.putalpha(t.split()[3]); return g
    return text_layer(size, s, f, center, col + (255,), tracking)

CANDY = [(200, 28, 38), (248, 249, 252)]
def trims(img, col, stripes=False):
    w, h = img.size
    if stripes:
        pole_stripes(img, (0, 0, w, 34), CANDY, band=34); pole_stripes(img, (0, h-34, w, h), CANDY, band=34); return
    d = ImageDraw.Draw(img)
    for y in (24, h-28): d.line([(0, y), (w, y)], fill=col, width=5)

def coeff_x(px):
    w, h = YEL_WH; c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], YELLOW_Q)
    fx = lambda u: (c[0]*u + c[1]*h/2 + c[2]) / (c[6]*u + c[7]*h/2 + 1)
    lo, hi = 0, w
    for _ in range(40):
        m = (lo+hi)/2
        if fx(m) < px: lo = m
        else: hi = m
    return int(lo)
CAP = coeff_x(POLE_X[0]-4)

# ---------------- palettes ----------------
# barber: bg, cm logo, side-text colour (None = silver), trim, rule accent
# tech: bg, qf logo, services ink, badge (True = brush badge, False = white text block), bottom strip, cap
# corner square: bg, icon logo, word ink, border
P = [
  dict(slug="navy-white", title="Navy & White — classic navy barber, crisp white tech",
       b_bg=(18, 30, 58), b_logo="silver", b_ink=None, trim=(170, 172, 178), rule=(170, 34, 44),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=True, strip=QBLUE, cap=QBLUE,
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(18, 30, 58)),
  dict(slug="charcoal", title="Charcoal — one slate-grey fascia, chrome + white logos",
       b_bg=(42, 45, 51), b_logo="silver", b_ink=None, trim=(150, 154, 162), rule=(170, 34, 44),
       t_bg=(42, 45, 51), t_logo="white", t_ink=(215, 220, 228), badge=True, strip=QBLUE, cap=QBLUE,
       s_bg=(42, 45, 51), s_logo="white", s_ink=(240, 242, 246), s_border=QBLUE),
  dict(slug="stone", title="Stone — warm light-grey fascia, gunmetal barber, red trims",
       b_bg=(226, 224, 218), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(150, 30, 40), rule=(150, 30, 40),
       t_bg=(226, 224, 218), t_logo="colour", t_ink=(34, 36, 42), badge=True, strip=QBLUE, cap=QBLUE,
       s_bg=(226, 224, 218), s_logo="colour", s_ink=(20, 22, 28), s_border=(150, 30, 40)),
  dict(slug="burgundy-white", title="Burgundy & White — barber-pole red meets Quick Fix blue",
       b_bg=(92, 18, 30), b_logo="silver", b_ink=None, trim=(200, 170, 110), rule=(200, 170, 110),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=True, strip=QBLUE, cap=QBLUE,
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(92, 18, 30)),
  dict(slug="black-blue", title="Black & Blue — chrome barber on black, solid Quick Fix blue tech",
       b_bg=(16, 16, 18), b_logo="silver", b_ink=None, trim=(170, 172, 178), rule=(170, 34, 44),
       t_bg=(26, 108, 228), t_logo="allwhite", t_ink=(255, 255, 255), badge=False, strip=(255, 255, 255), cap=(16, 16, 18),
       s_bg=(26, 108, 228), s_logo="allwhite", s_ink=(255, 255, 255), s_border=(16, 16, 18)),
  dict(slug="navy-blue", title="Navy & Blue — two blues from the barber pole, one family",
       b_bg=(16, 26, 52), b_logo="silver", b_ink=None, trim=(200, 170, 110), rule=(200, 170, 110),
       t_bg=(30, 112, 232), t_logo="allwhite", t_ink=(255, 255, 255), badge=False, strip=(200, 170, 110), cap=(16, 26, 52),
       s_bg=(16, 26, 52), s_logo="white", s_ink=(255, 255, 255), s_border=(30, 112, 232)),
  dict(slug="cream-navy", title="Cream & Navy — gunmetal barber on cream, white Quick Fix on navy",
       b_bg=(240, 234, 220), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(18, 30, 58), rule=(170, 34, 44),
       t_bg=(18, 30, 58), t_logo="white", t_ink=(230, 234, 242), badge=False, strip=QBLUE, cap=(18, 30, 58),
       s_bg=(18, 30, 58), s_logo="white", s_ink=(255, 255, 255), s_border=(240, 234, 220)),
  dict(slug="white-black", title="White & Black — white barber, black tech: the reverse of Brand Match",
       b_bg=(248, 249, 252), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(34, 36, 42), rule=(170, 34, 44),
       t_bg=(16, 16, 18), t_logo="white", t_ink=(215, 220, 228), badge=False, strip=QBLUE, cap=(16, 16, 18),
       s_bg=(16, 16, 18), s_logo="white", s_ink=(255, 255, 255), s_border=QBLUE),
  dict(slug="aluminium", title="Brushed Aluminium — one silver-metal fascia, dark logos, blue + red accents",
       b_bg=(196, 199, 204), b_logo="gunmetal", b_ink=(30, 32, 38), trim=(150, 30, 40), rule=(150, 30, 40),
       t_bg=(196, 199, 204), t_logo="colour", t_ink=(24, 26, 32), badge=False, strip=QBLUE, cap=QBLUE,
       s_bg=(196, 199, 204), s_logo="colour", s_ink=(18, 20, 26), s_border=QBLUE),
  dict(slug="ice-blue", title="Ice Blue — pale blue fascia, light and fresh, both logos in full colour",
       b_bg=(222, 233, 246), b_logo="gunmetal", b_ink=(24, 34, 58), trim=QBLUE, rule=(170, 34, 44),
       t_bg=(222, 233, 246), t_logo="colour", t_ink=(24, 34, 58), badge=False, strip=QBLUE, cap=QBLUE,
       s_bg=(248, 250, 253), s_logo="colour", s_ink=(14, 16, 22), s_border=QBLUE),
  dict(slug="petrol-white", title="Petrol & White — deep teal-blue barber, white tech, silver trims",
       b_bg=(14, 62, 78), b_logo="silver", b_ink=None, trim=(170, 172, 178), rule=(200, 170, 110),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=False, strip=(14, 62, 78), cap=(14, 62, 78),
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(14, 62, 78)),
  dict(slug="midnight-gold", title="Midnight & Gold — one midnight fascia with gold trims, premium after dark",
       b_bg=(12, 16, 30), b_logo="silver", b_ink=None, trim=(200, 170, 110), rule=(200, 170, 110),
       t_bg=(12, 16, 30), t_logo="white", t_ink=(220, 200, 150), badge=False, strip=(200, 170, 110), cap=(12, 16, 30),
       s_bg=(12, 16, 30), s_logo="white", s_ink=(255, 255, 255), s_border=(200, 170, 110)),
  dict(slug="red-white", title="Red & White — pole-red barber with chrome logo, white tech",
       b_bg=(200, 28, 38), b_logo="white", b_ink=(255, 255, 255), trim=(255, 255, 255), rule=(255, 255, 255),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=False, strip=(200, 28, 38), cap=(200, 28, 38),
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(200, 28, 38)),
  dict(slug="white-red-accents", title="White with Red — all-white fascia, red trims and rules",
       b_bg=(248, 249, 252), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(200, 28, 38), rule=(200, 28, 38),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=False, strip=(200, 28, 38), cap=(200, 28, 38),
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(200, 28, 38)),
  dict(slug="candy-stripe", title="Candy Stripe — white panels framed in red-and-white barber stripes",
       b_bg=(248, 249, 252), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(200, 28, 38), rule=(200, 28, 38), stripes=True,
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=False, strip=(200, 28, 38), cap=(200, 28, 38),
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(200, 28, 38)),
  dict(slug="white-barber-red-tech", title="White barber, Red tech — the shops swap colours",
       b_bg=(248, 249, 252), b_logo="gunmetal", b_ink=(34, 36, 42), trim=(200, 28, 38), rule=(200, 28, 38),
       t_bg=(200, 28, 38), t_logo="allwhite", t_ink=(255, 255, 255), badge=False, strip=(255, 255, 255), cap=(200, 28, 38),
       s_bg=(200, 28, 38), s_logo="allwhite", s_ink=(255, 255, 255), s_fix=(255, 255, 255), s_border=(255, 255, 255)),
  dict(slug="all-red", title="All Red — one bold red fascia, chrome and white logos",
       b_bg=(200, 28, 38), b_logo="white", b_ink=(255, 255, 255), trim=(255, 255, 255), rule=(255, 255, 255),
       t_bg=(200, 28, 38), t_logo="allwhite", t_ink=(255, 255, 255), badge=False, strip=(255, 255, 255), cap=(200, 28, 38),
       s_bg=(255, 255, 255), s_logo="colour", s_ink=(14, 16, 22), s_border=(200, 28, 38)),
  dict(slug="oxblood-white", title="Oxblood & White — deep red barber with white trims, white tech",
       b_bg=(120, 16, 26), b_logo="white", b_ink=(240, 236, 230), trim=(240, 236, 230), rule=(200, 170, 110),
       t_bg=(248, 249, 252), t_logo="colour", t_ink=(30, 34, 44), badge=False, strip=(120, 16, 26), cap=(120, 16, 26),
       s_bg=(248, 249, 252), s_logo="colour", s_ink=(14, 16, 22), s_border=(120, 16, 26)),
]

def red_sign(p):
    w, h = RED_WH; b = panel(w, h, p["b_bg"]); trims(b, p["trim"], p.get("stripes"))
    logo = scale_h(CM_LOGO[p["b_logo"]], 480); paste_c(b, logo, (w/2, h/2))
    f = font(INTER_B, 38); side = (w - logo.width)/4
    for x, lines in ((side, ["FADES", "BEARDS", "SHAVES"]), (w-side, ["WALK-INS", "WELCOME", "MON–SAT"])):
        for i, s in enumerate(lines):
            b.alpha_composite(ink_text(b.size, s, f, (x, 220+i*80), p["b_ink"] or (0, 0, 0), silver=p["b_ink"] is None))
        d = ImageDraw.Draw(b)
        for y in (172, 430): d.line([(x-95, y), (x+95, y)], fill=p["rule"], width=4)
    return b

def blue_sign(p):
    w, h = BLUE_WH; t = panel(w, h, p["s_bg"], brushed=False)
    ImageDraw.Draw(t).rectangle((0, 0, w-1, h-1), outline=p["s_border"], width=18)
    icon = QF_LOGO[p["s_logo"]].crop((0, 0, 192, QF.height)); paste_c(t, scale_h(icon, 360), (w/2, 225))
    lay = Image.new("RGBA", t.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = fit("QUICK FIX", INTER_BL, w-110, 80)
    wq = d.textlength("QUICK ", font=f); wf = d.textlength("FIX", font=f); x = (w-(wq+wf))/2
    on_blue = p["s_bg"][2] > 180 and p["s_bg"][0] < 80
    fixc = p.get("s_fix") or (p["s_ink"] if on_blue else QBLUE)
    d.text((x, 520), "QUICK ", font=f, fill=p["s_ink"], anchor="ls"); d.text((x+wq, 520), "FIX", font=f, fill=fixc, anchor="ls")
    t.alpha_composite(lay)
    t.alpha_composite(text_layer(t.size, "TECH", font(INTER_BL, 50), (w/2, 573), p["s_ink"] + (255,), tracking=22))
    return t

def yellow_sign(p):
    w, h = YEL_WH; s = Image.new("RGBA", (w, h))
    s.paste(panel(SPLIT, h, p["b_bg"]), (0, 0)); s.paste(panel(w-SPLIT, h, p["t_bg"]), (SPLIT, 0))
    d = ImageDraw.Draw(s)
    d.rectangle((SPLIT, h-18, w, h), fill=p["strip"]); d.rectangle((CAP, 0, w, h), fill=p["cap"])
    trims(s, p["trim"], p.get("stripes"))
    pole_stripes(s, (SPLIT-14, 0, SPLIT+14, h), [(196, 30, 42), (240, 240, 240), (30, 70, 170), (240, 240, 240)], band=20, angle=.6)
    paste_c(s, scale_fit(CM_LOGO[p["b_logo"]], SPLIT-140, 480), (SPLIT/2, h/2))
    x0 = SPLIT + 60; tw = CAP - SPLIT
    side_w = 0                                                      # long sign: logo + services only; badge lives on flyers
    lg = scale_fit(QF_LOGO[p["t_logo"]], tw - 120 - side_w, 360)
    sf = fit(SERVICES, INTER_B, lg.width-60, 56)
    top = (h - (lg.height + 96))/2
    s.alpha_composite(lg, (x0, int(top)))
    s.alpha_composite(text_layer(s.size, SERVICES, sf, (x0+lg.width/2, top+lg.height+68), p["t_ink"] + (255,)))
    return s

def restore_pole(img, photo):
    m = Image.new("L", photo.size, 0); ImageDraw.Draw(m).rectangle((POLE_X[0], 200, POLE_X[1], 640), fill=255)
    out = img.convert("RGB"); out.paste(photo, (0, 0), m.filter(ImageFilter.GaussianBlur(1.2))); return out

photo = Image.open(PHOTO).convert("RGB")
paths = []
RUN = [(i, p) for i, p in enumerate(P, 1) if i >= FIRST]
for i, p in RUN:
    red, blue, yel = red_sign(p), blue_sign(p), yellow_sign(p)
    img = place(photo, red, RED_Q, light=1.0, warm=(1.03, 1.0, .96), texture=0.03)
    img = place(img.convert("RGB"), blue, BLUE_Q, light=.97, warm=(1.03, 1.0, .96), texture=0.03)
    img = place(img.convert("RGB"), yel, YELLOW_Q, light=.82, warm=(.94, .97, 1.04), texture=0.015)
    img = label(restore_pole(img, photo).crop(CROP), p["title"])
    path = os.path.join(OUT, f"colour-{i}-{p['slug']}.jpg"); img.save(path, quality=90); paths.append(path)
    flat = Image.new("RGB", (YEL_WH[0], RED_WH[1]+YEL_WH[1]+120), (240, 240, 240))
    flat.paste(red.convert("RGB"), (0, 0)); flat.paste(blue.convert("RGB"), (RED_WH[0]+60, 0)); flat.paste(yel.convert("RGB"), (0, RED_WH[1]+80))
    flat.save(os.path.join(OUT, f"colour-{i}-{p['slug']}-flat-artwork.png"))
    print(path)

# overview: tight crop on the fascia, 2 columns
tiles = [Image.open(q).crop((250, 120, 1900, 560)).resize((1100, 293)) for q in paths]
caps = [f'{i}. {p["title"].split(" — ")[0]}' for i, p in RUN]
rows = (len(tiles)+1)//2
sheet = Image.new("RGB", (2*1100+30, rows*(293+60)+10), (18, 18, 20)); d = ImageDraw.Draw(sheet); f = font(INTER_B, 34)
for k, (t, c) in enumerate(zip(tiles, caps)):
    x = 10 + (k % 2)*1110; y = 10 + (k//2)*(293+60)
    sheet.paste(t, (x, y)); d.text((x+6, y+300), c, font=f, fill=(240, 240, 240))
sheet.save(os.path.join(OUT, "colour-schemes-overview.jpg" if FIRST == 1 else f"colour-schemes-overview-from-{FIRST}.jpg"), quality=90)
