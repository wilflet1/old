import random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

S = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(S, "fonts")
OUT = sys.argv[1]
PHOTO = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

def font(name, size, wght=None):
    p = name if name.startswith("/") else os.path.join(F, name)
    f = ImageFont.truetype(p, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

INTER_B = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
def sysfont(fam):
    import subprocess
    return subprocess.check_output(["fc-match", "-f", "%{file}", fam]).decode()
INTER_B = sysfont("Inter:style=Bold"); INTER_M = sysfont("Inter:style=Medium"); INTER_BL = sysfont("Inter:style=Black")

# ---------- photo geometry (pixel coords in the 2112x1320 street-view capture) ----------
LEFT_Q  = [(298, 340), (1023, 262), (1023, 489), (300, 521)]   # TL TR BR BL - barber face
RIGHT_Q = [(1027, 262), (1738, 368), (1738, 541), (1027, 489)]  # tech face, recedes right
LW, LH = 2200, 600
RW, RH = 2800, 600

# ---------- drawing helpers ----------
def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f); return b[2]-b[0], b[3]-b[1], b

def fit(s, fname, maxw, maxh, wght=None):
    lo, hi = 8, 900
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    while lo < hi:
        m = (lo+hi+1)//2
        w, h, _ = tsize(d, s, font(fname, m, wght))
        if w <= maxw and h <= maxh: lo = m
        else: hi = m-1
    return font(fname, lo, wght)

def text_layer(size, s, f, center, fill, tracking=0):
    L = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    if tracking:
        widths = [d.textlength(ch, font=f) for ch in s]
        total = sum(widths) + tracking*(len(s)-1)
        _, h, b = tsize(d, s, f)
        x = center[0]-total/2; y = center[1]-h/2-b[1]
        for ch, w in zip(s, widths):
            d.text((x, y), ch, font=f, fill=fill); x += w+tracking
    else:
        w, h, b = tsize(d, s, f)
        d.text((center[0]-w/2-b[0], center[1]-h/2-b[1]), s, font=f, fill=fill)
    return L

def glow(img, layer, color, radii=(40, 18, 6), strength=(0.9, 1.0, 1.0)):
    a = layer.split()[3]
    for r, k in zip(radii, strength):
        g = a.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v*k*1.6)))
        c = Image.new("RGBA", img.size, color + (0,)); c.putalpha(g)
        img.alpha_composite(c)
    img.alpha_composite(layer)

def shadow(img, layer, off=(8, 10), blur=8, alpha=160):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v*alpha//255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
    img.alpha_composite(sh, dest=off)
    img.alpha_composite(layer)

def outline(layer, px, color):
    a = layer.split()[3].filter(ImageFilter.MaxFilter(px*2+1))
    o = Image.new("RGBA", layer.size, color + (255,)); o.putalpha(a)
    o.alpha_composite(layer); return o

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :]*(1-t) + np.array(bot)[None, None, :]*t)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA"); return im

def noise(img, amt=6, seed=1):
    rng = np.random.default_rng(seed)
    a = np.array(img).astype(np.int16)
    n = rng.integers(-amt, amt+1, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3]+n, 0, 255); return Image.fromarray(a.astype(np.uint8), "RGBA")

def pole_stripes(img, box, colors, band=60, angle=1.0):
    x0, y0, x1, y1 = box
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    h = y1-y0; i = 0; x = x0-h*angle-band*3
    while x < x1+band:
        c = colors[i % len(colors)]
        d.polygon([(x, y1), (x+band, y1), (x+band+h*angle, y0), (x+h*angle, y0)], fill=c)
        x += band; i += 1
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).rectangle(box, fill=255)
    img.paste(L, (0, 0), ImageChops.multiply(L.split()[3], m))

def circuit(img, color, n=26, seed=3, alpha=70, area=None):
    rng = random.Random(seed); w, h = img.size
    x0, y0, x1, y1 = area or (0, 0, w, h)
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for _ in range(n):
        x = rng.uniform(x0, x1); y = rng.choice([y0+rng.uniform(10, 60), y1-rng.uniform(10, 60)])
        pts = [(x, y)]
        for _ in range(rng.randint(2, 4)):
            dx = rng.choice([-1, 1])*rng.uniform(40, 220)
            if rng.random() < .5: x += dx; y += rng.choice([-1, 1])*abs(dx)*.3
            else: x += dx
            y = min(max(y, y0+8), y1-8); pts.append((x, y))
        d.line(pts, fill=color+(alpha,), width=4, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse((p[0]-9, p[1]-9, p[0]+9, p[1]+9), outline=color+(alpha+40,), width=4)
    img.alpha_composite(L)

def frame(img, inset, color, width):
    w, h = img.size; d = ImageDraw.Draw(img)
    d.rectangle((inset, inset, w-inset-1, h-inset-1), outline=color, width=width)

# ---------- icons ----------
def scissors(size, color, thick=14):
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    s = size
    d.ellipse((s*.06, s*.62, s*.36, s*.92), outline=color, width=thick)
    d.ellipse((s*.64, s*.62, s*.94, s*.92), outline=color, width=thick)
    d.line([(s*.30, s*.66), (s*.80, s*.06)], fill=color, width=thick+4)
    d.line([(s*.70, s*.66), (s*.20, s*.06)], fill=color, width=thick+4)
    d.ellipse((s*.47, s*.38, s*.53, s*.44), fill=(0, 0, 0, 0))
    return L

def razor(size, color, thick=12):
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L); s = size
    d.rounded_rectangle((s*.08, s*.38, s*.62, s*.58), radius=s*.06, fill=color)
    d.polygon([(s*.62, s*.40), (s*.92, s*.30), (s*.94, s*.36), (s*.62, s*.56)], fill=color)
    return L

def chip(size, color, thick=12):
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L); s = size
    d.rounded_rectangle((s*.24, s*.24, s*.76, s*.76), radius=s*.06, outline=color, width=thick)
    d.rounded_rectangle((s*.38, s*.38, s*.62, s*.62), radius=s*.03, fill=color)
    for i in range(4):
        p = s*(.32+i*.12)
        d.line([(p, s*.08), (p, s*.24)], fill=color, width=thick)
        d.line([(p, s*.76), (p, s*.92)], fill=color, width=thick)
        d.line([(s*.08, p), (s*.24, p)], fill=color, width=thick)
        d.line([(s*.76, p), (s*.92, p)], fill=color, width=thick)
    return L

def phone(size, color, thick=12):
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L); s = size
    d.rounded_rectangle((s*.28, s*.06, s*.72, s*.94), radius=s*.09, outline=color, width=thick)
    d.line([(s*.43, s*.16), (s*.57, s*.16)], fill=color, width=thick)
    d.ellipse((s*.46, s*.80, s*.54, s*.88), fill=color)
    return L

def bolt(size, color):
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L); s = size
    d.polygon([(s*.58, s*.04), (s*.20, s*.56), (s*.46, s*.56), (s*.38, s*.96), (s*.80, s*.40), (s*.53, s*.40)], fill=color)
    return L

def mustache(size, color):
    L = Image.new("RGBA", (size*2, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L); s = size
    d.chord((s*.2, s*.25, s*1.0, s*.85), 0, 180, fill=color)
    d.chord((s*1.0, s*.25, s*1.8, s*.85), 0, 180, fill=color)
    d.ellipse((s*.02, s*.28, s*.36, s*.62), fill=color); d.ellipse((s*1.64, s*.28, s*1.98, s*.62), fill=color)
    d.ellipse((s*.06, s*.30, s*.30, s*.52), fill=(0, 0, 0, 0))
    a = L.split()[3]; cut = Image.new("L", L.size, 0); cd = ImageDraw.Draw(cut)
    cd.ellipse((s*.0, s*.12, s*.30, s*.44), fill=255); cd.ellipse((s*1.70, s*.12, s*2.0, s*.44), fill=255)
    L.putalpha(ImageChops.subtract(a, cut))
    return L

def paste_c(img, L, c):
    img.alpha_composite(L, dest=(int(c[0]-L.width/2), int(c[1]-L.height/2)))

# ======================= CONCEPTS =======================
# Each returns (barber_face, tech_face) as flat RGBA artwork.

def c1_neon():
    """Matte black panels, neon-tube lettering. Reads day and night."""
    b = noise(vgrad(LW, LH, (24, 24, 28), (12, 12, 14)), 5)
    frame(b, 22, (60, 60, 66), 6)
    pole_stripes(b, (0, LH-58, LW, LH-22), [(214, 36, 48), (245, 245, 245), (30, 70, 170), (245, 245, 245)], band=46)
    f = fit("Cool Man", os.path.join(F, "Pacifico-Regular.ttf"), 1250, 330)
    t = text_layer(b.size, "Cool Man", f, (LW*.42, 230), (255, 245, 250, 255))
    glow(b, t, (255, 40, 140), radii=(46, 20, 7))
    f2 = font(os.path.join(F, "Monoton-Regular.ttf"), 100)
    t2 = text_layer(b.size, "BARBER", f2, (LW*.42, 455), (220, 245, 255, 255), tracking=20)
    glow(b, t2, (40, 170, 255), radii=(30, 12, 4))
    sc = scissors(300, (255, 255, 255, 255), 16)
    sl = Image.new("RGBA", b.size, (0, 0, 0, 0)); paste_c(sl, sc, (LW*.86, 260))
    glow(b, sl, (40, 170, 255), radii=(30, 12, 4))
    sub = text_layer(b.size, "FADES · BEARDS · SHAVES", font(INTER_B, 34), (LW*.86, 470), (200, 200, 210, 255), tracking=4)
    b.alpha_composite(sub)

    t_ = noise(vgrad(RW, RH, (16, 18, 24), (8, 9, 12)), 5)
    circuit(t_, (0, 220, 255), n=34, alpha=55)
    frame(t_, 22, (60, 60, 66), 6)
    ic = chip(330, (255, 255, 255, 255), 14); il = Image.new("RGBA", t_.size, (0, 0, 0, 0)); paste_c(il, ic, (310, 290))
    glow(t_, il, (0, 220, 255), radii=(36, 14, 5))
    f = fit("TECH CORNER", os.path.join(F, "Orbitron.ttf"), 1900, 250, wght=900)
    tl = text_layer(t_.size, "TECH CORNER", f, (1540, 245), (235, 255, 255, 255), tracking=10)
    glow(t_, tl, (0, 220, 255), radii=(44, 18, 6))
    s2 = text_layer(t_.size, "PHONES  ·  LAPTOPS  ·  REPAIRS  ·  ACCESSORIES", font(INTER_B, 58), (1540, 450), (255, 255, 255, 255), tracking=8)
    glow(t_, s2, (255, 40, 140), radii=(16, 6, 2), strength=(.6, .7, .7))
    return b, t_, "neon-noir", "Neon Noir — matte black, neon-tube lettering, glows after dark"

def c2_heritage():
    """Heritage barber (navy/cream/pole stripe) + crisp white tech panel."""
    b = noise(vgrad(LW, LH, (20, 36, 72), (14, 26, 54)), 4)
    pole_stripes(b, (0, 0, LW, 54), [(196, 30, 42), (240, 232, 214), (240, 232, 214)], band=40)
    pole_stripes(b, (0, LH-54, LW, LH), [(196, 30, 42), (240, 232, 214), (240, 232, 214)], band=40)
    d = ImageDraw.Draw(b)
    d.line([(0, 60), (LW, 60)], fill=(205, 170, 95), width=6); d.line([(0, LH-60), (LW, LH-60)], fill=(205, 170, 95), width=6)
    f = fit("COOL MAN", os.path.join(F, "Rye-Regular.ttf"), 1250, 230)
    t = text_layer(b.size, "COOL MAN", f, (LW/2, 255), (244, 234, 212, 255), tracking=8)
    t = outline(t, 5, (160, 28, 40)); shadow(b, t, (10, 12), 4, 170)
    f2 = font(os.path.join(F, "Anton-Regular.ttf"), 92)
    t2 = text_layer(b.size, "— BARBERSHOP —", f2, (LW/2, 445), (205, 170, 95, 255), tracking=14)
    b.alpha_composite(t2)
    for x in (230, LW-230):
        r = razor(260, (205, 170, 95, 255)) if x > LW/2 else scissors(240, (205, 170, 95, 255), 14)
        paste_c(b, r, (x, 300))
    est = text_layer(b.size, "EST. 2026", font(INTER_B, 40), (230, 470), (244, 234, 212, 200), tracking=6); b.alpha_composite(est)
    est = text_layer(b.size, "WALK-INS", font(INTER_B, 40), (LW-230, 470), (244, 234, 212, 200), tracking=6); b.alpha_composite(est)

    t_ = noise(vgrad(RW, RH, (250, 251, 253), (232, 236, 242)), 3)
    d = ImageDraw.Draw(t_)
    d.rectangle((0, 0, 560, RH), fill=(20, 92, 255))
    pl = phone(360, (255, 255, 255, 255), 16); paste_c(t_, pl, (280, 300))
    d.polygon([(560, 0), (640, 0), (560, RH)], fill=(20, 92, 255))
    f = fit("TECH CORNER", os.path.join(F, "SpaceGrotesk.ttf"), 1950, 240, wght=700)
    tl = text_layer(t_.size, "TECH CORNER", f, (1700, 245), (14, 18, 30, 255), tracking=-4)
    t_.alpha_composite(tl)
    d.rectangle((760, 372, 2640, 380), fill=(20, 92, 255))
    s2 = text_layer(t_.size, "PHONES · LAPTOPS · REPAIRS · ACCESSORIES", font(INTER_M, 64), (1700, 465), (60, 68, 84, 255), tracking=4)
    t_.alpha_composite(s2)
    return b, t_, "heritage-clean", "Heritage & Clean — navy/cream classic barber meets bright white tech retail"

def c3_wrap():
    """One continuous black band wrapping the corner, unified by a single accent stripe."""
    def band(w, h, accent):
        im = noise(vgrad(w, h, (18, 18, 18), (10, 10, 10)), 4)
        d = ImageDraw.Draw(im); d.rectangle((0, h-44, w, h-26), fill=accent)
        return im
    gold = (212, 175, 90)
    b = band(LW, LH, gold)
    pole_stripes(b, (LW-120, 30, LW, LH-60), [(214, 36, 48), (245, 245, 245), (30, 70, 170), (245, 245, 245)], band=34, angle=.35)
    f = fit("Cool Man", os.path.join(F, "Pacifico-Regular.ttf"), 1050, 340)
    t = text_layer(b.size, "Cool Man", f, (720, 250), gold + (255,))
    shadow(b, t, (6, 8), 6, 200)
    d = ImageDraw.Draw(b)
    d.line([(1330, 120), (1330, 470)], fill=(80, 80, 80), width=4)
    f2 = font(os.path.join(F, "BebasNeue-Regular.ttf"), 210)
    b.alpha_composite(text_layer(b.size, "BARBER", f2, (1680, 230), (255, 255, 255, 255), tracking=16))
    b.alpha_composite(text_layer(b.size, "CUTS · FADES · SHAVES", font(INTER_B, 44), (1680, 415), (170, 170, 170, 255), tracking=5))
    m = mustache(110, gold + (255,)); paste_c(b, m, (720, 470))

    lime = (190, 255, 60)
    t_ = band(RW, RH, gold)
    d = ImageDraw.Draw(t_); d.rectangle((0, 30, 110, RH-60), fill=lime)
    bl = bolt(300, lime + (255,)); paste_c(t_, bl, (330, 280))
    f = fit("TECH CORNER", os.path.join(F, "Audiowide-Regular.ttf"), 1900, 230)
    t_.alpha_composite(text_layer(t_.size, "TECH CORNER", f, (1560, 230), (255, 255, 255, 255), tracking=6))
    s2 = text_layer(t_.size, "PHONES  ·  LAPTOPS  ·  REPAIRS  ·  GAMING", font(INTER_B, 60), (1560, 420), lime + (255,), tracking=8)
    t_.alpha_composite(s2)
    return b, t_, "black-wrap", "Black Wrap — one continuous band around the corner tying both shops together"

def c4_colour():
    """Loud colour blocking for maximum street visibility."""
    b = noise(vgrad(LW, LH, (226, 38, 44), (196, 24, 34)), 4)
    d = ImageDraw.Draw(b)
    for i in range(0, LW, 90):
        d.polygon([(i, 0), (i+40, 0), (i+40-LH*.0, LH), (i, LH)], fill=(214, 32, 40))
    f = fit("COOL MAN", os.path.join(F, "Anton-Regular.ttf"), 1450, 300)
    t = text_layer(b.size, "COOL MAN", f, (LW*.40, 235), (255, 255, 255, 255), tracking=6)
    shadow(b, t, (12, 14), 0, 255)
    d.rounded_rectangle((LW*.40-420, 400, LW*.40+420, 500), radius=50, fill=(20, 20, 24))
    b.alpha_composite(text_layer(b.size, "BARBERS  ·  NO APPOINTMENT", font(INTER_BL, 46), (LW*.40, 450), (255, 255, 255, 255), tracking=4))
    d.ellipse((LW*.83-210, LH/2-210, LW*.83+210, LH/2+210), fill=(255, 255, 255))
    d.ellipse((LW*.83-180, LH/2-180, LW*.83+180, LH/2+180), fill=(20, 20, 24))
    paste_c(b, scissors(230, (255, 255, 255, 255), 16), (LW*.83, LH/2-20))
    b.alpha_composite(text_layer(b.size, "CM", font(INTER_BL, 60), (LW*.83, LH/2+130), (226, 38, 44, 255), tracking=6))

    t_ = noise(vgrad(RW, RH, (255, 214, 0), (246, 196, 0)), 4)
    d = ImageDraw.Draw(t_)
    d.polygon([(0, 0), (720, 0), (560, RH), (0, RH)], fill=(18, 18, 22))
    paste_c(t_, chip(320, (255, 214, 0, 255), 16), (300, 300))
    f = fit("TECH CORNER", os.path.join(F, "Anton-Regular.ttf"), 1850, 290)
    tl = text_layer(t_.size, "TECH CORNER", f, (1650, 240), (18, 18, 22, 255), tracking=8)
    t_.alpha_composite(tl)
    t_.alpha_composite(text_layer(t_.size, "FIXED TODAY  ·  PHONES  ·  LAPTOPS  ·  ACCESSORIES", font(INTER_BL, 52), (1650, 470), (18, 18, 22, 255), tracking=4))
    return b, t_, "colour-block", "Colour Block — loud red & yellow fascia built to be read from the main road"

# ---------- compositing onto the photo ----------
def coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp(face, quad, size, ss=2):
    q = [(x*ss, y*ss) for x, y in quad]
    w, h = face.size
    c = coeffs(q, [(0, 0), (w, 0), (w, h), (0, h)])
    big = face.transform((size[0]*ss, size[1]*ss), Image.PERSPECTIVE, c, Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    return big.resize(size, Image.LANCZOS)

def detail(photo, mask):
    L = photo.convert("L"); hp = ImageChops.subtract(L, L.filter(ImageFilter.GaussianBlur(3)), 1, 128)
    return hp

def place(photo, face, quad, light=1.0, warm=(1, 1, 1)):
    w = warp(face, quad, photo.size)
    a = np.array(w).astype(np.float32)
    a[..., :3] *= np.array(warm)*light
    # keep the stucco/compression texture so the panel sits in the photo
    hp = np.array(detail(photo, None)).astype(np.float32)-128
    a[..., :3] += hp[..., None]*0.07
    # sign-box depth: darken the panel's bottom lip a touch
    a = np.clip(a, 0, 255).astype(np.uint8)
    w = Image.fromarray(a, "RGBA")
    # soft drop shadow beneath the box onto the soffit
    sh = Image.new("RGBA", photo.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(quad[3][0], quad[3][1]), (quad[2][0], quad[2][1]), (quad[2][0], quad[2][1]+10), (quad[3][0], quad[3][1]+12)], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    out = photo.convert("RGBA"); out.alpha_composite(sh); out.alpha_composite(w)
    # thin edge lip
    d = ImageDraw.Draw(out)
    d.line([quad[3], quad[2]], fill=(20, 20, 20, 255), width=3)
    return out

def label(img, text):
    d = ImageDraw.Draw(img); f = font(INTER_B, 34)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((28, img.height-92, 28+w+44, img.height-28), radius=16, fill=(0, 0, 0, 190))
    d.text((50, img.height-84), text, font=f, fill=(255, 255, 255))
    return img

photo = Image.open(PHOTO).convert("RGB")
# crop away the phone status bar / app chrome so concepts show only the street
CROP = (0, 105, 2112, 1030)
results = []
for fn in (c1_neon, c2_heritage, c3_wrap, c4_colour):
    bf, tf, slug, title = fn()
    img = place(photo, bf, LEFT_Q, light=1.0, warm=(1.03, 1.0, .96))
    img = place(img.convert("RGB"), tf, RIGHT_Q, light=.80, warm=(.94, .97, 1.04))
    img = img.convert("RGB").crop(CROP)
    img = label(img, title)
    p = os.path.join(OUT, f"concept-{len(results)+1}-{slug}.jpg"); img.save(p, quality=90)
    # flat artwork for a sign-maker
    flat = Image.new("RGB", (RW, LH+RH+60), (240, 240, 240))
    flat.paste(bf.convert("RGB"), (0, 0)); flat.paste(tf.convert("RGB"), (0, LH+60))
    flat.save(os.path.join(OUT, f"concept-{len(results)+1}-{slug}-flat-artwork.png"))
    results.append((p, title)); print(p)

# 2x2 contact sheet
th = [Image.open(p).resize((1056, 462)) for p, _ in results]
sheet = Image.new("RGB", (2112+30, 924+30), (15, 15, 15))
for i, t in enumerate(th):
    sheet.paste(t, (10+(i % 2)*(1056+10), 10+(i//2)*(462+10)))
sheet.save(os.path.join(OUT, "all-concepts-overview.jpg"), quality=88)
