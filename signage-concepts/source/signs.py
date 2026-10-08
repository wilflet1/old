from signlib import *

OUT = sys.argv[1]
PHOTO = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

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
