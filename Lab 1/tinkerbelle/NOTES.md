# Tinkerbelle, Part 2 build: handoff notes

CS 5424 Lab 1 Part 2 (Giorgi Samushia, Shuning Liu). A wizard-of-oz light: one browser page is
the *wizard* (keyboard), every other page on the same server is a *light* (the projector). The
light draws a field of about 1400 painted flowers on a canvas. People approach, touch, swipe and
flick; the wizard presses keys to match. Touched flowers burst into petals that drift, bounce off
other people's petals, and fly home. Gestures play harp chords over a drone pad.

Server: `python tinker.py` (Flask + Socket.IO, port 5001; venv in
`~/studies/cs5424-idd/repos/tinkerbelle-newnewUI/.venv`). Light: `http://<ip>:5001/?mode=blobs&season=cherry`,
click Tinkerbelle once (fullscreen + audio unlock). Wizard: `http://<ip>:5001/`, click Wizard.

## File map

- `static/index.js`   everything: layout, lifecycle, gestures, petals, tint buckets, sweeps, sound, captions, record mode
- `static/solo.js`    the take script (`SOLO_SCRIPT`), the captions (`CAPTIONS`), P/Esc to run/cancel
- `static/petals/`    artwork from the Claude Design sheet: `<species>-{a,b,c}.svg` and `<species>-centre.svg`,
                      greyscale + alpha, 256 px, petal up, base at (128,250). `gen-petals.js` regenerates them.
- `static/sounds/`    optional `ambient.mp3`, `tap.mp3`, `swipe.mp3` (any of mp3/ogg/wav/m4a); the light lists the
                      folder via `/sounds` at load. An ambient file makes `file` the default source and is
                      decoded at load into a Web Audio buffer, looped through the master (so it records).
                      File mode never falls back to the synth: not decoded yet or failed = silent, logged.
                      No ambient file = synth. B toggles files/synth. `ambient.mp3` is Pixabay's
                      "Uplifting Pad Texture" (96.8 s, credited in the Lab 1 README).
- `templates/index.html`  both pages; colour keys are `<tinker-button>` elements; wizard legend and preview
- `tinker.py`         relays every socket event to all pages; `/sounds` lists the sound folder

## Light URL parameters (defaults)

Field: `count` 1400, `cover` 0.85, `seed` 7, `season` cherry|summer|autumn, `tone` season base,
`exposure` 1.8, `gather` 12 s, `wave` 0.3, `bump` 0.7, `dir` right, `point` 50,50, `fade` 12 s,
`seasonfade` 15 s, `fps` 0 (overlay off), `debug` 0.
Look: `look` lights|paper (default lights) sets `blend edge pool grad vein halo fog fogsize centre`;
lights = additive 2 0 paletip 0 0 0 1 lit; paper = layered 2 0.3 darkbase 0.5 0.5 0 1.5 matte.
Any of those names overrides on its own. `band`, `outlier`, `sat` lo,hi, `full`, `pale` override every
season's palette numbers (see Palettes).
Sound: `sfx` 0.35, `amb` 0.6, `reverb` 0.5. Captions: `captions=off`. Record: `record=1`, `end` seconds.
Wizard URL: `point`, `point2` (start values; clicking the preview sets them), `aspect` w:h.

## Wizard keys

- Colours: 1 2 (emerald, violet, 6 s) · 7 8 3 4 (bud green, soft pink, magenta, gold) · 5 6 (teal, blue) ·
  G whole-field warm · K resting violet · 0 black. All fade over `fade` s as a sweep (below).
- Gestures at the touch point: Space tap · arrows swipe · Enter flick · D drag · H hold · A approach · L leave.
  Shift + any = at the second point. Kill sizes are % of the wall *width* (round on screen) and scale with
  sqrt(1400 / count): tap clears a hole 11% wide (its petals burst outward at 7-16% of the long edge per s,
  plus 6%/s toward the wall centre so two taps at 25 and 75 overlap in the middle), flick a line 12% long
  and 5% wide. A swipe is a swing:
  the hand travels 40% of the width from the point in 1.1 s (that length never scales), flowers in a
  feathered band 6% wide burst as it passes and throw their petals along the swing (9-20% of the long
  edge per s, a wide fan), and the hand parts the rest. Each frees 300-400 petals at 1400. Approach reaches 20%.
- S next season (sweep over `seasonfade`) · T age the field 40 s over 3 s · R reset to full bloom over 2 s ·
  Z pause/resume aging · M/N pad on/off · B files/synth · [ ] exposure ±0.1 · P/Esc run/cancel the take.
- Keys match on `event.code`; Shift only selects the second point. Colour fades run on the light, so a
  background wizard tab cannot stall them.

## How the field works

- Layout: seeded value noise, ridged so gaps are thin channels; `cover` sets the covered fraction.
  A floor of tiny dim flowers (10%) goes everywhere. Sizes: most 3-5% of wall height, 6% large, 15% tiny.
- Each flower rolls species (cherry, daisy, mum, star; mix per season), one of 3 shared petal
  arrangements, rotation, squash (20%), size, lifespan (100-200 s on the field clock), a hue offset
  (the clump's lean from a second noise field, ±6°), a saturation class (pale/mid/full) and a lightness jitter.
- Life: bud 10 s, bloom, wither 22 s, then a new flower buds at once. Touched flowers instead scatter
  their real petals; each petal leaves for home between 0.6 and 1.6 × `gather` and flies 4-7 s; the
  flower crossfades back in as petals land. Petals only collide with petals from other gestures,
  never in their first 1.5 s. A flying petal that crosses a living flower makes it flare, and the
  flare hops to two neighbours per 150 ms keeping `wave` of its strength.
- Colour sweeps: every flower carries its own HCL tone. A key picks a random origin; each flower starts
  after a delay by distance (spread over 60% of `fade`) and runs its own slow-in slow-out fade in the rest.
  A season sweep (`seasonfade`) also carries every flower's palette roll to a fresh roll from the new
  season, so the new palette shows as the sweep passes. The first 60% of the time is start delays by
  distance from the origin, so a 15 s sweep shows little for 5 s and is half turned at about 9 s.
  That is why the take fires each season key 8 s before its caption.

## Palettes

`SEASONS` in index.js. A flower's hue = the base tone (the season's, or the wizard's key) + its own offset.
Most roll inside `band` around the base (the clump's lean from the hue noise, ±6° jitter); an `outlier`
share take one of the season's named outliers instead: an offset with optional `sat` (chroma as a
fraction of full), `shade` (lightness multiplier) and `pale`. Saturation classes: `pale` share (light,
tinted), `full` share (chroma 70), the rest mid at `sat` lo..hi × 70. HCL hues: pink 0, crimson 30,
orange 55, gold 75, leaf green 130, purple 320, magenta 330. Bands past ±20 turn pink mauve and green olive.

- cherry `#ff8aa6` (h 356): band 12, outliers 20% = peach (+48, pale) 70% / magenta (-32, full, shade 0.8) 30%; pale 0.25, full 0.3, sat 0.7-0.95
- summer `#65c639` (h 130): band 15, outliers 40% = bright pink (-125) 45% / orange (-75) 35% / gold (-52) 20%, all full chroma, shade 1.1; pale 0.08, full 0.4, sat 0.8-1
- autumn `#e19c09` (h 75): band 12, outliers 40% = rust (-28, shade 0.75) 40% / crimson (-45, full, shade 0.65) 40% / deep purple (-115, shade 0.45) 20%; pale 0.06, full 0.35, sat 0.7-0.95

Small-tier flowers (most of them) draw at 0.7 lightness (`TIER`), which is what makes mid-chroma pink
read dusty; the base hue and the narrow band are what keep it pink rather than mauve.

## Tint buckets (the fade-performance fix)

A flower's colour is quantized (hue 10°, chroma 25, lightness 20) and every flower with the same
(colour, species, arrangement, blur, resolution) draws one shared tinted canvas, taken from pools
made at startup (1400 × 64 px, 400 × 128, 100 × 256, 320 halos) and recycled when unused. Retints are
queued and capped at 40 per frame; a flower keeps drawing its last clean bucket until its new one is
ready, and the overlay prints `tints`, `retint/s`, `q` and `overflow` (should stay 0).

## The two caches

1. `shapeCache`: greyscale composed flowers per (species, arrangement, blur, resolution), built from
   the petal art on first use, squash applied at draw time. 2. Tint buckets above: shape × colour.
Centres are cached once per species (`buildCentreCache`) and composited at draw time. Petal art is
rasterized at 256 and 64 px and cropped to its alpha bounds; the nearer raster is used per petal.

## Sound

Pad: A2 root ×2 detuned, E3 triangle, B3 sine, A3 triangle → lowpass 1.2 kHz → breath swell (0.1 Hz)
+ four LFOs (0.03/0.045/0.07/0.11 Hz on cutoff, detune, level, pan) → shared room. Harp: Karplus-Strong
rendered offline per pitch (lowpassed burst, 3 kHz loop filter, T60 3.5 s), A major pentatonic, broken
chords 60-90 ms apart rising for tap/swipe, falling for flick, root from x. Room: 5 s generated
impulse in a convolver, wet = `reverb`. All audio passes through `masterOut`, which record mode taps;
the file pad goes to the master dry (no room), the synth pad and harp through the room. The overlay's
`sound` field shows the source and the pad's state (`decoding`, `decoded`, `FAILED`, `none`). Record
mode waits up to 15 s for the pad to decode before its countdown.

## The take and record mode

`SOLO_SCRIPT` in solo.js (ms, action), both storyboards, 3:20: 0:00 reset + pad on · 0:15 approach 30,50 ·
0:22 tap · 0:28 leave · 0:50 approach 25,50 and 75,50 · 0:57 tap at both at the same moment (the clouds
collide in the centre) · 1:05 leave · 1:22 summer (caption 1:30) · 1:40 approach 25,50 · 1:47 swing right ·
1:53 leave · 2:15 approach 20,50 and 80,50 · 2:22 swing right from 20,50 and left from 80,50 at the same
moment (their 40% paths overlap in 40-60) · 2:30 leave · 2:47 autumn (caption 2:55) · 3:20 end, which in
record mode stops the recorder (`end=` on the URL cuts it shorter). `CAPTIONS` sits
above it as [s, text, hold?]; captions draw on the canvas during a take like film subtitles: pale
yellow `#F5E27A` Helvetica/Arial medium italic at 3% of the wall height, 1 px black outline, soft black
drop shadow, bottom centre 5% up from the edge, no band; 5 s each or their own hold (the two season
captions 8 s), 0.5 s in/out. P on any page starts the take everywhere.
`record=1` on the light: all UI hidden, cursor off, canvas fixed at 0,0 sized to the window; one click →
3 s countdown → the take runs while `canvas.captureStream(60)` + the audio master record to a VP9/Opus
webm at 24 Mb/s; the take's end downloads `storyboard-demo.webm`. Convert with
`~/studies/cs5424-idd/labs/lab1/convert-take.sh ~/Downloads/storyboard-demo.webm` (pads to even size, h264+aac).

## Renders and test harness (studies repo, not this one)

`~/studies/cs5424-idd/labs/lab1/renders/` holds every 1x render from the build (look comparisons,
close-ups, sweeps, captions, record fit; `take-lights-*` are stills of the 3:20 take at 0:24, 0:59, 1:01, 1:30, 1:49, 2:24, 2:26, 2:55; `season-*` one per season after a full re-roll). `~/studies/cs5424-idd/labs/lab1/tools/`
holds the headless Chrome scripts (`lib.mjs` + one per check; see its README). Headless fps is software
rendering: a floor, and under 20 fps the petal physics runs slow (dt is capped at 50 ms).

## Not done yet

- No real take recorded; the Part 2 video, storyboard and README sections (remix, reflections) are unwritten.
- Petal-flower collisions still let one petal hit several flowers along its path; `wave` tames the spread.
- Two gestures at once (1:23) put about 1000 petals in the air; fine on the laptop, slow in headless.
- The peach outlier in cherry reads tan on small flowers; summer's orange goes brown on the small tier.
- `grad`, `pool`, `vein` only affect the drawn fallback petals, not the artwork.
- The `mode=glow` and plain-colour lights still exist but get one whole-page fade, not the sweep.
- Sound is measured, not listened to, from this side. Cover proxy reads 0.79 for `cover=0.85`.
- `tap.mp3` / `swipe.mp3`, if ever added, still play as HTMLAudio: outside the master, so not recorded.
