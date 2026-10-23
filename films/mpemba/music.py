# Score + SFX for 《姆潘巴悬案》 The Mpemba File — synthesized in code.
# 100 BPM (beat 0.6 s, bar 2.4 s), 52.8 s = 22 bars. D minor → D major tag.
import numpy as np
from scipy.signal import lfilter, butter
import wave, sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music.wav')

SR = 44100
TK = 1.08                      # authored timeline -> video time (108 BPM original speed)
DUR = 54.4 / TK                # 50.370 s
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)
BEAT = 0.6
BAR = 2.4

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 / TK * SR)      # authored (0.6 s grid) time -> video time
    if i >= N or i < 0: return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l * 1.414
    R[i:i + len(sig)] += sig * r * 1.414

def env(n, a=0.002, d=0.2, s=0.0, rel=0.05, hold=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    if hold is None:
        e = e * np.exp(-np.maximum(0, t - a) / d)
    else:
        e = np.where(t < hold, e, e * np.exp(-(t - hold) / rel))
    return e

def lp(x, fc, order=2):
    b, a = butter(order, min(fc / (SR / 2), 0.99)); return lfilter(b, a, x)
def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)

# ---------- instruments (halftone-dossier palette) ----------
def kick(g=1.0):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 9) + 0.25 * np.exp(-t * 300) * rng.standard_normal(n) * 0.3
    return np.tanh(s * 1.6) * g

def snare():
    n = int(0.22 * SR); t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 1500, 8000) * np.exp(-t * 18)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return noise * 0.7 + tone * 0.5

def clap():
    n = int(0.25 * SR); out = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        i = int(off * SR); m = n - i; t = np.arange(m) / SR
        out[i:] += bp(rng.standard_normal(m), 900, 5000) * np.exp(-t * (60 if k < 2 else 16))
    return out * 0.6

def snap():
    n = int(0.08 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t * 70) * 0.8

def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (18 if open_ else 90)) * 0.35

def pluck(m, dur=0.35, bright=1.0):
    # marimba feel: fundamental + ~4x overtone, fast decay
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 7)
         + 0.35 * bright * np.sin(2 * np.pi * f * 3.99 * t) * np.exp(-t * 30)
         + 0.12 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 12))
    return s * np.minimum(1, t / 0.002)

def bell(m, dur=1.6):
    # music box
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.6)
         + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 11))
    return s * np.minimum(1, t / 0.001)

def bass(m, dur=0.22):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    ph = 2 * np.pi * f * t
    s = np.sin(ph) + 0.3 * np.sign(np.sin(ph)) * 0.5
    s = lp(s, 900)
    return s * env(n, 0.004, 0.18, hold=dur * 0.7, rel=0.03)

def pizz(m, dur=0.18):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = lp(np.sign(np.sin(2 * np.pi * f * t)) * 0.6 + np.sin(2 * np.pi * f * t), 1400)
    return s * np.exp(-t * 16) * np.minimum(1, t / 0.003)

def pad(ms, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in ms:
        f = mtof(m)
        for det in (-0.12, 0.12):
            ph = 2 * np.pi * f * (1 + det / 100) * t
            s += 2 / np.pi * np.arcsin(np.sin(ph))
    s = lp(s / (len(ms) * 2), 2200)
    a = np.minimum(1, t / 0.08); r = np.minimum(1, (dur - t) / 0.15)
    return s * a * np.clip(r, 0, 1)

# ---------- sound effects ----------
def stamp(big=False):
    n = int(0.9 * SR); t = np.arange(n) / SR
    f = 40 + 90 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4 if big else 7))
    click = lp(rng.standard_normal(n), 3000) * np.exp(-t * 55)
    s = np.tanh((boom * 1.4 + click * 0.9) * 1.5)
    if big:
        cr = hp(rng.standard_normal(n), 4000) * np.exp(-t * 3.2) * 0.35
        s = s + cr
    return s

def shutter():
    n = int(0.16 * SR); out = np.zeros(n)
    for off in (0, 0.06):
        i = int(off * SR); m = n - i; t = np.arange(m) / SR
        out[i:] += bp(rng.standard_normal(m), 1200, 6000) * np.exp(-t * 110)
    return out * 0.9

def boing(f0=220, f1=520, dur=0.4):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 14)) + 25 * np.sin(2 * np.pi * 18 * t) * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.7

def pop(f=900):
    n = int(0.12 * SR); t = np.arange(n) / SR
    fr = f * (1 + 1.2 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 35)

def clink(f=2600):
    n = int(0.3 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * 22) * 0.4

def whoosh(dur=0.55, up=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n); out = np.zeros(n)
    seg = 512
    for i in range(0, n, seg):
        p = i / n; fc = 400 + 3500 * (p if up else 1 - p)
        out[i:i + seg] = bp(x[max(0, i - 2048):i + seg], fc * 0.7, fc * 1.3)[-len(x[i:i + seg]):]
    return out * np.sin(np.pi * t / dur) ** 2 * 1.2

def plop():
    n = int(0.25 * SR); t = np.arange(n) / SR
    f = 260 * np.exp(-t * 6) + 80
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.9

def key_click():
    n = int(0.04 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 2500, 9000) * np.exp(-t * 160) * 0.5

def paper():
    n = int(0.3 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 800, 4000) * np.exp(-t * 12) * 0.4

def thump(f0=90):
    n = int(0.4 * SR); t = np.arange(n) / SR
    f = f0 + 60 * np.exp(-t * 20)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10) * 1.1

def sparkle():
    out = np.zeros(int(0.9 * SR))
    for k, m in enumerate([86, 90, 93, 98, 102]):
        b = bell(m, 0.7) * 0.35; i = int(k * 0.045 * SR)
        out[i:i + len(b)] += b[: len(out) - i]
    return out

def rattle():
    out = np.zeros(int(0.5 * SR))
    for k in range(7):
        i = int(k * 0.055 * SR); m = len(out) - i
        out[i:] += bp(rng.standard_normal(m), 300, 1800) * np.exp(-np.arange(m) / SR * 30) * 0.5
    return out

def roll(t0, t1):
    t = t0
    while t < t1:
        p = (t - t0) / (t1 - t0)
        add(snare(), t, 0.12 + 0.45 * p, pan=rng.uniform(-.2, .2))
        t += 0.125 * (1 - p) + 0.03 * p

# ---------- arrangement: user BGM (108 BPM, atempo 1.08 -> 100 BPM grid) ----------
USE_BGM = True
BGM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'bgm_orig.wav')
WINDOW_START = 38.27          # original 108 BPM, beat phase 0.49, bar-aligned
bgm = None
try:
    wb = wave.open(BGM_PATH)
    assert wb.getframerate() == SR and wb.getnchannels() == 2
    bn = wb.getnframes()
    bx = np.frombuffer(wb.readframes(bn), dtype=np.int16).astype(np.float64) / 32768
    bx = bx.reshape(-1, 2).T   # 2 x samples
    i0 = int(WINDOW_START * SR)
    seg_len = min(N, bn - i0)   # bn is per-channel frames — do NOT halve
    g = np.ones(N)
    # duck -7 dB under the five stamp hits (fast dip, 0.55 s recovery)
    for st in (2.4/TK, 5.4/TK, 27.6/TK, 39.6/TK, 49.4/TK):   # authored -> video time
        a, b = int(st * SR), int((st + 0.55) * SR)
        k = int(0.04 * SR)
        if a - k < 0 or b + k > N: continue
        ramp = np.linspace(1, 0.45, k); back = np.linspace(0.45, 1, k)
        g[a:a+k] = ramp; g[a+k:b-k] = 0.45 if b-k > a+k else g[a+k:b-k]
        g[b-k:b] = back
        g[a+k:b-k] = 0.45
    g[: int(0.8 * SR)] *= np.linspace(0.2, 1, int(0.8 * SR))   # fade-in
    g[-int(1.6 * SR):] *= np.linspace(1, 0, int(1.6 * SR))     # fade-out
    seg = bx[:, i0:i0 + seg_len] * g[:seg_len]
    # tame inter-sample overshoot from the BGM's own mastering
    seg = np.stack([lp(seg[0], 18000, order=8), lp(seg[1], 18000, order=8)])
    L[:seg_len] += seg[0] * 0.72
    R[:seg_len] += seg[1] * 0.72
    print('BGM window %.2f-%.2fs mixed under SFX' % (WINDOW_START, WINDOW_START + seg_len / SR))
except Exception as e:
    print('! BGM not used (%s) — falling back is NOT available, mix has SFX only' % e)

# ---------- sound-effect timetable (aligned with index.html) ----------
for i in range(5): add(pop(500 + 90 * i), 0.15 + i * 0.05, 0.24)   # 你信不信？ chars
for i in range(9): add(pop(560 + 70 * i), 0.6 + i * 0.05, 0.2)    # 热水比冷水先结冰。 chars
add(whoosh(0.35), 2.2, 0.3)                   # into the stamp
add(stamp(), 2.4, 0.75)                       # 真事。 stamp
add(whoosh(0.4), 3.9, 0.35)                   # into wipe
add(shutter(), 4.2, 0.6)                      # file-cover flash
add(thump(70), 4.65, 0.7)                     # folder slams down
add(stamp(), 5.4, 0.75)                       # 悬案 stamp
for i, tt in enumerate((5.9, 6.05, 6.2)): add(key_click(), tt, 0.8)
add(whoosh(0.4), 7.5, 0.35)
add(pop(820), 8.05, 0.3)                      # numeral 01
add(paper(), 8.4, 0.4)                        # student steps in
add(plop(), 9.3, 0.7)                         # pot goes in
h = np.sin(2 * np.pi * 55 * np.arange(int(2.0 * SR)) / SR) * 0.05
add(h, 9.6, 1.0)                              # freezer hum
add(pop(700), 10.9, 0.3)                      # liquid turns blue
add(clink(2400), 11.9, 0.5, 0.2)              # crystals start
add(clink(2600), 12.2, 0.45, 0.2)             # crystals deepen
add(sparkle(), 12.55, 0.45)
add(whoosh(0.4), 52.55, 0.3)                  # into sources credit
for i, tt in enumerate((52.85, 52.93, 53.01)):  # three source lines flash in
    add(key_click(), tt, 0.55); add(paper(), tt, 0.22)
add(bell(86, 1.6), 53.9, 0.15, -0.2)          # soft closing bell
add(whoosh(0.35), 12.55, 0.3)                 # teacher enters
add(boing(260, 620), 12.9, 0.45)              # bubble pops
add(whoosh(0.4), 15.3, 0.35)
for tt in (16.4, 17.4, 18.4):                 # index cards pinned
    add(thump(120), tt, 0.35); add(key_click(), tt + 0.02, 0.9)
add(whoosh(0.4), 21.3, 0.35)
for i in range(8): add(key_click(), 22.6 + i * 0.3, 0.35)          # thermometer ticks
add(clink(2900), 25.2, 0.5, 0.2); add(pop(1100), 25.25, 0.35)      # starburst 先冻！
add(paper(), 26.25, 0.45)                     # paper card slides in
add(stamp(), 27.6, 0.7)                       # 实测复现 stamp
add(whoosh(0.4), 28.5, 0.35)
for tt in (29.4, 30.6, 31.8, 33.0, 34.2):     # suspect cards pinned
    add(thump(110), tt, 0.35); add(key_click(), tt + 0.02, 0.9)
add(rattle(), 35.2, 0.8)                      # board shakes
add(whoosh(0.4, up=False), 36.9, 0.3)         # into redaction
for i, tt in enumerate((37.7, 38.0, 38.3)):   # redaction bars
    add(key_click(), tt, 0.7); add(paper(), tt, 0.3)
add(key_click(), 38.75, 1.0); add(paper(), 38.75, 0.4)             # final bar — then silence
# 38.9-39.6: TRUE SILENCE. The stamp lands alone.
add(stamp(big=True), 39.6, 0.68)              # 未结案
add(paper(), 43.9, 0.45)                      # file slides into drawer
add(thump(65), 44.4, 0.8)                     # drawer closes
add(paper(), 45.0, 0.3)
add(whoosh(0.5, up=False), 46.0, 0.35)        # pull back
add(pop(700), 48.15, 0.3)                     # end-card folder
for i in range(14): add(pop(500 + 70 * i), 48.4 + i * 0.03, 0.16)  # line 1 chars
for i in range(12): add(pop(480 + 70 * i), 49.0 + i * 0.03, 0.14)  # line 2 chars
add(stamp(), 49.4, 0.4)                       # small stamp on end folder
# (sparkle removed: stray ding at 47s video time)

# ---------- bus: light compression + limiting + fade-out ----------
mix = np.stack([L, R])
t = np.arange(N) / SR
fade = np.clip((DUR - t) / 1.5, 0, 1)
mix *= fade
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85   # keep crest: no soft-clip, loudnorm handles loudness
out = (mix.T * 32767).astype(np.int16)
w = wave.open(OUT, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(out.tobytes()); w.close()
print('ok', out.shape, '->', OUT)
