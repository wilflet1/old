"""Shared Quick Fix Tech sign parts: straight brand logo, Same Day panel, accessories
block, service icons and the TV-free product photo. All text is measured and centred
inside its box so nothing overlaps at any size."""
from signlib import *

QBLUE = (26, 110, 232)
INK = (16, 18, 24)
NAVY = (22, 30, 52)
WHITE = (255, 255, 255)
MONT = os.path.join(F, "Montserrat.ttf")
ACCESSORIES = ["CASES & SCREEN PROTECTORS", "CHARGERS & CABLES", "HEADPHONES & EARPHONES",
               "POWER BANKS", "MEMORY CARDS & MORE"]

def mont(size, wght): return font(MONT, size, wght)

def mont_fit(lines, maxw, maxh, wght, gap=0.28):
    """Largest Montserrat size where every line fits maxw and the stacked block fits maxh."""
    lo, hi = 8, 600
    while lo < hi:
        m = (lo+hi+1)//2; f = mont(m, wght)
        ws = [f.getbbox(t)[2]-f.getbbox(t)[0] for t in lines]
        cap = f.getbbox("H")[3]-f.getbbox("H")[1]
        block = cap*len(lines) + cap*gap*(len(lines)-1)
        if max(ws) <= maxw and block <= maxh: lo = m
        else: hi = m-1
    return mont(lo, wght)

def text_block(d, lines, f, x, ytop, fill, gap=0.28, align="l", width=None):
    """Draw lines with cap-height based spacing; returns block height. ytop = top of first cap."""
    cap = f.getbbox("H")[3]-f.getbbox("H")[1]; step = cap*(1+gap)
    for i, t in enumerate(lines):
        if isinstance(fill, list): col = fill[i]
        else: col = fill
        if align == "c": d.text((x + width/2, ytop + cap + i*step), t, font=f, fill=col, anchor="ms")
        else: d.text((x, ytop + cap + i*step), t, font=f, fill=col, anchor="ls")
    return cap + step*(len(lines)-1)

def block_h(f, n, gap=0.28):
    cap = f.getbbox("H")[3]-f.getbbox("H")[1]; return cap + cap*(1+gap)*(n-1)

# ---------- images / icons ----------
def scale_fit(im, w, h):
    k = min(w/im.width, h/im.height); return im.resize((max(1, round(im.width*k)), max(1, round(im.height*k))), Image.LANCZOS)

def clean_white(im, fade=36):
    a = np.clip(np.array(im).astype(np.float32)*255/236, 0, 255); h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = np.clip(np.minimum.reduce([xx, w-1-xx, yy, h-1-yy]).astype(np.float32)/fade, 0, 1)[..., None]
    return Image.fromarray((a*k + 255*(1-k)).astype(np.uint8))

def multiply_in(img, photo, xy):
    x, y = xy; box = (x, y, x+photo.width, y+photo.height)
    img.paste(ImageChops.multiply(img.crop(box).convert("RGB"), photo.convert("RGB")).convert("RGBA"), box[:2])

def glyph(fontfile, ch, size=400, axes=None):
    f = ImageFont.truetype(os.path.join(F, fontfile), size)
    if axes: f.set_variation_by_axes(axes)
    m = Image.new("L", (size*2, size*2), 0); ImageDraw.Draw(m).text((size//2, size//2), ch, font=f, fill=255)
    return m.crop(m.getbbox())

def crisp(mask, h):
    m = mask.resize((max(1, round(mask.width*h/mask.height)), h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2*h/150))
    a = np.clip((np.array(m).astype(np.float32)/255 - 0.38)/0.24, 0, 1)
    return Image.fromarray((a*255).astype(np.uint8), "L")

def tint(mask, col=QBLUE):
    im = Image.new("RGBA", mask.size, col + (0,)); im.putalpha(mask); return im

class Parts:
    def __init__(self, logo_dir, flyer_src):
        L = lambda n: Image.open(os.path.join(logo_dir, n))
        self.qf = L("quick-fix-tech-logo.png")
        self.mark = self.qf.crop((0, 0, 192, self.qf.height))
        no_tv = L("quick-fix-tech-flyer-no-tv.jpg").convert("RGB")
        pr = no_tv.crop((752, 252, 1598, 604))
        ImageDraw.Draw(pr).rectangle((0, 572-252, 935-752, 604-252), fill=(255, 255, 255))
        self.products = clean_white(pr)
        orig = np.array(Image.open(flyer_src).convert("RGB")).astype(np.float32)
        def fly(x0, x1, y0=561, y1=636):
            c = orig[y0:y1, x0-4:x1+4]
            return Image.fromarray((np.clip((c[..., 2]-c[..., 0]-40)/80, 0, 1)*255).astype(np.uint8), "L")
        # (label, mask, relative size) — phone/speaker crops carry less padding, so they run a touch taller
        self.icons = [
            ("PHONE", fly(60, 101), 1.15), ("HEADPHONE", glyph("MaterialSymbolsOutlined.ttf", "", axes=[0, 0, 48, 600]), 0.95),
            ("SPEAKER", fly(330, 371), 1.12), ("LAPTOP", fly(442, 520), 0.95),
            ("PS5", glyph("fa-brands-400.ttf", ""), 0.95), ("XBOX", fly(717, 779), 1.0)]
        self.clock = glyph("MaterialSymbolsOutlined.ttf", "", axes=[0, 0, 48, 600])

    def brand(self, img, box, mark_h=None):
        """Straight logo: original mark + level brand name + blue rule, fitted into box."""
        x0, y0, x1, y1 = box; d = ImageDraw.Draw(img); h = y1 - y0
        mh = mark_h or h
        mk = self.mark.resize((round(self.mark.width*mh/self.mark.height), mh), Image.LANCZOS)
        img.alpha_composite(mk, (x0, int(y0 + (h-mh)/2)))
        bx0 = x0 + mk.width + int(mh*0.11)
        f = mont_fit(["QUICK FIX TECH"], x1 - bx0, h*0.42, 900, 0)
        cap = f.getbbox("H")[3]-f.getbbox("H")[1]
        rule = max(8, int(cap*0.16)); block = cap + cap*0.38 + rule
        top = y0 + (h - block)/2; x = bx0
        for t, col in (("QUICK ", INK), ("FIX ", QBLUE), ("TECH", INK)):
            d.text((x, top + cap), t, font=f, fill=col, anchor="ls"); x += d.textlength(t, font=f)
        d.rounded_rectangle((bx0 + 3, top + cap*1.38, x, top + cap*1.38 + rule), radius=rule//2, fill=QBLUE)

    def same_day(self, img, box, sub=True):
        x0, y0, x1, y1 = box; d = ImageDraw.Draw(img); h = y1 - y0; pad = int(h*0.14)
        d.rounded_rectangle(box, radius=int(h*0.07), fill=QBLUE)
        ck = tint(crisp(self.clock, int(h*0.58)), WHITE)
        img.alpha_composite(ck, (x0 + pad, int(y0 + (h - ck.height)/2)))
        tx = x0 + pad + ck.width + int(pad*0.7); tw = x1 - int(pad*0.8) - tx
        wide = (x1 - x0) / h > 3
        head = ["SAME DAY REPAIRS"] if wide else ["SAME DAY", "REPAIRS"]
        fh = mont_fit(head, tw, (h - 2*pad)*(0.42 if wide else 0.68), 900)
        fs = mont_fit(["IN TODAY · BACK TODAY"], tw*(0.8 if wide else 1), (h - 2*pad)*(0.16 if wide else 0.11), 600, 0) if sub else None
        hb = block_h(fh, len(head)); hs = block_h(fs, 1) if sub else 0; gap = int(h*(0.12 if wide else 0.09)) if sub else 0
        top = y0 + (h - (hb + gap + hs))/2
        text_block(d, head, fh, tx, top, WHITE)
        if sub: text_block(d, ["IN TODAY · BACK TODAY"], fs, tx, top + hb + gap, (205, 225, 255))

    def accessories(self, img, box, head_h, cols=1, item_h=None):
        """Blue heading box + ticked list, laid out inside box."""
        x0, y0, x1, y1 = box; d = ImageDraw.Draw(img); w = x1 - x0
        hb = (x0, y0, x1, y0 + head_h); pad = int(head_h*0.16)
        d.rounded_rectangle(hb, radius=int(head_h*0.12), fill=QBLUE)
        two = head_h > 110
        lines = ["CELL PHONE", "ACCESSORIES"] if two else ["CELL PHONE ACCESSORIES"]
        fh = mont_fit(lines, w - 2*pad - 60, (head_h - 2*pad)*(0.82 if two else 0.62), 800)
        text_block(d, lines, fh, x0 + pad + 24, y0 + (head_h - block_h(fh, len(lines)))/2, WHITE)
        ly0 = y0 + head_h + int(head_h*0.18); rows = -(-len(ACCESSORIES)//cols)
        row_h = item_h or (y1 - ly0)/rows; colw = w/cols
        fl = mont_fit([max(ACCESSORIES, key=len)], colw - row_h*0.9 - 20, row_h*0.42, 600, 0)
        for i, t in enumerate(ACCESSORIES):
            c, r = divmod(i, rows) if cols > 1 else (0, i)
            cx = x0 + c*colw; cy = ly0 + r*row_h; s = row_h*0.5
            d.line([(cx+4, cy+s*0.55), (cx+4+s*0.38, cy+s*0.92), (cx+4+s, cy+s*0.1)], fill=QBLUE, width=max(4, int(s*0.18)), joint="curve")
            cap = fl.getbbox("H")[3]-fl.getbbox("H")[1]
            d.text((cx + s + 24, cy + s*0.5 + cap/2), t, font=fl, fill=NAVY, anchor="ls")

    def icon_row(self, img, box, labels=True, icon_h=None, label_w=0.86, label_h=0.12, label_gap=0.08):
        x0, y0, x1, y1 = box; d = ImageDraw.Draw(img); n = len(self.icons); tile = (x1-x0)/n; h = y1 - y0
        ih = icon_h or int(h*(0.5 if labels else 0.8))
        fl = mont_fit(["HEADPHONE"], tile*label_w, h*label_h, 700, 0) if labels else None
        for k, (name, m, rel) in enumerate(self.icons):
            cx = x0 + tile*k + tile/2
            ic = tint(crisp(m, int(ih*rel)))
            iy = y0 + (ih*1.15 - ic.height)/2 if labels else y0 + (h - ic.height)/2
            img.alpha_composite(ic, (int(cx - ic.width/2), int(iy)))
            if labels:
                text_block(d, [name, "REPAIRS"], fl, cx - tile/2, y0 + ih*1.15 + h*label_gap, INK, gap=0.5, align="c", width=tile)
            if k: d.line([(x0 + tile*k, y0 + h*0.06), (x0 + tile*k, y1 - h*0.06)], fill=QBLUE, width=max(3, int(h*0.012)))
