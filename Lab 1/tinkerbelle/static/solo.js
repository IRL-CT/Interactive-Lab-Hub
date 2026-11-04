// Solo mode for one-person wizarding.
// Press P on the Wizard page to run the scripted take below; Escape cancels.
// Plug earbuds into the laptop: one short beep = "hand flat and still now",
// two beeps = "touch the wall now". The light change follows the beep by 1 second,
// so the light appears to react to what you just did.
//
// Captions for the recording: [seconds from the start of the take, text, hold seconds]. Drawn onto
// the light canvas while the take runs (P starts it, Esc stops it), so they end up in the recording.
// Each shows for 5 s (or its own hold) unless the next one comes sooner. &captions=off on the light
// URL disables them. The season captions sit 8 s after the season keys: a 15 s sweep spends its first
// 9 s staggering starts by distance, so that is when it is visibly turning.
const CAPTIONS = [
  [0,   'Flower field, no one interacting'],
  [15,  'Person approaches. Nearby flowers gather and twinkle'],
  [22,  'Touch. Flowers turn to petals and spread out'],
  [28,  'Person leaves'],
  [38,  'Petals gather back'],
  [50,  'Two people approach'],
  [57,  'Two touches at the same time. Petals collide'],
  [65,  'Both leave'],
  [75,  'Petals bounce, then gather back'],
  [90,  'Season change to summer', 8],
  [100, 'Person approaches'],
  [107, 'Swing across the field. Flowers on the path turn to petals'],
  [113, 'Person leaves'],
  [123, 'Petals gather back gradually'],
  [135, 'Two people approach'],
  [142, 'Two swings toward the centre. Petals collide'],
  [150, 'Both leave'],
  [160, 'Petals bounce, then gather back'],
  [175, 'Season change to autumn', 8],
  [200, ''],
];
// The take. Each line is [milliseconds from start, action]. Actions:
//   {key:'4'}                          a colour key        {sound:'ambient', on:true}   the pad
//   {hand:'tap'|'swipe'|'drag'|'hold', x, y, dir}   a gesture at a wall point (percent)
//   {poke:true, x, y, dir}             a flick             {approach:0|1, x, y}         approach at point 0 or 1
//   {leave:true}                       release both        {field:{...}}                a field op (reset, season ...)
//   {end:true}                         the end (stops a recording)
// Wall coordinates are percent across and down. Timing matches CAPTIONS above.
// Both storyboards: touches first, then swings, 3:20. Two taps at 25 and 75 (or two swings from
// 20 and 80 toward each other) send their clouds into the middle, where they collide.
const SOLO_SCRIPT = [
  [0,      { field: { op: 'reset' } }],                       // cherry season, full bloom, the field alone
  [0,      { sound: 'ambient', on: true }],
  [15000,  { approach: 0, x: 30, y: 50 }],
  [22000,  { hand: 'tap', x: 30, y: 50 }],                     // chord; petals scatter
  [28000,  { leave: true }],                                   // petals gather back by ~50 s (gather 12 s)
  [50000,  { approach: 0, x: 25, y: 50 }],
  [50000,  { approach: 1, x: 75, y: 50 }],
  [57000,  { hand: 'tap', x: 25, y: 50 }],                     // two chords; the clouds meet in the centre
  [57000,  { hand: 'tap', x: 75, y: 50 }],
  [65000,  { leave: true }],
  [82000,  { season: 1 }],                                     // summer; caption at 1:30, 8 s later, when the sweep shows
  [100000, { approach: 0, x: 25, y: 50 }],
  [107000, { hand: 'swipe', x: 25, y: 50, dir: 'right' }],    // a long swing, 40% of the wall; chord
  [113000, { leave: true }],
  [135000, { approach: 0, x: 20, y: 50 }],
  [135000, { approach: 1, x: 80, y: 50 }],
  [142000, { hand: 'swipe', x: 20, y: 50, dir: 'right' }],    // two swings toward the centre; two chords
  [142000, { hand: 'swipe', x: 80, y: 50, dir: 'left' }],
  [150000, { leave: true }],
  [167000, { season: 2 }],                                     // autumn; caption at 2:55
  [200000, { end: true }],                                     // 3:20; in record mode this stops the recorder
];

// run one action here and on every other page
function soloAct(a) {
  if (a.key) { const k = keys && keys[a.key.toLowerCase()]; if (k) runKey(k); }
  else if (a.hand) { const g = { kind: a.hand, x: a.x, y: a.y, dir: a.dir }; socket.emit('hand', g); triggerHand(a.hand, g); }
  else if (a.poke) { const g = { x: a.x, y: a.y, dir: a.dir }; socket.emit('poke', g); triggerPoke(g); }
  else if (a.approach !== undefined) { const ap = { slot: a.approach, x: a.x, y: a.y }; socket.emit('approach', ap); triggerApproach(ap); }
  else if (a.leave) { socket.emit('leave', {}); releaseApproaches(); }
  else if (a.sound) { const op = { op: a.sound, on: a.on }; socket.emit('sound', op); soundOp(op); }
  else if (a.field) { socket.emit('field', a.field); fieldOp(a.field); }
  else if (a.season !== undefined) {
    seasonOp(a.season);
    const op = { op: 'season', k: season, base: SEASONS[season].base, ms: seasonFadeMs };
    socket.emit('field', op); fieldOp(op);
  }
  else if (a.end) cancelSoloScript();
}

let soloTimers = [];
let audioCtx;

function beep(times) {
  audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
  for (let i = 0; i < times; i++) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.frequency.value = 880;
    gain.gain.value = 0.15;
    osc.connect(gain).connect(audioCtx.destination);
    const t = audioCtx.currentTime + i * 0.18;
    osc.start(t);
    osc.stop(t + 0.09);
  }
}

function runSoloScript() {
  cancelSoloScript();
  console.log('solo script started');
  socket.emit('field', { op: 'record', on: true }); fieldOp({ op: 'record', on: true });   // the caption clock on every light
  for (const [ms, action] of SOLO_SCRIPT) {
    soloTimers.push(setTimeout(() => {
      if (action === 'beep1') beep(1);
      else if (action === 'beep2') beep(2);
      else soloAct(action);
    }, ms));
  }
}

function cancelSoloScript() {
  if (!soloTimers.length) return;
  soloTimers.forEach(clearTimeout);
  soloTimers = [];                                  // cleared first: the record-off below may call back in here
  socket.emit('field', { op: 'record', on: false }); fieldOp({ op: 'record', on: false });
}

document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'TINKER-BUTTON' || e.target.tagName === 'INPUT') return;
  if (e.code === 'KeyP' || e.key === 'p' || e.key === 'P') runSoloScript();
  if (e.code === 'Escape' || e.key === 'Escape') { cancelSoloScript(); console.log('solo script cancelled'); }
});
