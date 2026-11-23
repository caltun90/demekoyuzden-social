# mix.py — original score + sound effects synthesized with numpy, mixed under the voice.
#   python mix.py <story_dir>
# Reads <story>/voice/voice.wav and <story>/audio/cues.json (written by render.mjs), writes <story>/audio/mix.wav
# (+ music.wav / sfx.wav stems). No samples, no libraries beyond numpy + ffmpeg.
import sys, json, subprocess, pathlib
import numpy as np

SR = 48000
story = pathlib.Path(sys.argv[1])
cues = json.load(open(story / 'audio' / 'cues.json', encoding='utf-8'))
DUR = cues['DUR']
N = int(DUR * SR)
rng = np.random.default_rng(7)

def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def save(p, x):
    x = np.clip(x, -1, 1); st = np.stack([x, x], 1) if x.ndim == 1 else x
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', str(p)], input=st.astype(np.float32).tobytes(), check=True)
def band(x, lo, hi):            # FFT band-pass with soft edges
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4); return np.fft.irfft(X * m, len(x))
def env_ad(n, a, d):            # attack / exponential decay envelope (seconds)
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4))
def put(buf, t, x, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if i < len(buf) and j > i: buf[i:j] += x[:j - i] * g

# ------------------------------------------------------------------ instruments
def pluck(freq, dur=1.2, bright=.5):            # Karplus-Strong: an oud-like string
    n = int(dur * SR); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p) * 1.0; out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = .5 * (buf[i % p] + buf[(i + 1) % p]) * (.994 + bright * .004)
    return out * env_ad(n, .002, dur * .5)
def drum(kind='dum'):                            # frame drum: dum (low) / tek (slap)
    n = int(.4 * SR); t = np.arange(n) / SR
    if kind == 'dum': return np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * env_ad(n, .001, .16) * .9
    return band(rng.standard_normal(n), 1500, 6000) * env_ad(n, .0005, .03) * .5 + np.sin(2 * np.pi * 330 * t) * env_ad(n, .001, .04) * .2
def pad(freq, dur, amp=.08):                     # soft drone: detuned saws, low-passed
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(((t * freq * d) % 1 * 2 - 1) for d in (1, 1.004, .997, 2.002))
    x = band(x, 40, 900) * amp
    fade = np.minimum(1, np.minimum(t / .8, (dur - t) / .8)); return x * fade

# ------------------------------------------------------------------ score (Hicaz on D, 100 bpm)
HZ = {'D3': 146.8, 'Eb3': 155.6, 'F#3': 185.0, 'G3': 196.0, 'A3': 220.0, 'Bb3': 233.1, 'C4': 261.6, 'D4': 293.7, 'Eb4': 311.1, 'F#4': 370.0, 'A2': 110.0, 'D2': 73.4}
music = np.zeros(N)
beat = 60 / 100
cut = next((c['t'] for c in cues['cues'] if c['type'] == 'cut'), DUR * .6)
soot = sorted(c['t'] for c in cues['cues'] if c['type'] == 'whoosh')
t_soot = soot[1] if len(soot) > 1 else cut + 3.6
t_call = soot[2] if len(soot) > 2 else t_soot + 4.2
motif = ['D4', 'Eb4', 'F#4', 'Eb4', 'D4', 'C4', 'Bb3', 'A3']
t = 0.0; k = 0
while t < DUR - .5:
    sec = 'hall' if t < cut else 'kitchen' if t < t_soot else 'soot' if t < t_call else 'call'
    b = int(round(t / beat))
    if sec != 'soot':
        if b % 2 == 0: put(music, t, pluck(HZ[motif[k % len(motif)]], 1.0, .6), .32 if sec != 'call' else .26); k += 1
        if sec == 'kitchen' and b % 2 == 1: put(music, t, pluck(HZ['A3'], .6, .8), .18)
    if b % 4 == 0: put(music, t, drum('dum'), .5 if sec != 'call' else .3)
    if b % 4 == 2 and sec != 'call': put(music, t, drum('tek'), .35)
    if sec == 'hall' and b % 4 == 3: put(music, t + beat / 2, drum('tek'), .25)
    t += beat
put(music, 0, pad(HZ['D2'], cut + .3, .07))
put(music, t_soot, pad(HZ['A2'] * .5, t_call - t_soot + .3, .1))
put(music, t_call, pad(HZ['D3'], DUR - t_call, .06))
# final resolve chord
for f in ('D3', 'A3', 'D4', 'F#4'): put(music, DUR - 1.4, pluck(HZ[f], 1.4, .3), .3)

# ------------------------------------------------------------------ effects
sfx = np.zeros(N)
def noise(d): return rng.standard_normal(int(round(d * SR)))
for c in cues['cues']:
    t0, ty, d = c['t'], c['type'], c.get('dur', 1.0)
    n = int(d * SR)
    if ty == 'whoosh':
        x = noise(.45); tt = np.arange(len(x)) / SR
        x = band(x, 300, 3500) * np.sin(np.pi * tt / .45) ** 2; put(sfx, t0, x, .35)
    elif ty == 'rise':                           # the camera flies up with the smoke: air that swells, then stops dead
        x = noise(d); tt = np.arange(len(x)) / SR
        x = band(x, 250, 2600) * (tt / d) ** 1.7 * np.minimum(1, (d - tt) / .06); put(sfx, t0, x, .3)
    elif ty == 'lock':                           # a padlock snapping shut: a dry click, a low thunk, a short metal ring
        nb = int(.6 * SR); tt = np.arange(nb) / SR
        x = band(noise(.6), 1800, 8000)[:nb] * env_ad(nb, .0004, .01) * 1.3 + np.sin(2 * np.pi * 150 * tt) * env_ad(nb, .001, .045) * .9
        x += sum(np.sin(2 * np.pi * f * tt) * env_ad(nb, .0005, dc) * a for f, dc, a in [(860, .05, .8), (1730, .1, .6), (2950, .13, .45), (4410, .08, .3)])
        put(sfx, t0, x, .5)
    elif ty == 'shutters':
        for i in range(3):
            x = band(noise(.12), 500, 1800) * env_ad(int(.12 * SR), .001, .025); put(sfx, t0 + i * .13, x, .55)
    elif ty == 'wind':
        x = band(noise(d), 200, 1400); tt = np.arange(len(x)) / SR
        x *= (.55 + .45 * np.sin(2 * np.pi * .7 * tt)) * np.minimum(1, np.minimum(tt / .6, (d - tt) / .6)); put(sfx, t0, x, .16)
    elif ty == 'cut':
        put(sfx, t0, np.sin(2 * np.pi * 90 * np.arange(int(.3 * SR)) / SR) * env_ad(int(.3 * SR), .002, .08), .3)
    elif ty == 'simmer':
        x = band(noise(d), 2000, 8000) * .05
        for _ in range(int(d * 14)):
            tb = rng.uniform(0, d - .1); fb = rng.uniform(300, 750); nb = int(.06 * SR)
            b2 = np.sin(2 * np.pi * np.linspace(fb, fb * 1.6, nb) * np.arange(nb) / SR) * env_ad(nb, .002, .015)
            i = int(tb * SR); x[i:i + nb] += b2 * .25
        put(sfx, t0, x * np.minimum(1, np.arange(len(x)) / SR / .3), .55)
    elif ty == 'boom':
        nb = int(1.2 * SR); tt = np.arange(nb) / SR
        x = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 8)) * tt) * env_ad(nb, .003, .35) + band(noise(1.2), 60, 400) * env_ad(nb, .002, .12) * .4
        put(sfx, t0, x, .6)
    elif ty == 'scrape':
        x = np.zeros(n)
        for i in range(int(d * 5)):
            ns = int(.14 * SR); s = band(noise(.14), 1800, 5000) * np.sin(np.pi * np.arange(ns) / ns)
            j = int(i / 5 * SR); x[j:j + ns] += s[:max(0, min(ns, n - j))]
        put(sfx, t0, x, .22)
    elif ty == 'stir':
        x = band(noise(d), 150, 900); tt = np.arange(len(x)) / SR
        x *= (.5 + .5 * np.sin(2 * np.pi * 1.1 * tt)) ** 2 * np.minimum(1, np.minimum(tt / .2, (d - tt) / .2)); put(sfx, t0, x, .3)
    elif ty == 'pen':
        x = np.zeros(n)
        for _ in range(int(d * 7)):
            ts = rng.uniform(0, d - .2); ns = int(rng.uniform(.08, .2) * SR)
            s = band(noise(ns / SR), 2500, 9000) * np.sin(np.pi * np.arange(ns) / ns) ** 2; j = int(ts * SR); x[j:j + ns] += s[:max(0, min(ns, n - j))]
        put(sfx, t0, x, .12)
    elif ty == 'shimmer':
        nb = int(2.2 * SR); tt = np.arange(nb) / SR
        x = sum(np.sin(2 * np.pi * f * tt) * env_ad(nb, .01 + i * .06, .9) for i, f in enumerate([1174.7, 1480, 1760, 2349.3])) / 4
        put(sfx, t0, x, .22)
    elif ty == 'lamps':
        x = band(noise(d), 80, 600) * .25
        for _ in range(int(d * 3)):
            j = int(rng.uniform(0, d - .05) * SR); x[j:j + 200] += rng.standard_normal(200) * .6 * np.exp(-np.arange(200) / 40)
        put(sfx, t0, x * np.minimum(1, np.arange(len(x)) / SR / .5), .06)

# ------------------------------------------------------------------ mix: voice on top, music ducked under it
voice = load(story / 'voice' / 'voice.wav'); voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
win = int(.05 * SR); ve = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, mode='same'))
active = np.convolve((ve > .02).astype(float), np.ones(int(.25 * SR)) / int(.25 * SR), mode='same')
duck = 1 - .45 * np.clip(active, 0, 1)
def rms(x): return np.sqrt(np.mean(x[np.abs(x) > 1e-5] ** 2)) if np.any(np.abs(x) > 1e-5) else 1
vr = rms(voice)
music *= (vr / rms(music)) * 10 ** (-17 / 20)        # music ~17 dB under the voice (before ducking)
sfx *= (vr / max(rms(sfx), 1e-6)) * 10 ** (-16 / 20)  # effects ~11 dB under in LUFS terms
mix = voice + music * duck + sfx
fade = np.ones(N); fl = int(.3 * SR); fade[-fl:] = np.linspace(1, 0, fl); mix *= fade
out = story / 'audio'
save(out / 'music.wav', music * duck); save(out / 'sfx.wav', sfx)
save(out / 'premix.wav', mix / max(1e-6, np.abs(mix).max()) * .7)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out / 'premix.wav'), '-af', 'loudnorm=I=-14:TP=-2.3:LRA=11,aresample=48000', str(out / 'mix.wav')], check=True)
print('OK mix.wav', round(DUR, 2), 's')
