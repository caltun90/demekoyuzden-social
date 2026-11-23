# zarf.py — loudness envelope of a voice file, one value per video frame (0..1), for lip flaps.
#   python zarf.py <voice.wav> <env.json> [fps=30]
import sys, json, subprocess
import numpy as np
wav, out = sys.argv[1], sys.argv[2]
fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-ac', '1', '-ar', '24000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
hop = 24000 // fps
n = len(x) // hop
rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
ref = np.percentile(rms[rms > 1e-4], 95) if (rms > 1e-4).any() else 1
env = np.clip(rms / ref, 0, 1)
env = np.convolve(env, [.25, .5, .25], mode='same')
json.dump([round(float(v), 3) for v in env], open(out, 'w'))
print('OK', n, 'frames')
