import random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

S = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(S, "fonts")

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

