"""Quick Fix Tech flyer compacted into a landscape sign.

Changes from the flyer: no TV anywhere, the "SPEAKER | LAPTOP | PS5 | XBOX" and
"AND ALL TYPES OF..." lines removed, icon row = phone, headphones, speaker, laptop,
PS logo, Xbox, accessory photos dropped, accessories checklist kept, logo set straight
without the tagline, flat Same Day panel.

usage: python3 sign_compact.py <out_dir> <logo_dir> <quick-fix-flyer.jpg>
"""
from qfparts import *

OUT, LOGOS, FLYER_SRC = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
W, H = 3200, 1100
P = Parts(LOGOS, FLYER_SRC)

sign = noise(vgrad(W, H, (255, 255, 255), (246, 248, 252)), 2)
d = ImageDraw.Draw(sign)

P.brand(sign, (50, 30, 1340, 290))
fhl = mont_fit(["WE REPAIR", "CELL PHONES"], 1150, 320, 900, 0.3)
text_block(d, ["WE REPAIR", "CELL PHONES"], fhl, 66, 345, [INK, QBLUE], gap=0.3)

pr = scale_fit(P.products, 1040, 560); multiply_in(sign, pr, (1370, 655 - pr.height))

P.same_day(sign, (2440, 40, 3150, 360))
P.accessories(sign, (2440, 400, 3150, 1050), head_h=180)

d.line([(60, 696), (2380, 696)], fill=QBLUE, width=6)
P.icon_row(sign, (60, 712, 2380, 1050))
d.rectangle((0, H - 22, W, H), fill=QBLUE)

out = os.path.join(OUT, "quick-fix-tech-compact-sign.png")
sign.convert("RGB").save(out); sign.convert("RGB").save(out.replace(".png", ".jpg"), quality=93)
print(out)
