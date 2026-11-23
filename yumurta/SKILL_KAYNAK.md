---
name: yumurta-stili
description: Make a 30-65 s vertical story Short in the "egg-head" style (flat white egg-head cartoon cards with a plum outline and lidded eyes in a saturated 3D world with black ink lines, visible light sources with bloom and real cast shadows, gliding camera that never stops, whip zooms with motion blur, one-word captions, voice narration with the "You see / Bakın" pivot) using three.js + Canvas 2D + puppeteer frame capture. No Remotion, no Blender. Use when the user asks for a short "in the egg-head style", "yumurta kafa stiliyle" or "like the İs Odası short".
---

# Egg-head story Short (three.js + Canvas 2D, frame capture)

Sample: `stories/is-odasi/` (38.8 s, Turkish, Mimar Sinan's soot room, AI Studio voice trimmed and sped up ×1.3). The finished video is `ornek/is-odasi.mp4`.

Measured style targets: `STIL_KITABI.md` (summary) and `analiz/` (seven reports, raw numbers in `analiz/veri/`). Annotated reference frames: `referans/`. Read the style book before writing anything.

## Rules

- Story, characters and voice are always our own. Reference videos are study material only: never upload or ship them, and never say the reference channel's name in a voice-over or description.
- Every fact in the script is checked first. When sources disagree on a number, don't state the number ("yüzlerce", not "275").
- Every visual event is pinned to a word: in `story.js` use `W('word', n)`, never hand-typed seconds. If the voice changes, re-run `kelime_saat.py` and everything re-aligns.
- No pure black anywhere. The darkest tone is navy or violet (grade `lift`). Character ink is plum `#2a1a2c`; world ink is `#0b0a0c`.
- Heads are pure white in every set. Only a hint of the scene's light is allowed (see `FACE` / `GRADE` in the sample).
- The camera never stands still. Holds creep in about 0.25 %/frame and truck sideways (`drift`). At most one or two hard cuts per Short.
- The hook is three or four pictures in the first 5 s, one per phrase of the first sentence (9 of the 10 reference videos do this). In frame 0 the character is already doing something with the story's key object. One long shot of a standing character is not a hook.
- A hand that touches something must really touch it. If the thing is a 3D object (a pen on paper, a stirring stick, a lamp), that arm is an `Arm3D`, not a drawn arm.
- The light has a source you can see. Every set has ONE key light that is in the picture or plainly implied (a lamp, a window, the moon). It is warm against a cool fill (or the reverse) and it casts real shadows, the characters' included. Flat, even light is the most common reason a render looks cheap (contrast below 0.57 is flatter than every reference; `analiz/isik.md`).
- Faces follow the measured anatomy (`analiz/karakter.md`): a head wider than tall that is NOT an ellipse (pointed crown, fuller jaw, a bulge toward the side it looks at), an outline about three times heavier underneath than on top, eyes as the lower half of a dark disc hanging from a lid line and 0.28 head widths apart (not dots, not far apart), brows above them, the whole face slid toward where the character looks, 3.5 heads tall. The head's shade is a pale lavender crescent (about x0.89), never grey. Expressions change with the beat (a wide-eyed shock, a smug half-lid, a grin with teeth), not once per scene.
- A character that is not acting stands still: no idle bob, no breathing loop. It blinks every 0.9-2.4 s, four frames long (half, shut, shut, half), and once across every change of expression: `blinkAt(t, seed, [swap times])`. Acting lands two frames BEFORE its word.
- Lines: the world's ink is thin (3.4 px near, 2.2 px far at 1080 wide; creases thinner still) and is drawn before the lens blur. Painted texture lines (stone joints, plank gaps) are thinner and lighter than the ink: a dark tint of the surface, never black. The characters' own outline is the heaviest line in the frame. Targets: `analiz/cizgi.md`.
- Colour: warm and cool share the picture. Over a whole reference video about half the colour is warm and 40 % is blue; no reference has less than a sixth of blue. A set where one hue family holds 90 % (orange walls under orange light) is outside the style: give the walls a cool colour, or let the night be the ambient colour and the lamps make warm POOLS. A shadow is about half as bright as the lit part of the same surface and keeps its hue or goes cooler, never brown. Targets: `analiz/renk.md`.
- A lamp's glow is broad and flat (still a third of its strength 40 px from the source at 1080 wide), and only light sources glow. A lamp the camera comes close to also carries a weak, wide halo at its own depth (`kandil({ halo })`, or `glow()` for another lamp). About a third of the medium shots are framed past something close to the lens, which the lens blurs.

## Pipeline

1. **Targets.** Read `STIL_KITABI.md`, then the report for whatever you are about to build (`analiz/isik.md` before lighting a set, `analiz/karakter.md` before a new character). The numbers were measured on 10 reference Shorts and on the sample; `referans/` shows them drawn on real frames (line widths by colour, a lamp's glow rings, hue-family bars, face proportions, camera motion). Never copy a reference story, character or frame; only the numbers.
2. **Topic and facts.** One surprising true story with a physical or social mechanism, plus an everyday analogy that explains it. Write the facts and sources at the top of `stories/<name>/SCRIPT.md`.
3. **Script.** 30-65 s. Measured pace is 3.7 words/s in English; 2.4-2.9 words/s in Turkish reads the same. Beats:
   1. Paradox hook at 0.0 s.
   2. "Bakın," + setup.
   3. Someone laughs or objects (a quoted line).
   4. Escalation in 2-3 steps.
   5. Mechanism through an everyday analogy.
   6. One-line payoff (optionally cut mid-sentence so it loops into the hook).
4. **Voice.** `voice/voice.wav`. If the take is slow or has long pauses (TTS often is), first:
   - run `kelime_saat.py` on the raw take;
   - then `python tools/bosluk_kes.py raw.wav raw_words.json voice/voice.wav <tempo>`, which caps pauses at sentence end .22 s, comma .14 s, inside a phrase .09 s and applies `atempo`;
   - pick the tempo that lands at 2.4–2.9 words/s (İs Odası: AI Studio 52.7 s → 49.8 s → ×1.3 = 38.3 s).

   Then:
   - `python tools/kelime_saat.py voice.wav script.txt words.json`, which keeps the script's spelling and takes the times from Whisper.
   - `python tools/zarf.py voice.wav env.json`, the lip-flap envelope.
5. **Story file** (`stories/<name>/story.js`, copy the sample). It exports `NAME`, `FPS`, `DUR`, `CUES`, `setup(ctx)`, `frame(t, ctx)`.
   - **Sets:** far apart in x (0, 200, 300 …). `frame()` shows only the set the camera is in.
   - **Cast:** `new Toon(look, scene)`. Each frame: `place(x,y,z,cam,tint,scale,pitch)` and `draw({ mouth: flap(env,t), blink: blinkAt(t, seed, swaps), expr, look, lookY, armL, armR, propL, propR, lean, bob, laughMarks, sweat, soot, lit, shade, rim })`. Talking characters only during their quoted line.
     - `expr`: `neutral`, `smile`, `smug`, `focused`, `angry`, `proud`, `surprised`, `worried`, `laugh`, `grin`. `look` / `lookY` (-1..1) slide the whole face (a 3/4 turn); `gazeX` / `gazeY` move only the pupils; `brow` raises the brows; `lid` closes the lids further.
     - `lit` (-1 / 1) is the side the key light is on; `shade` is the hex of the head's shaded edge (cool at night); `rim: { color, a }` washes the lit edge with the lamp's colour. Keep `a` under about .5: heads stay white.
     - `toon.castFrom(lightPosition)` or `castFrom(direction, true)` turns the character's invisible shadow card to face the key light, so it throws the whole silhouette on floor and wall. Call it every frame after `place()`.
     - Look at every character and expression on one page before rendering: `node faces.mjs <story> [--zoom]` (the story must `export const LOOK`).
     - `pitch` leans the whole card toward the camera (someone bending over a desk).
     - `toon.hand(side, dx, dy)` and `toon.shoulder(side)` give world positions, e.g. to hang a glow or a smoke wisp on a held lamp.
     - **Hands on 3D things:** `draw({ noArmR: true })` leaves the drawn arm out, then `new Arm3D(scene, toon)` and each frame `arm.set(side, worldPoint, { tint })`. The tube has the same plum and width as a drawn arm.
   - **Windows and walls** (`engine/src/vista.js`):
     - `holedWall(w, h, [x0,y0,x1,y1], mat)` is a wall with an opening in one piece. Give the texture `rep: [1/tileW, 1/tileH]` in metres; the stones then keep one size all around the opening.
     - `vistaMat(nightCityTex() | dayGardenTex(), { yaw, az, el })` on a plane behind the opening shows a painted panorama sampled by view direction, so it slides behind the frame like a far view. `yaw` = `atan2(dx, dz)` from the camera's hold position to the window.
     - Paint your own panorama with `D('#hex')`, which returns the canvas colour that displays as that hex.
   - **Light** (see the comment at the top of the sample's `story.js`):
     - The frame is shown without an sRGB encode, so a lit surface needs a radiance of about 0.6-0.9 to read as lit. Night hall in the sample: `HemisphereLight` 1.25 (blue), six warm `PointLight`s of 6 with `decay 1, distance 0`, a `SpotLight` of 3 for the moon.
     - A far key (sun, moon) is a `SpotLight` with `decay 0` and `castShadow`; give it a `map` (a white-on-black canvas) to throw a window's lattice or a grate's bars. Walls made of `ShapeGeometry` cast shadows, so the sun only enters through a real opening.
     - Anything that emits light gets a colour ABOVE 1 (`new THREE.Color().setRGB(3.3, 2.05, .6)` for a flame). Only values above white bloom (`post.js`), so lamps glow and white heads never do. `look.bloom` sets the strength.
     - `beam(scene, from, to, { r0, r1, color, strength })` is a soft cone of light; `new Smoke(scene, { additive: true, near })` with a `path(u, t, i)` gives dust specks in it.
     - After building a set call a helper like the sample's `shadows(g)`: every Lambert mesh receives, solid meshes cast.
   - **Props** (`engine/src/props.js`): `kandil({ chain, s, light, range })` is a glass oil lamp on chains whose origin is the ring a hand holds (it carries a flame, a `PointLight` and `.flameAt()` for smoke); `voussoirArch()` and `spandrel()` build the striped arch of a mosque and the wall above it. `voussoirArch({ bevel })` chamfers every stone, so the joints of the arch are real grooves that the ink pass draws. `paint.js` has `domeTex()` (a dome unrolled: x around, y from crown to foot), `roundelTex()`, `ciniTex()` (repeating glazed tiles: `lale` medallions or `yildiz` stars) and `frizTex()` (a painted band for the middle of a tall wall).
   - **Walls need pattern.** A plain wall reads as empty however fine its masonry is. Give every big wall something drawn: a tile dado, a painted band, a panel around a window. Hang it 5 cm PROUD of the wall with a real moulding on its edge (never in the wall's plane), and keep it away from where heads will be. Paint patterns as LIGHT fills with thin dark outlines: a dark fill merges with its outline into one fat stroke.
   - **Camera:** `new CamPath(keys)`. A key is `{ t, pos, look, fov, move:'glide'|'whip'|'cut', dur, creep }`. A whip between sets more than 30 m apart becomes a whip PAN automatically. `cp.kick(t)` gives impact shakes.
   - **Look per beat:** `{ focus, coc, range, sat, lift, tint, flash, blur, bloom, vignette }`. `blur: 16` on whip frames.
   - **FX:** `Smoke` wisps (path(u,t)), `ribbon` (wind), `beam` (light), `glow`. All on layer 1, so the world ink skips them.
   - **CUES:** `{ t, type, dur }` for `audio/mix.py`. Types: whoosh, rise, lock, shutters, wind, cut, simmer, boom, scrape, stir, pen, shimmer, lamps. Pin every `dur` to words too. `mix.py` takes the set changes for the score from the first three `whoosh` cues, so use another type (`rise`) for extra swooshes.
6. **Stills before video.**
   ```bash
   node render.mjs <story> --stills=... --scale=0.5
   ```
   Check every beat for these problems:
   - captions covering faces (faces at 35-60 % height; captions sit at 70 %)
   - characters cut by the frame edge
   - a lamp or prop right at the lens
   - dark-on-dark smoke
   - empty frames during whips
   - a hat or a held prop sliced off in a straight line (it left the card's canvas)
   - a hand in one place and the thing it uses in another
   - a flat colour behind a window
   - a figure that drifts out of the frame late in a hold (check the LAST second of each hold, not only the first)
   - a set with no visible light source, or lit evenly from nowhere
   - brows hidden under a hat; a mustache that reads as a second mouth

   Things that only show in motion (cut a strip of 10 consecutive frames with ffmpeg and look at it):
   - a frame, a sill or a casing that flickers (two faces in one plane)
   - a held object that jumps between two positions

   Then watch the draft from start to finish. Numbers cannot see any of these.
7. **Draft and check against the targets.**
   ```bash
   node render.mjs <story> --scale=0.5
   node render.mjs <story> --stills=<one second per set and per beat> --scale=0.5
   ```
   Put the stills next to the sheets in `referans/` and go through `STIL_KITABI.md` → "Örnek videonun ölçümü":
   - the camera never stands still (every hold creeps in, a whip has motion blur);
   - every set shows its light source; warm and cool share the frame (no set more than ~75 % warm);
   - a shadow is about half the brightness of the lit part of the same surface, and bluish or violet, never brown;
   - nothing is pure black except ink lines; the darkest surfaces are navy or plum;
   - world lines are thin (most under 4 px at 1080 wide) and the characters' outline is the thickest line;
   - lamps glow broad and soft (still a third of their strength 40 px out); white heads never glow;
   - big walls carry a pattern; textures read as painted flats with thin lines, not as noise.
   The numbers bring you into the right range; watching the draft finds the rest.
8. **Sound.**
   ```bash
   node render.mjs <story> --cues
   python audio/mix.py stories/<story>
   ```
   - Music sits about 17 dB under the voice and is ducked another 45 % while the voice is active.
   - Effects sit about 11 dB under the voice.
   - Loudnorm to -14 LUFS, TP -2.3.
9. **Final.** `node render.mjs <story>` writes `out/<name>.mp4` (1080×1920, crf 16, AAC 256k).

## Gotchas (all hit while making İs Odası)

- **Lights.** Flat light was the biggest flaw of the early drafts (contrast 0.43-0.47; the flattest reference has 0.57). Cut the hemisphere fill down and let one key do the work. Warm point lights plus a strong blue fill turn cream walls PINK: make the warm light yellower (`#ffcb80`) and the fill weaker, and the lit walls go warm while the shade stays blue.
- **Flicker = two faces in one plane.** The kitchen's window casing lay exactly in the wall's plane and its top edge flickered in every frame. Nothing may share a plane: let a casing stand a few centimetres proud of the wall.
- **Never take a position from a cached draw.** The paper was redrawn only when the line grew, and the pen took its position from that function's return value with `|| end`. On frames where nothing was redrawn the pen jumped to the end of the line and back. Compute the position every frame; cache only the drawing.
- **NaN pixels bloom.** `pow()` of an interpolated value that dips to -1e-8 returns NaN: a black pixel with a huge white halo around it. Clamp before `pow`.
- **Brows under hats.** The face is drawn after the hat, and hats sit above -0.37 head heights, or the brows vanish and every face reads as blank.
- **Smoke.** Dark smoke vanishes on a night background. Use light warm grey `#b9adb8`, many small points (n 80, size .5, alpha .3) and a wavy path, or it reads as rain.
- **Whips between sets.** Interpolating positions 100 m apart flies through empty space and gives navy frames. Use the whip pan (built in), with 16 blur samples; 8 shows ghost copies.
- **Turkish word lookups.** `toLocaleLowerCase('tr-TR')` turns "İs" into "is" and "Ve" into "ve", so `W('İs')` returns the FIRST "is". Pin to a unique neighbouring word (`W('kazınıyor,') - .16`).
- **Font.** Captions use Segoe UI Black. Arial Rounded has no ğ/ş.
- **Orbiting vs panning.** Drifting only the camera position orbits the subject and doesn't read as a pan. Move the look point with it (truck).
- **Paper / props drawn on canvases.** Redraw only when the value changes (a `drawn` key) or capture slows down.
- **Colours come out darker than painted.** The final pass has no sRGB encode, so a canvas colour is shown as its linear value. Whites stay white, mid-tones sink. Use `D()` in paintings, and an unlit `MeshBasicMaterial` for things that must stay pale (the paper turned orange under a warm sun as a Lambert material).
- **Cream heads.** The card tint multiplies the head, and the grade's tint and saturation push it further. Set the card tint to `FACE[set] / GRADE[set]` so a white head shows as the near-white you chose.
- **Clipped hats and props.** A card is a canvas. Anything drawn past its edge is cut in a straight line. The canvas is 768 × 1184 design units for a 512 × 1024 figure (drawn at 1.5 px per unit, so close-ups stay sharp); if you add a taller hat or a longer prop, check a still.
- **Glows in front of characters.** A strong additive glow sprite between the camera and a card washes out the plum arms. Give the light source an HDR colour and let the bloom make most of the glow; a halo sprite sits at the lamp's own depth, and its brightest part is a ring just outside the glass, not the centre (the bloom already carries the first 20 px).
- **A halo that fills the frame.** The halo sprite has a real size in the world, so in a close-up it covers half the picture and paints a cool room orange (the hue-family share shows it). Turn it down there (`lamp.haloK = .3`) and keep a desk lamp's `glow()` small. Dust specks need a `near` fade, or the ones next to the lens become white blobs.
- **A comment that swallows code.** `const fl = new Mesh(...);   // a blue carpet   fl.rotation.x = ...; g.add(fl);` on ONE line: everything after `//` is comment, the floor is never added and nothing fails. The calligrapher's room had no floor for a long time; the dark navy under the desk was the empty background. After editing a long one-line statement, check that the thing is really in the picture.
- **Focus that outlives its shot.** A `look` chosen for one shot stays in force until the code says otherwise. The lamp shot's lens blur (5 px, focus at 5 m) ran on through the two shots of the dome, which came out soft; it showed only after fine lines were added there. Close the blur during the move to the next shot.
- **Painted lines grow with the surface.** A 9 px line on a dome texture is 20 px on screen when the dome is near. Keep painted lines at 3 to 5 px ON SCREEN at working distance: draw the texture larger rather than the line thicker.
- **Camera inside the smoke.** Where all wisps converge, a camera in the stream sees only haze. Shoot the target from the side.
- **Low windows show only sky.** A window at eye level sees the panorama from 0° up. `nightCityTex` raises its far shore to 4.6° so water and skyline fit in the opening.
