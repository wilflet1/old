"""Isolate the Cool Man + Quick Fix Tech logos and make a flyer without the TV-repair claim.

usage: python3 logos.py <cool-man.jpg> <quick-fix-flyer.jpg> <out_dir>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CM_SRC, QF_SRC, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

def smooth(x, lo, hi):
    t = np.clip((x-lo)/(hi-lo), 0, 1); return t*t*(3-2*t)

# ---------------- Cool Man: silver tools + key off the dark background ----------------
cm = np.array(Image.open(CM_SRC).convert("RGB")).astype(np.float32)
r, g, b = cm[..., 0], cm[..., 1], cm[..., 2]
H, W = r.shape
yy, xx = np.mgrid[0:H, 0:W]
# razors + pole live above the COOL MAN lettering; the red rule under it stays as the brand accent
tools = (yy < 192) & (xx > 300) & (xx < 720)
redness = smooth(r - np.maximum(g, b), 25, 70) * tools
v = np.clip(r*0.88 + 18, 0, 255)                     # red channel carries the chrome shading
silver = np.stack([v*0.97, v*0.99, v*1.03], -1)         # slightly cool steel
cm = cm*(1-redness[..., None]) + np.clip(silver, 0, 255)*redness[..., None]

# alpha from brightness above the near-black backdrop; unpremultiply over black
mx = cm.max(2)
alpha = smooth(mx, 44, 110)
# only keep the logo's own elements (kills room-light specks in the backdrop)
keep = np.zeros((H, W), bool)
for x0, y0, x1, y1 in [(330, 35, 700, 192), (285, 120, 370, 150), (630, 120, 715, 150),   # tools, EST./2019
                       (100, 195, 925, 303), (110, 303, 915, 322),                        # COOL MAN, red rule
                       (225, 322, 840, 370), (240, 370, 780, 414)]:                       # BARBER SHOP, EST. 2019
    keep[y0:y1, x0:x1] = True
alpha *= np.array(Image.fromarray(keep.astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)/255
rgb = np.where(alpha[..., None] > 0.02, cm/np.maximum(alpha[..., None], 0.02), 0)
rgba = np.dstack([np.clip(rgb, 0, 255), alpha*255]).astype(np.uint8)
logo = Image.fromarray(rgba, "RGBA").crop((96, 28, 930, 415))   # drops the "STYLE" sign + room lights
logo.save(os.path.join(OUT, "cool-man-logo-silver.png"))
on_black = Image.new("RGBA", logo.size, (0, 0, 0, 255)); on_black.alpha_composite(logo)
on_black.convert("RGB").save(os.path.join(OUT, "cool-man-logo-silver-on-black.png"))

# ---------------- Quick Fix Tech: key off the white background ----------------
qf_img = Image.open(QF_SRC).convert("RGB")
qf = np.array(qf_img).astype(np.float32)

def unmatte_white(arr):
    a = np.clip((255 - arr.min(2)) / 255 * 1.15, 0, 1)
    a = np.clip((a-0.06)/0.94, 0, 1)
    rgb = (arr - (1-a[..., None])*255) / np.maximum(a[..., None], 0.02)
    return np.dstack([np.clip(rgb, 0, 255), a*255]).astype(np.uint8)

ql = unmatte_white(qf[22:224, 10:930])
ql[200-22:, 740-10:, 3] = 0                                        # corner of the TV peeking into the crop
qlogo = Image.fromarray(ql, "RGBA")
qlogo.save(os.path.join(OUT, "quick-fix-tech-logo.png"))
# white version for dark panels: neutral (black/grey) ink -> white, blue kept
q = np.array(qlogo).astype(np.float32)
sat = q[..., :3].max(2) - q[..., :3].min(2)
neutral = (1 - smooth(sat, 40, 90))[..., None]
q[..., :3] = q[..., :3]*(1-neutral) + 255*neutral
Image.fromarray(q.astype(np.uint8), "RGBA").save(os.path.join(OUT, "quick-fix-tech-logo-white.png"))

bsrc = qf[0:250, 1060:1600]
bd = unmatte_white(bsrc)
# the lettering is white-on-blue: fill the brush shape solid so white text isn't keyed out
blue = Image.fromarray(((bsrc[..., 2]-bsrc[..., 0] > 80)*255).astype(np.uint8))
# letters = non-blue pixels not reachable from the border (fully enclosed by the brush)
reach = blue.copy(); hh, ww = bsrc.shape[:2]
for x in range(ww):
    for y in (0, hh-1):
        if reach.getpixel((x, y)) == 0: ImageDraw.floodfill(reach, (x, y), 128)
for y in range(hh):
    for x in (0, ww-1):
        if reach.getpixel((x, y)) == 0: ImageDraw.floodfill(reach, (x, y), 128)
holes = Image.fromarray(((np.array(reach) == 0)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
hull = np.array(holes.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)/255
bd[..., :3] = (bd[..., :3]*(1-hull[..., None]) + bsrc*hull[..., None]).astype(np.uint8)
bd[..., 3] = np.maximum(bd[..., 3], hull*255).astype(np.uint8)
bd[165:, :1128-1060, 3] = 0                                        # TV corner
badge = Image.fromarray(bd, "RGBA")
badge.save(os.path.join(OUT, "quick-fix-same-day-badge.png"))

# ---------------- flyer without the TV claim ----------------
fl = qf.copy()
# 1) headline: "CELL PHONES & TV" -> "CELL PHONES"
fl[308:400, 563:752] = fl[308:400, 752:756].mean((0, 1))

# 2) remove the TV from the product shot (keep phones + laptop in front of it)
tvm = Image.new("L", (1600, 900), 0); d = ImageDraw.Draw(tvm)
d.polygon([(754, 228), (1123, 174), (1123, 472), (754, 494)], fill=255)
d.rectangle((902, 462, 968, 522), fill=255)                       # stand
fg = Image.new("L", (1600, 900), 0); d = ImageDraw.Draw(fg)
d.polygon([(757, 402), (761, 396), (871, 395), (876, 400), (876, 406), (903, 406), (908, 412),
           (908, 570), (757, 570)], fill=255)                     # phones
d.polygon([(972, 408), (976, 404), (1166, 396), (1170, 400), (1170, 580), (904, 572), (901, 548), (958, 532)], fill=255)  # laptop
m = np.array(tvm).astype(np.float32)/255 * (1 - np.array(fg.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)/255)
m = np.array(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32)/255
left = fl[:, 748:752].mean(1)                                     # backdrop just left of the TV
right = fl[:, 1126:1132].mean(1)                                  # gap between TV and PS5
bg = np.zeros_like(fl)
t = np.clip((np.arange(1600) - 754) / (1123-754), 0, 1)[None, :, None]
rows_ok = (np.arange(900) < 392)[:, None, None]                   # below that, the laptop blocks the right sample
bg[:] = np.where(rows_ok, left[:, None, :]*(1-t) + right[:, None, :]*t, left[:, None, :])
fl = fl*(1-m[..., None]) + bg*m[..., None]

# 3) drop the "TV REPAIRS" tile and close the gap in the icon row
gap = 285 - 146
src = fl.copy()
fl[571:693, 147:1100-gap] = src[571:693, 147+gap:1100]
fl[557:571, 147:746-gap] = src[557:571, 147+gap:746]
fl[571:693, 1100-gap:1100] = src[571:693, 1100:1101]              # backdrop fill for the freed slot
Image.fromarray(np.clip(fl, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "quick-fix-tech-flyer-no-tv.jpg"), quality=94)
print("done")
