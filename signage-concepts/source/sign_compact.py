"""Quick Fix Tech flyer compacted into a landscape sign.

Changes from the flyer: no TV anywhere, the "SPEAKER | LAPTOP | PS5 | XBOX" and
"AND ALL TYPES OF..." lines removed, icon row = phone, headphones, speaker, laptop,
PS logo, Xbox (TV, PS5-controller, controller and radio tiles dropped), accessory
photos dropped, accessories checklist kept.

usage: python3 sign_compact.py <out_dir> <logo_dir> <quick-fix-flyer.jpg>
"""
from signlib import *

OUT, LOGOS, FLYER_SRC = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

W, H = 3200, 1100
QBLUE = (26, 110, 232)
INK = (16, 18, 24)
NAVY = (22, 30, 52)
MONT = os.path.join(F, "Montserrat.ttf")
def mont(size, wght): return font(MONT, size, wght)

def L(n): return Image.open(os.path.join(LOGOS, n))
QF, BADGE = L("quick-fix-tech-logo.png"), L("quick-fix-same-day-badge.png")
no_tv = Image.open(os.path.join(LOGOS, "quick-fix-tech-flyer-no-tv.jpg")).convert("RGB")
orig = np.array(Image.open(FLYER_SRC).convert("RGB")).astype(np.float32)

def scale_fit(im, w, h):
    k = min(w/im.width, h/im.height); return im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)

def clean_white(im, fade=36):
    a = np.clip(np.array(im).astype(np.float32)*255/236, 0, 255); h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = np.clip(np.minimum.reduce([xx, w-1-xx, yy, h-1-yy]).astype(np.float32)/fade, 0, 1)[..., None]
    return Image.fromarray((a*k + 255*(1-k)).astype(np.uint8))

def multiply_in(img, photo, xy):
    x, y = xy; box = (x, y, x+photo.width, y+photo.height)
    img.paste(ImageChops.multiply(img.crop(box).convert("RGB"), photo.convert("RGB")).convert("RGBA"), box[:2])

PRODUCTS = no_tv.crop((752, 252, 1598, 604))
ImageDraw.Draw(PRODUCTS).rectangle((0, 572-252, 935-752, 604-252), fill=(255, 255, 255))
PRODUCTS = clean_white(PRODUCTS)

# ---------- icons ----------
def blue_icon_from_flyer(x0, x1, y0=561, y1=636):
    c = orig[y0:y1, x0-4:x1+4]
    al = np.clip((c[..., 2] - c[..., 0] - 40) / 80, 0, 1)
    return Image.fromarray((al*255).astype(np.uint8), "L")

def glyph(fontfile, ch, size=400, axes=None):
    f = ImageFont.truetype(os.path.join(F, fontfile), size)
    if axes: f.set_variation_by_axes(axes)
    m = Image.new("L", (size*2, size*2), 0); ImageDraw.Draw(m).text((size//2, size//2), ch, font=f, fill=255)
    return m.crop(m.getbbox())

def crisp(mask, h):
    """Upscale a small icon mask and re-sharpen its edges so it prints clean at sign size."""
    m = mask.resize((round(mask.width*h/mask.height), h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
    a = np.array(m).astype(np.float32)/255
    a = np.clip((a-0.38)/0.24, 0, 1)
    return Image.fromarray((a*255).astype(np.uint8), "L")

def tint(mask, col=QBLUE):
    im = Image.new("RGBA", mask.size, col + (0,)); im.putalpha(mask); return im

ICONS = [
    ("PHONE",     crisp(blue_icon_from_flyer(60, 101), 172)),
    ("HEADPHONE", crisp(glyph("MaterialSymbolsOutlined.ttf", "", axes=[0, 0, 48, 600]), 140)),
    ("SPEAKER",   crisp(blue_icon_from_flyer(330, 371), 168)),
    ("LAPTOP",    crisp(blue_icon_from_flyer(442, 520), 140)),
    ("PS5",       crisp(glyph("fa-brands-400.ttf", ""), 140)),
    ("XBOX",      crisp(blue_icon_from_flyer(717, 779), 150)),
]

ACCESSORIES = ["CASES & SCREEN PROTECTORS", "CHARGERS & CABLES", "HEADPHONES & EARPHONES",
               "POWER BANKS", "MEMORY CARDS & MORE"]

def checkmark(d, x, y, s, col=QBLUE):
    d.line([(x, y+s*0.55), (x+s*0.38, y+s*0.9), (x+s, y+s*0.1)], fill=col, width=max(6, int(s*0.18)), joint="curve")

# ---------- compose ----------
sign = noise(vgrad(W, H, (255, 255, 255), (246, 248, 252)), 2)
d = ImageDraw.Draw(sign)

# left column: logo + headline
lg = scale_fit(QF, 1120, 260); sign.alpha_composite(lg, (60, 40))
f1 = fit("WE REPAIR", MONT, 1100, 150, wght=900)
f2 = fit("CELL PHONES", MONT, 1100, 150, wght=800)
d.text((70, 470), "WE REPAIR", font=f1, fill=INK, anchor="ls")
d.text((66, 640), "CELL PHONES", font=f2, fill=QBLUE, anchor="ls")

# middle: hero products
pr = scale_fit(PRODUCTS, 1180, 560); multiply_in(sign, pr, (1220, 650 - pr.height))

# right column: badge + accessories
bd = scale_fit(BADGE, 760, 340); sign.alpha_composite(bd, (W - bd.width - 30, 30))
rx0, rx1 = 2440, W - 50
tab_top, tab_bot = 400, 580
d.polygon([(rx0, tab_top), (rx1, tab_top), (rx1 - 50, tab_bot), (rx0, tab_bot)], fill=QBLUE)
ft = fit("ACCESSORIES", MONT, rx1 - rx0 - 120, 70, wght=800)
d.text((rx0 + 36, tab_top + 82), "CELL PHONE", font=ft, fill=(255, 255, 255), anchor="ls")
d.text((rx0 + 36, tab_top + 160), "ACCESSORIES", font=ft, fill=(255, 255, 255), anchor="ls")
fl = fit(max(ACCESSORIES, key=len), MONT, rx1 - rx0 - 90, 44, wght=600)
for i, s in enumerate(ACCESSORIES):
    y = 625 + i*84
    checkmark(d, rx0 + 6, y, 40)
    d.text((rx0 + 70, y + 38), s, font=fl, fill=NAVY, anchor="ls")

# bottom band: icon row
band_top = 720
d.line([(60, band_top - 24), (2380, band_top - 24)], fill=QBLUE, width=6)
tile = (2380 - 60) / len(ICONS)
fn = mont(42, 700)
for k, (name, m) in enumerate(ICONS):
    cx = 60 + tile*k + tile/2
    ic = tint(m); sign.alpha_composite(ic, (int(cx - ic.width/2), int(band_top + 10 + (160 - ic.height)/2)))
    d.text((cx, band_top + 225), name, font=fn, fill=INK, anchor="ms")
    d.text((cx, band_top + 285), "REPAIRS", font=fn, fill=INK, anchor="ms")
    if k:
        x = 60 + tile*k
        d.line([(x, band_top + 20), (x, band_top + 300)], fill=QBLUE, width=4)
d.rectangle((0, H - 22, W, H), fill=QBLUE)

out = os.path.join(OUT, "quick-fix-tech-compact-sign.png")
sign.convert("RGB").save(out)
sign.convert("RGB").save(out.replace(".png", ".jpg"), quality=93)
print(out)
