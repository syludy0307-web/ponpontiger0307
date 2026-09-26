"""Soundtrack for the evening forest walk (17.5 s), numpy only, deterministic.
wind + leaf rustle, evening birds, leaf-crunch footsteps synced to the walk cycles, soft music."""
import math
import numpy as np
from audio import SR, midi, pluck, pad_chord, lp_fft, hp_fft, write_wav

DUR = 17.5
N = int(SR * DUR)
rng = np.random.RandomState(4242)


def put(buf, sig, t0, pan=0.0, gain=1.0):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 + len(sig) <= 0:
        return
    if i0 < 0:
        sig = sig[-i0:]; i0 = 0
    sig = sig[:N - i0]
    l = math.cos((pan + 1) * math.pi / 4) * gain
    r = math.sin((pan + 1) * math.pi / 4) * gain
    buf[0, i0:i0 + len(sig)] += sig * l
    buf[1, i0:i0 + len(sig)] += sig * r


def wind():
    n = N
    t = np.arange(n) / SR
    base = lp_fft(rng.randn(n), 500) * 0.6
    gust = 0.55 + 0.45 * np.sin(2 * math.pi * t / 6.3) * np.sin(2 * math.pi * t / 2.9 + 1)
    rustle = hp_fft(lp_fft(rng.randn(n), 6500), 1800)
    rust_env = np.clip(0.3 + 0.7 * np.sin(2 * math.pi * t / 4.1 + 0.5) ** 2, 0, 1)
    l = base * gust + rustle * rust_env * 0.25
    r = lp_fft(rng.randn(n), 500) * 0.6 * gust + hp_fft(lp_fft(rng.randn(n), 6500), 1800) * rust_env * 0.25
    return np.stack([l, r]) * 0.35


def chirp(f0, f1, dur=0.07, vib=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / dur) ** 0.7 + vib * np.sin(2 * math.pi * 38 * t) * f0 * 0.03
    s = np.sin(2 * math.pi * np.cumsum(f) / SR)
    e = np.sin(math.pi * t / dur) ** 1.5
    return s * e


def bird_phrase(kind):
    parts = []
    if kind == 0:
        for i in range(3):
            parts.append((i * 0.11, chirp(3100 + 120 * i, 4200 + 150 * i, 0.07, 1)))
    elif kind == 1:
        parts.append((0.0, chirp(4800, 3400, 0.18, 0.5)))
        parts.append((0.24, chirp(4600, 3300, 0.16, 0.5)))
    else:
        for i in range(5):
            parts.append((i * 0.065, chirp(3600, 5200, 0.04)))
    L = int((max(p[0] for p in parts) + 0.25) * SR)
    out = np.zeros(L)
    for t0, s in parts:
        i0 = int(t0 * SR)
        out[i0:i0 + len(s)] += s[:L - i0]
    return out


def crunch(bright=1.0, dur=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = rng.randn(n)
    body = hp_fft(lp_fft(nz, 3200 * bright), 500) * np.exp(-t * 34)
    clicks = np.zeros(n)
    for _ in range(9):
        i = rng.randint(0, int(n * 0.7))
        clicks[i:i + 30] += rng.uniform(-1, 1) * np.exp(-np.arange(min(30, n - i)) / 6.0)
    clicks = hp_fft(clicks, 1500)
    return (body * 0.8 + clicks * 0.5) * np.minimum(1, t / 0.004)


def music(buf):
    prog = [([53, 60, 64, 67, 69], 0.0, 4.6), ([50, 57, 60, 64, 65], 4.4, 4.6),
            ([46, 53, 57, 60, 62], 8.8, 4.6), ([48, 55, 60, 62, 64], 13.2, 2.2), ([53, 60, 64, 67, 72], 15.2, 2.4)]
    for notes, t0, d in prog:
        put(buf, pad_chord(notes, d + 0.6), t0, 0.0, 0.8)
    mel = [(0.9, 72), (1.6, 74), (2.3, 77), (3.4, 76), (4.6, 74), (5.3, 72), (6.0, 69), (7.2, 72),
           (8.9, 77), (9.35, 79), (9.8, 81), (10.9, 79), (11.6, 77), (12.4, 74), (13.3, 76), (14.2, 72),
           (15.3, 77), (16.0, 81)]
    for i, (t0, m) in enumerate(mel):
        p = -0.3 + 0.6 * ((i * 37) % 10) / 10
        put(buf, pluck(midi(m), 2.0, 0.45), t0, p, 0.30)
        put(buf, pluck(midi(m), 2.0, 0.45), t0 + 0.36, -p, 0.08)
    put(buf, pluck(midi(96), 2.4, 0.3), 9.0, 0.3, 0.10)  # soft chime on the close-up


def build():
    buf = np.zeros((2, N))
    buf += wind()
    birds = [(0.5, 0, 0.5), (1.7, 1, -0.6), (2.8, 2, 0.3), (4.5, 0, -0.4), (6.1, 1, 0.6), (7.6, 2, -0.2),
             (10.4, 0, 0.5), (12.6, 1, -0.5), (14.3, 2, 0.4), (15.9, 0, -0.3)]
    for t0, k, p in birds:
        put(buf, bird_phrase(k), t0, p, 0.05)
    # footsteps: woman contacts at S-local t = k*0.52, dog at (k-0.3)*0.40 (see BackWalkers)
    for start, end, g0, g1 in ((3.2, 9.25, 0.55, 0.32), (13.2, 17.3, 0.22, 0.12)):
        for k in range(0, 40):
            t = start + k * 0.52
            if start + 0.05 <= t <= end:
                g = g0 + (g1 - g0) * (t - start) / (end - start)
                put(buf, crunch(1.0), t, 0.05 * (-1) ** k, g)
            td = start + (k - 0.3) * 0.40
            if start + 0.05 <= td <= end:
                g = (g0 + (g1 - g0) * (td - start) / (end - start)) * 0.45
                put(buf, crunch(1.5, 0.07), td, -0.25, g)
    mus = np.zeros((2, N))
    music(mus)
    buf += mus * 0.9
    t = np.arange(N) / SR
    fade = np.clip(t / 0.5, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1) ** 1.3
    buf = np.tanh(buf * fade * 1.1) / 1.1
    buf /= max(1e-6, np.abs(buf).max()) / 0.8
    return buf.astype(np.float32)


if __name__ == "__main__":
    import sys
    b = build()
    write_wav(sys.argv[1] if len(sys.argv) > 1 else "forest/audio.wav", b)
    print("ok", b.shape)
