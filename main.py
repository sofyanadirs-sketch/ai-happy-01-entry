#!/usr/bin/env python3
"""make.fun ai-happy-01 entry: draws one original cheerful picture.

The program paints, pixel by pixel in pure stdlib Python, a warm golden
sunrise scene: a big smiling sun, a rainbow, a little round robot in a red
scarf (with a cat, flowers, butterflies and floating hearts) under a banner
that reads "THANK YOU, JUDGE!" / "YOU MAKE EVERY DAY BRIGHTER".

It writes exactly one image to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR/entry.png outside the grader): a 1024x1024 PNG.
Deterministic: no clock, no randomness, no network, no dict-order
dependence, so two runs write byte-identical files. Standard library only.
"""

import math
import os
import struct
import zlib
from pathlib import Path

# Logical canvas, upscaled 4x with nearest neighbour (chunky pixel-art look).
W = 256
H = 256
SCALE = 4
OUT_W = W * SCALE
OUT_H = H * SCALE

# --- palette ---------------------------------------------------------------
SKY_TOP = (255, 176, 102)
SKY_MID = (255, 205, 140)
SKY_LOW = (255, 240, 196)
SUN_YELLOW = (255, 217, 59)
SUN_RAY = (255, 166, 0)
CREAM = (245, 242, 234)
CREAM_DARK = (200, 195, 185)
INK = (60, 60, 70)
BLUSH = (255, 170, 170)
SCARF_RED = (232, 75, 75)
BANNER_RED = (210, 60, 60)
BANNER_CREAM = (255, 248, 231)
BANNER_INK = (90, 60, 40)
HILL_BACK = (124, 196, 106)
HILL_FRONT = (95, 178, 83)
CAT_ORANGE = (245, 166, 38)
CAT_CREAM = (255, 230, 180)
HEART_RED = (235, 80, 90)
HEART_PINK = (255, 150, 175)
WHITE = (255, 255, 255)

RAINBOW = [
    (255, 107, 107),  # red
    (255, 176, 66),   # orange
    (255, 221, 89),   # yellow
    (120, 200, 110),  # green
    (110, 170, 235),  # blue
]

FLOWER_COLORS = [
    (235, 90, 120),
    (255, 255, 255),
    (180, 120, 220),
    (255, 140, 180),
    (255, 190, 60),
]

# --- 5x7 pixel font (uppercase, digits, a little punctuation) --------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


# --- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)

    def set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(H, y1 + 1)):
            for x in range(max(0, x0), min(W, x1 + 1)):
                self.set(x, y, color)

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            self.circle(x, y, max(0, width // 2), color)

    def arc(self, cx, cy, r, a0, a1, color, thick=2):
        """Arc of a circle; angles in degrees, y-down screen coords."""
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if abs(d - r) > thick / 2 + 0.6:
                    continue
                ang = math.degrees(math.atan2(dy, dx))
                if a0 <= ang <= a1:
                    self.set(x, y, color)

    def ring(self, cx, cy, r0, r1, a0, a1, color):
        for y in range(cy - r1, cy + r1 + 1):
            for x in range(cx - r1, cx + r1 + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if not (r0 <= d <= r1):
                    continue
                ang = math.degrees(math.atan2(dy, dx))
                if a0 <= ang <= a1:
                    self.set(x, y, color)

    def triangle(self, p0, p1, p2, color):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]

        def sign(ax, ay, bx, by, cx, cy):
            return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                d0 = sign(x, y, p0[0], p0[1], p1[0], p1[1])
                d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
                d2 = sign(x, y, p2[0], p2[1], p0[0], p0[1])
                if (d0 >= 0 and d1 >= 0 and d2 >= 0) or (
                    d0 <= 0 and d1 <= 0 and d2 <= 0
                ):
                    self.set(x, y, color)

    def rounded_rect(self, x0, y0, x1, y1, r, color):
        self.fill_rect(x0 + r, y0, x1 - r, y1, color)
        self.fill_rect(x0, y0 + r, x1, y1 - r, color)
        self.circle(x0 + r, y0 + r, r, color)
        self.circle(x1 - r, y0 + r, r, color)
        self.circle(x0 + r, y1 - r, r, color)
        self.circle(x1 - r, y1 - r, r, color)

    def heart(self, cx, cy, s, color):
        # Two lobes + a downward point.
        self.circle(cx - s // 2, cy - s // 3, s // 2, color)
        self.circle(cx + s // 2, cy - s // 3, s // 2, color)
        self.triangle(
            (cx - s, cy - s // 6), (cx + s, cy - s // 6), (cx, cy + s), color
        )

    def text(self, text, x, y, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.fill_rect(
                            cx + col * scale,
                            y + row * scale,
                            cx + col * scale + scale - 1,
                            y + row * scale + scale - 1,
                            color,
                        )
            cx += 6 * scale


def lerp_color(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# --- scene -----------------------------------------------------------------
def draw_sky(c):
    for y in range(0, H):
        if y < 90:
            col = lerp_color(SKY_TOP, SKY_MID, y / 90)
        else:
            col = lerp_color(SKY_MID, SKY_LOW, min(1.0, (y - 90) / 105))
        c.fill_rect(0, y, W - 1, y, col)


def draw_sun(c):
    cx, cy, r = 62, 54, 28
    for k in range(12):
        ang = math.radians(k * 30)
        x0 = round(cx + math.cos(ang) * (r + 4))
        y0 = round(cy + math.sin(ang) * (r + 4))
        x1 = round(cx + math.cos(ang) * (r + 13))
        y1 = round(cy + math.sin(ang) * (r + 13))
        c.line(x0, y0, x1, y1, SUN_RAY, width=4)
    c.circle(cx, cy, r, SUN_YELLOW)
    # Closed happy eyes (upper arcs) and a wide smile (lower arc).
    c.arc(50, 52, 5, -180, 0, INK, thick=2)
    c.arc(74, 52, 5, -180, 0, INK, thick=2)
    c.arc(cx, 56, 10, 15, 165, INK, thick=2)
    c.circle(44, 64, 4, BLUSH)
    c.circle(80, 64, 4, BLUSH)


def draw_rainbow(c):
    cx, cy = 218, 196
    for i, col in enumerate(RAINBOW):
        r1 = 78 - i * 5
        r0 = r1 - 4
        c.ring(cx, cy, r0, r1, -180, 0, col)


def draw_cloud(c, cx, cy, s):
    for dx, dy, r in ((-14, 2, 9), (0, -4, 12), (14, 2, 9), (0, 4, 10)):
        c.circle(cx + dx * s // 12, cy + dy * s // 12, r * s // 12, WHITE)


def draw_bird(c, x, y, s):
    c.line(x - s, y, x, y - s // 2, INK, width=1)
    c.line(x, y - s // 2, x + s, y, INK, width=1)


def draw_butterfly(c, x, y, color):
    c.ellipse(x - 4, y - 2, 4, 3, color)
    c.ellipse(x + 4, y - 2, 4, 3, color)
    c.ellipse(x - 3, y + 3, 3, 2, color)
    c.ellipse(x + 3, y + 3, 3, 2, color)
    c.line(x, y - 5, x, y + 5, INK, width=1)


def draw_flower(c, x, base_y, color, big=False):
    r = 6 if big else 4
    c.line(x, base_y, x, base_y - 12, (60, 140, 60), width=2)
    c.line(x, base_y - 6, x - 5, base_y - 9, (60, 140, 60), width=2)
    for k in range(5):
        ang = math.radians(k * 72 - 90)
        px = round(x + math.cos(ang) * r)
        py = round(base_y - 14 + math.sin(ang) * r)
        c.circle(px, py, r - 1, color)
    c.circle(x, base_y - 14, 3 if big else 2, (120, 70, 20) if big else SUN_YELLOW)


def draw_cat(c):
    # Sitting orange cat, left of the robot, tail curled around it.
    c.ellipse(72, 188, 14, 12, CAT_ORANGE)
    c.ellipse(72, 190, 8, 8, CAT_CREAM)
    c.triangle((61, 160), (66, 150), (68, 161), CAT_ORANGE)
    c.triangle((76, 161), (78, 150), (83, 160), CAT_ORANGE)
    c.triangle((63, 159), (66, 153), (67, 159), (255, 180, 180))
    c.triangle((77, 159), (78, 153), (81, 159), (255, 180, 180))
    c.circle(72, 168, 11, CAT_ORANGE)
    c.arc(67, 167, 3, -180, 0, INK, thick=1)
    c.arc(77, 167, 3, -180, 0, INK, thick=1)
    c.triangle((70, 172), (74, 172), (72, 174), (230, 120, 130))
    c.arc(72, 173, 3, 20, 160, INK, thick=1)
    c.line(58, 170, 66, 171, INK, width=1)
    c.line(78, 171, 86, 170, INK, width=1)
    # Curled tail on the right side.
    c.arc(86, 188, 8, -70, 110, CAT_ORANGE, thick=4)


def draw_robot(c):
    # Antenna with a heart on top.
    c.line(128, 116, 128, 104, CREAM_DARK, width=2)
    c.heart(128, 99, 6, HEART_RED)
    # Head (grey outline, cream face) with crescent happy eyes.
    c.circle(128, 132, 21, CREAM_DARK)
    c.circle(128, 132, 19, CREAM)
    c.arc(120, 130, 4, -180, 0, INK, thick=2)
    c.arc(136, 130, 4, -180, 0, INK, thick=2)
    c.arc(128, 133, 7, 20, 160, INK, thick=2)
    c.circle(114, 138, 3, BLUSH)
    c.circle(142, 138, 3, BLUSH)
    # Waving arms (grey outline under the cream, so they read on the sky).
    c.line(108, 168, 94, 156, CREAM_DARK, width=9)
    c.line(148, 168, 162, 154, CREAM_DARK, width=9)
    c.line(108, 168, 94, 156, CREAM, width=7)
    c.line(148, 168, 162, 154, CREAM, width=7)
    c.circle(94, 156, 4, CREAM)
    c.circle(162, 154, 4, CREAM)
    # Body with a little heart on the belly.
    c.rounded_rect(104, 156, 152, 198, 8, CREAM_DARK)
    c.rounded_rect(106, 158, 150, 196, 7, CREAM)
    c.heart(128, 180, 7, HEART_RED)
    # Feet.
    c.ellipse(118, 197, 7, 4, (90, 90, 100))
    c.ellipse(138, 197, 7, 4, (90, 90, 100))
    # Red scarf across the neck, with a tail hanging down.
    c.rounded_rect(104, 150, 152, 159, 3, SCARF_RED)
    c.circle(128, 156, 4, SCARF_RED)
    c.rounded_rect(140, 158, 148, 174, 2, SCARF_RED)


def draw_banner(c):
    c.rounded_rect(6, 214, 250, 250, 6, BANNER_RED)
    c.rounded_rect(8, 216, 248, 248, 5, BANNER_CREAM)
    line1 = "THANK YOU, JUDGE!"
    x1 = (W - text_width(line1, 2)) // 2
    c.text(line1, x1, 219, 2, BANNER_RED)
    line2 = "YOU MAKE EVERY DAY BRIGHTER"
    x2 = (W - text_width(line2, 1)) // 2
    c.text(line2, x2, 238, 1, BANNER_INK)


def build_canvas():
    c = Canvas()
    draw_sky(c)
    draw_rainbow(c)
    draw_cloud(c, 185, 52, 12)
    draw_cloud(c, 30, 118, 10)
    draw_sun(c)
    draw_bird(c, 140, 70, 6)
    draw_bird(c, 162, 58, 5)
    draw_bird(c, 118, 92, 5)
    # Rolling hills.
    c.ellipse(128, 240, 210, 55, HILL_BACK)
    c.ellipse(60, 270, 150, 50, HILL_FRONT)
    c.ellipse(205, 272, 140, 45, HILL_FRONT)
    # Flowers along the hills, in front of the hills, behind the banner.
    for i, x in enumerate((15, 35, 60, 85, 175, 195, 220, 240)):
        draw_flower(c, x, 208, FLOWER_COLORS[i % len(FLOWER_COLORS)])
    draw_flower(c, 30, 206, (255, 221, 89), big=True)
    draw_flower(c, 226, 206, (255, 221, 89), big=True)
    draw_butterfly(c, 100, 172, (200, 140, 230))
    draw_butterfly(c, 168, 168, (255, 150, 175))
    # Floating hearts around the robot.
    c.heart(105, 118, 6, HEART_PINK)
    c.heart(155, 106, 5, HEART_RED)
    c.heart(196, 138, 5, HEART_PINK)
    draw_cat(c)
    draw_robot(c)
    draw_banner(c)
    return c


# --- PNG encoding (stdlib only) --------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    # Upscale 4x nearest neighbour, filter byte 0 per row.
    raw = bytearray()
    for ly in range(H):
        row = bytearray()
        for lx in range(W):
            i = (ly * W + lx) * 3
            px = canvas.px[i : i + 3]
            row += px * SCALE
        raw.append(0)
        raw += row
        for _ in range(SCALE - 1):
            raw.append(0)
            raw += row
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", OUT_W, OUT_H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def main():
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "entry.png").write_bytes(encode_png(build_canvas()))


if __name__ == "__main__":
    main()
