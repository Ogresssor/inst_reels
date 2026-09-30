"""Продающие Reels по сценариям из PROMPTS.md: робот-дачник, новогоднее колесо, панно и ролик-витрина.

    python3 crafts.py                    # все четыре
    python3 crafts.py robot showcase     # выборочно

Результат: output/reel_robot.mp4, reel_wheel.mp4, reel_panno.mp4, reel_showcase.mp4
Текст держится в безопасной зоне Instagram/VK: не выше 250 px, не ниже 1570 px, не правее 930 px.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_reel as base
import music
import variants as v
from make_reel import H, PINK, PURPLE, W, clamp, ease_io, ease_out_back, lerp, place, text_badge
from music import SR, bass, bell, clap, crash, hat, hp_noise, hz, kick, pad, riser
from variants import INK, YELLOW, Mix, filt, paste_center, saw, scaled, with_alpha

ASSETS = os.path.join(base.ROOT, "assets")
ASPECT = W / H
TX = 490  # центр текста по X: справа кнопки лайков
random.seed(21)
rng = np.random.default_rng(21)


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


IMG = {k: load(f"{k}.jpg") for k in ("robot_1", "robot_2", "wheel_1", "wheel_2", "birthday_board")}


# =====================================================================
# Камера, карточки, эффекты
# =====================================================================
def crop(img, cx, cy, h):
    pw, ph = img.size
    h = min(h, ph, pw / ASPECT)
    w = h * ASPECT
    x0 = clamp(cx - w / 2, 0, pw - w)
    y0 = clamp(cy - h / 2, 0, ph - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def blur_bg(img, tint=(40, 20, 50), k=0.45):
    pw, ph = img.size
    s = max(W / pw, H / ph) * 1.2
    b = img.resize((int(pw * s), int(ph * s)), Image.BICUBIC)
    b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
    return Image.blend(b.filter(ImageFilter.GaussianBlur(40)), Image.new("RGB", (W, H), tint), k)


def card(img, width, radius=30, border=10):
    im = img.resize((width, int(width * img.height / img.width)), Image.LANCZOS)
    c = base.rounded_card(im, radius, border)
    sh = Image.new("RGBA", (c.width + 120, c.height + 120), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (60, 75), c.split()[3])
    return c, sh.filter(ImageFilter.GaussianBlur(30))


def draw_card(frame, cd, cx, cy, s=1.0, ang=0.0):
    c, sh = cd
    c, sh = scaled(c, s), scaled(sh, s)
    if abs(ang) > 0.05:
        c = c.rotate(ang, Image.BICUBIC, expand=True)
        sh = sh.rotate(ang, Image.BICUBIC, expand=True)
    paste_center(frame, sh, cx, cy + 15)
    paste_center(frame, c, cx, cy)


class Twinkle:
    """Мерцание гирлянды: яркие точки исходного фото разбиты на группы, каждая «дышит» в своём ритме."""

    def __init__(self, img, thr=235, groups=5):
        a = np.asarray(img).astype(np.float32)
        lum = a.mean(axis=2)
        m = (lum > thr).astype(np.float32)
        lab = rng.integers(0, groups, size=(img.height // 24 + 1, img.width // 24 + 1))
        g = np.kron(lab, np.ones((24, 24)))[: img.height, : img.width]
        self.base = a
        self.masks = []
        for k in range(groups):
            mk = Image.fromarray((m * (g == k) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))
            self.masks.append(np.asarray(mk).astype(np.float32)[..., None] / 255 * np.array([255, 190, 90]) * 2.2)
        self.ph = rng.uniform(0, 6.28, groups)
        self.sp = rng.uniform(2.5, 5.0, groups)

    def at(self, t, boost=1.0):
        out = self.base.copy()
        for mk, ph, sp in zip(self.masks, self.ph, self.sp):
            out += mk * (0.35 + 0.65 * max(0.0, math.sin(t * sp + ph))) * boost
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


SNOW = [(random.uniform(0, W), random.uniform(0, H), random.uniform(3, 9), random.uniform(60, 160),
         random.uniform(0, 6.28)) for _ in range(140)]


def snow(frame, t, alpha=1.0):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x, y, r, vy, ph in SNOW:
        yy = (y + vy * t) % (H + 20) - 10
        xx = x + math.sin(t * 0.8 + ph) * 25
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, int(200 * alpha)))
    frame.paste(ov, (0, 0), ov)


def flash(frame, k, col=(255, 255, 255), amt=0.7):
    if k <= 0:
        return frame
    return Image.blend(frame, Image.new("RGB", (W, H), col), clamp(k, 0, 1) * amt)


def badge(lines, size, style):
    fill, fg = style
    return text_badge(lines, size, fill=fill, fg=fg)


def show_texts(frame, texts, t, dur):
    for img, t_in, y in texts:
        place(frame, img, TX, y, t_in, t, dur - 0.08)


# =====================================================================
# Музыка
# =====================================================================
def ks_pluck(f, dur, bright=0.6, decay=0.996):
    """Karplus-Strong: струна (укулеле / пиццикато)."""
    n = int((dur + 0.3) * SR)
    p = max(2, int(SR / f))
    y = np.zeros(n + p + 1)
    y[: p + 1] = filt(rng.uniform(-1, 1, p + 1), 2000 + 6000 * bright) if p > 64 else rng.uniform(-1, 1, p + 1)
    i = p + 1
    while i < len(y):
        k = min(p, len(y) - i)
        y[i: i + k] = decay * 0.5 * (y[i - p: i - p + k] + y[i - p - 1: i - p - 1 + k])
        i += k
    y = y[p + 1: p + 1 + n]
    rel = np.clip((dur + 0.3 - np.arange(n) / SR) / 0.3, 0, 1)
    return y / (np.max(np.abs(y)) + 1e-9) * rel


def whistle(f, dur):
    t = np.arange(int((dur + 0.08) * SR)) / SR
    vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.12) / 0.15, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = np.sin(ph) + 0.05 * np.sin(2 * ph) + 0.03 * filt(rng.standard_normal(len(t)), 4000)
    return s * np.minimum(1, t / 0.03) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)


def bleep(f, dur=0.08):
    t = np.arange(int(dur * SR)) / SR
    return np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-t * 12) * 0.5


def tick():
    t = np.arange(int(0.04 * SR)) / SR
    return (np.sin(2 * np.pi * 2400 * t) * 0.6 + hp_noise(len(t)) * 0.4) * np.exp(-t * 180)


def sleigh():
    out = np.zeros(int(0.18 * SR))
    for _ in range(5):
        o = int(rng.uniform(0, 0.02) * SR)
        t = np.arange(len(out) - o) / SR
        out[o:] += hp_noise(len(t), 3) * np.exp(-t * rng.uniform(25, 45))
    return out / np.max(np.abs(out))


# ---------- робот: укулеле + свист + «бип-буп», 118 BPM ----------
RB = 60 / 118
ROBOT_BEATS = [4, 6, 6, 6, 8]
ROBOT_DUR = sum(ROBOT_BEATS) * RB + 0.6
R_CH = {"C": ["C4", "E4", "G4", "C5"], "Am": ["A3", "E4", "A4", "C5"], "F": ["F3", "C4", "F4", "A4"],
        "G": ["G3", "D4", "G4", "B4"]}
R_PROG = ["C", "Am", "F", "G", "C", "Am", "F", "C"]
R_MEL = [
    [("G5", 0, .5), ("E5", .5, .5), ("G5", 1, 1), ("C6", 2, 1), ("G5", 3, 1)],
    [("A5", 0, .5), ("G5", .5, .5), ("E5", 1, 1), ("C5", 2, 1.5)],
    [("F5", 0, .5), ("A5", .5, .5), ("C6", 1, 1), ("A5", 2, .5), ("F5", 2.5, .5), ("A5", 3, 1)],
    [("G5", 0, 1), ("B5", 1, .5), ("D6", 1.5, 1.5), ("B5", 3, .5), ("G5", 3.5, .5)],
    [("G5", 0, .5), ("E5", .5, .5), ("G5", 1, 1), ("C6", 2, 1), ("G5", 3, 1)],
    [("A5", 0, .5), ("G5", .5, .5), ("E5", 1, 1), ("C5", 2, 1.5)],
    [("F5", 0, .5), ("A5", .5, .5), ("C6", 1, 1), ("B5", 2, .5), ("D6", 2.5, .5), ("G5", 3, 1)],
    [("C6", 0, 2)],
]


def robot_music():
    m = Mix(ROBOT_DUR)
    total = sum(ROBOT_BEATS)
    for bar, ch in enumerate(R_PROG):
        b0 = bar * 4
        notes = R_CH[ch]
        last = b0 + 4 > total
        for e in range(8 if not last else 1):  # «островной» бой: вниз на долю, вверх на «и»
            down = e % 2 == 0
            order = notes if down else notes[::-1]
            for j, n in enumerate(order):
                m.add("uke", ks_pluck(hz(n), RB * (0.45 if not last else 1.5), 0.6), (b0 + e / 2) * RB + j * 0.012,
                      0.2 if down else 0.11)
        m.add("bass", bass(hz(notes[0]) / 2, RB * 0.9), b0 * RB, 0.5)
        if not last:
            m.add("bass", bass(hz(notes[0]) * 0.75, RB * 0.9), (b0 + 2) * RB, 0.4)
        for n, st, du in R_MEL[bar]:
            m.add("whistle", whistle(hz(n), du * RB * 0.92), (b0 + st) * RB, 0.22)
        if bar >= 1 and not last:
            for e in range(4):
                m.add("drums", kick() if e % 2 == 0 else clap(), (b0 + e) * RB, 0.6 if e % 2 == 0 else 0.3)
                m.add("drums", hat(), (b0 + e + 0.5) * RB, 0.1)
    # «бип-буп» на хуке, на переходах и в финале
    for i, n in enumerate(["C6", "G6", "E6", "C7"]):
        m.add("bleep", bleep(hz(n)), i * 0.11, 0.35)
    for b in np.cumsum(ROBOT_BEATS)[:-1]:
        for i, n in enumerate(["G6", "C7"]):
            m.add("bleep", bleep(hz(n)), b * RB - 0.18 + i * 0.09, 0.25)
    for i, n in enumerate(["C6", "E6", "G6", "C7", "E7"]):
        m.add("bleep", bleep(hz(n), 0.1), (total - 2) * RB + i * 0.09, 0.3)
    # тиканье часов на кадре с панелью
    s2 = ROBOT_BEATS[0]
    for k in range(ROBOT_BEATS[1] * 2):
        m.add("tick", tick(), (s2 + k / 2) * RB, 0.35 if k % 2 == 0 else 0.22)
    return m.render({"uke": (0.4, 0.2, 6000, False), "bass": (0.5, 0, 900, False),
                     "whistle": (0.58, 0.35, 5000, False), "drums": (0.5, 0.05, None, False),
                     "bleep": (0.65, 0.2, 5000, False), "tick": (0.6, 0.1, None, False)}, fade_out=0.8)


# ---------- колесо: Jingle Bells (public domain), 128 BPM ----------
WB = 60 / 128
WHEEL_BEATS = [4, 6, 6, 6, 10]
WHEEL_DUR = sum(WHEEL_BEATS) * WB + 0.8
JINGLE = [("E5", 0, 1), ("E5", 1, 1), ("E5", 2, 2), ("E5", 4, 1), ("E5", 5, 1), ("E5", 6, 2),
          ("E5", 8, 1), ("G5", 9, 1), ("C5", 10, 1.5), ("D5", 11.5, .5), ("E5", 12, 4),
          ("F5", 16, 1), ("F5", 17, 1), ("F5", 18, 1.5), ("F5", 19.5, .5), ("F5", 20, 1), ("E5", 21, 1),
          ("E5", 22, 1), ("E5", 23, .5), ("E5", 23.5, .5), ("G5", 24, 1), ("G5", 25, 1), ("F5", 26, 1),
          ("D5", 27, 1), ("C5", 28, 4)]
W_CH = [["C3", "E4", "G4"], ["C3", "E4", "G4"], ["C3", "E4", "G4"], ["C3", "E4", "G4"],
        ["F2", "F4", "A4"], ["C3", "E4", "G4"], ["G2", "F4", "B4"], ["C3", "E4", "G4", "C5"]]


def wheel_music():
    m = Mix(WHEEL_DUR)
    for i, n in enumerate(["C7", "G6", "E7"]):  # «дзынь» на хуке
        m.add("celesta", bell(hz(n), 1.2), i * 0.06, 0.25)
    for n, st, du in JINGLE:
        m.add("celesta", bell(hz(n), du * WB), st * WB, 0.45)
        m.add("glock", bell(hz(n) * 2, du * WB * 0.5), st * WB, 0.12)
    for bar, ch in enumerate(W_CH):
        b0 = bar * 4
        last = bar == len(W_CH) - 1
        for n in ch[1:]:
            m.add("strings", pad(hz(n), 4 * WB if not last else 3.0), b0 * WB, 0.08)
        root = hz(ch[0])
        for e, f in ((0, root), (2, root * 1.5)) if not last else ((0, root),):
            m.add("pizz", ks_pluck(f, WB * 0.8, 0.3, 0.99), (b0 + e) * WB, 0.55)
        if not last:
            for e in range(8):
                m.add("bells", sleigh(), (b0 + e / 2) * WB, 0.28 if e % 2 == 0 else 0.16)
            if bar >= 1:
                m.add("drums", kick(), b0 * WB, 0.5)
                m.add("drums", kick(), (b0 + 2) * WB, 0.4)
    end = 28 * WB
    m.add("fx", crash(), end, 0.12)
    for i, n in enumerate(["C6", "E6", "G6", "C7", "E7", "G7"]):
        m.add("fx", bell(hz(n), 0.4), end + i * 0.05, 0.14)
    return m.render({"celesta": (0.55, 0.45, None, False), "glock": (0.65, 0.4, None, False),
                     "strings": (0.45, 0.5, 3000, False), "pizz": (0.45, 0.15, 2500, False),
                     "bells": (0.6, 0.15, None, False), "drums": (0.5, 0, 2000, False),
                     "fx": (0.55, 0.4, None, False)}, fade_out=1.0)


# =====================================================================
# Ролики
# =====================================================================
def timeline(beats, beat):
    starts = np.cumsum([0] + list(beats)) * beat
    return starts


def scene_at(T, starts):
    k = int(np.searchsorted(starts, T, side="right") - 1)
    return min(k, len(starts) - 2), T - starts[min(k, len(starts) - 2)]


def cam(img, a, b, t):
    e = ease_io(t)
    return crop(img, *(lerp(a[i], b[i], e) for i in range(3)))


# ---------- 1. Робот-дачник ----------
BLUE, SUN = (30, 110, 200), (255, 205, 40)
R_ST = [(BLUE, (255, 255, 255)), (SUN, INK), ((70, 160, 70), (255, 255, 255))]
R_STARTS = timeline(ROBOT_BEATS, RB)
R_TEXTS = [
    [(badge(["Знакомьтесь —", "робот-дачник!"], 76, R_ST[1]), 0.15, 1300)],
    [(badge(["Собран вручную"], 70, R_ST[0]), 0.15, 1250),
     (badge(["из настоящих деталей"], 58, R_ST[1]), 0.5, 1390)],
    [(badge(["Сам сажает,", "сам поливает,", "сам удобряет"], 64, R_ST[2]), 0.15, 1330)],
    [(badge(["Лучший подарок", "для дачника"], 72, R_ST[1]), 0.15, 1380)],
    [(badge(["Хочешь такого же?"], 66, R_ST[0]), 0.25, 1360),
     (badge(["Пиши «РОБОТ» в директ"], 56, R_ST[1]), 0.8, 1480),
     (badge(["на заказ"], 52, R_ST[2]), 0.0, 300)],
]
R_BG2, R_BG1 = blur_bg(IMG["robot_2"], (30, 60, 30)), blur_bg(IMG["robot_1"], (30, 40, 60))
R_CARD2, R_CARD1 = card(IMG["robot_2"], 1000), card(IMG["robot_1"], 700)


def robot_frame(T):
    k, t = scene_at(T, R_STARTS)
    dur = R_STARTS[k + 1] - R_STARTS[k]
    p = t / dur
    im = IMG["robot_1"]
    if k == 0:
        f = cam(im, (560, 620, 1280), (578, 420, 600), min(1, p * 1.15))
    elif k == 1:
        f = cam(im, (370, 800, 560), (680, 760, 560), p)
    elif k == 2:
        f = cam(im, (610, 1070, 520), (850, 930, 600), p)
    elif k == 3:
        f = R_BG2.copy()
        draw_card(f, R_CARD2, W / 2, 820, lerp(0.92, 1.0, ease_io(p)))
    else:
        f = R_BG1.copy()
        ang = 3.5 * math.sin(t * 2 * math.pi * 1.1) * math.exp(-t * 1.3)  # «кивок»
        draw_card(f, R_CARD1, W / 2, 830, lerp(0.85, 1.0, ease_out_back(t / 0.5)), ang)
    if k < 3:
        f = Image.composite(base.BLACK, f, base.VIG)
    base.overlay_particles(f, T)
    show_texts(f, R_TEXTS[k], t, dur if k < 4 else 99)
    return flash(f, 1 - t / 0.12 if k > 0 else 1 - T / 0.15)


# ---------- 2. Новогоднее колесо ----------
RED, GOLD = (180, 25, 45), (245, 195, 70)
W_ST = [(RED, (255, 255, 255)), (GOLD, (60, 20, 10)), ((20, 90, 60), (255, 255, 255))]
W_STARTS = timeline(WHEEL_BEATS, WB)
W_TEXTS = [
    [(badge(["Включаем", "новогоднее настроение"], 66, W_ST[1]), 0.1, 1330)],
    [(badge(["Колесо обозрения"], 70, W_ST[0]), 0.15, 1270),
     (badge(["ручной работы"], 62, W_ST[1]), 0.5, 1400)],
    [(badge(["Каждая деталь —", "вручную"], 70, W_ST[2]), 0.15, 1330)],
    [(badge(["Украсит дом,", "садик или офис"], 70, W_ST[0]), 0.15, 1330)],
    [(badge(["Успейте заказать", "до Нового года"], 66, W_ST[0]), 0.3, 1370),
     (badge(["Пиши «ЁЛКА» в директ"], 56, W_ST[1]), 1.0, 1510),
     (badge(["светится!"], 54, W_ST[2]), 0.0, 300)],
]
TW1, TW2 = Twinkle(IMG["wheel_1"], 245, 4), Twinkle(IMG["wheel_2"], 225, 6)
W_BG = blur_bg(IMG["wheel_2"], (20, 10, 20), 0.35)
W_CARD_W = 720


def wheel_frame(T):
    k, t = scene_at(T, W_STARTS)
    dur = W_STARTS[k + 1] - W_STARTS[k]
    p = t / dur
    if k == 0:
        f = cam(TW2.at(T), (480, 700, 1280), (540, 470, 820), p)
    elif k == 1:
        f = cam(TW1.at(T), (450, 480, 780), (650, 520, 680), p)
    elif k == 2:
        f = cam(TW1.at(T), (360, 960, 560), (480, 1060, 520), p)
    elif k == 3:
        f = cam(TW2.at(T), (480, 620, 1150), (480, 660, 1280), p)
    else:
        f = W_BG.copy()
        src = TW2.at(T, boost=1.0 + min(1.0, t / 1.5))  # «огоньки ярче»
        c = base.rounded_card(src.resize((W_CARD_W, int(W_CARD_W * src.height / src.width)), Image.BICUBIC), 30, 10)
        s = lerp(0.88, 1.0, ease_out_back(t / 0.6))
        c = scaled(c, s)
        sh = Image.new("RGBA", (c.width + 100, c.height + 100), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 160), (50, 65), c.split()[3])
        paste_center(f, sh.filter(ImageFilter.GaussianBlur(25)), W / 2, 850)
        paste_center(f, c, W / 2, 830)
    f = Image.composite(Image.new("RGB", (W, H), (10, 5, 15)), f, base.VIG)
    if k in (0, 3, 4):
        snow(f, T, 0.8 if k < 4 else 1.0)
    show_texts(f, W_TEXTS[k], t, dur if k < 4 else 99)
    return flash(f, 1 - t / 0.12 if k > 0 else 1 - T / 0.2, (255, 235, 200), 0.6)


# ---------- 3. Панно (сценарий из PROMPTS.md) ----------
MB = music.BEAT
P_BEATS = [4, 5, 5, 5, music.TOTAL_BEATS - music.FINAL_BEAT]
assert sum(P_BEATS[:4]) == music.FINAL_BEAT
P_STARTS = timeline(P_BEATS, MB)
P_ST = [(PINK, (255, 255, 255)), (PURPLE, (255, 255, 255)), ((255, 255, 255), PURPLE)]
P_TEXTS = [
    [(badge(["Этот подарок", "не купить в магазине"], 68, P_ST[0]), 0.15, 1330)],
    [(badge(["Ручная работа"], 76, P_ST[1]), 0.15, 1330)],
    [(badge(["Конверт для денег", "или пожеланий"], 68, P_ST[0]), 0.15, 1300)],
    [(badge(["Любой цвет и надпись"], 62, P_ST[2]), 0.15, 1270),
     (badge(["под ваш повод"], 66, P_ST[1]), 0.5, 1400)],
    [(badge(["Закажи к празднику"], 66, P_ST[0]), 0.35, 1370),
     (badge(["Пиши «ПАННО» в директ"], 56, P_ST[2]), 1.0, 1500)],
]
BOARD = IMG["birthday_board"]
P_BG = blur_bg(BOARD, (60, 10, 70))
P_CARD = card(BOARD, 720)


def panno_frame(T):
    k, t = scene_at(T, P_STARTS)
    dur = P_STARTS[k + 1] - P_STARTS[k]
    p = t / dur
    if k == 0:
        f = cam(BOARD, (940, 640, 1000), (960, 1000, 1900), ease_out_back(min(1, p * 1.3)) * 0.9 + p * 0.1)
    elif k == 1:
        f = cam(BOARD, (420, 1420, 1150), (740, 1640, 1250), p)
    elif k == 2:
        f = cam(BOARD, (1290, 1760, 1200), (1300, 2330, 1050), p)
    elif k == 3:
        f = cam(BOARD, (966, 1200, 2200), (966, 1288, 2576), p)
    else:
        f = P_BG.copy()
        draw_card(f, P_CARD, W / 2, 830, lerp(0.85, 1.0, ease_out_back(t / 0.5)))
    if k < 4:
        f = Image.composite(base.BLACK, f, base.VIG)
    base.overlay_particles(f, T, confetti_t=(t - 0.1) if k == 4 else None)
    show_texts(f, P_TEXTS[k], t, dur if k < 4 else 99)
    return flash(f, 1 - t / 0.15 if k > 0 else 1 - T / 0.2)


# ---------- 4. Витрина «3 поделки — какую выберешь?» ----------
PB = v.PB  # 128 BPM, музыка из variants.pop_music: дроп на 8-й доле
S_BEATS = [8, 8, 8, 4, 4]
S_STARTS = timeline(S_BEATS, PB)
S_HOOK = [(IMG["robot_1"], (578, 420, 640)), (IMG["wheel_2"], (540, 470, 820)), (BOARD, (940, 700, 1100)),
          (IMG["robot_1"], (525, 760, 520)), (IMG["wheel_1"], (400, 1000, 560)), (BOARD, (1290, 1900, 1100)),
          (IMG["robot_1"], (850, 930, 560)), (BOARD, (420, 1450, 1150))]
S_TEXTS = [
    [(v.stamp(["Делаю подарки,", "которых нет", "в магазинах"], 70, rot=-2), 0.1, 1300)],
    [(v.stamp(["1 — Робот-дачник"], 70, fill=(30, 110, 200), fg=(255, 255, 255), rot=3), 0.05, 1350)],
    [(v.stamp(["2 — Новогоднее колесо"], 62, fill=(180, 25, 45), fg=(255, 255, 255), rot=-3), 0.05, 1350)],
    [(v.stamp(["3 — Панно на ДР"], 70, fill=PINK, fg=(255, 255, 255), rot=3), 0.05, 1350)],
    [(v.stamp(["Какую выберешь?"], 72, rot=-2), 0.05, 300),
     (v.stamp(["Пиши цифру", "в комментариях"], 64, fill=PINK, fg=(255, 255, 255), rot=2), 0.5, 1460)],
]
S_POL = []
for im, cap in ((IMG["robot_1"], "1"), (IMG["wheel_2"], "2"), (BOARD, "3")):
    th = im.resize((370, 493), Image.LANCZOS)
    pc = base.rounded_card(th, 18, 8)
    S_POL.append((pc, text_badge([cap], 80, fill=YELLOW, fg=INK, pad=(34, 10))))
S_COLLAGE = [(280, 690, -6), (770, 710, 6), (520, 1130, 3)]
S_BG = Image.blend(blur_bg(IMG["wheel_2"], (40, 10, 50), 0.5), blur_bg(BOARD, (40, 10, 50), 0.5), 0.5)


def showcase_frame(T):
    k, t = scene_at(T, S_STARTS)
    beat = T / PB
    tb = (beat % 1) * PB
    punch = math.exp(-tb * 9)
    fl = 0.0
    if k == 0:  # быстрая нарезка по одной доле
        i = min(int(beat), len(S_HOOK) - 1)
        im, (cx, cy, h) = S_HOOK[i]
        f = crop(im, cx, cy, h * lerp(1.0, 0.9, beat % 1))
        f = Image.blend(f, Image.new("RGB", (W, H), INK), 0.25)
        fl = 1 - tb / 0.08
    elif k in (1, 2, 3):
        p = t / (S_STARTS[k + 1] - S_STARTS[k])
        if k == 1:
            f = cam(IMG["robot_1"], (560, 600, 1280), (575, 520, 900), p)
        elif k == 2:
            f = cam(TW2.at(T), (480, 640, 1280), (520, 520, 900), p)
        else:
            f = cam(BOARD, (966, 1288, 2576), (960, 900, 1800), p)
        if punch > 0.05:
            f = f.resize((int(W * (1 + 0.04 * punch)), int(H * (1 + 0.04 * punch))), Image.BICUBIC)
            f = f.crop(((f.width - W) // 2, (f.height - H) // 2, (f.width - W) // 2 + W, (f.height - H) // 2 + H))
        f = Image.composite(base.BLACK, f, base.VIG)
        fl = 1 - t / 0.1
    else:  # коллаж: три карточки падают по долям
        f = S_BG.copy()
        for j, ((pc, num), (cx, cy, ang)) in enumerate(zip(S_POL, S_COLLAGE)):
            tj = t - j * PB * 0.5
            if tj < 0:
                continue
            s = lerp(1.6, 1.0, ease_out_back(tj / 0.3)) * (1 + 0.03 * punch)
            img = scaled(pc, 0.95 * s).rotate(ang, Image.BICUBIC, expand=True)
            paste_center(f, with_alpha(img, clamp(tj / 0.12, 0, 1)), cx, cy)
            paste_center(f, num, cx - 150, cy - 230)
        base.overlay_particles(f, T, confetti_t=t - 0.2)
        fl = 1 - t / 0.12
    show_texts(f, S_TEXTS[k], t, (S_STARTS[k + 1] - S_STARTS[k]) if k < 4 else 99)
    return v.rgb_split(flash(f, fl, amt=0.55), int(16 * max(0, 1 - tb / 0.1)) if k < 4 else 0)


# =====================================================================
REELS = {
    "robot": (sum(ROBOT_BEATS) * RB + 0.6, robot_frame, robot_music),
    "wheel": (WHEEL_DUR, wheel_frame, wheel_music),
    "panno": (music.DURATION, panno_frame, music.build),
    "showcase": (v.POP_DUR, showcase_frame, v.pop_music),
}

if __name__ == "__main__":
    os.makedirs(v.OUT_DIR, exist_ok=True)
    for name in sys.argv[1:] or REELS:
        dur, fn, mus = REELS[name]
        v.encode(name, dur, fn, mus(), crf=24 if name == "showcase" else 20)
