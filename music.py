"""Синтез фоновой музыки: «Happy Birthday» (public domain) — музыкальная шкатулка + лёгкий вальсовый бит.

Мелодия в 3/4, 112 BPM: затакт + 8 тактов + хвост = 28 долей = 15 секунд.
Смены сцен в make_reel.py привязаны к сильным долям (константа BEAT).
"""
import wave

import numpy as np

SR = 44100
BPM = 112
BEAT = 60 / BPM
TOTAL_BEATS = 28
DURATION = TOTAL_BEATS * BEAT

rng = np.random.default_rng(3)


def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    return 440.0 * 2 ** ((names[note[:-1]] + 12 * (int(note[-1]) + 1) - 69) / 12)


# (нота, начало в долях, длительность в долях)
MELODY = [
    ("G4", 0, .75), ("G4", .75, .25),
    ("A4", 1, 1), ("G4", 2, 1), ("C5", 3, 1),
    ("B4", 4, 2), ("G4", 6, .75), ("G4", 6.75, .25),
    ("A4", 7, 1), ("G4", 8, 1), ("D5", 9, 1),
    ("C5", 10, 2), ("G4", 12, .75), ("G4", 12.75, .25),
    ("G5", 13, 1), ("E5", 14, 1), ("C5", 15, 1),
    ("B4", 16, 1), ("A4", 17, 1), ("F5", 18, .75), ("F5", 18.75, .25),
    ("E5", 19, 1), ("C5", 20, 1), ("D5", 21, 1),
    ("C5", 22, 3),
    ("G5", 25, .5), ("E5", 25.5, .5), ("C6", 26, 2),
]
# аккорд на каждый такт (такт начинается с доли 1, 4, 7, ...)
CHORDS = [
    (1, ["C3", "E4", "G4", "C5"]), (4, ["G2", "D4", "G4", "B4"]), (7, ["G2", "D4", "F4", "B4"]),
    (10, ["C3", "E4", "G4", "C5"]), (13, ["C3", "E4", "G4", "A#4"]), (16, ["F2", "F4", "A4", "C5"]),
    (19, ["G2", "E4", "G4", "C5"]), (22, ["C3", "E4", "G4", "C5"]), (25, ["C3", "E4", "G4", "C5"]),
]
FINAL_BEAT = 19  # начало финальной сцены — «с днём рождения тебя» (последняя фраза)

N = int(DURATION * SR) + SR
t_all = np.arange(N) / SR


def buf():
    return np.zeros(N)


def add(dst, sig, start_s, gain=1.0):
    i = int(start_s * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    dst[i: i + len(sig)] += sig * gain


def env_t(dur):
    return np.arange(int(dur * SR)) / SR


def bell(f, dur):
    t = env_t(dur + 1.2)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2)
         + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4)
         + 0.2 * np.sin(2 * np.pi * 4.07 * f * t) * np.exp(-t * 9)
         + 0.1 * np.sin(2 * np.pi * 6.1 * f * t) * np.exp(-t * 14))
    return s * np.minimum(1, t / 0.003)


def pluck(f, dur, bright=0.5):
    t = env_t(dur + 0.4)
    s = sum((bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t) for k in range(1, 7))
    e = np.exp(-t * 5) * np.minimum(1, t / 0.004)
    rel = np.clip((dur + 0.4 - t) / 0.4, 0, 1)
    return s * e * rel


def pad(f, dur):
    t = env_t(dur + 0.3)
    s = sum(np.sin(2 * np.pi * f * d * t + d) for d in (0.996, 1.0, 1.004)) / 3
    s += 0.3 * np.sin(2 * np.pi * 2 * f * t)
    a = np.minimum(1, t / 0.25) * np.clip((dur + 0.3 - t) / 0.5, 0, 1)
    return s * a


def bass(f, dur):
    t = env_t(dur)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.exp(-t * 2.5) * np.minimum(1, t / 0.005) * np.clip((dur - t) / 0.05, 0, 1)


def kick():
    t = env_t(0.35)
    ph = 2 * np.pi * np.cumsum(45 + 90 * np.exp(-t * 30)) / SR
    return np.sin(ph) * np.exp(-t * 9)


def hp_noise(n, amount=1):
    x = rng.standard_normal(n)
    for _ in range(amount):
        x = np.diff(x, prepend=0)
    return x / np.max(np.abs(x))


def clap():
    t = env_t(0.25)
    n = hp_noise(len(t))
    e = np.exp(-t * 25) + 0.6 * np.exp(-np.maximum(0, t - 0.012) * 30) * (t > 0.012)
    return n * e


def hat():
    t = env_t(0.06)
    return hp_noise(len(t), 2) * np.exp(-t * 70)


def crash():
    t = env_t(2.5)
    return hp_noise(len(t), 2) * np.exp(-t * 1.8) * np.minimum(1, t / 0.005)


def riser(dur):
    t = env_t(dur)
    n = hp_noise(len(t))
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 1500 * (t / dur) ** 2) / SR)
    return (0.6 * n + 0.4 * sweep) * (t / dur) ** 2


def pan(sig, p):
    return np.stack([sig * np.sqrt(1 - p), sig * np.sqrt(p)], axis=1)


def reverb(x, mix=0.25):
    out = x.copy()
    for d, g in ((0.0297, 0.5), (0.0371, 0.45), (0.0411, 0.42), (0.0437, 0.4)):
        k = int(d * SR)
        y = np.zeros_like(x)
        for i in range(0, len(x), k):  # фидбек-комб поблочно
            seg = x[i: i + k]
            y[i: i + len(seg)] = seg + (g * y[i - k: i - k + len(seg)] if i >= k else 0)
        out += mix * y / 4
    return out


def build():
    mel, box, chords, low, drums, fx = buf(), buf(), buf(), buf(), buf(), buf()

    for note, st, du in MELODY:
        f = hz(note)
        add(box, bell(f, du * BEAT), st * BEAT, 0.55)
        add(mel, pluck(f, du * BEAT * 0.9, 0.55), st * BEAT, 0.35)
        if st >= FINAL_BEAT:  # в финале мелодия удвоена октавой ниже
            add(mel, pluck(f / 2, du * BEAT * 0.9, 0.4), st * BEAT, 0.25)

    for bar, (b, notes) in enumerate(CHORDS):
        dur = 3 * BEAT if b < 25 else 3 * BEAT + 1.0
        root = hz(notes[0])
        for n in notes[1:]:
            add(chords, pad(hz(n), dur), b * BEAT, 0.09)
        add(low, bass(root, BEAT * 0.95), b * BEAT, 0.55)
        if b >= 4 and b < 25:  # «ум-ца-ца»: стабы на 2 и 3 долю
            for k in (1, 2):
                for n in notes[1:]:
                    add(chords, pluck(hz(n), BEAT * 0.35, 0.35), (b + k) * BEAT, 0.08)
                add(low, bass(root * 2, BEAT * 0.4), (b + k) * BEAT, 0.12)

    # ритм-секция: вступает во 2-м такте, в финале — плотнее
    for b in range(4, 25):
        pos = (b - 1) % 3
        tt = b * BEAT
        full = b >= FINAL_BEAT
        if pos == 0:
            add(drums, kick(), tt, 0.9 if full else 0.7)
        else:
            add(drums, clap(), tt, 0.28 if full else 0.18)
        add(drums, hat(), tt + BEAT / 2, 0.12)
        if full:
            add(drums, hat(), tt, 0.1)
    add(drums, kick(), 25 * BEAT, 0.9)

    # переходы
    for b in (7, 13):
        add(fx, crash(), b * BEAT, 0.08)
    add(fx, riser(2 * BEAT), (FINAL_BEAT - 2) * BEAT, 0.22)
    add(fx, crash(), FINAL_BEAT * BEAT, 0.2)
    for i, n in enumerate(["C6", "E6", "G6", "C7", "E7", "G7"]):  # блестящий глиссандо
        add(fx, bell(hz(n), 0.3), FINAL_BEAT * BEAT + i * 0.04, 0.12)

    mix = (pan(reverb(box, 0.45), 0.6) + pan(reverb(mel, 0.2), 0.42) + pan(reverb(chords, 0.3), 0.5)
           + pan(low, 0.5) + pan(drums, 0.5) + pan(reverb(fx, 0.3), 0.55))
    # мягкая сатурация, fade-in/out
    mix = np.tanh(mix / np.max(np.abs(mix)) * 1.3)  # лёгкий лимитер без перегруза
    n_out = int(DURATION * SR)
    mix = mix[:n_out]
    fade = np.ones(n_out)
    fade[: int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
    fo = int(1.2 * SR)
    fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    mix *= fade[:, None]
    return mix / np.max(np.abs(mix)) * 0.89


def write_wav(path):
    data = (build() * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path


if __name__ == "__main__":
    print(write_wav("music.wav"), f"{DURATION:.2f}s")
