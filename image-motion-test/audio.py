"""16 s soundtrack, synthesized with numpy (deterministic): calm intro -> 120 BPM groove -> outro.
Section boundaries match the cuts at 5.0 s and 12.0 s."""
import math
import struct
import numpy as np

SR = 48000
DUR = 16.0
BPM = 120.0
SPB = 60.0 / BPM
N = int(SR * DUR)
rng = np.random.RandomState(1234)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def env_adsr(n, a, d, s, r, sus_len):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sl = max(0, int(sus_len * SR))
    e = np.concatenate([np.linspace(0, 1, max(a, 1), endpoint=False),
                        np.linspace(1, s, max(d, 1), endpoint=False),
                        np.full(sl, s, np.float64),
                        np.linspace(s, 0, max(r, 1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def add(buf, sig, t0, pan=0.0, gain=1.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    sig = sig[:N - i0]
    l = math.cos((pan + 1) * math.pi / 4) * gain
    r = math.sin((pan + 1) * math.pi / 4) * gain
    buf[0, i0:i0 + len(sig)] += sig * l
    buf[1, i0:i0 + len(sig)] += sig * r


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # small signals only
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def hp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def pluck(freq, dur=1.6, bright=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k, amp in enumerate([1.0, 0.5, 0.32, 0.2, 0.12, 0.07], start=1):
        s += amp * (bright ** (k - 1)) * np.sin(2 * math.pi * freq * k * t + 0.3 * k) * np.exp(-t * (2.2 + 1.3 * k))
    s *= np.minimum(1, t / 0.004)
    return s


def pad_chord(notes, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        f = midi(m)
        for det in (-0.07, 0.0, 0.07):
            ph = rng.uniform(0, 2 * math.pi)
            ff = f * 2 ** (det / 12)
            # soft saw (few harmonics)
            for k in range(1, 7):
                s += (0.5 / k) * np.sin(2 * math.pi * ff * k * t + ph * k) / 3
    s = lp_fft(s, 1400)
    e = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 0.8)
    return s * np.clip(e, 0, 1) / max(1, len(notes))


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 28)
    ph = 2 * math.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7.5)
    s += 0.25 * np.sin(ph * 2) * np.exp(-t * 30)
    return np.tanh(1.6 * s) * 0.95


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    nz = rng.randn(n)
    nz = hp_fft(lp_fft(nz, 5200), 900)
    e = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        e += np.where(t >= d, np.exp(-(t - d) * 60), 0)
    e += 0.6 * np.exp(-t * 14)
    return nz * e * 0.55


def hat(open_=False):
    n = int((0.25 if open_ else 0.08) * SR)
    t = np.arange(n) / SR
    nz = hp_fft(rng.randn(n), 7000)
    return nz * np.exp(-t * (18 if open_ else 70)) * 0.22


def bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 9):
        s += np.sin(2 * math.pi * freq * k * t) / k * (0.8 ** (k - 1))
    s = lp_fft(s, 520)
    return s * env_adsr(n, 0.005, 0.12, 0.6, 0.06, dur - 0.2) * 0.5


def stab(notes, dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        f = midi(m)
        for det in (-0.1, 0.1):
            for k in range(1, 6):
                s += np.sin(2 * math.pi * f * 2 ** (det / 12) * k * t) / k
    s = lp_fft(s, 2600)
    return s * np.exp(-t * 11) * 0.12


def whoosh(dur, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = rng.randn(n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        u = i / n if up else 1 - i / n
        a = math.exp(-2 * math.pi * (300 + 5200 * u * u) / SR)
        acc = (1 - a) * nz[i] + a * acc
        y[i] = acc
    y /= max(1e-9, np.abs(y).max())
    e = (t / dur) ** 2 if up else (1 - t / dur) ** 2
    return y * e * 0.3


def pop(freq=900):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.8 * np.exp(-t * 60))
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * 0.25


def build():
    buf = np.zeros((2, N))
    # ---------------- intro 0-5 s: pad + sparse plucks (F major pentatonic), dozing mood
    add(buf, pad_chord([53, 60, 64, 67, 69], 5.6), 0.0, 0.0, 0.95)
    mel = [(0.6, 77, -0.3), (1.25, 81, 0.2), (1.9, 79, -0.1), (2.6, 84, 0.3), (3.3, 81, -0.2),
           (3.75, 79, 0.1), (4.2, 77, -0.25)]
    for t0, m, p in mel:
        add(buf, pluck(midi(m), 1.8, 0.5), t0, p, 0.36)
        add(buf, pluck(midi(m), 1.8, 0.5), t0 + 0.33, -p, 0.10)  # echo
    add(buf, whoosh(0.9, True), 4.1, 0.0, 0.9)
    # ---------------- groove 5-16 s
    prog = [([53, 57, 60, 64], 41), ([55, 59, 62, 65], 43), ([57, 60, 64, 67], 45), ([48, 55, 60, 64], 36)]
    t = 5.0
    beat = 0
    end = 15.5
    k = kick(); c = clap(); h = hat(); ho = hat(True)
    while t < end - 1e-6:
        chord, root = prog[(beat // 4) % 4]
        add(buf, k, t, 0.0, 0.75)
        if beat % 2 == 1:
            add(buf, c, t, 0.05, 0.8)
        add(buf, h, t + SPB / 2, 0.25, 0.9)
        if t >= 12.0:
            add(buf, h, t + SPB / 4, -0.25, 0.5)
            add(buf, h, t + 3 * SPB / 4, -0.25, 0.5)
        if beat % 4 == 3:
            add(buf, ho, t + SPB / 2, 0.3, 0.6)
        add(buf, bass(midi(root), SPB * 0.45), t, 0.0, 0.8)
        add(buf, bass(midi(root + 12), SPB * 0.3), t + SPB / 2, 0.0, 0.5)
        add(buf, stab([n + 12 for n in chord]), t + SPB / 2, -0.2 if beat % 2 else 0.2, 0.9)
        t += SPB
        beat += 1
    add(buf, pad_chord([53, 60, 64, 67, 72], 11.0), 5.0, 0.0, 0.25)
    # crash-ish swell at 12.0 and the pose pops at the start of shot 3
    add(buf, hat(True) * 2.2, 12.0, 0.0, 0.8)
    for i in range(8):
        add(buf, pop(760 + 60 * i), 12.0 + 0.05 * i, -0.5 + i / 7.0, 0.5)
    add(buf, whoosh(0.35, False), 12.95, 0.0, 0.6)
    # final chord + fade
    add(buf, pad_chord([53, 60, 64, 69, 72], 1.2), 15.0, 0.0, 0.6)
    fade = np.ones(N)
    i0 = int(15.4 * SR)
    fade[i0:] = np.linspace(1, 0, N - i0) ** 1.5
    buf *= fade
    # gentle bus glue
    buf = np.tanh(buf * 1.1) / 1.1
    buf /= max(1e-6, np.abs(buf).max()) / 0.8
    return buf.astype(np.float32)


def write_wav(path, buf):
    data = np.clip(buf.T, -1, 1).astype('<f4').tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 3, 2, SR, SR * 8, 8, 32))
        f.write(b'data' + struct.pack('<I', len(data)) + data)


if __name__ == "__main__":
    import sys
    b = build()
    write_wav(sys.argv[1] if len(sys.argv) > 1 else "out/audio.wav", b)
    print("ok", b.shape, float(np.abs(b).max()))
