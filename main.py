#!/usr/bin/env python3
"""make.fun news-image-01 entry: sums up 13 November 2026 world news in one image.

Themes of the day: Ukraine-Russia peace talks with heavy overnight strikes,
COP31 climate summit final appeal, Middle East escalation.
Drawn as a front-page editorial collage. Deterministic Pillow, no network.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024

def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def build():
    img = Image.new("RGB", (W, H), (28, 30, 38))
    d = ImageDraw.Draw(img)
    fb = font(30); fs = font(22); ft = font(46)

    # masthead
    d.rectangle([0, 0, W, 92], fill=(16, 18, 24))
    d.text((40, 26), "FRIDAY, 13 NOVEMBER 2026", font=ft, fill=(240, 240, 240))
    d.rectangle([0, 92, W, 98], fill=(200, 40, 40))

    # panel 1: peace talks (left) - two delegations, handshake, broken skyline behind
    d.rectangle([24, 122, 500, 470], fill=(58, 62, 74))
    # skyline silhouette
    for (bx, bw, bh) in [(40,30,120),(75,22,90),(100,34,150),(140,26,110),(170,30,140),(210,24,100),(240,32,130),(280,26,95),(310,30,120),(350,24,105),(380,30,135),(420,28,110)]:
        d.rectangle([bx, 330-bh, bx+bw, 330], fill=(38, 40, 50))
    # smoke columns
    for (sx, sy) in [(90, 210), (290, 190)]:
        for k in range(5):
            d.ellipse([sx-14+k*2, sy-k*26, sx+14+k*2, sy-k*26+22], fill=(70, 66, 72))
    # table + flags
    d.rectangle([60, 340, 464, 356], fill=(90, 80, 66))
    d.rectangle([96, 250, 100, 340], fill=(120, 110, 95)); d.ellipse([80, 236, 116, 262], fill=(60, 130, 200))  # blue flag
    d.rectangle([420, 250, 424, 340], fill=(120, 110, 95)); d.ellipse([404, 236, 440, 262], fill=(210, 70, 60))  # red flag
    # handshake: two arms meeting
    d.line([130, 395, 235, 380], fill=(224, 182, 150), width=26)
    d.line([390, 395, 285, 380], fill=(198, 158, 126), width=26)
    d.ellipse([225, 366, 295, 402], fill=(214, 172, 140))
    # people around table
    for px in (110, 190, 260, 340, 410):
        d.ellipse([px-18, 392, px+18, 428], fill=(70, 74, 88))
        d.ellipse([px-13, 372, px+13, 398], fill=(216, 178, 148))
    d.text((40, 434), "TALKS RESUME — STRIKES GO ON", font=fs, fill=(235, 225, 210))

    # panel 2: COP31 (right) - globe with green leaves and thermometer
    d.rectangle([524, 122, 1000, 470], fill=(40, 58, 52))
    d.ellipse([600, 150, 800, 350], fill=(70, 130, 190))
    # continents blobs
    for (bx, by, bw, bh) in [(640,180,40,26),(700,210,54,30),(650,260,44,34),(730,170,30,22),(690,300,36,20)]:
        d.ellipse([bx, by, bx+bw, by+bh], fill=(110, 180, 110))
    # red thermometer rising over globe
    d.rounded_rectangle([860, 160, 886, 420], radius=13, fill=(230, 230, 230))
    d.rounded_rectangle([866, 250, 880, 420], radius=7, fill=(220, 50, 40))
    d.ellipse([848, 400, 898, 450], fill=(220, 50, 40))
    for ty in range(180, 400, 40):
        d.line([890, ty, 912, ty], fill=(220, 220, 220), width=4)
    d.text((544, 434), "COP31: CLIMATE FINAL APPEAL", font=fs, fill=(210, 230, 215))

    # panel 3: globe with tension arc (bottom wide) - Middle East radar strike theme
    d.rectangle([24, 494, 1000, 830], fill=(52, 48, 60))
    d.ellipse([90, 540, 330, 780], fill=(64, 110, 70))   # landmass stylized
    d.ellipse([130, 590, 200, 660], fill=(200, 160, 90))
    # radar dish with blast
    d.arc([380, 560, 520, 700], 200, 340, fill=(230, 230, 230), width=10)
    d.line([450, 630, 450, 560], fill=(230, 230, 230), width=8)
    # blast star
    bx, by = 620, 640
    for a in range(8):
        ang = a * math.pi / 4
        d.line([bx, by, bx+60*math.cos(ang), by+60*math.sin(ang)], fill=(255, 170, 60), width=12)
    d.ellipse([bx-40, by-40, bx+40, by+40], fill=(255, 210, 90))
    # missile arc trail
    for t in range(12):
        mx = 380 + t*20
        my = 700 - t*14
        d.ellipse([mx-5, my-5, mx+5, my+5], fill=(240, 240, 240))
    d.text((40, 770), "MIDDLE EAST: RADAR STRIKE ESCALATES TENSIONS", font=fs, fill=(240, 220, 200))

    # ticker strip
    d.rectangle([0, 854, W, 920], fill=(200, 40, 40))
    d.text((40, 866), "13 NOV 2026 — TALKS • CLIMATE • ESCALATION", font=fb, fill=(255, 255, 255))
    d.rectangle([0, 920, W, H], fill=(16, 18, 24))
    d.text((40, 946), "WORLD NEWS IN ONE IMAGE", font=fs, fill=(140, 145, 160))

    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def main():
    img = build()
    out = os.environ.get("MF_OUT", "/output/entry.png")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print("wrote", out)

if __name__ == "__main__":
    main()
