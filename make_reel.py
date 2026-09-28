"""Собирает вертикальный Reels (1080x1920, 30 fps) из одной фотографии подарка.

Запуск:  python3 make_reel.py  ->  output/gift_reel.mp4
Зависимости: pip install pillow numpy imageio-ffmpeg
"""
import math
import os
import random
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "gift.webp")
OUT = os.path.join(ROOT, "output", "gift_reel.mp4")

W, H, FPS = 1080, 1920, 30
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

PINK = (236, 72, 153)
PURPLE = (147, 51, 234)
PASTEL = [(255, 214, 232), (200, 230, 255), (255, 245, 180), (190, 250, 225),
          (230, 205, 255), (255, 220, 190)]

photo = Image.open(SRC).convert("RGB")
PW, PH = photo.size
ASPECT = W / H

random.seed(7)


# ---------- helpers ----------
def clamp(v, a, b):
    return max(a, min(b, v))


def ease_io(t):
    t = clamp(t, 0, 1)
    return t * t * (3 - 2 * t)


def ease_out_back(t):
    t = clamp(t, 0, 1)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def crop_frame(cx, cy, h):
    """Кадр 9:16 из фото с центром (cx, cy) и высотой окна h (субпиксельно)."""
    h = min(h, PH, PW / ASPECT)
    w = h * ASPECT
    x0 = clamp(cx - w / 2, 0, PW - w)
    y0 = clamp(cy - h / 2, 0, PH - h)
    return photo.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


# Фон для финальной сцены: размытое фото на весь экран + фото целиком по центру
_bg = photo.resize((W, int(W / PW * PH * 1.5)), Image.BICUBIC)
_bg = _bg.crop((0, (_bg.height - H) // 2, W, (_bg.height - H) // 2 + H))
BLUR_BG = Image.blend(_bg.filter(ImageFilter.GaussianBlur(40)),
                      Image.new("RGB", (W, H), (60, 10, 70)), 0.45)
FULL_W = 820
FULL = photo.resize((FULL_W, int(FULL_W / PW * PH)), Image.LANCZOS)


def rounded_card(img, radius=36, border=10):
    w, h = img.size
    card = Image.new("RGBA", (w + 2 * border, h + 2 * border), (0, 0, 0, 0))
    m = Image.new("L", card.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, *card.size), radius + border, fill=255)
    card.paste((255, 255, 255, 255), (0, 0), m)
    im = Image.new("L", img.size, 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w, h), radius, fill=255)
    card.paste(img, (border, border), im)
    return card


FULL_CARD = rounded_card(FULL)
_sh = Image.new("RGBA", (FULL_CARD.width + 120, FULL_CARD.height + 120), (0, 0, 0, 0))
_sh.paste((0, 0, 0, 150), (60, 75), FULL_CARD.split()[3])
FULL_SHADOW = _sh.filter(ImageFilter.GaussianBlur(30))


def final_scene(t):
    """Финал: фото целиком появляется с лёгким «наездом»."""
    frame = BLUR_BG.copy()
    s = lerp(0.9, 1.0, ease_out_back(t / 0.7)) * lerp(1.0, 1.03, t / 4)
    card = FULL_CARD.resize((int(FULL_CARD.width * s), int(FULL_CARD.height * s)), Image.BICUBIC)
    sh = FULL_SHADOW.resize((int(FULL_SHADOW.width * s), int(FULL_SHADOW.height * s)), Image.BICUBIC)
    cy = H // 2 - 20
    frame.paste(sh, (W // 2 - sh.width // 2, cy - sh.height // 2), sh)
    frame.paste(card, (W // 2 - card.width // 2, cy - card.height // 2), card)
    return frame


# ---------- text ----------
_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def text_badge(lines, size=64, fill=PINK, fg=(255, 255, 255), path=FONT_BOLD, pad=(44, 26)):
    f = font(path, size)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    boxes = [d.textbbox((0, 0), ln, font=f) for ln in lines]
    lh = int(size * 1.22)
    tw = max(b[2] - b[0] for b in boxes)
    bw, bh = tw + 2 * pad[0], lh * len(lines) + 2 * pad[1]
    img = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 28, 20 + bw, 28 + bh), 34, fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10)))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((20, 20, 20 + bw, 20 + bh), 34, fill=fill + (255,))
    for i, (ln, b) in enumerate(zip(lines, boxes)):
        x = 20 + (bw - (b[2] - b[0])) / 2 - b[0]
        y = 20 + pad[1] + i * lh + (lh - size) / 2 - b[1] * 0.35
        dr.text((x, y), ln, font=f, fill=fg)
    return img


def place(frame, badge, cx, cy, t_in, t, t_out=None):
    """Появление: pop + подъём; исчезновение: fade."""
    if t < t_in:
        return
    k = ease_out_back((t - t_in) / 0.45)
    a = clamp((t - t_in) / 0.25, 0, 1)
    if t_out is not None:
        a *= clamp((t_out - t) / 0.25, 0, 1)
    if a <= 0:
        return
    s = max(0.01, lerp(0.6, 1.0, k))
    b = badge.resize((max(1, int(badge.width * s)), max(1, int(badge.height * s))), Image.BICUBIC)
    if a < 1:
        b.putalpha(b.split()[3].point(lambda v: int(v * a)))
    y = cy + (1 - clamp(k, 0, 1)) * 60
    frame.paste(b, (int(cx - b.width / 2), int(y - b.height / 2)), b)


# ---------- particles ----------
def star(draw, x, y, r, col, a):
    c = col + (int(255 * a),)
    draw.polygon([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22),
                  (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)], fill=c)


SPARKS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(10, 26),
           random.uniform(0, 6.28), random.uniform(2, 4.5)) for _ in range(28)]
CONFETTI = [dict(x=random.uniform(0, W), y=random.uniform(-H, 0), vy=random.uniform(380, 700),
                 sw=random.uniform(20, 60), ph=random.uniform(0, 6.28), rot=random.uniform(2, 7),
                 col=random.choice(PASTEL + [PINK, (255, 255, 255)]), sz=random.uniform(14, 26))
            for _ in range(90)]


def overlay_particles(frame, t, confetti_t=None):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x, y, r, ph, sp in SPARKS:
        a = max(0.0, math.sin(t * sp + ph)) ** 3
        if a > 0.05:
            star(d, x, y + math.sin(t + ph) * 12, r * (0.6 + 0.4 * a), (255, 255, 255), a * 0.9)
    if confetti_t is not None and confetti_t >= 0:
        for c in CONFETTI:
            y = c["y"] + c["vy"] * confetti_t + H * 0.55
            if -40 < y < H + 40:
                x = c["x"] + math.sin(confetti_t * 2 + c["ph"]) * c["sw"]
                w = c["sz"] * abs(math.cos(confetti_t * c["rot"] + c["ph"]))
                d.rectangle((x - w / 2, y - c["sz"] / 3, x + w / 2 + 1, y + c["sz"] / 3), fill=c["col"] + (235,))
    frame.paste(ov, (0, 0), ov)


def vignette():
    y, x = np.ogrid[:H, :W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    m = np.clip((r - 0.75) / 0.7, 0, 1) * 150
    return Image.fromarray(m.astype(np.uint8), "L")


VIG = vignette()
BLACK = Image.new("RGB", (W, H), (20, 0, 25))

# ---------- scenario ----------
# (длительность, камера start (cx,cy,h), камера end, тексты)
SCENES = [
    # 1. Хук: крупно шарики, отъезд
    (3.0, (470, 330, 560), (480, 470, 900),
     [(["Этот подарок", "не купить в магазине"], 70, PINK, 0.25, 1060)]),
    # 2. Надпись и бант
    (2.6, (230, 690, 600), (360, 860, 720),
     [(["Ручная работа"], 72, PURPLE, 0.2, 330),
      (["каждая деталь — с любовью"], 50, (255, 255, 255), 0.7, 470)]),
    # 3. Сердечки, девушка, конверт
    (2.8, (620, 880, 620), (430, 1050, 760),
     [(["Под любой повод", "и любимые цвета"], 62, PINK, 0.2, 360)]),
]
FINAL_DUR = 4.2


def cam(a, b, t):
    e = ease_io(t)
    return crop_frame(lerp(a[0], b[0], e), lerp(a[1], b[1], e), lerp(a[2], b[2], e))


def build_badges():
    out = []
    for dur, a, b, texts in SCENES:
        items = []
        for lines, size, col, t_in, y in texts:
            if col == (255, 255, 255):
                bd = text_badge(lines, size, fill=(255, 255, 255), fg=PURPLE)
            else:
                bd = text_badge(lines, size, fill=col)
            items.append((bd, t_in, y))
        out.append(items)
    return out


BADGES = build_badges()
FINAL_TOP = text_badge(["Идеальный подарок", "на день рождения"], 66, fill=PINK)
FINAL_CTA = text_badge(["Хочешь такой же?", "Пиши в Директ ✉"], 60, fill=(255, 255, 255), fg=PURPLE)
FINAL_TAG = text_badge(["на заказ • любой дизайн"], 42, fill=PURPLE, pad=(34, 16))


def render():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    total = sum(s[0] for s in SCENES) + FINAL_DUR
    n = int(total * FPS)
    starts = np.cumsum([0] + [s[0] for s in SCENES])
    for i in range(n):
        T = i / FPS
        if T < starts[-1]:
            k = int(np.searchsorted(starts, T, side="right") - 1)
            dur, a, b, _ = SCENES[k]
            t = T - starts[k]
            frame = cam(a, b, t / dur)
            frame = Image.composite(BLACK, frame, VIG)
            overlay_particles(frame, T)
            for bd, t_in, y in BADGES[k]:
                place(frame, bd, W / 2, y, t_in, t, dur - 0.1)
            flash = max(0.0, 1 - t / 0.18) if k > 0 else 0.0
        else:
            t = T - starts[-1]
            frame = final_scene(t)
            overlay_particles(frame, T, confetti_t=t - 0.2)
            place(frame, FINAL_TOP, W / 2, 230, 0.35, t)
            place(frame, FINAL_TAG, W / 2, 1830, 1.1, t)
            place(frame, FINAL_CTA, W / 2, 1665, 1.6, t)
            flash = max(0.0, 1 - t / 0.25)
        if T < 0.2:  # мягкий вход из белого
            flash = max(flash, 1 - T / 0.2)
        if flash > 0:
            frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), flash * 0.85)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    print("saved", OUT, f"{total:.1f}s")


if __name__ == "__main__":
    render()
