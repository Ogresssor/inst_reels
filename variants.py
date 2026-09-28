"""Три альтернативных варианта Reels: своя музыка, свой визуальный стиль и анимации.

    python3 variants.py            # все три
    python3 variants.py pop lofi   # выборочно

Результат: output/reel_pop.mp4, output/reel_cinema.mp4, output/reel_lofi.mp4
"""
import math
import os
import random
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_reel as base
from make_reel import (FONT_BOLD, H, PINK, PURPLE, W, clamp, crop_frame, ease_io, ease_out_back, font,
                       lerp, photo, text_badge)
from music import SR, bass, bell, clap, crash, hat, hp_noise, hz, kick, pad, pan, pluck, reverb, riser

FPS = base.FPS
OUT_DIR = os.path.join(base.ROOT, "output")
SERIF_I = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
SERIF_BI = "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf"
YELLOW = (255, 225, 77)
INK = (25, 20, 30)
rng = np.random.default_rng(11)


# =====================================================================
# Аудио: общие инструменты и микшер
# =====================================================================
def env_t(dur):
    return np.arange(int(dur * SR)) / SR


def saw(f, dur, bright=0.9, att=0.005, dec=3.0, sus=0.0, rel=0.12, detune=0.0):
    t = env_t(dur + rel)
    kmax = int(min(40, 9000 / f))
    s = np.zeros_like(t)
    for d in ((1.0,) if not detune else (1 - detune, 1.0, 1 + detune)):
        for k in range(1, kmax + 1):
            s += np.sin(2 * np.pi * f * d * k * t + k * d) * (bright ** (k - 1)) / k
    e = np.minimum(1, t / att) * (sus + (1 - sus) * np.exp(-t * dec))
    return s * e * np.clip((dur + rel - t) / rel, 0, 1)


def piano(f, dur):
    t = env_t(dur + 1.6)
    s = sum(np.sin(2 * np.pi * f * k * math.sqrt(1 + 0.0003 * k * k) * t) * np.exp(-t * (0.7 + 0.6 * k)) / k ** 1.4
            for k in range(1, 9) if f * k < SR / 2.2)
    damp = np.where(t > dur, np.exp(-(t - dur) * 5), 1.0)
    return s * np.minimum(1, t / 0.002) * damp


def rhodes(f, dur):
    t = env_t(dur + 0.6)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
    if f * 7.1 < SR / 2.2:
        s += 0.15 * np.sin(2 * np.pi * 7.1 * f * t) * np.exp(-t * 20)
    s *= 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    damp = np.where(t > dur, np.exp(-(t - dur) * 8), 1.0)
    return s * np.minimum(1, t / 0.01) * np.exp(-t * 0.9) * damp


def snare_soft():
    t = env_t(0.25)
    return hp_noise(len(t)) * np.exp(-t * 22) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5


def filt(x, fc, kind="low", order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-6
    r = (f / fc) if kind == "low" else (fc / f)
    return np.fft.irfft(X / np.sqrt(1 + r ** (2 * order)), n=len(x))


class Mix:
    def __init__(self, dur):
        self.dur = dur
        self.n = int((dur + 2) * SR)
        self.stems = {}

    def add(self, stem, sig, t, g=1.0):
        buf = self.stems.setdefault(stem, np.zeros(self.n))
        i = int(t * SR)
        if 0 <= i < self.n:
            s = sig[: self.n - i]
            buf[i: i + len(s)] += s * g

    def render(self, cfg, fade_out=1.0, pump=None):
        """cfg: stem -> (pan, reverb, lowpass_hz|None, pumped)"""
        out = np.zeros((self.n, 2))
        for name, buf in self.stems.items():
            p, rv, lp, pumped = cfg.get(name, (0.5, 0.0, None, False))
            if lp:
                buf = filt(buf, lp)
            if pumped and pump is not None:
                buf = buf * pump[: self.n]
            if rv:
                buf = reverb(buf, rv)
            out += pan(buf, p)
        out = np.tanh(out / np.max(np.abs(out)) * 1.3)
        n = int(self.dur * SR)
        out = out[:n]
        fo = int(fade_out * SR)
        out[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
        out[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
        return out / np.max(np.abs(out)) * 0.89


def write_wav(path, data):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


# =====================================================================
# Видео: общие хелперы
# =====================================================================
def encode(name, dur, frame_fn, audio, crf=18):
    wav = os.path.join(OUT_DIR, f"_{name}.wav")
    out = os.path.join(OUT_DIR, f"reel_{name}.mp4")
    write_wav(wav, audio)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        proc.stdin.write(frame_fn(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print("saved", out, f"{dur:.1f}s")


def text_img(lines, size, path, color=(255, 255, 255), shadow=160, spacing=1.25):
    f = font(path, size)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    boxes = [d.textbbox((0, 0), ln, font=f) for ln in lines]
    lh = int(size * spacing)
    tw = max(b[2] - b[0] for b in boxes)
    pad = 40
    img = Image.new("RGBA", (tw + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(sh), ImageDraw.Draw(img)
    for i, (ln, b) in enumerate(zip(lines, boxes)):
        x = pad + (tw - (b[2] - b[0])) / 2 - b[0]
        y = pad + i * lh
        ds.text((x + 3, y + 5), ln, font=f, fill=(0, 0, 0, shadow))
        dt.text((x, y), ln, font=f, fill=color + (255,))
    return Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), img)


def with_alpha(img, a):
    if a >= 1:
        return img
    img = img.copy()
    img.putalpha(img.split()[3].point(lambda v: int(v * a)))
    return img


def paste_center(frame, img, cx, cy):
    frame.paste(img, (int(cx - img.width / 2), int(cy - img.height / 2)), img)


def scaled(img, s):
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)


def heart(size, col):
    im = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * 4
    r = s * 0.27
    d.ellipse((s * 0.5 - 2 * r + 2, s * 0.12, s * 0.5 + 2, s * 0.12 + 2 * r), fill=col)
    d.ellipse((s * 0.5 - 2, s * 0.12, s * 0.5 + 2 * r - 2, s * 0.12 + 2 * r), fill=col)
    d.polygon([(s * 0.5 - 2 * r + 6, s * 0.12 + r * 1.35), (s * 0.5 + 2 * r - 6, s * 0.12 + r * 1.35),
               (s * 0.5, s * 0.92)], fill=col)
    return im.resize((size, size), Image.LANCZOS)


# =====================================================================
# 1) POP — 128 BPM, нарезка в бит
# =====================================================================
POP_BPM = 128
PB = 60 / POP_BPM
POP_DUR = 32 * PB + 1.0

POP_CHORDS = {"Am": ["A2", "C4", "E4", "A4"], "F": ["F2", "C4", "F4", "A4"],
              "C": ["C3", "C4", "E4", "G4"], "G": ["G2", "B3", "D4", "G4"]}
POP_PROG = ["Am", "F", "Am", "F", "C", "G", "F", "G"]
POP_MOTIF = {  # (нота, доля в такте, длительность)
    "Am": [("E5", 0, .5), ("E5", 1, .5), ("D5", 1.5, .5), ("C5", 2, 1), ("A4", 3, .5), ("C5", 3.5, .5)],
    "F": [("A4", 0, .5), ("C5", 1, .5), ("A5", 1.5, 1), ("G5", 2.5, .5), ("F5", 3, 1)],
    "C": [("E5", 0, .5), ("G5", .5, .5), ("E5", 1, .5), ("C5", 1.5, 1), ("D5", 2.5, .5), ("E5", 3, 1)],
    "G": [("D5", 0, 1), ("B4", 1, .5), ("D5", 1.5, .5), ("G5", 2, 1.5)],
}


def pop_music():
    m = Mix(POP_DUR)
    for bar, ch in enumerate(POP_PROG):
        b0 = bar * 4
        notes = POP_CHORDS[ch]
        root = hz(notes[0])
        if bar < 2:  # вступление: «приглушённые» плаки восьмыми
            for e in range(8):
                for n in notes[1:]:
                    m.add("intro", pluck(hz(n), PB * 0.4, 0.3 + 0.2 * bar), (b0 + e / 2) * PB, 0.12)
            if bar == 1:
                m.add("drums", clap(), (b0 + 1) * PB, 0.25)
                for k in range(8):  # нарастающая дробь
                    m.add("drums", clap(), (b0 + 2 + k / 4) * PB, 0.08 + 0.03 * k)
                m.add("fx", riser(4 * PB), b0 * PB, 0.3)
            continue
        for n in notes[1:]:
            m.add("pad", saw(hz(n), 4 * PB, 0.75, att=0.02, sus=1, dec=0, detune=0.006), b0 * PB, 0.05)
        for e in range(4):
            m.add("bass", saw(root, PB * 0.4, 0.6, dec=6), (b0 + e + 0.5) * PB, 0.25)
            m.add("bass", bass(root, PB * 0.5), (b0 + e + 0.5) * PB, 0.5)
            m.add("drums", kick(), (b0 + e) * PB, 1.0)
            m.add("drums", hat(), (b0 + e + 0.5) * PB, 0.22)
            if e in (1, 3):
                m.add("drums", clap(), (b0 + e) * PB, 0.4)
        for n, st, du in POP_MOTIF[ch]:
            m.add("lead", saw(hz(n), du * PB * 0.85, 0.7, dec=2.5, sus=0.35), (b0 + st) * PB, 0.16)
            m.add("bell", bell(hz(n) * 2, du * PB), (b0 + st) * PB, 0.12)
    for b in (8, 24):
        m.add("fx", crash(), b * PB, 0.25)
    m.add("fx", riser(2 * PB), 22 * PB, 0.2)
    # финальный аккорд
    end = 32 * PB
    m.add("drums", kick(), end, 1.0)
    m.add("fx", crash(), end, 0.3)
    for n in ["C3", "C4", "E4", "G4", "C5", "E5"]:
        m.add("pad", saw(hz(n), 1.0, 0.7, att=0.005, dec=2.5, detune=0.006), end, 0.06)
    for i, n in enumerate(["C6", "E6", "G6", "C7"]):
        m.add("bell", bell(hz(n), 0.3), end + i * 0.05, 0.12)

    t = np.arange(m.n) / SR
    tb = np.mod(t, PB)
    pump = np.where(t >= 8 * PB, 1 - 0.6 * np.exp(-tb / 0.07), 1.0)
    return m.render({"intro": (0.5, 0.25, 2500, False), "pad": (0.5, 0.2, 5000, True),
                     "bass": (0.5, 0.0, 1800, True), "drums": (0.5, 0.0, None, False),
                     "lead": (0.42, 0.3, 7000, False), "bell": (0.62, 0.35, None, False),
                     "fx": (0.55, 0.3, None, False)}, fade_out=0.8, pump=pump)


def stamp(text, size=92, fill=YELLOW, fg=INK, rot=0):
    b = text_badge(text if isinstance(text, list) else [text], size, fill=fill, fg=fg, pad=(40, 18))
    return b.rotate(rot, Image.BICUBIC, expand=True)


POP_INTRO = [(stamp("ПОДАРИ", 110, rot=4), 0, 560), (stamp("ЭМОЦИИ", 110, fill=PINK, fg=(255, 255, 255), rot=-3), 2, 760),
             (stamp("А НЕ ПРОСТО", 84, rot=2), 4, 1160), (stamp("ВЕЩЬ", 130, fill=(255, 255, 255), rot=-4), 6, 1370)]
POP_CUTS = [  # (cx, cy, h) + слово
    ((480, 300, 600), "ШАРИКИ"), ((330, 560, 520), "ЛЕНТЫ"), ((390, 800, 440), "БАНТ"),
    ((630, 900, 480), "СЕРДЕЧКИ"), ((180, 720, 420), "НАДПИСЬ"), ((650, 1180, 420), "РОЗЫ"),
    ((200, 1100, 460), "ДЕТАЛИ"), ((480, 640, 1150), "ЛЮБОВЬ"),
]
POP_WORDS = [stamp(w, 120, fill=(YELLOW if i % 2 == 0 else PINK), fg=(INK if i % 2 == 0 else (255, 255, 255)),
                   rot=(5 if i % 2 == 0 else -5)) for i, (_, w) in enumerate(POP_CUTS)]
POP_FINAL_TOP = stamp(["ХОЧЕШЬ", "ТАКОЙ ЖЕ?"], 92, rot=-3)
POP_FINAL_CTA = stamp("ПИШИ В ДИРЕКТ ✉", 72, fill=PINK, fg=(255, 255, 255), rot=2)


def pop_in(frame, img, cx, cy, t_in, t, dur=0.22):
    if t < t_in:
        return
    k = ease_out_back((t - t_in) / dur)
    paste_center(frame, scaled(img, lerp(1.8, 1.0, k) if k < 1 else 1.0), cx, cy)


def rgb_split(frame, s):
    if s < 1:
        return frame
    a = np.asarray(frame).copy()
    a[:, :, 0] = np.roll(a[:, :, 0], s, axis=1)
    a[:, :, 2] = np.roll(a[:, :, 2], -s, axis=1)
    return Image.fromarray(a)


def pop_frame(T):
    beat = T / PB
    tb = (beat % 1) * PB  # время от последней доли
    punch = math.exp(-tb * 9)
    if beat < 8:  # интро: общий план, медленный наезд, слова в бит
        e = ease_io(beat / 8)
        frame = crop_frame(480, lerp(640, 560, e), lerp(1280, 1050, e) / (1 + 0.03 * punch * (beat >= 4)))
        frame = Image.blend(frame, Image.new("RGB", (W, H), INK), 0.35)
        for img, b, y in POP_INTRO:
            pop_in(frame, img, W / 2, y, b * PB, T)
        split = 0
    elif beat < 24:  # дроп: смена кадра каждые 2 доли
        k = int((beat - 8) // 2)
        (cx, cy, h), _ = POP_CUTS[k]
        local = (beat - 8 - 2 * k) / 2
        frame = crop_frame(cx, cy, h * lerp(1.0, 0.86, local) / (1 + 0.07 * punch))
        frame = Image.composite(base.BLACK, frame, base.VIG)
        pop_in(frame, POP_WORDS[k], W / 2, 1480, (8 + 2 * k) * PB + 0.02, T, 0.18)
        split = int(18 * max(0, 1 - (local * 2 * PB) / 0.12))
    else:  # финал
        t = T - 24 * PB
        frame = base.BLUR_BG.copy()
        s = lerp(1.25, 1.0, ease_out_back(t / 0.35)) * (1 + 0.025 * punch) if beat < 32 else 1 + 0.04 * punch
        card, sh = scaled(base.FULL_CARD, s * 0.95), scaled(base.FULL_SHADOW, s * 0.95)
        paste_center(frame, sh, W / 2, H / 2 + 20)
        paste_center(frame, card, W / 2, H / 2)
        base.overlay_particles(frame, T, confetti_t=t - 0.1)
        pop_in(frame, POP_FINAL_TOP, W / 2, 230, 24 * PB + 0.1, T)
        pop_in(frame, POP_FINAL_CTA, W / 2, 1720, 26 * PB, T)
        split = int(22 * max(0, 1 - t / 0.15))
    fl = max(0.0, 1 - tb / 0.08) if (beat >= 8 and int(beat) % 2 == 0 and beat < 25) else 0.0
    if fl:
        frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), fl * 0.6)
    return rgb_split(frame, split)


# =====================================================================
# 2) CINEMA — пианино и струнные, мягкие переходы
# =====================================================================
CB = 60 / 72
CBAR = 4 * CB
CINEMA_DUR = 15.5
CIN_CHORDS = [["C3", "G3", "C4", "E4"], ["B2", "G3", "B3", "D4"], ["A2", "E3", "A3", "C4"],
              ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"]]
CIN_MELODY = [
    [("G5", 0, 1.5), ("E5", 1.5, .5), ("D5", 2, 1), ("C5", 3, 1)],
    [("D5", 0, 1.5), ("B4", 1.5, .5), ("G4", 2, 2)],
    [("C5", 0, 1.5), ("E5", 1.5, .5), ("A5", 2, 1.5), ("G5", 3.5, .5)],
    [("F5", 0, 1), ("E5", 1, 1), ("C5", 2, 1), ("D5", 3, 1)],
    [("E5", 0, 3), ("C6", 0.5, 2.5)],
]


def cinema_music():
    m = Mix(CINEMA_DUR)
    for bar, ch in enumerate(CIN_CHORDS):
        b0 = bar * CBAR
        last = bar == len(CIN_CHORDS) - 1
        pattern = [0, 1, 2, 3, 2, 1, 2, 3] if not last else [0, 1, 2, 3]
        for i, idx in enumerate(pattern):
            m.add("pianoL", piano(hz(ch[idx]), CB * 0.5 if not last else 3.0), b0 + i * CB / 2, 0.16)
        for n, st, du in CIN_MELODY[bar]:
            m.add("pianoR", piano(hz(n), du * CB), b0 + st * CB, 0.26)
        if bar >= 1:
            for n in ch[1:]:
                m.add("strings", pad(hz(n), CBAR * (1.0 if not last else 0.6)), b0, 0.10 if bar > 1 else 0.06)
            m.add("strings", pad(hz(ch[0]), CBAR), b0, 0.14)
    for i, n in enumerate(["C6", "E6", "G6", "C7"]):
        m.add("shimmer", bell(hz(n), 1.0), 4 * CBAR + 0.3 + i * 0.12, 0.08)
    return m.render({"pianoL": (0.4, 0.45, 5000, False), "pianoR": (0.58, 0.5, 7000, False),
                     "strings": (0.5, 0.6, 2600, False), "shimmer": (0.6, 0.7, None, False)}, fade_out=2.0)


CIN_SHOTS = [  # (start, end, cam_a, cam_b)
    (0.0, CBAR + 0.6, (480, 420, 760), (470, 330, 560)),
    (CBAR - 0.6, 2 * CBAR + 0.6, (220, 720, 640), (360, 820, 640)),
    (2 * CBAR - 0.6, 3 * CBAR + 0.6, (640, 860, 620), (600, 1100, 620)),
]
CIN_TEXTS = [
    (text_img(["Когда хочется", "удивить…"], 108, SERIF_BI), 0.8, CBAR - 0.4, 1380),
    (text_img(["…и подарить", "не вещь, а эмоции"], 104, SERIF_BI), CBAR + 0.5, 2 * CBAR - 0.4, 1380),
    (text_img(["Каждая деталь —", "вручную"], 104, SERIF_BI), 2 * CBAR + 0.5, 3 * CBAR - 0.4, 1380),
    (text_img(["Подарок, который", "запомнится"], 92, SERIF_BI), 3 * CBAR + 0.6, 99, 250),
    (text_img(["на заказ  ·  пишите в Директ"], 60, SERIF_BI, color=(255, 240, 225)), 3 * CBAR + 1.8, 99, 1740),
]
_bok = Image.new("L", (160, 160), 0)
ImageDraw.Draw(_bok).ellipse((20, 20, 140, 140), fill=255)
BOKEH_SPRITE = _bok.filter(ImageFilter.GaussianBlur(10))
BOKEH = [(random.uniform(0, W), random.uniform(0, H), random.uniform(60, 180), random.uniform(0.08, 0.22),
          random.uniform(-25, 25), random.uniform(-40, -10), random.uniform(0, 6.28)) for _ in range(16)]
GRAIN = [Image.fromarray(np.clip(rng.normal(128, 10, (H // 2, W // 2)), 0, 255).astype(np.uint8), "L")
         .resize((W, H), Image.NEAREST) for _ in range(6)]
CIN_FINAL = base.rounded_card(photo.resize((760, int(760 / photo.width * photo.height)), Image.LANCZOS),
                              radius=8, border=6)
CIN_FINAL_SH = Image.new("RGBA", (CIN_FINAL.width + 120, CIN_FINAL.height + 120), (0, 0, 0, 0))
CIN_FINAL_SH.paste((0, 0, 0, 170), (60, 70), CIN_FINAL.split()[3])
CIN_FINAL_SH = CIN_FINAL_SH.filter(ImageFilter.GaussianBlur(35))
_cbg = crop_frame(480, 640, 1280).filter(ImageFilter.GaussianBlur(45))
CIN_BG = Image.blend(_cbg, Image.new("RGB", (W, H), (40, 20, 30)), 0.5)
_ya = np.clip((np.arange(H) - 1050) / 500, 0, 1) ** 1.3 * 170
CIN_SHADE = Image.new("RGBA", (W, H), (20, 5, 15, 0))
CIN_SHADE.putalpha(Image.fromarray(np.repeat(_ya[:, None], W, 1).astype(np.uint8)))


def wipe(img, p, feather=160):
    """Мягкое проявление текста слева направо."""
    if p >= 1:
        return img
    a = np.asarray(img.split()[3]).astype(np.float32)
    x = np.arange(img.width)[None, :]
    m = np.clip((p * (img.width + feather) - x) / feather, 0, 1)
    out = img.copy()
    out.putalpha(Image.fromarray((a * m).astype(np.uint8)))
    return out


def grade(frame, T):
    small = frame.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize((W, H))
    a = np.asarray(frame).astype(np.float32)
    g = np.asarray(small).astype(np.float32)
    a = 255 - (255 - a) * (255 - g * 0.2) / 255  # мягкое свечение (screen)
    a = a * np.array([1.04, 0.99, 0.9]) + np.array([8, 3, 0])
    grain = np.asarray(GRAIN[int(T * 12) % len(GRAIN)]).astype(np.float32)[..., None] - 128
    a = np.clip(a + grain * 0.5, 0, 255).astype(np.uint8)
    out = Image.fromarray(a)
    return Image.composite(Image.new("RGB", (W, H), (25, 10, 15)), out, base.VIG)


def cinema_frame(T):
    frame = None
    for st, en, ca, cb in CIN_SHOTS:
        if st <= T < en:
            e = ease_io((T - st) / (en - st))
            img = crop_frame(*(lerp(ca[i], cb[i], e) for i in range(3)))
            a = clamp((T - st) / 1.2, 0, 1) if st > 0 else 1.0
            frame = img if frame is None or a >= 1 else Image.blend(frame, img, a)
    fst = 3 * CBAR - 0.6
    if T >= fst:
        t = T - fst
        fin = CIN_BG.copy()
        s = lerp(1.06, 1.0, ease_io(t / 3)) * lerp(1.0, 1.02, t / 6)
        paste_center(fin, scaled(CIN_FINAL_SH, s), W / 2, H / 2 + 40)
        paste_center(fin, scaled(CIN_FINAL, s), W / 2, H / 2 + 20)
        a = clamp(t / 1.2, 0, 1)
        frame = fin if frame is None or a >= 1 else Image.blend(frame, fin, a)
    if T < 1.5:  # открытие из размытия и темноты
        k = ease_io(T / 1.5)
        frame = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)),
                            frame.filter(ImageFilter.GaussianBlur((1 - k) * 18)) if k < 1 else frame, k)
    frame = grade(frame, T)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for x, y, r, a, vx, vy, ph in BOKEH:
        spr = BOKEH_SPRITE.resize((int(r), int(r)))
        alpha = spr.point(lambda v, a=a * (0.6 + 0.4 * math.sin(T * 0.9 + ph)): int(v * a))
        col = Image.new("RGBA", spr.size, (255, 225, 190, 255))
        col.putalpha(alpha)
        ov.alpha_composite(col, (int((x + vx * T) % (W + 200) - 100), int((y + vy * T) % (H + 200) - 100)))
    frame.paste(ov, (0, 0), ov)
    if T < 3 * CBAR:
        frame.paste(CIN_SHADE, (0, 0), with_alpha(CIN_SHADE, clamp((3 * CBAR - T) / 0.8, 0, 1)))
    d = ImageDraw.Draw(frame)
    d.rectangle((36, 36, W - 36, H - 36), outline=(255, 245, 235), width=2)
    for img, t_in, t_out, y in CIN_TEXTS:
        if t_in <= T < t_out:
            a = clamp((t_out - T) / 0.6, 0, 1)
            tx = with_alpha(wipe(img, ease_io((T - t_in) / 1.4)), a)
            paste_center(frame, tx, W / 2, y - 18 * ease_io((T - t_in) / 2))
    return frame


# =====================================================================
# 3) LO-FI / скрапбук — полароиды падают на бумагу
# =====================================================================
LB = 60 / 84
LBAR = 4 * LB
LOFI_DUR = 21 * LB
LOFI_CHORDS = [["F2", "A3", "C4", "E4", "G4"], ["E2", "G3", "B3", "D4"], ["D2", "F3", "A3", "C4", "E4"],
               ["C2", "E3", "G3", "B3", "D4"], ["F2", "A3", "C4", "E4", "G4"], ["C2", "E3", "G3", "B3"]]
LOFI_MEL = [[("C5", 0.5), ("A4", 1.5), ("G4", 2.5)], [("B4", 0.5), ("D5", 2), ("E5", 3.5)],
            [("F5", 0.5), ("E5", 1.5), ("C5", 2.5)], [("D5", 0.5), ("B4", 1.5), ("G4", 3)],
            [("A4", 0.5), ("C5", 1.5), ("E5", 2.5)], [("G5", 0)]]


def swing(b):
    return math.floor(b) + (0.58 if abs(b % 1 - 0.5) < 1e-6 else b % 1)


def lofi_music():
    m = Mix(LOFI_DUR + 0.5)
    for bar, ch in enumerate(LOFI_CHORDS):
        b0 = bar * 4
        last = bar == len(LOFI_CHORDS) - 1
        for n in ch[1:]:
            m.add("keys", rhodes(hz(n), 2.2 * LB), (b0) * LB, 0.12)
            if not last:
                m.add("keys", rhodes(hz(n), 1.2 * LB), swing(b0 + 2.5) * LB, 0.08)
        m.add("bass", bass(hz(ch[0]), 1.8 * LB), b0 * LB, 0.6)
        if not last:
            m.add("bass", bass(hz(ch[0]) * 1.5, 0.8 * LB), swing(b0 + 2.5) * LB, 0.4)
        for n, st in LOFI_MEL[bar]:
            m.add("mel", bell(hz(n), LB), (b0 + st) * LB, 0.25)
        if last:
            break
        for k, b in enumerate([0, 1.5, 2.5]):
            m.add("drums", kick(), swing(b0 + b) * LB, 0.8 if k == 0 else 0.55)
        for b in (1, 3):
            m.add("drums", snare_soft(), (b0 + b) * LB, 0.5)
        for e in range(8):
            m.add("hats", hat(), swing(b0 + e / 2) * LB, 0.14 if e % 2 == 0 else 0.09)
    # винил: потрескивание + шипение
    n = m.n
    cr = np.zeros(n)
    idx = rng.integers(0, n, int(LOFI_DUR * 14))
    cr[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(0.2, 1, len(idx))
    m.stems["vinyl"] = filt(cr, 3000, "high", 1) * 0.35 + filt(rng.standard_normal(n), 5000) * 0.015
    return m.render({"keys": (0.45, 0.35, 2200, False), "bass": (0.5, 0.0, 600, False),
                     "mel": (0.62, 0.45, 4000, False), "drums": (0.5, 0.05, 3500, False),
                     "hats": (0.58, 0.0, 6000, False), "vinyl": (0.5, 0.0, None, False)}, fade_out=1.2)


def paper():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([255, 230, 238]), np.array([234, 226, 255])
    a = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3)).copy()
    a += rng.normal(0, 3.5, (H, W, 1))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for yy in range(30, H, 54):
        for xx in range(30, W, 54):
            d.ellipse((xx - 2, yy - 2, xx + 2, yy + 2), fill=(222, 196, 222))
    return img


PAPER = paper()


def polaroid(box, caption, width=440, bottom=100):
    x0, y0, x1, y1 = box
    ph = photo.crop(box)
    ph = ph.resize((width, int(width * (y1 - y0) / (x1 - x0))), Image.LANCZOS)
    pad = 22
    card = Image.new("RGBA", (ph.width + 2 * pad, ph.height + pad + bottom), (255, 253, 248, 255))
    card.paste(ph, (pad, pad))
    if caption:
        f = font(SERIF_I, 46 if width < 600 else 58)
        d = ImageDraw.Draw(card)
        tw = d.textlength(caption, font=f)
        d.text(((card.width - tw) / 2, ph.height + pad + (bottom - 60) / 2), caption, font=f, fill=(90, 60, 90))
    tape = Image.new("RGBA", (150, 46), (255, 240, 170, 170))
    tape = tape.rotate(random.uniform(-8, 8), Image.BICUBIC, expand=True)
    full = Image.new("RGBA", (card.width + 80, card.height + 110), (0, 0, 0, 0))
    shadow = Image.new("RGBA", full.size, (0, 0, 0, 0))
    shadow.paste((60, 20, 60, 110), (48, 72), card.split()[3])
    full.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    full.alpha_composite(card, (40, 55))
    full.alpha_composite(tape, ((full.width - tape.width) // 2, 55 - tape.height // 2))
    return full


random.seed(5)
LOFI_POLS = [  # (кроп, подпись, центр, угол) — приземление на каждую «снейр»-долю
    ((150, 60, 700, 540), "шарики", (300, 560, -8)),
    ((10, 590, 340, 920), "с днём рождения!", (780, 640, 7)),
    ((250, 700, 540, 990), "бантик", (320, 1060, 5)),
    ((480, 780, 780, 1080), "сердечки", (770, 1130, -6)),
    ((40, 940, 360, 1260), "она", (310, 1560, -4)),
    ((500, 990, 790, 1280), "розы", (760, 1590, 8)),
]
LOFI_CARDS = []
for (box, cap, (cx, cy, ang)) in LOFI_POLS:
    p = polaroid(box, cap, 360)
    LOFI_CARDS.append((p, p.rotate(ang, Image.BICUBIC, expand=True), cx, cy, ang))
LOFI_BIG = polaroid((0, 0, photo.width, photo.height), "сделано с любовью", 640, 120)
LOFI_BIG_ANG = -3
LOFI_BIG_ROT = LOFI_BIG.rotate(LOFI_BIG_ANG, Image.BICUBIC, expand=True)
LOFI_TITLE = text_badge(["Подарок своими руками"], 64, fill=(255, 255, 255), fg=(120, 50, 130), path=SERIF_BI)
LOFI_CTA = text_badge(["Сделаю такой же для тебя —", "пиши в Директ"], 56, fill=PINK, path=SERIF_BI)
LOFI_HEARTS = [(heart(s, c), x, y, r) for s, c, x, y, r in [
    (90, PINK, 170, 440, -15), (70, PURPLE, 930, 520, 12), (80, (255, 150, 180), 140, 1330, 10),
    (100, PINK, 940, 1300, -10), (60, (255, 190, 90), 880, 330, 20)]]
LAND = [(1 + 2 * i) * LB for i in range(len(LOFI_POLS))]
BIG_LAND = 13 * LB


def drop(frame, card_raw, card_rot, cx, cy, ang, t_land, T, fall=0.4):
    t0 = t_land - fall
    if T < t0:
        return
    if T >= t_land + 0.3:
        paste_center(frame, card_rot, cx, cy)
        return
    k = (T - t0) / fall
    if k < 1:
        s = lerp(1.5, 1.0, k * k)
        a = clamp(k * 2.5, 0, 1)
        img = with_alpha(scaled(card_raw, s).rotate(ang + 18 * (1 - k), Image.BICUBIC, expand=True), a)
        paste_center(frame, img, cx, cy - 120 * (1 - k))
    else:  # лёгкий отскок после приземления
        s = 1 + 0.035 * math.sin((T - t_land) / 0.3 * math.pi)
        paste_center(frame, scaled(card_rot, s), cx, cy)


def lofi_frame(T):
    frame = PAPER.copy()
    wob = math.sin(T * 1.3) * 1.5
    t_title = ease_out_back(T / 0.5)
    if T > 0:
        paste_center(frame, scaled(LOFI_TITLE.rotate(-2 + wob * 0.3, Image.BICUBIC, expand=True),
                                   lerp(0.5, 1, t_title)), W / 2, 180)
    for (raw, rot, cx, cy, ang), tl in zip(LOFI_CARDS, LAND):
        drop(frame, raw, rot, cx, cy, ang, tl, T)
    if T >= BIG_LAND - 0.5:
        k = clamp((T - (BIG_LAND - 0.5)) / 0.5, 0, 1)
        veil = Image.new("RGBA", (W, H), (255, 235, 245, int(150 * k)))
        frame.paste(veil, (0, 0), veil)
        drop(frame, LOFI_BIG, LOFI_BIG_ROT, W / 2, 900, LOFI_BIG_ANG, BIG_LAND, T, fall=0.5)
        for i, (hi, x, y, r) in enumerate(LOFI_HEARTS):
            ti = BIG_LAND + 0.25 + i * 0.18
            if T >= ti:
                s = ease_out_back((T - ti) / 0.35) * (1 + 0.06 * math.sin(T * 5 + i))
                paste_center(frame, scaled(hi, max(0.01, s)).rotate(r, Image.BICUBIC, expand=True), x, y)
        if T >= BIG_LAND + 0.9:
            s = ease_out_back((T - BIG_LAND - 0.9) / 0.4)
            paste_center(frame, scaled(LOFI_CTA.rotate(2, Image.BICUBIC, expand=True), max(0.01, s)), W / 2, 1720)
    base.overlay_particles(frame, T)
    return frame


# =====================================================================
VARIANTS = {
    "pop": (POP_DUR, pop_frame, pop_music),
    "cinema": (CINEMA_DUR, cinema_frame, cinema_music),
    "lofi": (LOFI_DUR, lofi_frame, lofi_music),
}

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in sys.argv[1:] or VARIANTS:
        dur, fn, mus = VARIANTS[name]
        encode(name, dur, fn, mus(), crf=25 if name == "cinema" else 18)  # зерно плохо жмётся
