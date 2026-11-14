#!/usr/bin/env python3
"""make.fun news-image-01 entry: sums up 13 November 2026 world news in one image.

Themes of the day: Ukraine-Russia peace talks with heavy overnight strikes,
COP31 climate summit final appeal, Middle East escalation.
Front-page editorial collage drawn with a pure-stdlib framebuffer (no Pillow);
a tiny 5x7 bitmap font renders the headlines, so no system fonts are needed.
Deterministic, no network.
"""
import math
import os
import struct
import zlib

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# ---------------------------------------------------------------------------
# 5x7 bitmap font (subset: A-Z, 0-9, punctuation used by headlines)
# ---------------------------------------------------------------------------
FONT = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11110","10001","10001","10001","10001","10001","11110"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'G': ["01110","10001","10000","10111","10001","10001","01110"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'I': ["11111","00100","00100","00100","00100","00100","11111"],
    'J': ["00111","00010","00010","00010","00010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01111","10000","10000","01110","00001","00001","11110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","10001","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","11011","10001"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10001","10011","10101","11001","10001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","01110"],
    '2': ["01110","10001","00001","00110","01000","10000","11111"],
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["00110","01000","10000","11110","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","00010","01100"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    '-': ["00000","00000","00000","11111","00000","00000","00000"],
    ':': ["00000","00100","00100","00000","00100","00100","00000"],
    ',': ["00000","00000","00000","00000","00000","00100","01000"],
    '.': ["00000","00000","00000","00000","00000","00100","00100"],
    '•': ["00000","00000","00100","01110","01110","00100","00000"],
    '!': ["00100","00100","00100","00100","00100","00000","00100"],
}


class FB:
    """A tiny RGB framebuffer with primitive shape fills and PNG export."""

    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w = w
        self.h = h
        self.px = [list(bg) for _ in range(w * h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = list(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.set(x, y, c)

    def fill_ellipse(self, cx, cy, rx, ry, c):
        cx = int(cx)
        cy = int(cy)
        rx = max(1, int(rx))
        ry = max(1, int(ry))
        for y in range(cy - ry, cy + ry + 1):
            if not (0 <= y < self.h):
                continue
            dy = (y - cy) / ry
            span = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            x0 = max(0, int(cx - span))
            x1 = min(self.w, int(cx + span) + 1)
            base = y * self.w
            for x in range(x0, x1):
                self.px[base + x] = list(c)

    def thick_line(self, x0, y0, x1, y1, width, c):
        steps = max(abs(int(x1) - int(x0)), abs(int(y1) - int(y0)), 1)
        r = max(1, width // 2)
        for i in range(steps + 1):
            t = i / steps
            self.fill_ellipse(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, r, c)

    def arc(self, cx, cy, r, a0deg, a1deg, width, c, steps=None):
        steps = steps or max(int(abs(a1deg - a0deg) * r / 2), 24)
        rr = max(1, width // 2)
        a0 = math.radians(a0deg)
        a1 = math.radians(a1deg)
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.fill_ellipse(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), rr, rr, c)

    def radial_glow(self, cx, cy, r, color, strength):
        """Alpha-blended glow disc fading with distance."""
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy2 = (y - cy) * (y - cy)
            row = y * self.w
            for x in range(max(0, cx - r), min(self.w, cx + r + 1)):
                d2 = (x - cx) * (x - cx) + dy2
                if d2 > r * r:
                    continue
                a = strength * (1.0 - math.sqrt(d2) / r)
                if a <= 0:
                    continue
                base = self.px[row + x]
                self.px[row + x] = [
                    min(255, int(base[k] + (color[k] - base[k]) * a)) for k in range(3)
                ]

    def text(self, x, y, s, c, scale=3, spacing=1):
        """Draw a string with the built-in 5x7 bitmap font, scaled."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT['?'] if '?' in FONT else FONT[' '])
            for gy, rowbits in enumerate(glyph):
                for gx, bit in enumerate(rowbits):
                    if bit == '1':
                        self.fill_rect(
                            cx + gx * scale, y + gy * scale,
                            cx + gx * scale + scale, y + gy * scale + scale, c,
                        )
            cx += (5 + spacing) * scale
        return cx

    def text_width(self, s, scale=3, spacing=1):
        return len(s) * (5 + spacing) * scale

    def save_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            for (r, g, b) in self.px[y * self.w:(y + 1) * self.w]:
                raw += bytes((r, g, b))
        comp = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", comp)
        png += chunk(b"IEND", b"")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)


def build():
    fb = FB(W, H, (28, 30, 38))

    # ---- masthead ----
    fb.fill_rect(0, 0, W, 92, (16, 18, 24))
    fb.text(40, 30, "FRIDAY, 13 NOVEMBER 2026", (240, 240, 240), scale=5)
    fb.fill_rect(0, 92, W, 98, (200, 40, 40))

    # ---- panel 1: peace talks (left) ----
    fb.fill_rect(24, 122, 500, 470, (58, 62, 74))
    for (bx, bw, bh) in [(40, 30, 120), (75, 22, 90), (100, 34, 150), (140, 26, 110),
                         (170, 30, 140), (210, 24, 100), (240, 32, 130), (280, 26, 95),
                         (310, 30, 120), (350, 24, 105), (380, 30, 135), (420, 28, 110)]:
        fb.fill_rect(bx, 330 - bh, bx + bw, 330, (38, 40, 50))
    # smoke columns (soft-ish: layered tones)
    for (sx, sy) in [(90, 210), (290, 190)]:
        for k in range(5):
            col = (72, 68, 74) if k % 2 == 0 else (64, 60, 66)
            fb.fill_ellipse(sx + k, sy - k * 26, 16 + k * 2, 12, col)
    # table + flags
    fb.fill_rect(60, 340, 464, 356, (90, 80, 66))
    fb.fill_rect(96, 250, 100, 340, (120, 110, 95))
    fb.fill_ellipse(98, 249, 18, 13, (60, 130, 200))
    fb.fill_rect(420, 250, 424, 340, (120, 110, 95))
    fb.fill_ellipse(422, 249, 18, 13, (210, 70, 60))
    # handshake: two arms meeting
    fb.thick_line(130, 395, 235, 380, 26, (224, 182, 150))
    fb.thick_line(390, 395, 285, 380, 26, (198, 158, 126))
    fb.fill_ellipse(260, 384, 36, 18, (214, 172, 140))
    # people around table
    for px in (110, 190, 260, 340, 410):
        fb.fill_ellipse(px, 410, 18, 18, (70, 74, 88))
        fb.fill_ellipse(px, 385, 13, 13, (216, 178, 148))
    fb.text(40, 436, "TALKS RESUME - STRIKES GO ON", (235, 225, 210), scale=2)

    # ---- panel 2: COP31 (right) ----
    fb.fill_rect(524, 122, 1000, 470, (40, 58, 52))
    # globe with meridian shading
    fb.fill_ellipse(700, 250, 100, 100, (70, 130, 190))
    fb.fill_ellipse(676, 250, 78, 100, (86, 146, 202))
    for (bx, by, bw, bh) in [(640, 180, 40, 26), (700, 210, 54, 30), (650, 260, 44, 34),
                             (730, 170, 30, 22), (690, 300, 36, 20)]:
        fb.fill_ellipse(bx + bw // 2, by + bh // 2, bw // 2, bh // 2, (110, 180, 110))
    # thermometer (tube + bulb + mercury + ticks)
    fb.fill_rect(860, 160, 886, 420, (230, 230, 230))
    fb.fill_rect(866, 250, 880, 420, (220, 50, 40))
    fb.fill_ellipse(873, 425, 25, 25, (220, 50, 40))
    fb.fill_ellipse(873, 425, 16, 16, (240, 90, 70))
    for ty in range(180, 400, 40):
        fb.thick_line(890, ty, 912, ty, 4, (220, 220, 220))
    fb.text(544, 436, "COP31: CLIMATE FINAL APPEAL", (210, 230, 215), scale=2)

    # ---- panel 3: Middle East radar strike (bottom wide) ----
    fb.fill_rect(24, 494, 1000, 830, (52, 48, 60))
    fb.fill_ellipse(210, 660, 120, 120, (64, 110, 70))
    fb.fill_ellipse(165, 625, 35, 35, (200, 160, 90))
    # radar dish (arc) + mast
    fb.arc(450, 630, 70, 200, 340, 10, (230, 230, 230))
    fb.thick_line(450, 630, 450, 560, 8, (230, 230, 230))
    fb.fill_ellipse(450, 556, 10, 10, (255, 255, 255))
    # blast star with glow
    bx, by = 620, 640
    fb.radial_glow(bx, by, 90, (255, 170, 60), 0.45)
    for a in range(8):
        ang = a * math.pi / 4
        fb.thick_line(bx, by, bx + 62 * math.cos(ang), by + 62 * math.sin(ang), 12, (255, 170, 60))
    fb.fill_ellipse(bx, by, 40, 40, (255, 210, 90))
    fb.fill_ellipse(bx, by, 26, 26, (255, 240, 170))
    # missile arc trail (dimmer with distance)
    for t in range(12):
        mx = 380 + t * 20
        my = 700 - t * 14
        col = (240, 240, 240) if t > 6 else (200, 200, 210)
        fb.fill_ellipse(mx, my, 5, 5, col)
    fb.text(40, 772, "MIDDLE EAST: RADAR STRIKE ESCALATES TENSIONS", (240, 220, 200), scale=2)

    # ---- ticker strip ----
    fb.fill_rect(0, 854, W, 920, (200, 40, 40))
    fb.text(40, 876, "13 NOV 2026 - TALKS : CLIMATE : ESCALATION", (255, 255, 255), scale=3)
    fb.fill_rect(0, 920, W, H, (16, 18, 24))
    fb.text(40, 950, "WORLD NEWS IN ONE IMAGE", (140, 145, 160), scale=2)

    return fb


def main():
    out = os.path.join(OUT, "entry.png")
    fb = build()
    fb.save_png(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
