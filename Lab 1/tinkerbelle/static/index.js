const control = document.getElementById('control');

// ============================================================================
// Optional shapes for the light page. Open the light as
//   http://<ip>:5001/?mode=glow    one soft patch of colour, dark edges
//   http://<ip>:5001/?mode=blobs   a field of flowers that breathe, on a <canvas>
// With no ?mode the page stays a plain flat colour (original behaviour).
//
// blobs options (all in the URL):
//   fade=<s>      how long a colour key's change takes (default 12); seasonfade=<s> for a season change (default 15).
//                 A change sweeps across the field from a random point: each flower starts at an offset
//                 by distance, spread over 60% of the time, and runs its own eased fade in the remaining 40%
//   dir=<right|left|up|down|angle-in-degrees>   direction of a swipe/flick (default right)
//   count=<n>     how many flowers (default 1400)
//   cover=<0..1>  fraction of the wall the drifts cover (default 0.85); the rest is thin dark channels,
//                 with a sparse floor of tiny dim flowers everywhere so no region is pure black
//   season=<0|1|2|name>   starting palette (see SEASONS); the wizard's S key cycles them
//   palette tunables (override every season's defaults, so they can be set on the projector):
//     band=<deg>     hue band around the base most flowers stay in (per season, 15-25)
//     outlier=<frac> share of flowers that take one of the season's outlier hues instead (0.2-0.4)
//     sat=<lo,hi>    chroma range of the mid class as a fraction of full (default 0.65,0.9)
//     full=<frac>    share of fully saturated flowers (per season, 0.25-0.3)
//     pale=<frac>    share of pale flowers: light with a clear tint (per season, 0.08-0.2)
//   seed=<n>      change the layout
//   tone=<hex>    starting colour before the wizard sends anything (default: the season's base colour)
//   gather=<s>    centre of the window in which a touched flower's petals start flying home: each petal
//                 leaves between 0.6x and 1.6x this and takes 4-7 s, so a flower reassembles petal by petal (default 12)
//   bump=<0..1>   how brightly two petals flash when they collide (default 0.7)
//   captions=off  no captions during a scripted take (see CAPTIONS in solo.js)
//   record=1      record mode: every bit of UI hidden, cursor off; one click, a 3 s countdown, then the
//                 take in solo.js runs while the canvas (60 fps) and the audio master are captured to
//                 storyboard-demo.webm, downloaded when the take ends. end=<s> cuts the take short
//   exposure=<x>  starting brightness multiplier, 0.6..2.0 (default 1.8); the wizard's [ and ] step it
//   wave=<0..1>   how far a flare travels when a flying petal hits a flower (default 0.3)
//
// All motion integrates real elapsed time (dt, capped at 50 ms so a stall never teleports anything);
// nothing steps per frame, so 30 and 220 fps look the same.
//   sfx=<0..1>    harp volume (default 0.35); amb=<0..1> pad volume (default 0.6); reverb=<0..1> wet share (default 0.5)
//   point=x,y     touch point in %, used when the wizard's gesture carries none (default 50,50)
//
// Performance model: a flower is a list of petals, but while it is alive it is drawn as ONE
// cached bitmap. Two caches per flower: a greyscale shape composed from its petals (rebuilt only
// when its bloom step changes: bud, full, withering) and a tinted copy of that shape (rebuilt
// only when its colour changes). So a frame costs one drawImage per living flower, plus one per
// petal for flowers that are dying, and the GPU-backed 2D canvas handles that easily.
// ============================================================================
const params = new URLSearchParams(window.location.search);
// ---- look: how the flowers are drawn. Two default sets, and every property can be set on its own:
//   look=lights|paper
//   blend=additive|layered   additive: bodies add up like light. layered: petals darken where they
//                            overlap inside a flower, flowers sit over each other at ~0.8 alpha sorted
//                            by size, and a soft halo per flower is drawn additively underneath
//   edge=<px>   petal edge softness      pool=<0..1>  darkening at the petal rim, like watercolour pooling
//   grad=paletip|darkbase    base-to-tip gradient: pale base and colour at the tip / darker base, lightest mid
//   vein=<0..1> central vein and a little noise inside the petal
//   halo=<0..1> strength of the per-flower halo (drawn in either blend)
//   fog=<0..1> background patch strength
//   fogsize=<x> background patch radius multiplier (they also get softer when > 1)
//   centre=lit|matte   lit: the glowing centres. matte: textured, no glow; darker than the petals for
//                      cherry, a yellow-brown dotted disc for daisy, near nothing for chrysanthemum
const LOOKS = {
  lights: { blend: 'additive', edge: 2, pool: 0,   grad: 'paletip',  vein: 0,   halo: 0,   fog: 0,   fogsize: 1,   centre: 'lit' },
  paper:  { blend: 'layered',  edge: 2, pool: 0.3, grad: 'darkbase', vein: 0.5, halo: 0.5, fog: 0,   fogsize: 1.5, centre: 'matte' },
};
const LOOK = { ...(LOOKS[params.get('look')] || LOOKS.lights) };
for (const k of Object.keys(LOOK)) {
  if (params.get(k) === null) continue;
  LOOK[k] = typeof LOOK[k] === 'number' ? Number(params.get(k)) : params.get(k);
}
// ?debug=1 shows runtime errors on the page itself (useful on a phone with no console)
if (params.get('debug')) window.addEventListener('error', (e) => {
  const d = document.createElement('pre');
  d.style.cssText = 'position:fixed;top:40px;left:0;color:#f66;background:#000;z-index:9;font:14px monospace;white-space:pre-wrap;';
  d.textContent = `${e.message}\n${(e.filename || '').split('/').pop()}:${e.lineno}`;
  document.body.appendChild(d);
});
const lightMode = params.get('mode');
const spreadMs = Number(params.get('spread') || 900);
const blobCount = Number(params.get('count') || 1400);
const coverFrac = Math.min(0.97, Math.max(0.1, Number(params.get('cover') || 0.85)));

// deterministic pseudo-random so the layout is the same on every reload (change ?seed= to reshuffle)
let seed = Number(params.get('seed') || 7);
const rand = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };

// ---- layout: organic placement in three depth tiers. [x%, y%, radius% of the long screen edge, opacity, tier]
// Depth by size: the small tier is dim, washed toward the background and a touch blurrier; the large
// tier is the brightest. Opacities are low enough that two overlapping flowers don't add up to white.
const TIER = [ // small, large, glow patch, floor
  { op: 0.5,  light: 0.7, blur: 0.6 },
  { op: 0.75, light: 1.0, blur: 0 },
  { op: 0.30, light: 1.0, blur: 0 },
  { op: 0.35, light: 0.55, blur: 1.0 },   // the floor: tiny, dim, everywhere
];
// ---- low-frequency value noise, seeded: it shapes where the clumps are and what hue each leans to
function makeNoise(seedOffset, cellsX, cellsY) {
  const g = []; let x = (seed + seedOffset) >>> 0;
  const r = () => { x = (x * 1664525 + 1013904223) % 4294967296; return x / 4294967296; };
  for (let j = 0; j <= cellsY; j++) { g[j] = []; for (let i = 0; i <= cellsX; i++) g[j][i] = r(); }
  const sm = (t) => t * t * (3 - 2 * t);
  return (u, v) => {                       // u, v in 0..1 -> 0..1
    const fx = u * cellsX, fy = v * cellsY, i = Math.min(cellsX - 1, Math.floor(fx)), j = Math.min(cellsY - 1, Math.floor(fy));
    const tx = sm(fx - i), ty = sm(fy - j);
    return (g[j][i] * (1 - tx) + g[j][i + 1] * tx) * (1 - ty) + (g[j + 1][i] * (1 - tx) + g[j + 1][i + 1] * tx) * ty;
  };
}
// density: two octaves, stretched across the wall so the clumps run as drifts and streams
const nA = makeNoise(11, 5, 3), nB = makeNoise(29, 11, 7);
// ridged: the gaps sit along the contours of the noise, so they come out as thin winding channels
// between drifts rather than empty quarters of the wall
const densityRaw = (x, y) => Math.abs(2 * (0.68 * nA(x / 100, y / 100) + 0.32 * nB(x / 100, y / 100)) - 1);
// the threshold that leaves `coverFrac` of the wall inside the clumps: read it off a sample grid
const densityCut = (() => { const v = []; for (let j = 0; j < 40; j++) for (let i = 0; i < 70; i++) v.push(densityRaw(i / 69 * 100, j / 39 * 100)); v.sort((a, b) => a - b); return v[Math.floor(v.length * (1 - coverFrac))]; })();
const density = (x, y) => { const d = (densityRaw(x, y) - densityCut) / 0.08; return d <= 0 ? 0 : d >= 1 ? 1 : d * d * (3 - 2 * d); };   // a soft edge on each drift
// hue: a slower field; each clump leans to one hue in the season band
const nH = makeNoise(53, 4, 3);
const hueField = (x, y) => nH(x / 100, y / 100) * 2 - 1;   // -1..1

// ---- layout. Sizes are radii in % of the long edge; on a 16:9 wall the largest flowers are about
// 6% of its height across, most 2-4%, and a fifth are tiny (about 1%). Placement follows the
// density field: dense inside the clumps, near-empty in the gaps.
const blobSpots = [];
{
  const cell = 3, cols = Math.ceil(100 / cell) + 1, occ = new Map();   // coarse grid for the min-gap test
  const key = (x, y) => Math.floor(y / cell) * cols + Math.floor(x / cell);
  const tooClose = (x, y, gap) => {
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const list = occ.get(key(x + dx * cell, y + dy * cell)); if (!list) continue;
      for (const [bx, by] of list) if (Math.hypot(bx - x, by - y) < gap) return true;
    }
    return false;
  };
  const place = (x, y, r, op, tier) => { blobSpots.push([x, y, r, op, tier]); const k = key(x, y); (occ.get(k) || occ.set(k, []).get(k)).push([x, y]); };
  // background patches only when fog > 0
  if (LOOK.fog > 0) for (let n = 0, tries = 0; n < Math.round(blobCount * 0.03) && tries < 2000; tries++) {
    const x = 5 + rand() * 90, y = 5 + rand() * 90; if (rand() > density(x, y)) continue;
    place(x, y, (8 + rand() * 6) * LOOK.fogsize, TIER[2].op * LOOK.fog, 2); n++;
  }
  // the floor: a tenth of the count, tiny and dim, placed everywhere regardless of the drifts
  for (let n = 0, tries = 0; n < Math.round(blobCount * 0.1) && tries < blobCount * 5; tries++) {
    const x = 1 + rand() * 98, y = 1 + rand() * 98;
    if (tooClose(x, y, 1.2)) continue;
    place(x, y, 0.24 + rand() * 0.1, TIER[3].op, 3); n++;
  }
  let tries = 0;
  while (blobSpots.length < blobCount && tries++ < blobCount * 60) {
    const x = 1 + rand() * 98, y = 1 + rand() * 98;
    if (rand() > density(x, y)) continue;                              // in a channel: mostly rejected
    const u = rand();
    const big = u < 0.06, tiny = u > 0.85;
    // radii in % of the long edge: on 16:9, large ~6-7% of the wall height across, most 3-5%, tiny ~1%
    const r = big ? 1.7 + rand() * 0.3 : tiny ? 0.26 + rand() * 0.1 : 0.84 + rand() * 0.56;
    const tier = tiny ? 0 : 1;
    if (tooClose(x, y, big ? 2.4 : tiny ? 0.5 : 1.1)) continue;
    place(x, y, r, TIER[tier].op, tier);
  }
  blobSpots.sort((a, b) => b[2] - a[2]);   // patches first, then bodies large to small (the body pass re-sorts small to large)
}
const isGlow = blobSpots.map((b) => b[4] === 2);
const tierOf = blobSpots.map((b) => b[4]);
// layered blend draws bodies back to front by radius, so a large flower sits in front of small ones
const bodyOrder = blobSpots.map((_, i) => i).filter((i) => !isGlow[i]).sort((a, b) => blobSpots[a][2] - blobSpots[b][2]);
const patchOrder = blobSpots.map((_, i) => i).filter((i) => isGlow[i]);

// ---- colour ripple: changes travel outward from the centre of the field
const origin = [50, 50];
const maxDist = Math.max(...blobSpots.map(([x, y]) => Math.hypot(x - origin[0], y - origin[1])));
const blobDelay = blobSpots.map(([x, y]) => Math.hypot(x - origin[0], y - origin[1]) / maxDist * spreadMs);

function dirVector(d) {
  const named = { right: 0, left: 180, up: 270, down: 90 };
  const deg = d in named ? named[d] : Number(d);
  return [Math.cos(deg * Math.PI / 180), Math.sin(deg * Math.PI / 180)];
}
const defaultDir = params.get('dir') || 'right';

// ---- history of received colours, so delayed flowers can look into the past
const colorHistory = [];
if (params.get('tone')) colorHistory.push([0, '#' + params.get('tone').replace('#', '')]);
function colorAt(msAgo) {
  const t = performance.now() - msAgo;
  let best = colorHistory[0] ? colorHistory[0][1] : SEASONS[season].base;   // before the wizard sends anything: the season's base
  for (const [when, c] of colorHistory) {
    if (when <= t) best = c; else break;
  }
  return best;
}

// ---- hand gestures: the wizard mimics what the visitor's hand does at the wall.
// Every gesture is a "hand": a point that moves along a path for a while and pushes, pulls or
// carries the flowers near it. Surviving flowers keep a displacement (offX/offY) that always
// decays back home, so after any gesture the field slowly returns to how it was.
//   tap    (Space)      kills the flowers within KILL.tap of the touch point (they burst into
//                       petals); a ripple then startles the ones further out
//   swipe  (arrow keys) a swing: the hand travels SWIPE_LEN ahead of the touch point in about a second,
//                       flowers in a band 2 x KILL.swipe wide burst as it passes (petals thrown
//                       along the swing) and it parts the rest
//   drag   (D)          a slow hand moves through; flowers near it are carried along, then released
//   hold   (H)          a hand rests on the wall; flowers gather in toward it, then drift back
//   flick  (Enter)      kills the flowers along a line from the touch point in the swipe direction;
//                       their petals all fly that way
// The touch point travels with the gesture event: the wizard's ?point=x,y, or its ?point2=x,y
// when Shift is held. Two keypresses with different points make two patches; overlapping patches
// just overlap. A gesture with no point falls back to this light's own ?point= (default centre).
const handPoint = (params.get('point') || '50,50').split(',').map(Number);
let handPoint2 = params.get('point2') ? params.get('point2').split(',').map(Number) : null;
let pointSet = params.has('point');   // does this page have a point of its own to send with gestures?
const hands = [];   // {t0, kind, from:[x,y], to:[x,y], ms, radius, force, mode}
// Flowers have velocity: a hand accelerates them, they coast and slow (VEL_TAU), and their
// displacement then drifts home (RETURN_TAU). So nothing teleports - it starts, moves, settles.
//   force  = acceleration in %/s^2 at zero distance (swipe/drag/hold, applied while the hand is near)
//   kick   = one-off velocity in %/s given when the tap's ripple front passes a flower
const GESTURES = {
  tap:   { ms: 700,  radius: 22, kick: 34,   mode: 'ripple',  travel: 0 },
  swipe: { ms: 1100, radius: 14, force: 180, mode: 'repel',   travel: 40, ahead: true },   // ahead: the path starts at the point (a swing), not centred on it
  drag:  { ms: 2600, radius: 12, force: 110, mode: 'carry',   travel: 55 },
  hold:  { ms: 3000, radius: 22, rate: 1.6,  mode: 'bloom',   travel: 0 },   // rate = how fast the bloom builds, per second
};
const VEL_TAU = 0.28;   // seconds for a pushed flower to coast to a stop
function triggerHand(kind, opts) {
  const g = GESTURES[kind]; if (!g) return;
  if (lightMode !== 'blobs') return;                 // the wizard page only sends; nothing to move here
  const x = (opts && opts.x) ?? handPoint[0], y = (opts && opts.y) ?? handPoint[1];
  const vec = dirVector((opts && opts.dir) || defaultDir);
  playSfx(kind, x);
  if (kind === 'swipe') killAlong(x, y, vec, SWIPE_LEN, KILL.swipe, g.ms);
  else if (KILL[kind]) killAround(x, y, KILL[kind]);
  const half = g.ahead ? 0 : g.travel / 2, len = g.ahead ? g.travel : g.travel / 2;
  hands.push({ t0: performance.now(), kind, ...g, hit: new Set(),
    from: [x - vec[0] * half, y - vec[1] * half], to: [x + vec[0] * len, y + vec[1] * len], vec });
}
// where a hand is, 0..1 along its path, eased so it starts and stops gently
function handPos(h, now) {
  const u = Math.min(1, (now - h.t0) / h.ms);
  const e = h.travel ? d3.easeSinInOut(u) : 0;
  return [h.from[0] + (h.to[0] - h.from[0]) * e, h.from[1] + (h.to[1] - h.from[1]) * e, u];
}

// per-flower motion state, in % of the screen: displacement from home, velocity, and excitement
const offX = blobSpots.map(() => 0), offY = blobSpots.map(() => 0);
const velX = blobSpots.map(() => 0), velY = blobSpots.map(() => 0);
const bloom = blobSpots.map(() => 0);    // 0..1: how excited a flower is (hold gesture); fades on its own
const BLOOM_TAU = 1.8;                   // seconds for the excitement to fade after the hand leaves
const RETURN_TAU = 4500;                 // ms time-constant for displaced flowers drifting back

// ---- lifecycle: every flower is born, blooms, withers and goes; after a while a new flower buds
// in the same home slot, with its own shade, size and shape - never the same flower back.
// Ages run on the field clock (fieldTime), which the wizard can pause or jump for a take.
// A touched flower is different: its petals scatter, drift for `gather` seconds of real time, then
// fly home and the same flower recomposes. That runs on real time even while aging is paused.
const BUD_MS = 10000;                                      // bud -> full size
const WITHER_MS = 22000;                                   // the last stretch of a life: shrinks, dims, loses colour
const gatherMs = Number(params.get('gather') || 12) * 1000;   // petals away -> start flying home (URL value in seconds)
const RETURN_MIN_MS = 4000, RETURN_MAX_MS = 7000;          // each petal's own flight home, eased
const away = blobSpots.map(() => 0);                       // petals still out for this slot
const petalTotal = blobSpots.map(() => 0), returnBegan = blobSpots.map(() => false);
// while petals fly home the flower is drawn underneath at low alpha, ramping up as they land, so
// there is never a frame with neither petal nor flower
const reassembleAlpha = (i) => returnBegan[i] ? 0.15 + 0.85 * (1 - away[i] / Math.max(1, petalTotal[i])) : 0;
const TIME_STEP_MS = 40000;                                // how far the T key jumps the field clock
const newLifespan = () => 100000 + rand() * 100000;        // 100-200 s, so the field never ages in lockstep
const lifespan = blobSpots.map(() => 0);   // ms, per flower; set at (re)birth
const birth = blobSpots.map(() => 0);      // fieldTime at which this flower budded
const deadAt = blobSpots.map(() => null);  // real time it went, or null while alive
const sizeMul = blobSpots.map(() => 1);
let fieldTime = 0, agingPaused = false;
// ---- captions during a scripted take, styled like film subtitles: one short line, bottom centre
// 5% up from the edge, pale yellow Helvetica/Arial medium italic at 3% of the wall height, a 1 px
// black outline and a soft black drop shadow so it reads on any background; half a second in and
// out. Drawn on the canvas so the recording has them. The lines live in CAPTIONS at the top of solo.js.
let recordStart = null;
const captionsOn = params.get('captions') !== 'off';
const recordMode = params.get('record') === '1' && lightMode === 'blobs';
const recordEndMs = params.get('end') ? Number(params.get('end')) * 1000 : null;
let countdownEnd = null, recorder = null, recordChunks = [], recordStarted = false;
if (recordMode) {   // nothing but the field and the captions: no buttons, panels, overlay, cursor or scroll bars
  const st = document.createElement('style');
  st.textContent = '#user, #controlPanel, #legend, #preview { display: none !important; } html { background: #000 !important; } html, body { overflow: hidden !important; cursor: none !important; margin: 0 !important; padding: 0 !important; max-width: none !important; width: 100% !important; height: 100% !important; background: transparent; }';
  document.head.appendChild(st);
  document.addEventListener('click', () => { if (recordStarted) return; recordStarted = true; beginTake(); }, { once: false });
}
// the audio master: everything audible goes through here, so a recording can tap it too
let masterNode = null, recordDest = null;
function masterOut(c) {
  if (masterNode && masterNode.context === c) return masterNode;
  masterNode = c.createGain(); masterNode.connect(c.destination);
  if (recordMode) { recordDest = c.createMediaStreamDestination(); masterNode.connect(recordDest); }
  return masterNode;
}
async function beginTake() {
  getAudioCtx();                                                  // unlocked by this click
  if (document.fullscreenEnabled) document.documentElement.requestFullscreen().catch(() => {});
  if (soundSource === 'file' && ambientDecode && !ambientBuf && !ambientFail) {   // the pad must be ready before the take starts
    console.log('take: waiting for the ambient file to decode');
    await Promise.race([ambientDecode, new Promise((r) => setTimeout(r, 15000))]);
    if (!ambientBuf) console.warn('take: ambient file not ready after 15 s; the take runs without a pad');
  }
  countdownEnd = performance.now() + 3000;
  setTimeout(startRecording, 3000);
}
function startRecording() {
  countdownEnd = null;
  const c = getAudioCtx(); masterOut(c);
  const stream = canvas.captureStream(60);
  if (recordDest) for (const t of recordDest.stream.getAudioTracks()) stream.addTrack(t);
  const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'].find((m) => MediaRecorder.isTypeSupported(m)) || '';
  recorder = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 24e6, audioBitsPerSecond: 192e3 });
  recordChunks = [];
  recorder.ondataavailable = (e) => { if (e.data && e.data.size) recordChunks.push(e.data); };
  recorder.onstop = () => {
    const blob = new Blob(recordChunks, { type: 'video/webm' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'storyboard-demo.webm';
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
    window.recordingDone = { bytes: blob.size, mime };
  };
  recorder.start(1000);
  window.recordingStartedAt = performance.now();
  runSoloScript();                                                // the take; its end (or end=) stops the recorder
  if (recordEndMs) setTimeout(stopRecording, recordEndMs);
}
function stopRecording() {
  cancelSoloScript();                                             // sends record-off, which stops the recorder
  if (recorder && recorder.state === 'recording') recorder.stop();
}
function drawCountdown(now) {
  if (countdownEnd === null) return;
  const left = countdownEnd - now; if (left <= 0) return;
  const n = Math.ceil(left / 1000), frac = (left / 1000) % 1;
  ctx.save(); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.globalCompositeOperation = 'source-over';
  ctx.font = `200 ${Math.round(H * 0.18)}px "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.globalAlpha = 0.6 * Math.min(1, frac * 4); ctx.fillStyle = '#f2ede4';
  ctx.fillText(String(n), W / 2, H / 2);
  ctx.restore();
}
const CAPTION_HOLD = 5, CAPTION_FADE = 0.5;
const CAPTION_SIZE = 0.03, CAPTION_UP = 0.05, CAPTION_COLOR = '#F5E27A';   // size and height above the edge as fractions of wall height
function drawCaptions(now) {
  if (recordStart === null || !captionsOn || typeof CAPTIONS === 'undefined') return;
  const t = (now - recordStart) / 1000;
  for (let k = 0; k < CAPTIONS.length; k++) {
    const [at, text, hold] = CAPTIONS[k]; if (!text || t < at) continue;
    const end = Math.min(at + (hold || CAPTION_HOLD), k + 1 < CAPTIONS.length ? CAPTIONS[k + 1][0] : Infinity);
    if (t >= end) continue;
    const a = Math.min(1, (t - at) / CAPTION_FADE, (end - t) / CAPTION_FADE);
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.globalCompositeOperation = 'source-over';
    const px = Math.round(H * CAPTION_SIZE), x = W / 2, y = H - H * CAPTION_UP;
    ctx.font = `italic 500 ${px}px Helvetica, "Helvetica Neue", Arial, sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.globalAlpha = a;
    ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = px * 0.25; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = px * 0.06;   // the soft drop shadow
    ctx.lineJoin = 'round'; ctx.lineWidth = 2; ctx.strokeStyle = '#000';   // 2 px centred on the glyph edge = 1 px showing outside it
    ctx.strokeText(text, x, y);
    ctx.shadowColor = 'transparent';                                        // the fill sits clean on top of the outline
    ctx.fillStyle = CAPTION_COLOR; ctx.fillText(text, x, y);
    ctx.restore();
    break;
  }
}
let ffLeft = 0, ffTotal = 0;   // ms of aging still to apply from T presses; drained over FF_MS
const FF_MS = 3000;
const resetAt = blobSpots.map(() => -1e9), resetFrom = blobSpots.map(() => null);   // R: each flower eases from its old look
const RESET_MS = 2000;
// exposure: a global brightness multiplier on flower alpha, glow alpha and lightness, stepped by the wizard
let exposure = Math.min(2, Math.max(0.6, Number(params.get('exposure') || 1.8)));
function setExposure(v) { exposure = Math.round(Math.min(2, Math.max(0.6, v)) * 10) / 10; }

// how old a flower is and what that looks like: [scale, alpha, wither 0..1, blur px]
// The blur is the flower's glow: soft in full bloom, tight for buds and withering flowers.
let BLUR_FULL = LOOK.edge, BLUR_TIGHT = Math.min(0.3, LOOK.edge);   // edge= is the softness in full bloom; zeroed once the painted petals load
function lifeLook(i) {
  const age = fieldTime - birth[i];
  if (age < BUD_MS) { const u = d3.easeSinOut(age / BUD_MS); return [0.25 + 0.75 * u, u, 0, BLUR_TIGHT + (BLUR_FULL - BLUR_TIGHT) * u]; }
  const w = (age - (lifespan[i] - WITHER_MS)) / WITHER_MS;
  if (w <= 0) return [1, 1, 0, BLUR_FULL];
  const lateW = Math.max(0, (w - 0.75) / 0.25);                    // glow only goes in the last quarter of withering
  return [1 - 0.45 * w, 1 - 0.8 * w, w, BLUR_FULL - (BLUR_FULL - BLUR_TIGHT) * lateW];
}
// withering drains colour and light; hue stays so the flower still reads as itself
function wither(color, w) {
  const c = d3.hcl(color); if (isNaN(c.h)) return color;
  c.c *= 1 - 0.8 * w; c.l *= 1 - 0.5 * w;
  return c.formatRgb();
}
// ---- the wizard's preview of the wall: a rectangle in the wall's aspect. Click sets the touch
// point, shift-click the second point; both show as dots. URL point= / point2= are the start values.
// The light page reports its aspect when it connects or resizes, so the preview matches the wall.
const preview = document.getElementById('preview');
function placeDots() {
  if (!preview) return;
  const put = (id, pt) => { const d = document.getElementById(id); if (!d) return; d.hidden = !pt; if (pt) { d.style.left = pt[0] + '%'; d.style.top = pt[1] + '%'; } };
  put('dot1', pointSet ? handPoint : null); put('dot2', handPoint2);
}
let previewAspect = 16 / 9;
function setAspect(ratio) {
  if (!preview) return;
  if (ratio > 0) previewAspect = ratio;
  const w = parseFloat(getComputedStyle(preview).width) || 320;   // hidden at load: fall back to the CSS width
  preview.style.height = Math.round(w / previewAspect) + 'px';
}
if (preview && !lightMode) {
  setAspect(params.get('aspect') ? Number(params.get('aspect').split(':')[0]) / Number(params.get('aspect').split(':')[1] || 1) : 16 / 9);
  placeDots();
  preview.addEventListener('click', (e) => {
    const r = preview.getBoundingClientRect();
    const pt = [Math.round((e.clientX - r.left) / r.width * 1000) / 10, Math.round((e.clientY - r.top) / r.height * 1000) / 10];
    if (e.shiftKey) handPoint2 = pt; else { handPoint[0] = pt[0]; handPoint[1] = pt[1]; pointSet = true; }
    placeDots();
  });
}
function fieldOp(op) {
  if (op.op === 'aspect') { setAspect(op.v); return; }        // sent by light pages; only the wizard's preview cares
  if (op.op === 'record') { recordStart = op.on ? performance.now() : null; if (!op.on && recorder && recorder.state === 'recording') recorder.stop(); return; }   // the take started / stopped
  if (lightMode !== 'blobs') return;
  if (op.op === 'advance') { ffLeft += op.ms; ffTotal = ffLeft; }
  else if (op.op === 'reset') resetField(true);
  else if (op.op === 'pause') agingPaused = !!op.on;
  else if (op.op === 'season') { seasonOp(op.k); if (op.base) fadeTone(op.base, seasonFadeMs, null, true); }   // every flower re-rolls into the new palette as the sweep reaches it
  else if (op.op === 'fade') fadeTone(op.hex, fadeMs, op.easing);   // the light sets the pace, not the key
  else if (op.op === 'exposure') setExposure(op.v);
}
// A fade run by the light page itself (the season change uses this). The wizard's own colour keys
// fade on the wizard page and stream 'hex' frames; that stops if the wizard's tab is in the
// background, because browsers pause animation frames there. The light page is always rendering.
let toneFade = null;   // {f: t -> colour, t0, ms, ease}
// HCL fade that reaches black. d3.hcl('#000') has chroma NaN and the interpolator keeps the
// start's value for a NaN end, so a plain interpolateHcl to black stops at a dark version of
// the start colour. Give achromatic ends an explicit chroma of 0 and the other end's hue.
function hclFade(a, b) {
  const A = d3.hcl(a), B = d3.hcl(b);
  if (isNaN(A.c)) A.c = 0; if (isNaN(B.c)) B.c = 0;
  if (isNaN(A.h)) A.h = isNaN(B.h) ? 0 : B.h; if (isNaN(B.h)) B.h = A.h;
  return d3.interpolateHcl(A, B);
}
const fadeMs = Number(params.get('fade') || 12) * 1000, seasonFadeMs = Number(params.get('seasonfade') || 15) * 1000;
function fadeTone(hex, ms, easing, reroll) {
  if (!lightMode) return;                                            // a wizard page shows nothing
  if (lightMode === 'blobs') { startSweep(hex, ms || fadeMs, reroll); return; }
  const from = current || '#000';                                    // plain lights: one fade for the whole page
  toneFade = { f: hclFade(from, hex), t0: performance.now(), ms: Number(ms) || fadeMs, ease: eases[easing] || d3.easeSinInOut };
  requestAnimationFrame(plainFade);
}
// ---- the sweep. Every flower carries its own tone (HCL, numeric). A colour change picks a random
// origin on the wall; each flower starts after a delay proportional to its distance from it, spread
// over SWEEP_SPREAD of the fade, and then runs its own slow-in slow-out fade in the rest. A new
// change during a sweep starts from wherever each flower is at that moment. A season sweep also
// carries each flower's palette roll (hue offset, saturation class, shade) from the old season's to
// a fresh roll from the new one, so the new palette shows as the sweep passes rather than only as
// flowers die and re-bud over the next few minutes.
const SWEEP_SPREAD = 0.6;
const toneH = new Float32Array(blobSpots.length), toneC = new Float32Array(blobSpots.length), toneL = new Float32Array(blobSpots.length);
let sweep = null;   // {t0, ms, origin, maxDist, h, c, l, fromH, fromC, fromL, roll?: {from, to} palette rolls}
function startSweep(hex, ms, reroll) {
  const to = d3.hcl(hex), now = performance.now();
  const origin = [rand() * 100, rand() * 100];
  const maxDist = Math.max(...[[0, 0], [100, 0], [0, 100], [100, 100]].map(([x, y]) => Math.hypot(x - origin[0], y - origin[1])));
  if (sweep) stepSweep(now);                                           // settle each flower where it is right now
  sweep = { t0: now, ms: Number(ms) || fadeMs, origin, maxDist, h: to.h, c: isNaN(to.c) ? 0 : to.c, l: to.l,
            fromH: Float32Array.from(toneH), fromC: Float32Array.from(toneC), fromL: Float32Array.from(toneL), roll: null };
  if (reroll) sweep.roll = { from: { off: Float32Array.from(hueOff), sat: Float32Array.from(satMul), pale: Float32Array.from(pale), shade: Float32Array.from(shade) },
                             to: blobSpots.map((_, i) => rollPaletteFor(SEASONS[season], i)) };
}
function stepSweep(now) {
  if (!sweep) return;
  const sw = sweep, spread = sw.ms * SWEEP_SPREAD, own = sw.ms - spread;
  let allDone = true;
  for (let i = 0; i < blobSpots.length; i++) {
    const delay = Math.hypot(blobSpots[i][0] - sw.origin[0], blobSpots[i][1] - sw.origin[1]) / sw.maxDist * spread;
    const u = Math.min(1, Math.max(0, (now - sw.t0 - delay) / own));
    if (u < 1) allDone = false;
    const e = u <= 0 ? 0 : u >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * u);   // slow in, slow out
    const toH = isNaN(sw.h) ? sw.fromH[i] : sw.h;                              // to black or grey: keep the hue
    let dh = toH - sw.fromH[i]; dh -= Math.round(dh / 360) * 360;              // the short way round the wheel
    toneH[i] = sw.fromH[i] + dh * e; toneC[i] = sw.fromC[i] + (sw.c - sw.fromC[i]) * e; toneL[i] = sw.fromL[i] + (sw.l - sw.fromL[i]) * e;
    if (sw.roll) {   // the palette roll rides the same fade (offsets are plain numbers, not angles: no wrap)
      const f = sw.roll.from, t = sw.roll.to[i];
      hueOff[i] = f.off[i] + (t.off - f.off[i]) * e; satMul[i] = f.sat[i] + (t.sat - f.sat[i]) * e;
      pale[i] = f.pale[i] + (t.pale - f.pale[i]) * e; shade[i] = f.shade[i] + (t.shade - f.shade[i]) * e;
    }
  }
  if (allDone) sweep = null;
}
function stepToneFade(now) {
  if (!toneFade) return null;
  const u = Math.min(1, (now - toneFade.t0) / toneFade.ms);
  const c = toneFade.f(toneFade.ease(u));
  if (u >= 1) toneFade = null;
  return c;
}
function plainFade(now) {
  const c = stepToneFade(now); if (c === null) return;
  current = c; paint(c);
  if (toneFade) requestAnimationFrame(plainFade);
}


// ---- death by touch. A killed flower breaks into petals of its own colour and is gone at once;
// its slot takes the normal regrowth delay, so a touched area stays dark for a while, then buds.
// Sizes are in % of the wall WIDTH on both axes (wallDist), so a hole is round on screen, and they
// scale with the flower count so a gesture always frees about the same number of petals: at 1400
// a tap clears a hole 11% of the wall wide, a flick a line 12% long, a swipe (a swing) a feathered
// band 6% wide along the hand's 40% path (the odds of a kill fall to nothing at the band's edge), so
// each frees 300-400 petals (a flower has 5-32); fewer flowers, bigger gestures. The swing's length
// does not scale: it is the arm's reach, and two swings from 20 and 80 have to meet in the middle.
const KILL_SCALE = Math.sqrt(1400 / blobCount);
const KILL = { tap: 5.5 * KILL_SCALE, swipe: 3 * KILL_SCALE, flick: 2.5 * KILL_SCALE };   // radius (tap), half-width of the band (swipe) or line (flick)
const FLICK_LEN = 12 * KILL_SCALE;             // how far along the swipe direction a flick reaches
const SWIPE_LEN = 40;                          // how far the swing's hand travels from the touch point, % of width
const wallDist = (dx, dy) => Math.hypot(dx, dy * H / W);   // dx, dy in % of width / height -> distance in % of width
const pendingKills = [];   // {i, at, vec}: deaths staggered by a few hundred ms so a patch/line dies as a sweep
const petals = [];         // {sprite, x, y, len, w, vx, vy, born, life, ang, spin, sway, hits}  world px

// ---- collisions: a flying petal that crosses a living flower makes it flare (brightness up
// sharply, decaying over ~1.5 s). 150 ms later the flower passes a weaker flare to its neighbours;
// each hop keeps `wave` of the strength, so a wave travels a few flowers and dies. Nothing dies.
// A coarse grid of the living flowers, rebuilt each frame, keeps the checks to a few per petal.
const waveKeep = Math.min(1, Math.max(0, Number(params.get('wave') ?? 0.3)));
const flare = blobSpots.map(() => 0), flareLock = blobSpots.map(() => 0);   // strength; time a flower is immune to a hop
const pendingHops = [];        // {at, from, strength}
const FLARE_TAU = 0.5;         // s: e-fold; ~1.5 s to fade
const HOP_MS = 150, HOP_RADIUS = 8, HOP_MIN = 0.08;   // radius in % of screen
const GRID = 8;                // cell size, % of screen
const grid = new Map();        // "cx,cy" -> [flower indices], living flowers only
const cellKey = (x, y) => ((x / GRID) | 0) + ',' + ((y / GRID) | 0);
function rebuildGrid() {
  grid.clear();
  for (let i = 0; i < blobSpots.length; i++) {
    if (isGlow[i] || deadAt[i] !== null) continue;
    const k = cellKey(blobSpots[i][0] + offX[i] + apX[i], blobSpots[i][1] + offY[i] + apY[i]);
    const cell = grid.get(k); cell ? cell.push(i) : grid.set(k, [i]);
  }
}
function* nearCells(x, y) {   // the cell holding (x, y) and its eight neighbours
  const cx = (x / GRID) | 0, cy = (y / GRID) | 0;
  for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) { const c = grid.get((cx + a) + ',' + (cy + b)); if (c) yield* c; }
}
function flareFlower(i, strength, now) {
  if (strength <= flare[i]) return;
  flare[i] = Math.min(1.5, strength);
  const next = strength * waveKeep;
  if (next >= HOP_MIN) pendingHops.push({ at: now + HOP_MS, from: i, strength: next });
}
function stepFlares(now, dt) {
  const k = Math.exp(-dt / FLARE_TAU);
  for (let i = 0; i < flare.length; i++) if (flare[i] > 0.001) flare[i] *= k; else flare[i] = 0;
  for (let h = pendingHops.length - 1; h >= 0; h--) {
    const hop = pendingHops[h]; if (hop.at > now) continue;
    pendingHops.splice(h, 1);
    if (deadAt[hop.from] !== null) continue;
    const fx = blobSpots[hop.from][0] + offX[hop.from], fy = blobSpots[hop.from][1] + offY[hop.from];
    const near = [];                                            // the two nearest free neighbours, so a wave is a line of flowers, not a flood
    for (const j of nearCells(fx, fy)) {
      if (j === hop.from || flareLock[j] > now) continue;
      const d = Math.hypot(blobSpots[j][0] + offX[j] - fx, blobSpots[j][1] + offY[j] - fy);
      if (d <= HOP_RADIUS) near.push([d, j]);
    }
    near.sort((a, b) => a[0] - b[0]);
    for (const [, j] of near.slice(0, 2)) {
      flareLock[j] = now + 1200;                                // so the wave moves outward and doesn't bounce back
      flareFlower(j, hop.strength, now);
    }
  }
}
const PETAL_COAST = 1.2;   // s: the burst spreads, then the petal is just drifting
const TAP_PULL = 6;        // %/s of the long edge added toward the wall centre for tap petals: a burst travels ~1.2 x its
                           // speed, so with this two taps at 25 and 75 overlap in the middle (without it their fronts only touch)
const PETAL_FALL = 1.0;    // %/s: settling speed of a drifting petal
const PETAL_BOUNCE = 0.6;  // restitution when two clouds meet
const PETAL_RADIUS = 0.25; // contact distance as a fraction of the two petals' combined length
const PETAL_FREE_MS = 1500;    // a petal cannot touch anything in its first 1.5 s, so clouds spread first
const PETAL_REHIT_MS = 250;    // the same pair is resolved at most this often
const PETAL_SETTLE = 0.012;    // fraction of the long edge per second: slower than this after a hit = drifting, no more contacts
const SPIN_TAU = 3.0;      // s: tumble damps toward a gentle rock
const bump = Math.min(1, Math.max(0, Number(params.get('bump') ?? 0.7)));   // flash on contact
const petalGrid = new Map();   // cell -> [petal indices], rebuilt each frame for petal-petal collisions
let petalBounces = 0;          // count of petal-petal bounces so far (shown in the ?fps=1 overlay)
let gestureSeq = 0, petalSeq = 0;   // every gesture numbers its petals, so a burst never collides with itself
function killAround(x, y, r) {
  const now = performance.now(), gesture = ++gestureSeq;
  blobSpots.forEach(([bx, by], i) => {
    if (isGlow[i] || deadAt[i] !== null) return;
    const d = wallDist(bx + offX[i] - x, by + offY[i] - y);
    if (d < r) pendingKills.push({ i, at: now + d / r * 160, vec: null, gesture });
  });
}
// a swing: the band from the touch point SWIPE_LEN ahead along vec, KILL.swipe to either side with
// round ends; feathered, so the stroke has a soft edge rather than a cut one. Flowers die as the
// hand reaches them (over `ms`, the hand's travel time) and throw their petals along the swing.
function killAlong(x, y, vec, len, half, ms) {
  const now = performance.now(), gesture = ++gestureSeq;
  blobSpots.forEach(([bx, by], i) => {
    if (isGlow[i] || deadAt[i] !== null) return;
    const px = bx + offX[i] - x, py = (by + offY[i] - y) * H / W;
    const along = px * vec[0] + py * vec[1], side = Math.abs(px * vec[1] - py * vec[0]);
    const over = along < 0 ? -along : along > len ? along - len : 0;        // outside the band's length: round caps
    const d = Math.hypot(over, side) / half;
    if (d > 1 || rand() < d) return;                                          // the odds of a kill fall linearly to the edge
    pendingKills.push({ i, at: now + Math.max(0, along) / len * ms, vec, gesture, swing: true });
  });
}
function triggerPoke(opts) {
  if (lightMode !== 'blobs') return;
  const x = (opts && opts.x) ?? handPoint[0], y = (opts && opts.y) ?? handPoint[1];
  const vec = dirVector((opts && opts.dir) || defaultDir);
  const now = performance.now(), gesture = ++gestureSeq;
  playSfx('flick', x);
  blobSpots.forEach(([bx, by], i) => {
    if (isGlow[i] || deadAt[i] !== null) return;
    const px = bx + offX[i] - x, py = (by + offY[i] - y) * H / W;   // in % of width on both axes
    const along = px * vec[0] + py * vec[1];             // distance along the flick line
    const side = Math.abs(px * vec[1] - py * vec[0]);    // distance off the line
    if (along < -KILL.flick || along > FLICK_LEN || side > KILL.flick) return;
    pendingKills.push({ i, at: now + Math.max(0, along) / FLICK_LEN * 380, vec, gesture });
  });
}
function wanderAt(i, now) {
  const [px, py, amp] = wander[i];
  return [amp * Math.sin(now / px * 2 * Math.PI + phase[i]), amp * Math.cos(now / py * 2 * Math.PI + phase[i])];
}
function die(i, vec, now, gesture, swing) {
  // The flower's own petals detach: each keeps its on-screen position, angle, size and colour,
  // and gets a velocity. Tap: outward from the flower centre. Flick: all downwind, slight fan.
  // Swing: downwind in a wide fan, a little faster than a tap, so two swings' clouds cross.
  const f = drawSize[i] / S, [sx, sy] = squash[i], sway = drawSway[i];
  const cs = Math.cos(sway), sn = Math.sin(sway);
  const toWorld = (px, py) => { const X = px * sx, Y = py * sy; return [drawX[i] + f * (X * cs - Y * sn), drawY[i] + f * (X * sn + Y * cs)]; };
  const tints = new Map();   // one tinted drawing per variant used by this flower
  const long = Math.max(W, H);
  for (const p of petalsOf[i]) {
    const a = petalArt(species[i], p, p.len * R * f);   // f = device px per S unit
    if (!tints.has(a.cv)) tints.set(a.cv, tintPetal(species[i], p, tintedColor[i] || '#888', p.len * R * f));
    const sprite = tints.get(a.cv);
    const ph = p.len * R, base = p.dist * R;
    const [bx, by] = toWorld(Math.sin(p.ang) * base, -Math.cos(p.ang) * base);
    const [tx, ty] = toWorld(Math.sin(p.ang) * (base + ph), -Math.cos(p.ang) * (base + ph));
    const dx = tx - bx, dy = ty - by, len = Math.hypot(dx, dy);
    const x = (bx + tx) / 2, y = (by + ty) / 2;
    let ang, speed;
    if (swing)    { ang = Math.atan2(vec[1], vec[0]) + (rand() - 0.5) * 1.4; speed = (9 + rand() * 11) * long / 100; }   // swing: thrown along it, wide fan
    else if (vec) { ang = Math.atan2(vec[1], vec[0]) + (rand() - 0.5) * 0.7; speed = (12 + rand() * 12) * long / 100; }   // flick: all downwind, a bit faster
    else          { ang = Math.atan2(y - drawY[i], x - drawX[i]) + (rand() - 0.5) * 1.0; speed = (7 + rand() * 9) * long / 100; }   // tap: outward
    let vx = Math.cos(ang) * speed, vy = Math.sin(ang) * speed;
    if (!vec) { const cx = W / 2 - x, cy = H / 2 - y, d = Math.hypot(cx, cy) || 1; vx += cx / d * TAP_PULL * long / 100; vy += cy / d * TAP_PULL * long / 100; }   // tap: lean toward the centre
    petals.push({ sprite, x, y, len, w: ph * a.aspect * p.w * f * (sx + sy) / 2, bf: a.baseFrac,
      ang: Math.atan2(dx, -dy), vx, vy,
      born: now, spin: (rand() - 0.5) * (vec ? 0.7 : 1.0), sway: rand() * 6.28, hits: new Set([i]), flash: -1e9,
      id: ++petalSeq, gesture, settled: false, contacts: new Map(),   // contacts: other petal id -> last time resolved (flash once per pair)
      home: i, petal: p, leaveAt: now + gatherMs * (0.6 + rand()), retMs: RETURN_MIN_MS + rand() * (RETURN_MAX_MS - RETURN_MIN_MS), ret: null });
  }
  away[i] = petalTotal[i] = petalsOf[i].length; returnBegan[i] = false;
  deadAt[i] = now;
  offX[i] = offY[i] = velX[i] = velY[i] = bloom[i] = 0;   // no drifting home for the dead
  onFlowerGone(i, now);
}

// where petal p of slot i sits on the wall right now: [x, y, angle] in world px. Used to fly it home.
function petalHome(i, p, now) {
  const [bx, by, br] = blobSpots[i];
  const [wx, wy] = wanderAt(i, now);
  const long = Math.max(W, H);
  const cx = (bx + wx) / 100 * W, cy = (by + wy) / 100 * H;
  const size = br * sizeMul[i] * 2 / 100 * long * (1 + 0.10 * Math.sin(now / (2600 + 900 * (i % 5)) + phase[i]));
  const sway = (rotation[i] + 6 * Math.sin(now / 5200 + phase[i])) * Math.PI / 180;
  const f = size / S, [sx, sy] = squash[i], cs = Math.cos(sway), sn = Math.sin(sway);
  const toWorld = (px, py) => { const X = px * sx, Y = py * sy; return [cx + f * (X * cs - Y * sn), cy + f * (X * sn + Y * cs)]; };
  const ph = p.len * R, base = p.dist * R;
  const [x0, y0] = toWorld(Math.sin(p.ang) * base, -Math.cos(p.ang) * base);
  const [x1, y1] = toWorld(Math.sin(p.ang) * (base + ph), -Math.cos(p.ang) * (base + ph));
  return [(x0 + x1) / 2, (y0 + y1) / 2, Math.atan2(x1 - x0, -(y1 - y0))];
}
// a petal landed: when the last one is home the flower is drawn again, with a brief glow
function petalLanded(i, now) {
  if (--away[i] > 0) return;
  deadAt[i] = null; away[i] = 0; returnBegan[i] = false;
  offX[i] = offY[i] = velX[i] = velY[i] = 0;
  flare[i] = Math.max(flare[i], 1.2);
}

// ---- approach (A / Shift+A): someone walks up to a spot on the wall. Flowers within APPROACH.radius
// (% of the wall width, round on screen, scaled with the count like the kills) drift a few percent
// toward the point over 2 s, twinkle for about 4 s, and warm toward rose - only those flowers, not
// the field. L releases both points: they relax home and cool over 2 s.
// The old whole-field warm shift is on G, the resting colour on K.
const APPROACH = { radius: 20 * KILL_SCALE, drift: 3.5, driftMs: 2000, twinkleMs: 4000, releaseMs: 2000, warm: '#d4577f' };
const approaches = [null, null];   // per point slot: {x, y, t0, released}
const apX = blobSpots.map(() => 0), apY = blobSpots.map(() => 0);   // approach displacement, % of screen
const apWarm = blobSpots.map(() => 0), apTwinkle = blobSpots.map(() => 0);
function triggerApproach(opts) {
  if (lightMode !== 'blobs') return;
  const slot = opts && opts.slot ? 1 : 0;
  const x = (opts && opts.x) ?? (slot && handPoint2 ? handPoint2[0] : handPoint[0]);
  const y = (opts && opts.y) ?? (slot && handPoint2 ? handPoint2[1] : handPoint[1]);
  approaches[slot] = { x, y, t0: performance.now(), released: null };
}
function releaseApproaches() {
  const now = performance.now();
  for (const a of approaches) if (a && a.released === null) a.released = now;
}
// per frame: fold every active approach into each flower's drift, warmth and twinkle
function stepApproaches(now) {
  const alive = approaches.some((a) => a);
  for (let i = 0; i < blobSpots.length; i++) { apX[i] = apY[i] = 0; apWarm[i] = 0; apTwinkle[i] = 0; }
  if (!alive) return;
  approaches.forEach((a, k) => {
    if (!a) return;
    const age = now - a.t0;
    const on = d3.easeSinInOut(Math.min(1, age / APPROACH.driftMs));
    const off = a.released === null ? 1 : 1 - d3.easeSinInOut(Math.min(1, (now - a.released) / APPROACH.releaseMs));
    if (off <= 0) { approaches[k] = null; return; }
    const env = on * off;
    const tw = a.released === null && age < APPROACH.twinkleMs ? Math.min(1, age / 300) * (1 - Math.pow(age / APPROACH.twinkleMs, 3)) : 0;
    for (let i = 0; i < blobSpots.length; i++) {
      if (isGlow[i] || deadAt[i] !== null) continue;
      const [bx, by] = blobSpots[i];
      const ddx = a.x - bx, ddy = (a.y - by) * H / W, d = Math.hypot(ddx, ddy);   // % of width on both axes
      if (d >= APPROACH.radius || d < 0.01) continue;
      const fall = 1 - d / APPROACH.radius;
      apX[i] += ddx / d * APPROACH.drift * fall * env; apY[i] += ddy / d * APPROACH.drift * fall * env * W / H;   // the same drift on screen either way
      apWarm[i] = Math.min(1, apWarm[i] + fall * env);
      if (tw) apTwinkle[i] = Math.max(apTwinkle[i], tw * fall * (0.5 + 0.5 * Math.sin(now / 55 + phase[i] * 9)));   // fast, staggered
    }
  });
}

// ---- per-flower personality
const phase = blobSpots.map((_, i) => i * 1.7);
const rotation = blobSpots.map(() => rand() * 360);
const wander = blobSpots.map(() => [9000 + rand() * 12000, 11000 + rand() * 14000, 1.5 + rand() * 2.5]); // [period x, period y, amplitude %]
const heartYellow = blobSpots.map(() => rand() < 0.7);   // star centres only
// ---- palette. The wizard's colour keys set the base tone; a season sets how flowers vary around it.
// Each flower rolls, at birth: a hue - most stay inside the season's narrow band around the base
// (the clump's lean), an `outlier` share take one of the season's named outlier hues (an offset from
// the base, so they follow the wizard's colour keys too; optional chroma and shade of their own) -
// and a saturation class: pale (near white with a tint), mid (most flowers), or full (a few).
// A season change re-rolls every flower as the sweep reaches it (see startSweep); a new flower
// rolls from the current season. Hues are HCL degrees: pink 0, crimson 30, orange 55, gold 75,
// leaf green 130, purple 320, magenta 330. Bands are narrow: past +-20 pink turns mauve and green olive.
// An outlier's `sat` is its chroma as a fraction of full, `shade` scales its lightness, `pale` lifts it.
const SEASONS = [
  { name: 'cherry', base: '#ff8aa6', band: 12, outlier: 0.2, pale: 0.25, full: 0.3, sat: [0.7, 0.95],   // pink, white, peach, a little magenta
    outliers: [{ off: 48, w: 0.7, sat: 0.7, pale: 0.4 }, { off: -32, w: 0.3, sat: 1, shade: 0.8 }],
    mix: { cherry: 0.60, daisy: 0.15, mum: 0.15, star: 0.10 } },
  { name: 'summer', base: '#65c639', band: 15, outlier: 0.4, pale: 0.08, full: 0.4, sat: [0.8, 1],      // leaf green with bright pink, orange, some gold
    outliers: [{ off: -125, w: 0.45, sat: 1, shade: 1.1 }, { off: -75, w: 0.35, sat: 1, shade: 1.1 }, { off: -52, w: 0.2, sat: 1, shade: 1.1 }],
    mix: { cherry: 0.15, daisy: 0.55, mum: 0.20, star: 0.10 } },
  { name: 'autumn', base: '#e19c09', band: 12, outlier: 0.4, pale: 0.06, full: 0.35, sat: [0.7, 0.95],  // gold, rust, crimson, some deep purple
    outliers: [{ off: -28, w: 0.4, sat: 0.9, shade: 0.75 }, { off: -45, w: 0.4, sat: 1, shade: 0.65 }, { off: -115, w: 0.2, sat: 0.9, shade: 0.45 }],
    mix: { cherry: 0.10, daisy: 0.20, mum: 0.60, star: 0.10 } },
];
// URL overrides apply to every season
{
  const num = (k) => params.get(k) !== null ? Number(params.get(k)) : null;
  const band = num('band'), outlier = num('outlier'), full = num('full'), paleShare = num('pale');
  const sat = params.get('sat') ? params.get('sat').split(',').map(Number) : null;
  for (const sn of SEASONS) {
    if (band !== null) sn.band = band; if (outlier !== null) sn.outlier = outlier;
    if (full !== null) sn.full = full; if (paleShare !== null) sn.pale = paleShare;
    if (sat && sat.length === 2) sn.sat = sat;
  }
}
let season = Math.max(0, SEASONS.findIndex((x, k) => String(k) === params.get('season') || x.name === params.get('season')));
{ // every flower starts at the season's base tone (or ?tone=)
  const start = d3.hcl(params.get('tone') ? '#' + params.get('tone').replace('#', '') : SEASONS[season].base);
  toneH.fill(isNaN(start.h) ? 0 : start.h); toneC.fill(isNaN(start.c) ? 0 : start.c); toneL.fill(start.l);
}
const hueOff = blobSpots.map(() => 0), satMul = blobSpots.map(() => 0.5), pale = blobSpots.map(() => 0);
const shade = blobSpots.map(() => 1);   // lightness multiplier: < 1 for the deep outliers (rust, purple)
const lightJitter = blobSpots.map(() => (rand() - 0.5) * 10);
function rollPaletteFor(sn, i) {   // one flower's roll from season sn: {off, sat, pale, shade}
  let o = null;
  if (rand() < sn.outlier) { let u = rand() * sn.outliers.reduce((a, b) => a + b.w, 0); o = sn.outliers.find((c) => (u -= c.w) < 0) || sn.outliers[sn.outliers.length - 1]; }
  const off = o ? o.off + (rand() - 0.5) * 8 : hueField(blobSpots[i][0], blobSpots[i][1]) * sn.band + (rand() - 0.5) * 12;   // the clump's lean plus a little spread
  const u = rand();
  if (!o && u < sn.pale)        return { off, sat: 0.35 + rand() * 0.15, pale: 0.5 + rand() * 0.15, shade: 1 };   // pale: light, still clearly tinted
  const cls = u < sn.pale + sn.full ? 1.0 : sn.sat[0] + rand() * (sn.sat[1] - sn.sat[0]);              // full / mid
  return { off, sat: o && o.sat !== undefined ? o.sat : cls, pale: o && o.pale !== undefined ? o.pale : 0, shade: o && o.shade !== undefined ? o.shade : 1 };   // outliers never roll pale; they may set it
}
function rollPalette(i) {
  const r = rollPaletteFor(SEASONS[season], i);
  hueOff[i] = r.off; satMul[i] = r.sat; pale[i] = r.pale; shade[i] = r.shade;
}
function seasonOp(k) {
  season = ((k % SEASONS.length) + SEASONS.length) % SEASONS.length;
  SPECIES_MIX = SEASONS[season].mix;
  if (typeof buildCentreCache === 'function' && artLoaded) buildCentreCache();   // the chrysanthemum centre follows the season's base
}

// ---- species. A flower is a list of petals; each petal is a drawImage of its species' petal
// sprite at its own angle, base distance and length (all in sprite units, relative to the centre).
//   petals  count range        rings   [distance from centre, length] per ring, as a fraction of R
//   width   petal width as a fraction of its length
const SPECIES = {
  cherry: { petals: [5, 6],   rings: [[0.14, 0.82]],                               width: 0.62, grad: 'paletip', art: 'cherry',        centreBox: 0.95 },   // cherry is always pale at the base
  daisy:  { petals: [18, 22], rings: [[0.20, 0.78], [0.16, 0.50]],                 width: 0.24, innerEvery: 2,   art: 'daisy',         centreBox: 1.0 },
  mum:    { petals: [24, 32], rings: [[0.10, 0.88], [0.08, 0.66], [0.06, 0.46]],   width: 0.22, art: 'chrysanthemum', centreBox: 1.3, total: true },   // 24-32 in all, over three staggered rings, inner ones shorter
  star:   { petals: [8, 10],  rings: [[0.10, 0.86]],                               width: 0.40, art: 'star',          centreBox: 0.9 },
};
// `art` is the file prefix in static/petals/ (<art>-a.svg, -b, -c and <art>-centre.svg);
// `width` is only the fallback aspect if the artwork fails to load; `centreBox` sizes the centre art in R
let SPECIES_MIX = SEASONS[season].mix;   // the season's mix; default seasons are defined above
function rollSpecies() {
  let u = rand() * Object.values(SPECIES_MIX).reduce((a, b) => a + b, 0);
  for (const [name, p] of Object.entries(SPECIES_MIX)) { if ((u -= p) < 0) return name; }
  return 'cherry';
}
// per petal: ring, angle (small jitter), length (small jitter; one in eight noticeably short), width factor
function buildPetals(name) {
  const sp = SPECIES[name], out = [];
  const nTotal = sp.petals[0] + Math.floor(rand() * (sp.petals[1] - sp.petals[0] + 1));
  const n = sp.total ? Math.round(nTotal / sp.rings.length) : nTotal;   // `total`: the count is spread over the rings
  sp.rings.forEach(([dist, len], ring) => {
    const every = ring > 0 && sp.innerEvery ? sp.innerEvery : 1;
    for (let k = 0; k < n; k += every) {
      const ang = (k + ring * 0.5) * 2 * Math.PI / n + (rand() - 0.5) * 0.12;
      const short = rand() < 1 / 8 ? 0.7 : 1;
      out.push({ ring, ang, dist, len: len * short * (0.92 + rand() * 0.16), w: 0.9 + rand() * 0.2, v: Math.floor(rand() * 3) });   // v: which of the three petal drawings
    }
  });
  return out;
}
const species = blobSpots.map(() => 'cherry');
const petalsOf = blobSpots.map(() => []);
// Flowers share petal arrangements: each species has SHAPES_PER_SPECIES canonical ones, and a
// flower picks one (plus its own rotation, squash, size and colour). Sharing the arrangement is what
// lets flowers share a tinted sprite: a tint is a greyscale shape times a colour, so the shape has
// to be common too.
const SHAPES_PER_SPECIES = 3;   // one arrangement per petal drawing; more would thin the tint sharing
const shapeIdx = blobSpots.map(() => 0);
const shapeDefs = {};
function shapeDef(name, idx) {
  const list = shapeDefs[name] || (shapeDefs[name] = []);
  return list[idx] || (list[idx] = buildPetals(name));
}
const squash = blobSpots.map(() => [1, 1]);         // 20% of flowers are squashed on one axis, so they read as turned
// a new flower in slot i: fresh shade, size, shape and heart; ages from now on the field clock
function rebirth(i) {
  lifespan[i] = newLifespan(); birth[i] = fieldTime; deadAt[i] = null;
  sizeMul[i] = 0.8 + rand() * 0.4;
  if (W) shapeK[i] = pickShapeK(i);
  rollPalette(i); lightJitter[i] = (rand() - 0.5) * 10;
  heartYellow[i] = rand() < 0.7; rotation[i] = rand() * 360;
  species[i] = rollSpecies(); shapeIdx[i] = Math.floor(rand() * SHAPES_PER_SPECIES); petalsOf[i] = shapeDef(species[i], shapeIdx[i]);
  squash[i] = rand() < 0.2 ? (rand() < 0.5 ? [0.75 + rand() * 0.15, 1] : [1, 0.75 + rand() * 0.15]) : [1, 1];
  shapeBlur[i] = -1; tintedColor[i] = null;      // force a recompose and retint
  offX[i] = offY[i] = velX[i] = velY[i] = bloom[i] = 0;
}
// everything in bloom, at staggered ages, so nothing withers in lockstep (also the starting state)
function resetField(animated) {
  const now = performance.now();
  blobSpots.forEach((_, i) => {
    if (isGlow[i]) return;
    if (animated) { resetFrom[i] = deadAt[i] !== null ? [0.25, 0, 0] : lifeLook(i); resetAt[i] = now; }
    rebirth(i);
    birth[i] = fieldTime - BUD_MS - rand() * (lifespan[i] - BUD_MS - WITHER_MS);
    away[i] = 0; returnBegan[i] = false;
  });
  petals.length = 0;
  ffLeft = 0;
}
// Colours are quantized so flowers fall into shared tint buckets: hue in steps of 10 degrees,
// chroma in steps of 25 (about the saturation classes), lightness in 4-5 steps.
// The per-flower jitter still decides which bucket a flower lands in, so the field keeps its variety.
const HUE_STEP = 10, CHROMA_STEP = 25, CHROMA_FLOOR = 70, LIGHT_STEP = 20;   // 4-5 hue steps across a season band, 3 chroma classes, 4 lightness levels
function quantize(c) {   // c: d3.hcl, mutated
  c.h = Math.round(c.h / HUE_STEP) * HUE_STEP;
  c.c = Math.round(c.c / CHROMA_STEP) * CHROMA_STEP;
  c.l = Math.round(c.l / LIGHT_STEP) * LIGHT_STEP;
  return c;
}
const quantMemo = new Map();   // colour string -> quantized colour string (for wither / warm outputs)
function quantizeStr(color) {
  let q = quantMemo.get(color);
  if (q === undefined) { const c = d3.hcl(color); q = isNaN(c.h) ? color : quantize(c).formatRgb(); if (quantMemo.size > 4000) quantMemo.clear(); quantMemo.set(color, q); }
  return q;
}
// this flower's own shade of its current tone, quantized. All arithmetic; the colour string is only
// rebuilt when the quantized values move, which is what makes a 1400-flower sweep cheap per frame.
const qH = new Int16Array(blobSpots.length).fill(-9999), qC = new Int16Array(blobSpots.length), qL = new Int16Array(blobSpots.length);
const tintStr = blobSpots.map(() => '#000');
function tintOf(i) {
  const tl = toneL[i];
  if (tl < 1.5) { if (qH[i] !== -1) { qH[i] = -1; tintStr[i] = '#000000'; } return tintStr[i]; }   // black stays black
  const dark = Math.min(1, tl / 20);                                                   // chroma dies out toward black
  let h = toneH[i] + hueOff[i];
  const c = Math.max(toneC[i], CHROMA_FLOOR) * satMul[i] * dark;                      // chroma from the class, not from the key's own vividness
  const ts = tl * shade[i];                                                            // deep outliers sit below the base lightness
  let l = (ts + (92 - ts) * pale[i] + lightJitter[i]) * TIER[tierOf[i]].light;        // pale toward light; small tier dims
  l = Math.min(92, l + (100 - l) * (exposure - 1) * 0.25);                            // exposure lifts lightness gently; never white
  const hq = Math.round(h / HUE_STEP), cq = Math.round(c / CHROMA_STEP), lq = Math.round(l / LIGHT_STEP);
  if (hq !== qH[i] || cq !== qC[i] || lq !== qL[i]) {
    qH[i] = hq; qC[i] = cq; qL[i] = lq;
    tintStr[i] = d3.hcl(hq * HUE_STEP, cq * CHROMA_STEP, lq * LIGHT_STEP).formatRgb();
  }
  return tintStr[i];
}

// ---- sprites, built once: one greyscale petal per species (tinted later), the glow patch,
// and the species centres in their own colours. Nothing on the canvas is pure white.
const S = 128, C = S / 2, R = C * 0.95;          // sprite px; flower radius inside it
const P = 64;                                    // petal sprite px: base at the bottom middle, tip at the top
function makeCanvas(w = S, h = S) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
// outline of each petal as a path in a P x P box (base at (P/2, P*0.95), tip at (P/2, P*0.05))
const PETAL_PATHS = {
  cherry: (c) => { const x = P / 2, b = P * 0.95, t = P * 0.05;        // rounded oval with a notched tip
    c.moveTo(x, b); c.bezierCurveTo(P * 0.05, P * 0.75, P * 0.02, P * 0.25, x - P * 0.14, t + P * 0.06);
    c.quadraticCurveTo(x, t + P * 0.2, x + P * 0.14, t + P * 0.06);
    c.bezierCurveTo(P * 0.98, P * 0.25, P * 0.95, P * 0.75, x, b); },
  daisy:  (c) => { const x = P / 2, b = P * 0.95, t = P * 0.05;        // long narrow tongue, rounded end
    c.moveTo(x - P * 0.12, b); c.lineTo(x - P * 0.22, P * 0.35); c.quadraticCurveTo(x - P * 0.22, t, x, t);
    c.quadraticCurveTo(x + P * 0.22, t, x + P * 0.22, P * 0.35); c.lineTo(x + P * 0.12, b); c.closePath(); },
  mum:    (c) => { const x = P / 2, b = P * 0.95, t = P * 0.05;        // thin spoon, a little wider near the tip
    c.moveTo(x - P * 0.07, b); c.bezierCurveTo(x - P * 0.10, P * 0.6, x - P * 0.26, P * 0.3, x - P * 0.02, t);
    c.bezierCurveTo(x + P * 0.26, P * 0.28, x + P * 0.12, P * 0.6, x + P * 0.07, b); c.closePath(); },
  star:   (c) => { const x = P / 2, b = P * 0.95, t = P * 0.05;        // pointed ellipse: the original look
    c.moveTo(x, b); c.quadraticCurveTo(P * 0.02, P * 0.55, x, t); c.quadraticCurveTo(P * 0.98, P * 0.55, x, b); },
};
function buildPetalSprite(name) {
  const cv = makeCanvas(P, P), c = cv.getContext('2d');
  const grad = SPECIES[name].grad || LOOK.grad;
  const g = c.createLinearGradient(0, P * 0.95, 0, P * 0.05);       // base -> tip
  if (grad === 'darkbase') { g.addColorStop(0, 'rgb(190,190,190)'); g.addColorStop(0.6, 'rgb(252,252,252)'); g.addColorStop(1, 'rgb(228,228,228)'); }
  else                     { g.addColorStop(0, 'rgb(250,250,250)'); g.addColorStop(0.55, 'rgb(225,225,225)'); g.addColorStop(1, 'rgb(150,150,150)'); }
  c.fillStyle = g; c.beginPath(); PETAL_PATHS[name](c); c.fill();
  c.save(); c.clip();
  if (LOOK.pool > 0) {                                              // rim darkening: an inner stroke, like pigment pooling at the edge
    c.strokeStyle = `rgba(0,0,0,${(0.35 * LOOK.pool).toFixed(3)})`; c.lineWidth = 2.6; c.beginPath(); PETAL_PATHS[name](c); c.stroke();
  }
  if (LOOK.vein > 0) {                                              // a central vein fading toward the tip, and a light speckle
    const vein = c.createLinearGradient(0, P * 0.95, 0, P * 0.05);
    vein.addColorStop(0, `rgba(0,0,0,${(0.14 * LOOK.vein).toFixed(3)})`); vein.addColorStop(0.8, `rgba(0,0,0,${(0.06 * LOOK.vein).toFixed(3)})`); vein.addColorStop(1, 'rgba(0,0,0,0)');
    c.strokeStyle = vein; c.lineWidth = 1.3; c.beginPath(); c.moveTo(P / 2, P * 0.93); c.lineTo(P / 2, P * 0.12); c.stroke();
    for (let k = 0; k < 140; k++) {
      c.fillStyle = `rgba(${rand() < 0.5 ? '0,0,0' : '255,255,255'},${(0.10 * LOOK.vein * rand()).toFixed(3)})`;
      c.fillRect(rand() * P, rand() * P, 1.5, 1.5);
    }
  }
  c.restore();
  return cv;
}
const petalSprites = Object.fromEntries(Object.keys(SPECIES).map((n) => [n, buildPetalSprite(n)]));   // fallback only

// ---- the petal and centre artwork: static/petals/<species>-{a,b,c}.svg and <species>-centre.svg,
// greyscale with alpha, 256 px, petal pointing up with its base at (128, 250). Each SVG is
// rasterized once at load and the petals are cropped to their alpha bounds, so a sprite box is the
// petal itself: `aspect` is width/height and `baseFrac` where the base sits across the crop.
// Until the files arrive (or if one is missing) the drawn fallback above is used.
const ART_PX = 256, ART_SMALL_PX = 64;   // each petal is rasterized at both; the nearer one is drawn
const art = {};            // species -> { petals: [{cv, aspect, baseFrac}, ...3], centre: canvas }
let artLoaded = 0;
function loadSvg(url, px = ART_PX) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => { const cv = makeCanvas(px, px); cv.getContext('2d').drawImage(img, 0, 0, px, px); resolve(cv); };
    img.onerror = () => resolve(null);
    img.src = url;
  });
}
function cropToAlpha(cv, margin = 2) {
  const scale = cv.width / ART_PX;   // so the base x (128 in the file) is found at any raster size
  const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
  let x0 = cv.width, y0 = cv.height, x1 = -1, y1 = -1;
  for (let y = 0; y < cv.height; y++) for (let x = 0; x < cv.width; x++) {
    if (d[(y * cv.width + x) * 4 + 3] > 6) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 < 0) return null;
  x0 = Math.max(0, x0 - margin); y0 = Math.max(0, y0 - margin); x1 = Math.min(cv.width - 1, x1 + margin); y1 = Math.min(cv.height - 1, y1 + margin);
  const w = x1 - x0 + 1, h = y1 - y0 + 1, out = makeCanvas(w, h);
  out.getContext('2d').drawImage(cv, x0, y0, w, h, 0, 0, w, h);
  return { cv: out, aspect: w / h, baseFrac: (ART_PX / 2 * scale - x0) / w };   // the base is at x = 128 in the file
}
async function loadArt() {
  if (!lightMode) return;
  for (const [name, sp] of Object.entries(SPECIES)) {
    const urls = ['a', 'b', 'c'].map((v) => `static/petals/${sp.art}-${v}.svg`);
    const [big, small, centre] = await Promise.all([
      Promise.all(urls.map((u) => loadSvg(u, ART_PX))), Promise.all(urls.map((u) => loadSvg(u, ART_SMALL_PX))),
      loadSvg(`static/petals/${sp.art}-centre.svg`)]);
    const petals = big.map((cv) => cv && cropToAlpha(cv)), petalsSmall = small.map((cv) => cv && cropToAlpha(cv, 1));
    if (petals.every(Boolean) && petalsSmall.every(Boolean) && centre) { art[name] = { petals, petalsSmall, centre }; artLoaded++; }
    else console.warn(`petal artwork missing for ${name}; using the drawn fallback`);
  }
  if (artLoaded) { BLUR_FULL = 0; BLUR_TIGHT = 0; }   // the painted petals already have soft edges; no code blur on top
  shapeBlur.fill(-1); dropAllBuckets(); buildCentreCache();   // every flower recomposes with the artwork
}
const artReady = loadArt();
// what to draw for petal p of species `name`: the artwork variant nearest the height it will be
// drawn at (px on the device), or the fallback
const ART_SWITCH_PX = Math.sqrt(ART_PX * ART_SMALL_PX);   // ~128: below this the 64 px raster is nearer
function petalArt(name, p, px = ART_PX) {
  const a = art[name];
  if (!a) return { cv: petalSprites[name], aspect: SPECIES[name].width, baseFrac: 0.5 };
  return (px < ART_SWITCH_PX ? a.petalsSmall : a.petals)[p.v % 3];
}
// each flower's cached bitmaps are sized to the flower: half, full or double the base S, so a small
// flower is not a downscaled 128 px blur and a large one is not an upscaled one
const shapeK = blobSpots.map(() => 1);
function pickShapeK(i) {
  const nominal = blobSpots[i][2] * sizeMul[i] * 2 / 100 * Math.max(W, H);   // its on-screen size in full bloom
  return nominal <= 72 ? 0.5 : nominal <= 150 ? 1 : 2;
}
// a petal drawing in one flower's colour, for its petals when they scatter
function tintPetal(name, p, color, px = ART_PX) {
  const src = petalArt(name, p, px).cv;
  const cv = makeCanvas(src.width, src.height), c = cv.getContext('2d');
  c.drawImage(src, 0, 0);
  c.globalCompositeOperation = 'multiply'; c.fillStyle = color; c.fillRect(0, 0, cv.width, cv.height);
  c.globalCompositeOperation = 'destination-in'; c.drawImage(src, 0, 0);
  return cv;
}
// the centre artwork tinted and placed in an S x S box, sized by the species' centreBox (in R)
const CENTRE_TINT = {
  matte: { daisy: '#d9a441', cherry: '#e8d2a0', mum: null, star: '#e0c98c' },   // null: the flower's own colour
  lit:   { daisy: '#ffc93d', cherry: '#f3d68c', mum: null, star: '#f6e3a0' },
};
function drawCentreArt(t, name, color, k = 1) {
  const a = art[name]; if (!a) return false;
  const tint = (CENTRE_TINT[LOOK.centre === 'matte' ? 'matte' : 'lit'][name]) || color;
  const box = SPECIES[name].centreBox * R * k, Sk = S * k, Ck = C * k;
  const cv = makeCanvas(Sk, Sk), c = cv.getContext('2d');
  if (name === 'cherry') {
    // the drawing's disc is near-black, which reads as a hole: lay a mid tone of the petal colour
    // under it and screen the drawing on top, so the disc takes the mid tone and the stamens stay light
    const mid = d3.hcl(color); if (!isNaN(mid.h)) { mid.l *= 0.62; mid.c *= 0.8; }
    c.fillStyle = mid.formatRgb(); c.beginPath(); c.arc(Ck, Ck, box * 32 / 256, 0, Math.PI * 2); c.fill();
    c.globalCompositeOperation = 'screen'; c.drawImage(a.centre, Ck - box / 2, Ck - box / 2, box, box);
    c.globalCompositeOperation = 'multiply'; c.fillStyle = tint; c.globalAlpha = 0.5; c.fillRect(0, 0, Sk, Sk); c.globalAlpha = 1;
  } else {
    c.drawImage(a.centre, Ck - box / 2, Ck - box / 2, box, box);
    c.globalCompositeOperation = 'multiply'; c.fillStyle = tint; c.fillRect(0, 0, Sk, Sk);
  }
  c.globalCompositeOperation = 'destination-in'; c.drawImage(a.centre, Ck - box / 2, Ck - box / 2, box, box);
  t.drawImage(cv, -C, -C, S, S);   // the context is scaled by k, so S units
  return true;
}
function buildGlowSprite() {
  const cv = makeCanvas(), ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(C, C, 0, C, C, C);
  const soft = LOOK.fogsize > 1;                                    // larger patches also fall off more gently
  g.addColorStop(0, `rgba(250,250,250,${soft ? 0.8 : 1})`); g.addColorStop(soft ? 0.25 : 0.35, `rgba(250,250,250,${soft ? 0.4 : 0.55})`); g.addColorStop(1, 'rgba(250,250,250,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, S, S);
  return cv;
}
function buildCentreSprite(kind) {
  const cv = makeCanvas(), c = cv.getContext('2d');
  const disc = (r, stops) => { const g = c.createRadialGradient(C, C, 0, C, C, r); stops.forEach(([o, col]) => g.addColorStop(o, col)); c.fillStyle = g; c.fillRect(0, 0, S, S); };
  if (LOOK.centre === 'matte') {
    // matte: no glow, a firm edge, some texture
    if (kind === 'daisy') {
      disc(R * 0.24, [[0, '#c9922f'], [0.7, '#a86f22'], [0.93, '#7a4d17'], [1, 'rgba(122,77,23,0)']]);
      for (let k = 0; k < 90; k++) {                                 // florets: a speckle of lighter and darker dots
        const a = rand() * Math.PI * 2, d = Math.sqrt(rand()) * R * 0.21;
        c.fillStyle = rand() < 0.5 ? 'rgba(232,186,90,0.55)' : 'rgba(90,55,15,0.5)';
        c.beginPath(); c.arc(C + Math.cos(a) * d, C + Math.sin(a) * d, R * 0.016, 0, Math.PI * 2); c.fill();
      }
    }
    else if (kind === 'cherry') {
      disc(R * 0.11, [[0, 'rgba(78,22,52,0.95)'], [0.85, 'rgba(78,22,52,0.9)'], [1, 'rgba(78,22,52,0)']]);
      c.fillStyle = '#c9a862';
      for (let k = 0; k < 7; k++) { const a = k * Math.PI * 2 / 7 + 0.4; c.beginPath(); c.arc(C + Math.cos(a) * R * 0.17, C + Math.sin(a) * R * 0.17, R * 0.025, 0, Math.PI * 2); c.fill(); }
    }
    else if (kind === 'mum') disc(R * 0.06, [[0, 'rgba(60,20,40,0.6)'], [0.8, 'rgba(60,20,40,0.5)'], [1, 'rgba(60,20,40,0)']]);
    else if (kind === 'starY') disc(13, [[0, '#d9c27a'], [0.8, '#b89a4a'], [1, 'rgba(184,154,74,0)']]);
    else disc(13, [[0, '#d8cdb5'], [0.8, '#b3a88f'], [1, 'rgba(179,168,143,0)']]);
    return cv;
  }
  if (kind === 'daisy') disc(R * 0.26, [[0, '#ffc93d'], [0.55, '#f0962c'], [0.85, 'rgba(214,110,30,0.6)'], [1, 'rgba(214,110,30,0)']]);
  else if (kind === 'cherry') {
    disc(R * 0.13, [[0, 'rgba(70,18,48,0.95)'], [0.7, 'rgba(70,18,48,0.7)'], [1, 'rgba(70,18,48,0)']]);
    c.fillStyle = '#f3d68c';
    for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3 + 0.4; c.beginPath(); c.arc(C + Math.cos(a) * R * 0.19, C + Math.sin(a) * R * 0.19, R * 0.03, 0, Math.PI * 2); c.fill(); }
  }
  else if (kind === 'mum') disc(R * 0.07, [[0, 'rgba(60,20,40,0.55)'], [1, 'rgba(60,20,40,0)']]);
  else if (kind === 'starY') disc(15, [[0, '#f6e3a0'], [0.5, 'rgba(255,209,102,0.9)'], [1, 'rgba(255,209,102,0)']]);
  else disc(15, [[0, 'rgba(243,233,210,0.95)'], [0.5, 'rgba(243,233,210,0.5)'], [1, 'rgba(243,233,210,0)']]);
  return cv;
}

// ---- glow patches borrow a shade: each is tinted like one nearby flower, picked once, and
// re-picked (with a short fade) only when that flower dies - so patches don't flicker as the
// field turns over.
const glowSrc = blobSpots.map(() => -1), glowPrev = blobSpots.map(() => null), glowSwapAt = blobSpots.map(() => -1e9);
const GLOW_FADE_MS = 1500;
function nearestLiving(i, exclude = -1) {
  const [gx, gy] = blobSpots[i]; let best = -1, bd = Infinity;
  blobSpots.forEach(([bx, by], j) => {
    if (isGlow[j] || j === exclude || deadAt[j] !== null) return;
    const d = Math.hypot(bx - gx, by - gy); if (d < bd) { bd = d; best = j; }
  });
  return best;
}
function onFlowerGone(j, now) {
  glowSrc.forEach((src, i) => {
    if (src !== j) return;
    const next = nearestLiving(i, j); if (next < 0) return;
    glowPrev[i] = tintedColor[i]; glowSrc[i] = next; glowSwapAt[i] = now;
  });
}

let canvas, ctx, W = 0, H = 0, dpr = 1;
let shapeBlur = [], tintedColor = [], centreSprites = {}, glowSprite;
let patchTinted = [];   // background patches keep a canvas each (there are few, and only with fog > 0)
const drawX = blobSpots.map(() => 0), drawY = blobSpots.map(() => 0), drawSize = blobSpots.map(() => 0), drawSway = blobSpots.map(() => 0);
const drawAlpha = blobSpots.map(() => 0), drawPush = blobSpots.map(() => 0), drawBloom = blobSpots.map(() => 1), drawOn = blobSpots.map(() => false);
if (lightMode) {
  document.documentElement.style.height = '100%';
  document.body.style.margin = '0';
  document.body.style.minHeight = '100vh';
  document.body.style.overflow = 'hidden';
  document.body.style.background = '#000';
}
if (lightMode === 'blobs') {
  canvas = document.createElement('canvas');
  canvas.style.cssText = recordMode
    ? 'position:fixed;top:0;left:0;margin:0;transform:none;z-index:10;display:block;'   // on top of everything, sized in px by resize()
    : 'position:fixed;inset:0;width:100%;height:100%;z-index:-1;';
  document.body.appendChild(canvas);
  ctx = canvas.getContext('2d');
  const resize = () => {
    dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    if (recordMode) { canvas.style.width = W + 'px'; canvas.style.height = H + 'px'; canvas.style.left = '0px'; canvas.style.top = '0px'; }   // edge to edge, exactly the window
  };
  resize(); window.addEventListener('resize', () => { resize(); socket.emit('field', { op: 'aspect', v: W / H }); });
  glowSprite = buildGlowSprite();
  for (const k of ['daisy', 'cherry', 'mum', 'starY', 'starW']) centreSprites[k] = buildCentreSprite(k);
  shapeBlur = blobSpots.map(() => -1);
  patchTinted = blobSpots.map((_, i) => isGlow[i] ? makeCanvas() : null);
  tintedColor = blobSpots.map(() => null);
  resetField();
  glowSrc.forEach((_, i) => { if (isGlow[i]) glowSrc[i] = nearestLiving(i); });
}

// ---- compose: the flower's petals into its greyscale shape (squash and glow-blur baked in)
// ---- shared greyscale shapes: one canvas per (species, arrangement, blur, resolution), composed
// on first use. Nothing here is per flower; squash is applied at draw time.
const shapeCache = new Map();
function composeShape(name, idx, blur, k) {
  const Sk = Math.round(S * k), cv = makeCanvas(Sk, Sk), c = cv.getContext('2d');
  c.filter = blur > 0.05 ? `blur(${blur}px)` : 'none';
  c.setTransform(k, 0, 0, k, 0, 0); c.translate(C, C);          // S units from here on
  const layered = LOOK.blend === 'layered', petals = shapeDef(name, idx);
  const order = layered ? [...petals].sort((a, b) => b.ring - a.ring) : petals;   // inner rings first, outer on top
  if (layered) c.globalCompositeOperation = 'multiply';           // petals darken where they overlap
  for (const p of order) {
    const ph = p.len * R, a = petalArt(name, p, ph * k);          // the raster nearest the petal's device height
    const pw = ph * a.aspect * p.w;
    c.save(); c.rotate(p.ang); c.globalAlpha = layered ? 0.92 : (p.ring === 0 ? 1 : 0.9);
    c.drawImage(a.cv, -a.baseFrac * pw, -(p.dist * R) - ph, pw, ph);
    c.restore();
  }
  return cv;
}
function canonicalShape(name, idx, blur, k) {
  const key = `${name}|${idx}|${blur}|${k}`;
  let cv = shapeCache.get(key);
  if (!cv) { cv = composeShape(name, idx, blur, k); shapeCache.set(key, cv); }
  return cv;
}
// a flower's shape settled for this life stage: remember the key and force a new bucket
function compose(i, blur) { shapeBlur[i] = blur; tintedColor[i] = null; }

// ---- shared tints. A bucket is (quantized colour, species, arrangement, blur, resolution); every
// flower in it draws the same canvas. Canvases come from pools made at startup, never allocated
// mid-fade; a bucket that goes unused is recycled. Retints are queued and at most RETINT_BUDGET
// are done per frame, the rest carry over - a bucket landing a frame late is invisible.
const RETINT_BUDGET = 40;
const tintPools = { 64: [], 128: [], 256: [] }, POOL_SIZES = { 64: 1400, 128: 400, 256: 100 };   // most flowers are small, so most buckets are 64 px
const haloPool = [], HALO_POOL = 320;
let poolOverflow = 0;   // canvases allocated because a pool ran dry (should stay 0)
function initTintPools() {
  for (const Sk of [64, 128, 256]) for (let n = 0; n < POOL_SIZES[Sk]; n++) tintPools[Sk].push(makeCanvas(Sk, Sk));
  if (LOOK.halo > 0) for (let n = 0; n < HALO_POOL; n++) haloPool.push(makeCanvas(S, S));
}
const buckets = new Map(), haloBuckets = new Map();
const retintQueue = [];
let frameNo = 0, retintsThisSecond = 0, retintsPerSecond = 0, retintsAt = performance.now();
window.retintsPerSecond = 0;
const flowerBucket = blobSpots.map(() => null), flowerShown = blobSpots.map(() => null);
const flowerHalo = blobSpots.map(() => null), flowerHaloShown = blobSpots.map(() => null);
function takeCanvas(map, pool, Sk) {
  if (pool.length) return pool.pop();
  let victim = null;   // recycle the least recently used clean bucket of this size
  for (const b of map.values()) if (!b.dirty && b.used < frameNo - 1 && b.cv.width === Sk && (!victim || b.used < victim.used)) victim = b;
  if (victim) { map.delete(victim.key); return victim.cv; }
  poolOverflow++; return makeCanvas(Sk, Sk);
}
function bucketFor(i, color) {
  const k = shapeK[i], Sk = Math.round(S * k), blur = shapeBlur[i];
  const key = `${color}|${species[i]}|${shapeIdx[i]}|${blur}|${k}`;
  let b = buckets.get(key);
  if (!b) {
    b = { key, cv: takeCanvas(buckets, tintPools[Sk], Sk), color, name: species[i], idx: shapeIdx[i], blur, k, dirty: true, used: frameNo,
          centreAlpha: Math.max(0, Math.min(1, d3.hcl(color).l / 55)) };   // the centre dims with the tone, so a fade to black takes it
    buckets.set(key, b); retintQueue.push(b);
  }
  b.used = frameNo;
  return b;
}
function haloBucketFor(color) {
  let b = haloBuckets.get(color);
  if (!b) { b = { key: color, cv: takeCanvas(haloBuckets, haloPool, S), color, halo: true, dirty: true, used: frameNo }; haloBuckets.set(color, b); retintQueue.push(b); }
  b.used = frameNo;
  return b;
}
function retintBucket(b) {
  const t = b.cv.getContext('2d'), Sk = b.cv.width;
  const src = b.halo ? glowSprite : canonicalShape(b.name, b.idx, b.blur, b.k);
  t.setTransform(1, 0, 0, 1, 0, 0); t.globalCompositeOperation = 'source-over'; t.clearRect(0, 0, Sk, Sk);
  t.drawImage(src, 0, 0);
  t.globalCompositeOperation = 'multiply'; t.fillStyle = b.color; t.fillRect(0, 0, Sk, Sk);
  t.globalCompositeOperation = 'destination-in'; t.drawImage(src, 0, 0);
  t.globalCompositeOperation = 'source-over';
  b.dirty = false; retintsThisSecond++;
}
function runRetints(now) {
  let done = 0;
  while (done < RETINT_BUDGET && retintQueue.length) {
    const b = retintQueue.shift();
    if (b.used < frameNo - 2) {   // nobody wants it any more (its flowers moved on): free it instead
      const map = b.halo ? haloBuckets : buckets; if (map.get(b.key) === b) map.delete(b.key);
      (b.halo ? haloPool : tintPools[b.cv.width]).push(b.cv); continue;
    }
    retintBucket(b); done++;
  }
  if (now - retintsAt >= 1000) { retintsPerSecond = retintsThisSecond * 1000 / (now - retintsAt); window.retintsPerSecond = retintsPerSecond; retintsThisSecond = 0; retintsAt = now; }
}
// assign flower i to the bucket for its colour; it keeps drawing its last clean bucket until the new one is tinted
function assignBucket(i, color) {
  tintedColor[i] = color;
  flowerBucket[i] = bucketFor(i, color);
  if (LOOK.halo > 0) flowerHalo[i] = haloBucketFor(color);
}
if (lightMode === 'blobs') initTintPools();   // (after the definitions above; the setup block runs earlier)
function dropAllBuckets() {   // the artwork or look changed: everything retints from scratch
  for (const b of buckets.values()) tintPools[b.cv.width].push(b.cv);
  for (const b of haloBuckets.values()) haloPool.push(b.cv);
  buckets.clear(); haloBuckets.clear(); retintQueue.length = 0; shapeCache.clear();
  flowerBucket.fill(null); flowerShown.fill(null); flowerHalo.fill(null); flowerHaloShown.fill(null); tintedColor.fill(null);
}
// background patches: their own canvas each, tinted in place (only exist with fog > 0)
function retintPatch(i, color) {
  const t = patchTinted[i].getContext('2d');
  t.globalCompositeOperation = 'source-over'; t.clearRect(0, 0, S, S); t.drawImage(glowSprite, 0, 0);
  t.globalCompositeOperation = 'multiply'; t.fillStyle = color; t.fillRect(0, 0, S, S);
  t.globalCompositeOperation = 'destination-in'; t.drawImage(glowSprite, 0, 0);
  t.globalCompositeOperation = 'source-over';
  tintedColor[i] = color;
}

// ---- centres: one tinted sprite per species, built once (chrysanthemum takes the season's base
// colour, rebuilt on a season change) and composited at draw time
const centreCache = {};
function buildCentreCache() {
  for (const name of Object.keys(SPECIES)) {
    const a = art[name]; if (!a) { centreCache[name] = null; continue; }
    const cv = makeCanvas(), t = cv.getContext('2d');
    t.translate(C, C);
    drawCentreArt(t, name, SEASONS[season].base, 1);
    centreCache[name] = cv;
  }
}
function centreSpriteFor(i) {
  const c = centreCache[species[i]]; if (c) return c;
  return centreSprites[species[i] === 'star' ? (heartYellow[i] ? 'starY' : 'starW') : species[i]];
}

// ?fps=1 shows the frame rate and petal count in the corner of the light page
const fpsBox = params.get('fps') && !recordMode ? Object.assign(document.body.appendChild(document.createElement('div')),
  { style: 'position:fixed;top:4px;right:8px;color:#8f8;font:14px monospace;z-index:9' }) : null;
let fpsCount = 0, fpsAt = performance.now(), petalPeak = 0, petalPeakAt = 0;
window.fpsLast = 0;
let lastFrame = performance.now();
function renderBlobs() {
  const now = performance.now();
  if (petals.length >= petalPeak || now - petalPeakAt > 2000) { petalPeak = petals.length; petalPeakAt = now; }
  if (++fpsCount && now - fpsAt >= 1000) {
    window.fpsLast = fpsCount * 1000 / (now - fpsAt); fpsCount = 0; fpsAt = now;
    if (fpsBox) fpsBox.textContent = `${window.fpsLast.toFixed(0)} fps  ${petalPeak} petals  ${flare.filter((f) => f > 0.05).length} flaring  ${petalBounces} bounces  art ${artLoaded}/4  tints ${buckets.size}+${haloBuckets.size} retint/s ${retintsPerSecond.toFixed(0)} q ${retintQueue.length}${poolOverflow ? ' overflow ' + poolOverflow : ''}  exposure ${exposure.toFixed(1)}  sound ${soundLabel()}`;
  }
  const dt = Math.min((now - lastFrame) / 1000, 0.05); lastFrame = now;
  if (!agingPaused) fieldTime += dt * 1000;
  stepSweep(now);
  stepApproaches(now);
  stepFlares(now, dt);
  // T fast-forwards: the requested aging is spread over FF_MS of real time so it can be watched
  if (ffLeft > 0) { const step = Math.min(ffLeft, ffTotal * dt * 1000 / FF_MS); fieldTime += step; ffLeft -= step; }

  // scheduled deaths whose moment has come
  for (let k = pendingKills.length - 1; k >= 0; k--) {
    const p = pendingKills[k]; if (p.at > now) continue;
    pendingKills.splice(k, 1);
    if (deadAt[p.i] === null) die(p.i, p.vec, now, p.gesture, p.swing);
  }
  // hands accelerate the (living) flowers near them
  for (const h of hands) {
    const [hx, hy, u] = handPos(h, performance.now());
    if (h.mode === 'ripple') {
      // an expanding ring: each flower gets one outward kick when the front reaches it
      const front = h.radius * d3.easeSinOut(Math.min(1, u * 1.4));
      blobSpots.forEach(([bx, by], j) => {
        if (isGlow[j] || deadAt[j] !== null || h.hit.has(j)) return;
        const ddx = bx - hx, ddy = by - hy, dist = Math.hypot(ddx, ddy);
        if (dist > front || dist < 0.01) return;
        h.hit.add(j);
        const k = h.kick * (1 - 0.6 * dist / h.radius);     // weaker further out
        velX[j] += ddx / dist * k; velY[j] += ddy / dist * k;
      });
      continue;
    }
    blobSpots.forEach(([bx, by], j) => {
      if (isGlow[j] || deadAt[j] !== null) return;
      const ddx = bx + offX[j] - hx, ddy = by + offY[j] - hy, dist = Math.hypot(ddx, ddy);
      if (dist >= h.radius || dist < 0.01) return;
      if (h.mode === 'bloom') { bloom[j] = Math.min(1, bloom[j] + (1 - dist / h.radius) * h.rate * dt); return; }
      const a = (1 - dist / h.radius) * h.force * dt;
      if (h.mode === 'repel')        { velX[j] += ddx / dist * a;        velY[j] += ddy / dist * a; }
      else if (h.mode === 'carry')   { velX[j] += h.vec[0] * a;          velY[j] += h.vec[1] * a; }
    });
  }
  // integrate: velocity moves the flower and coasts to a stop; displacement drifts home
  const coast = Math.exp(-dt / VEL_TAU), bloomFade = Math.exp(-dt / BLOOM_TAU);
  for (let j = 0; j < offX.length; j++) {
    offX[j] += velX[j] * dt; offY[j] += velY[j] * dt;
    velX[j] *= coast; velY[j] *= coast;
    bloom[j] *= bloomFade;
  }
  const decay = Math.exp(-dt * 1000 / RETURN_TAU);
  for (let j = 0; j < offX.length; j++) {
    offX[j] *= decay; offY[j] *= decay;
    const m = Math.hypot(offX[j], offY[j]);
    if (m > 30) { offX[j] *= 30 / m; offY[j] *= 30 / m; }
  }

  rebuildGrid();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const long = Math.max(W, H);

  frameNo++; runRetints(now);   // the retint budget for this frame, before anything draws
  // pass 0: every flower's state for this frame (life, colour, position, glow); drawing comes after
  blobSpots.forEach(([bx, by, br, op], i) => {
    drawOn[i] = false;
    // where in its life this flower is. A touched flower is not drawn while its petals are away.
    let life = [1, 1, 0];
    if (!isGlow[i]) {
      if (deadAt[i] !== null && !returnBegan[i]) return;   // petals away; drawn again (faintly at first) once they start home
      if (fieldTime - birth[i] >= lifespan[i]) {
        onFlowerGone(i, now); rebirth(i);      // withered away quietly; a new bud starts at once, so only touched slots go dark
      }
      life = lifeLook(i);
      if (now - resetAt[i] < RESET_MS && resetFrom[i]) {           // R: ease scale, alpha and wither from the old look
        const u = d3.easeSinInOut((now - resetAt[i]) / RESET_MS), f = resetFrom[i];
        life = [f[0] + (life[0] - f[0]) * u, f[1] + (life[1] - f[1]) * u, f[2] + (life[2] - f[2]) * u, life[3]];
      }
      const blur = Math.round((life[3] + Math.min(TIER[tierOf[i]].blur, artLoaded ? 1 : 9)) * 4) / 4;   // quarter-px steps; with artwork the small tier gets at most 1 px of depth
      if (blur !== shapeBlur[i]) compose(i, blur);
    }
    // breathing + slow wander
    const breathe = Math.sin(now / (2600 + 900 * (i % 5)) + phase[i]);
    let [dx, dy] = wanderAt(i, now);
    let scale = (1 + 0.10 * breathe) * life[0];
    let push = 0;
    const visibility = life[1] * (deadAt[i] !== null ? reassembleAlpha(i) : 1);
    dx += offX[i] + apX[i]; dy += offY[i] + apY[i];
    const speed = Math.hypot(velX[i], velY[i]);
    push += Math.min(speed / 25, 1) * 0.8;                    // moving flowers glow
    push += bloom[i] * 1.2;                                   // held flowers glow more
    push += apTwinkle[i] * 0.9;                               // approached flowers twinkle
    push += flare[i] * 1.3;                                   // hit by a petal: flares
    push = Math.min(push, 1.6);
    scale *= 1 + 0.18 * Math.min(speed / 25, 1) + 0.45 * bloom[i] + 0.12 * Math.min(flare[i], 1);   // and open up

    // colour: this flower's own shade of its tone; the bucket changes only when the quantized shade does
    let c;
    if (isGlow[i]) {
      c = glowSrc[i] >= 0 ? tintOf(glowSrc[i]) : SEASONS[season].base;   // the borrowed shade
      const u = (now - glowSwapAt[i]) / GLOW_FADE_MS;
      if (u < 1 && glowPrev[i]) c = hclFade(glowPrev[i], c)(Math.round(u * 12) / 12);
    } else {
      c = tintOf(i);
      if (life[2] > 0) c = quantizeStr(wither(c, Math.round(life[2] * 8) / 8));   // in steps, so a withering flower changes bucket 8 times, not every frame
      if (apWarm[i] > 0.02) c = quantizeStr(hclFade(c, APPROACH.warm)(Math.round(apWarm[i] * 0.7 * 8) / 8));   // warmer near an approach, in 8 steps
    }
    if (c !== tintedColor[i]) { if (isGlow[i]) retintPatch(i, c); else assignBucket(i, c); }
    if (!isGlow[i]) {   // draw the newest tinted bucket; until it is tinted, the last one
      const b = flowerBucket[i]; if (b) { b.used = frameNo; if (!b.dirty) flowerShown[i] = b; }
      const h = flowerHalo[i]; if (h) { h.used = frameNo; if (!h.dirty) flowerHaloShown[i] = h; }
    }

    const x = (bx + dx) / 100 * W, y = (by + dy) / 100 * H;
    const size = br * sizeMul[i] * 2 / 100 * long * scale;
    const sway = (rotation[i] + 6 * Math.sin(now / 5200 + phase[i])) * Math.PI / 180;
    drawX[i] = x; drawY[i] = y; drawSize[i] = size; drawSway[i] = sway;   // where it is, for its petals if it dies
    drawAlpha[i] = Math.min(1, op * exposure) * visibility;                 // exposure lifts flower and glow-patch alpha alike
    drawPush[i] = push; drawBloom[i] = life[0]; drawOn[i] = true;
  });

  const body = (i, alpha, withCentre) => {
    const cv = isGlow[i] ? patchTinted[i] : (flowerShown[i] && flowerShown[i].cv); if (!cv) return;
    const half = drawSize[i] / 2;
    ctx.save(); ctx.translate(drawX[i], drawY[i]); ctx.rotate(drawSway[i]); ctx.scale(squash[i][0], squash[i][1]);
    ctx.globalAlpha = alpha;
    ctx.drawImage(cv, -half, -half, drawSize[i], drawSize[i]);
    if (withCentre) {   // the species centre, composited on top
      const cs = centreSpriteFor(i);
      if (cs) { ctx.globalAlpha = alpha * flowerShown[i].centreAlpha; ctx.drawImage(cs, -half, -half, drawSize[i], drawSize[i]); }
    }
    ctx.restore();
  };
  // background patches and halos: always additive, always underneath
  ctx.globalCompositeOperation = 'lighter';
  for (const i of patchOrder) if (drawOn[i]) body(i, drawAlpha[i]);
  if (LOOK.halo > 0) for (const i of bodyOrder) {
    if (!drawOn[i]) continue;
    const hs = drawSize[i] * 1.6 * (0.7 + 0.3 * drawBloom[i]);              // scaled to the flower's size and bloom
    const a = drawAlpha[i] * LOOK.halo * (0.5 + 0.6 * Math.min(drawPush[i], 1));
    if (a < 0.01) continue;
    const hb = flowerHaloShown[i]; if (!hb) continue;
    ctx.globalAlpha = Math.min(1, a);
    ctx.drawImage(hb.cv, drawX[i] - hs / 2, drawY[i] - hs / 2, hs, hs);
  }
  if (LOOK.blend === 'layered') {
    // bodies over each other at ~0.8 alpha, small to large so large flowers occlude
    ctx.globalCompositeOperation = 'source-over';
    for (const i of bodyOrder) {
      if (!drawOn[i]) continue;
      body(i, drawAlpha[i] * 0.8, true);
      if (drawPush[i] > 0.02) { ctx.globalCompositeOperation = 'lighter'; body(i, drawAlpha[i] * 0.45 * Math.min(drawPush[i], 1)); ctx.globalCompositeOperation = 'source-over'; }
    }
  } else {
    // additive: overlapping flowers brighten, like light on a wall (the original look)
    ctx.globalCompositeOperation = 'lighter';
    for (const i of bodyOrder) {
      if (!drawOn[i]) continue;
      body(i, drawAlpha[i], true);
      if (drawPush[i] > 0.02) body(i, drawAlpha[i] * 0.6 * Math.min(drawPush[i], 1));   // brighten while moving: draw again
    }
  }

  // detached petals: the burst slows, then each petal drifts and tumbles about the wall, bouncing
  // off the edges and off other petals, until its gather time; then it flies home along an eased
  // path and the flower recomposes when its last petal lands. (world px; one drawImage each)
  const petalCoast = Math.exp(-dt / PETAL_COAST), fall = PETAL_FALL * long / 100, spinDamp = Math.exp(-dt / SPIN_TAU);
  for (const p of petals) {
    if (p.ret) continue;
    if (now >= p.leaveAt) { p.ret = { t0: now, x: p.x, y: p.y, ang: p.ang }; returnBegan[p.home] = true; continue; }
    p.vx = p.vx * petalCoast + Math.sin(now / 900 + p.sway) * 0.3 * fall * (1 - petalCoast);
    p.vy = p.vy * petalCoast + fall * (1 - petalCoast);
    p.spin *= spinDamp;                                       // tumble settles ...
    p.x += p.vx * dt; p.y += p.vy * dt;
    p.ang += (p.spin + 0.45 * Math.cos(now / 650 + p.sway) / 0.65) * dt;   // ... into a gentle rock (derivative of 0.45*sin)
    const m = p.len * 0.5;                                    // keep on the wall: bounce off the edges
    if (p.x < m) { p.x = m; p.vx = Math.abs(p.vx) * 0.8; } else if (p.x > W - m) { p.x = W - m; p.vx = -Math.abs(p.vx) * 0.8; }
    if (p.y < m) { p.y = m; p.vy = Math.abs(p.vy) * 0.8; } else if (p.y > H - m) { p.y = H - m; p.vy = -Math.abs(p.vy) * 0.8; }
    if (Math.hypot(p.vx, p.vy) > 0.03 * long) {                 // only a petal still flying can hit a flower
      const px = p.x / W * 100, py = p.y / H * 100;
      for (const j of nearCells(px, py)) {
        if (p.hits.has(j)) continue;
        if (Math.hypot(drawX[j] - p.x, drawY[j] - p.y) < drawSize[j] * 0.3) { p.hits.add(j); flareFlower(j, 1, now); }
      }
    }
  }
  // petal-petal collisions: only between petals from different gestures (a burst never collides
  // with itself; the point is two people's clouds meeting), never in a petal's first 1.5 s, at most
  // once per pair per 250 ms, and a petal that a hit has slowed to a drift resolves nothing more.
  // Petals flying home ignore everything so they always arrive.
  petalGrid.clear();
  petals.forEach((p, k) => {
    if (p.ret || p.settled || now - p.born < PETAL_FREE_MS) return;
    const key = cellKey(p.x / W * 100, p.y / H * 100);
    const cell = petalGrid.get(key); cell ? cell.push(k) : petalGrid.set(key, [k]);
  });
  for (const [key, cell] of petalGrid) {
    const [cx, cy] = key.split(',').map(Number);
    for (let a = 0; a <= 1; a++) for (let b = -1; b <= 1; b++) {      // this cell and half its neighbours, so each pair is seen once
      if (a === 0 && b < 0) continue;
      const other = a === 0 && b === 0 ? cell : petalGrid.get((cx + a) + ',' + (cy + b)); if (!other) continue;
      for (const ki of cell) for (const kj of other) {
        if (other === cell && kj <= ki) continue;
        const p = petals[ki], q = petals[kj];
        if (p.gesture === q.gesture || p.settled || q.settled) continue;
        const dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy), r = (p.len + q.len) * PETAL_RADIUS;
        if (d >= r || d < 0.01) continue;
        const last = p.contacts.get(q.id);
        if (last !== undefined && now - last < PETAL_REHIT_MS) continue;
        const nx = dx / d, ny = dy / d;
        const vp = p.vx * nx + p.vy * ny, vq = q.vx * nx + q.vy * ny;
        if (vp - vq <= 0) continue;                              // already separating
        if (last === undefined) { petalBounces++; p.flash = q.flash = now; }   // the flash fires once per pair
        p.contacts.set(q.id, now); q.contacts.set(p.id, now);
        const push = (r - d) / 2;                                // separate so they don't stick
        p.x -= nx * push; p.y -= ny * push; q.x += nx * push; q.y += ny * push;
        const jp = (vq - vp) * (1 + PETAL_BOUNCE) / 2;           // impulse along the normal (restitution PETAL_BOUNCE)
        p.vx += nx * jp; p.vy += ny * jp; q.vx -= nx * jp; q.vy -= ny * jp;
        const kick = Math.min(0.4, Math.abs(jp) / long * 6);     // a nudge to the tumble sized by the impulse
        p.spin += (rand() - 0.5) * kick; q.spin += (rand() - 0.5) * kick;
        const settle = PETAL_SETTLE * long;                      // slowed to a drift: ride the ambient motion from here on
        if (Math.hypot(p.vx, p.vy) < settle) p.settled = true;
        if (Math.hypot(q.vx, q.vy) < settle) q.settled = true;
      }
    }
  }
  // draw, and fly the returning ones home
  for (let k = petals.length - 1; k >= 0; k--) {
    const p = petals[k];
    if (p.ret) {
      const u = Math.min(1, (now - p.ret.t0) / p.retMs), e = d3.easeSinInOut(u);
      const [hx, hy, ha] = petalHome(p.home, p.petal, now);
      let da = ha - p.ret.ang; da -= Math.round(da / (2 * Math.PI)) * 2 * Math.PI;   // turn the short way
      p.x = p.ret.x + (hx - p.ret.x) * e; p.y = p.ret.y + (hy - p.ret.y) * e; p.ang = p.ret.ang + da * e;
      // landed: the flower sprite was drawn under it this frame (returnBegan is set), so it can go
      if (u >= 1 && returnBegan[p.home]) { petals.splice(k, 1); petalLanded(p.home, now); continue; }
    }
    ctx.save();
    ctx.translate(p.x, p.y); ctx.rotate(p.ang);
    ctx.globalCompositeOperation = LOOK.blend === 'layered' ? 'source-over' : 'lighter';
    ctx.globalAlpha = 0.95;
    const bx0 = -(p.bf ?? 0.5) * p.w;
    ctx.drawImage(p.sprite, bx0, -p.len / 2, p.w, p.len);
    const fl = 1 - (now - p.flash) / 200;                      // a 200 ms flash on contact, drawn again additively
    if (fl > 0) { ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = fl * bump; ctx.drawImage(p.sprite, bx0, -p.len / 2, p.w, p.len); }
    ctx.restore();
  }

  const cutoff = now - spreadMs - 2000;
  while (colorHistory.length > 1 && colorHistory[1][0] < cutoff) colorHistory.shift();
  while (hands.length && now - hands[0].t0 > hands[0].ms) hands.shift();
  drawCaptions(now); drawCountdown(now);
  requestAnimationFrame(renderBlobs);
}
if (lightMode === 'blobs') requestAnimationFrame(renderBlobs);

function paint(color) {
  if (lightMode === 'glow') {
    document.body.style.background =
      `radial-gradient(circle at 50% 50%, ${color} 0%, ${color} 25%, #000 75%) no-repeat`;
  } else if (lightMode === 'blobs') {
    if (!sweep || sweep.hex !== color) { startSweep(color, fadeMs); sweep.hex = color; }   // a bare 'hex' sweeps like a key
  } else {
    document.body.style.backgroundColor = color;
  }
}

const light = document.getElementById('light');

const socket = io();
const interpolate = d3.interpolateHcl;  // hue-based: fades travel through the colour wheel instead of through grey
const eases = Object.fromEntries(Object.entries(d3).filter((a) => a.toString().startsWith('ease')).map(([a, b]) => [a.substring(4), b]))
const audio = new Audio();

audio.loop = true;
let current;      // the colour this page last asked for (the wizard's next fade starts from it)
let keys;         // letter -> <tinker-button>, built once the page has loaded
window.onload = () => {
  keys = [...document.querySelectorAll('tinker-button')].reduce((obj, btn) => { obj[btn.letter.toLowerCase()] = btn; return obj; }, {});
};
function playSound(soundLink, duration) {   // the original per-key sound (needs a URL); kept for the button component
  if (!soundLink) return;
  if (!audio.paused) audio.pause();
  audio.src = soundLink; audio.play().catch(() => {});
  setTimeout(() => audio.pause(), duration);
}

// ---- sound. Only light pages play, so a wizard window on the same laptop doesn't double it.
// Two layers. Files: static/sounds/ambient.*, tap.*, swipe.* (mp3/ogg/wav/m4a); the server lists the
// folder on every request to /sounds and the light page asks at load, so dropping a file in and
// reloading is enough. If an ambient file is listed the source defaults to 'file' and the file is
// fetched and decoded at load into an AudioBuffer (a 97 s mp3 takes about a second), then played
// through the audio master so a recording has it. File mode never falls back to the synth: if the
// pad is asked for before the decode is done, or the decode failed, it stays silent and says so on
// the console (and in the ?fps=1 overlay). Synth: no ambient file, or the wizard forces it with B.
// Browsers refuse audio until the page has been clicked once: click "Tinkerbelle" on the light
// page before the take.
//   M / N   ambient on / off      B  synth <-> files      Space, arrows, Enter  a note with the gesture
// Gestures play notes: a pentatonic scale in the key of the ambient pad (A), picked by the touch
// point's x across the wall (left low, right high), with a ~2 s release so gestures a moment apart
// ring together as a chord. Two people at two points land on the same scale, so they harmonize.
const clamp01 = (v) => Math.min(1, Math.max(0, v));
const sfxVol = clamp01(Number(params.get('sfx') ?? 0.35)), ambVol = clamp01(Number(params.get('amb') ?? 0.6));
const reverbMix = clamp01(Number(params.get('reverb') ?? 0.5));   // wet share of the shared reverb
let soundFiles = {};        // {ambient, tap, swipe} -> url, as found at page load
let soundSource = 'synth';  // 'file' once /sounds lists an ambient file; B flips it. 'synth': notes and pad from Web Audio
let ambientWanted = false, ambientPlay = null, ambientSynth = null, actx = null;   // ambientPlay: {src, gain} of the playing file
let ambientBuf = null, ambientDecode = null, ambientFail = null;   // the decoded pad, the pending decode, or why it failed
if (lightMode) fetch('sounds').then((r) => r.json()).then((j) => { soundFiles = j; if (j.ambient) { soundSource = 'file'; loadAmbient(j.ambient); } }).catch(() => {});
function getAudioCtx() {
  const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
  actx = actx || new AC();
  if (actx.state === 'suspended') actx.resume();
  return actx;
}
// fetch and decode the pad at load. A context made before any click sits suspended but decodes fine.
function loadAmbient(url) {
  const c = getAudioCtx(); if (!c) { ambientFail = 'no Web Audio'; return; }
  ambientDecode = fetch(url).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status + ' fetching ' + url); return r.arrayBuffer(); })
    .then((b) => c.decodeAudioData(b))
    .then((buf) => { ambientBuf = buf; console.log(`ambient file decoded: ${buf.duration.toFixed(1)} s, ${buf.numberOfChannels} ch, ${buf.sampleRate} Hz`); return buf; })
    .catch((e) => { ambientFail = String(e); console.warn('ambient file failed; the pad stays silent in file mode (B for the synth):', e); });
}
const ambientState = () => ambientBuf ? 'decoded' : ambientFail ? 'FAILED' : soundFiles.ambient ? 'decoding' : 'none';
const useFile = (name) => soundSource === 'file' && soundFiles[name];
const soundLabel = () => `${soundSource}${Object.keys(soundFiles).length ? ' [' + Object.keys(soundFiles).join(',') + ']' : ' [no files]'} pad:${ambientState()}`;
function playSfx(kind, x) {
  if (!lightMode) return;
  const file = kind === 'flick' ? 'swipe' : kind;            // in file mode a flick borrows the swipe sound
  if (useFile(file)) { const a = new Audio(soundFiles[file]); a.volume = sfxVol; a.play().catch(() => {}); return; }
  playNote(x ?? 50, kind);
}
// A major pentatonic over two octaves, A3..A5; the pad's drone is A2 (110 Hz)
// A major pentatonic over two octaves, A3..A5; the pad's drone is A2 (110 Hz)
const SCALE = [220, 246.94, 277.18, 329.63, 369.99, 440, 493.88, 554.37, 659.26, 739.99, 880];
// ---- harp. Each note is a plucked string rendered once into a buffer (Karplus-Strong: a burst
// of noise through a delay line the length of one period, averaged each pass so the highs die
// first), with a second string a few cents off for a little chorus. Rendering offline sidesteps
// Web Audio's minimum feedback delay, which would cap a live Karplus-Strong loop at ~340 Hz.
// A gesture plays a broken chord: three or four scale steps 40-70 ms apart, rising for tap and
// swipe, falling for flick, from a root picked by x across the wall. Everything goes through a
// small room: two feedback delays with a lowpass in the loop, so the notes ring.
const harpBuf = new Map();   // frequency -> AudioBuffer
// ---- harp: Karplus-Strong. The string is a delay line one period long, excited by a short
// low-passed noise burst (a fingertip, not a pick), with a one-pole low-pass at ~3 kHz in the
// loop so the highs die first, and the loss set for a 3-4 s ring. Rendered offline into a buffer
// once per pitch; a second string a few cents sharp adds a little shimmer.
function pluckBuffer(c, f) {
  const key = f.toFixed(2); if (harpBuf.has(key)) return harpBuf.get(key);
  const sr = c.sampleRate, secs = 4.2, out = c.createBuffer(1, Math.round(sr * secs), sr), d = out.getChannelData(0);
  const aLoop = 1 - Math.exp(-2 * Math.PI * 3000 / sr), aBurst = 1 - Math.exp(-2 * Math.PI * 1200 / sr);
  const string = (freq, gain) => {
    const N = Math.round(sr / freq), line = new Float32Array(N);
    let s0 = 0, s1 = 0;
    for (let i = 0; i < N; i++) { const w = Math.random() * 2 - 1; s0 += aBurst * (w - s0); s1 += aBurst * (s0 - s1); line[i] = s1; }   // two-pole low-passed burst
    const T60 = 3.5, loss = Math.pow(0.001, N / (sr * T60));
    let idx = 0, y = 0;
    for (let i = 0; i < d.length; i++) {
      y += aLoop * (line[idx] - y);                     // loop low-pass
      const nxt = y * loss;
      d[i] += nxt * gain; line[idx] = nxt; idx = (idx + 1) % N;
    }
  };
  string(f, 0.75); string(f * 1.0025, 0.3);
  let peak = 0; for (let i = 0; i < d.length; i++) peak = Math.max(peak, Math.abs(d[i]));
  if (peak > 0) for (let i = 0; i < d.length; i++) d[i] /= peak;
  harpBuf.set(key, out); return out;
}
// ---- the room: one generated impulse (5 s, stereo, exponential tail) in a convolver, shared by
// the pad and the harp, with a high-shelf cut on the wet path so nothing hisses. reverb= sets the wet share.
let room = null;   // {ctx, input}
function roomBus(c) {
  if (room && room.ctx === c) return room.input;
  const input = c.createGain(), dry = c.createGain(), wet = c.createGain();
  dry.gain.value = 1 - 0.35 * reverbMix; wet.gain.value = reverbMix;
  const secs = 5, n = Math.round(c.sampleRate * secs), ir = c.createBuffer(2, n, c.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = ir.getChannelData(ch); let lp = 0;
    for (let i = 0; i < n; i++) { const t = i / c.sampleRate; lp += 0.35 * ((Math.random() * 2 - 1) - lp); d[i] = lp * Math.exp(-t * Math.log(1000) / secs) * (t < 0.02 ? t / 0.02 : 1); }
  }
  const conv = c.createConvolver(); conv.buffer = ir;
  const shelf = c.createBiquadFilter(); shelf.type = 'highshelf'; shelf.frequency.value = 3500; shelf.gain.value = -8;
  input.connect(dry).connect(masterOut(c));
  input.connect(conv); conv.connect(shelf); shelf.connect(wet); wet.connect(masterOut(c));
  room = { ctx: c, input }; return input;
}
function playNote(x, kind) {
  const c = getAudioCtx(); if (!c) return;
  const root = Math.min(SCALE.length - 4, Math.max(0, Math.floor(x / 100 * (SCALE.length - 3))));
  const n = 3 + (Math.random() < 0.5 ? 1 : 0);
  const steps = [0, 2, 4, 7].slice(0, n).map((k) => Math.min(SCALE.length - 1, root + k));   // root, third, fifth, octave in scale steps
  if (kind === 'flick') steps.reverse();
  const bus = roomBus(c), vol = sfxVol * (kind === 'flick' ? 0.55 : 0.45);   // low: the harp sits under the pad
  let t = c.currentTime + 0.01;
  steps.forEach((idx, k) => {
    const src = c.createBufferSource(); src.buffer = pluckBuffer(c, SCALE[idx]);
    const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol * (1 - 0.08 * k), t + 0.003);
    src.connect(g).connect(bus); src.start(t); src.stop(t + 4.2);
    t += 0.06 + Math.random() * 0.03 + (Math.random() - 0.5) * 0.02;   // 60-90 ms apart, with a little wobble
  });
}
// ---- pad: root, fifth and major ninth, no third. Detuned sines and triangles in a low register
// through a low-pass near 1.2 kHz. Four slow LFOs at unrelated rates move the cutoff, one
// oscillator's detune, the amplitude and the stereo position, so the texture never repeats; a
// sixth breath per minute swells the level, shallow, never to silence. Into the shared room.
function ambientOn() {
  ambientOff(true);
  if (soundSource === 'file') {   // never the synth from here: a take must not record the wrong pad
    if (ambientBuf) { startAmbientFile(); return; }
    if (ambientFail) { console.warn('ambient: file failed to decode, staying silent:', ambientFail); return; }
    if (!ambientDecode) { console.warn('ambient: file mode but no ambient file listed, staying silent'); return; }
    console.warn('ambient: file still decoding, silent until it is ready');
    ambientDecode.then(() => { if (ambientWanted && soundSource === 'file' && !ambientPlay && ambientBuf) { console.log('ambient: decoded, starting late'); startAmbientFile(); } });
    return;
  }
  const c = getAudioCtx(); if (!c) return;
  const t = c.currentTime, nodes = [];
  const lfo = (hz, depth, target, phase = 0) => {   // a slow sine pushing `target` by +-depth
    const o = c.createOscillator(); o.frequency.value = hz; const g = c.createGain(); g.gain.value = depth;
    o.connect(g).connect(target); o.start(t + phase); nodes.push(o); return o;
  };
  const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1200; lp.Q.value = 0.5;
  const voices = [[110, 'sine', 0.5, 0], [110, 'sine', 0.45, 4], [165, 'triangle', 0.16, -3], [246.94, 'sine', 0.12, 2], [220, 'triangle', 0.08, 0]];   // A2 A2 E3 B3 A3
  const oscs = voices.map(([f, type, v, cents]) => {
    const o = c.createOscillator(); o.type = type; o.frequency.value = f; o.detune.value = cents;
    const g = c.createGain(); g.gain.value = v; o.connect(g).connect(lp); o.start(t); nodes.push(o); return o;
  });
  const swell = c.createGain(); swell.gain.value = 0.72;              // breath: +-0.14 around 0.72, six per minute
  const pan = c.createStereoPanner(); pan.pan.value = 0;
  const master = c.createGain(); master.gain.setValueAtTime(0, t); master.gain.linearRampToValueAtTime(ambVol, t + 6);
  lp.connect(swell).connect(pan).connect(master).connect(roomBus(c));
  lfo(0.03, 260, lp.frequency, 0.3);                                  // cutoff drifts 940-1460 Hz
  lfo(0.045, 5, oscs[1].detune, 1.1);                                 // the second root wanders +-5 cents
  lfo(0.07, 0.06, swell.gain, 2.0);                                   // a slow amplitude wander
  lfo(0.11, 0.4, pan.pan, 0.7);                                       // and a slow stereo drift
  lfo(0.1, 0.14, swell.gain, 0);                                      // the breath, ~6 per minute
  ambientSynth = { master, nodes };
}
// the decoded pad, looped, straight into the master (it is a finished texture: no shared room on top)
function startAmbientFile() {
  const c = getAudioCtx(); if (!c) return;
  const t = c.currentTime, src = c.createBufferSource(), gain = c.createGain();
  src.buffer = ambientBuf; src.loop = true;
  gain.gain.setValueAtTime(0, t); gain.gain.linearRampToValueAtTime(ambVol, t + 3);
  src.connect(gain).connect(masterOut(c)); src.start(t);
  ambientPlay = { src, gain };
}
function ambientOff(quick) {
  if (ambientPlay) {
    const c = getAudioCtx(), a = ambientPlay, ms = quick ? 0.3 : 3; ambientPlay = null;
    if (c) { const t = c.currentTime; a.gain.gain.cancelScheduledValues(t); a.gain.gain.setValueAtTime(a.gain.gain.value, t); a.gain.gain.linearRampToValueAtTime(0, t + ms); a.src.stop(t + ms + 0.05); }
  }
  if (ambientSynth) {
    const c = getAudioCtx(), a = ambientSynth, ms = quick ? 0.3 : 3; ambientSynth = null; if (!c) return;
    const t = c.currentTime;
    a.master.gain.cancelScheduledValues(t); a.master.gain.setValueAtTime(a.master.gain.value, t);
    a.master.gain.linearRampToValueAtTime(0, t + ms);
    a.nodes.forEach((o) => o.stop(t + ms + 0.05));
  }
}
function soundOp(op) {
  if (!lightMode) return;
  if (op.op === 'ambient') { ambientWanted = !!op.on; ambientWanted ? ambientOn() : ambientOff(false); }
  else if (op.op === 'source') { soundSource = op.v; if (ambientWanted) ambientOn(); }   // restart so the two can be compared live
}

const runKey = (key) => {
  const { color: { hex }, duration, easing, sound_only, soundLink } = key
  const ease = eases[easing]
  if (sound_only) {
    playSound(soundLink, duration);
    socket.emit('audio', {soundLink, duration})
    return
  }
  if(soundLink){
    playSound(soundLink, duration);
    socket.emit('audio', {soundLink, duration})
  }

  // Every light page fades itself from wherever it is, over the full duration. (The original
  // code animated on the wizard and streamed a 'hex' per frame; that stalled whenever the
  // wizard's tab was in the background, and it also compounded the interpolation so a fade
  // finished in a fraction of its time.)
  current = hex;
  socket.emit('field', { op: 'fade', hex, ms: duration, easing });
  fadeTone(hex, duration, easing);
}



// Keys are matched on event.code (the physical key: Space, Enter, ArrowLeft, KeyA ...), never on
// event.key, because Shift changes what event.key reports ('a' -> 'A', and layout-dependent for
// punctuation). Shift is read separately: it means "at the second point".
const CODE_KEYS = { Space: ' ', Enter: 'Enter', ArrowLeft: 'ArrowLeft', ArrowRight: 'ArrowRight', ArrowUp: 'ArrowUp', ArrowDown: 'ArrowDown', BracketLeft: '[', BracketRight: ']' };
function keyName(event) {
  const c = event.code || '';
  if (c in CODE_KEYS) return CODE_KEYS[c];
  if (/^Key[A-Z]$/.test(c)) return c[3].toLowerCase();
  if (/^Digit[0-9]$/.test(c)) return c[5];
  return event.key.length === 1 ? event.key.toLowerCase() : event.key;   // no code (synthetic events): fall back to key
}
document.onkeydown = (event) => {
  if (event.isComposing || event.target.tagName === 'TINKER-BUTTON' || event.target.tagName === 'INPUT') {
    return;
  }
  const k = keyName(event), shift = event.shiftKey;
  // gestures: what the visitor's hand is doing at the wall. The touch point goes along only if
  // this page has one (URL ?point=, or a click on the preview); Shift means the second point.
  const pt = shift && handPoint2 ? handPoint2 : pointSet ? handPoint : null;
  const at = pt ? { x: pt[0], y: pt[1] } : {};
  const arrows = { ArrowRight: 'right', ArrowLeft: 'left', ArrowUp: 'up', ArrowDown: 'down' };
  let gesture = null;
  if (k === ' ') gesture = { kind: 'tap', ...at };
  else if (arrows[k]) gesture = { kind: 'swipe', dir: arrows[k], ...at };
  else if (k === 'd') gesture = { kind: 'drag', ...at };
  else if (k === 'h') gesture = { kind: 'hold', ...at };
  if (gesture) { event.preventDefault(); socket.emit('hand', gesture); triggerHand(gesture.kind, gesture); return; }
  if (k === 'a') { const ap = { slot: shift ? 1 : 0, ...at }; socket.emit('approach', ap); triggerApproach(ap); return; }
  if (k === 'l') { socket.emit('leave', {}); releaseApproaches(); return; }
  if (k === 'Enter') { event.preventDefault(); socket.emit('poke', at); triggerPoke(at); return; }
  // field clock and sound: T jump the clock forward, R reset to full bloom, Z pause/resume aging,
  // S next season (base colour fades over 5 s on the light; new flowers roll from the new palette),
  // [ ] exposure down/up, M/N ambient on/off. Light pages act on these; this page relays (and acts if it is one).
  let field = null, sound = null;
  if (k === 's') {
    seasonOp(season + 1);
    field = { op: 'season', k: season, base: SEASONS[season].base, ms: 5000 };
    current = SEASONS[season].base;                 // so the next colour key fades from where the light ends up
    paint(current);
  }
  else if (k === '[') { setExposure(exposure - 0.1); field = { op: 'exposure', v: exposure }; }   // tracked here too, so steps accumulate
  else if (k === ']') { setExposure(exposure + 0.1); field = { op: 'exposure', v: exposure }; }
  else if (k === 't') field = { op: 'advance', ms: TIME_STEP_MS };
  else if (k === 'r') field = { op: 'reset' };
  else if (k === 'z') { agingPaused = !agingPaused; field = { op: 'pause', on: agingPaused }; }
  else if (k === 'm') sound = { op: 'ambient', on: true };
  else if (k === 'n') sound = { op: 'ambient', on: false };
  else if (k === 'b') { soundSource = soundSource === 'file' ? 'synth' : 'file'; sound = { op: 'source', v: soundSource }; }
  if (field) { socket.emit('field', field); fieldOp(field); return; }
  if (sound) { socket.emit('sound', sound); soundOp(sound); return; }
  if (keys && keys[k]) runKey(keys[k]);   // colour keys
}



socket.on('connect', () => {
  if (lightMode === 'blobs') socket.emit('field', { op: 'aspect', v: W / H });   // so the wizard's preview matches this wall
  socket.on('hex', (val) => { current = val; paint(val) })
  socket.on('hand', (v) => { triggerHand(v.kind, v) })
  socket.on('poke', (v) => { triggerPoke(v || {}) })
  socket.on('field', (v) => { fieldOp(v) })
  socket.on('approach', (v) => { triggerApproach(v || {}) })
  socket.on('leave', () => { releaseApproaches() })
  socket.on('sound', (v) => { soundOp(v) })
  socket.on('audio', (val) => {playSound(val.soundLink, val.duration);})
  socket.on('pauseAudio', (val) => {audio.pause();})
  socket.onAny((event, ...args) => {
    console.log(event, args);
  });
});

// enter controller mode
control.onclick = () => {
  console.log('control')
  // make sure you're not in fullscreen
  if (document.fullscreenElement) {
    document.exitFullscreen()
      .then(() => console.log('exited full screen mode'))
      .catch((err) => console.error(err));
  }
  // make buttons and controls visible
  document.getElementById('user').classList.remove('fadeOut');
  document.getElementById('controlPanel').style.opacity = 0.6;
  for (const id of ['legend', 'preview']) { const el = document.getElementById(id); if (el) el.hidden = false; }
  setAspect(); placeDots();   // now visible, so the height can be laid out
};

light.onclick = () => {
  // safari requires playing on input before allowing audio
  audio.muted = true;
  audio.play().then(audio.muted = false)
  getAudioCtx();   // unlock Web Audio for the synth sounds
  for (const id of ['legend', 'preview']) { const el = document.getElementById(id); if (el) el.hidden = true; }

  // in light mode make it full screen and fade buttons
  document.documentElement.requestFullscreen();
  document.getElementById('user').classList.add('fadeOut');
  document.getElementById('controlPanel').style.opacity = 0;
};


