const control = document.getElementById('control');
const light = document.getElementById('light');
const femaleBtn = document.getElementById('female');
const play = document.getElementById('play');
const pause = document.getElementById('pause');
const audioIn = document.getElementById('audioIn');
const audio = new Audio();
let pickr;

const stage = document.getElementById('stage');
const glow = document.getElementById('glow');
const labelEl = document.getElementById('label');
const cardEl = document.getElementById('card');

const socket = io();

// ---------------------------------------------------------------------------
// Shared simulation parameters. The server owns these; we get the current set
// on connect and patches whenever the controller changes something.
// ---------------------------------------------------------------------------

const P = {
  coupling: 0.05,
  periodCoupling: 0.06,
  periodMin: 0.7,
  periodMax: 2.5,
  flashColor: '#ffe83d',
  femaleColor: '#ff9e2c',
  nightColor: '#050b05',
  flashDuration: 260,
  responseDelay: 2000,
  manual: false,
  sound: true,
  running: true,
  decor: true,
  showLabels: true,
  card: '',
};

// A firefly is insensitive to other flashes for the first bit of its own
// cycle, the way a real one is right after it flashes. Without this, a firefly
// that is already ahead of the group keeps getting pushed further ahead.
const REFRACTORY = 0.12;

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

// ---------------------------------------------------------------------------
// This device
// ---------------------------------------------------------------------------

const me = {
  id: null,
  num: null,             // our number *within* our role: "Male Firefly 2"
  role: 'idle',          // 'male' | 'female' | 'controller' | 'idle'
  phase: Math.random(),  // 0..1, fires at 1
  period: 1.4,           // seconds, this firefly's own natural rhythm
  lastFlashAt: -Infinity,
  flashStartedAt: null,  // drives the glow envelope
  pendingReply: null,    // female: timer for her delayed answer
};

socket.on('identity', (data) => {
  me.id = data.id;
  if (data.params) Object.assign(P, data.params);
  scatterSelf();
  applyParams();
  renderControls();
});

socket.on('params', (patch) => {
  Object.assign(P, patch);
  applyParams();
  renderControls();
});

socket.on('role', (data) => {
  // controller reassigned us from its roster
  setRole(data.role, false);
});

// the roster usually arrives before anyone has picked a role, so keep the
// latest copy and re-render once this device becomes the controller
let lastRoster = [];
socket.on('roster', (list) => {
  lastRoster = list;
  // our own number can change when roles are reassigned, so read it back
  const mine = list.find((d) => d.id === me.id);
  if (mine) {
    const renumbered = me.num !== mine.num;
    me.num = mine.num;
    // our starting rhythm depends on which firefly we are, and that only
    // arrives here, a moment after tapping the role button
    if (renumbered) scatterSelf();
    updateLabel();
  }
  renderRoster(lastRoster);
});

socket.on('pulse', (p) => {
  if (!p || p.id === me.id) return;
  if (me.role === 'male' && p.role === 'male') {
    // males entrain to each other; a female's answer is a reply, not a metronome
    onNeighbourPulse(p.period);
  } else if (me.role === 'female' && p.role === 'male') {
    onMaleCall();
  }
});

// original tinkerbelle events, still live
socket.on('hex', (val) => { setNight(val); });
socket.on('audio', (val) => { getSound(encodeURI(val)); });
socket.on('pauseAudio', () => { audio.pause(); });

socket.on('flashNow', () => {
  if (me.role === 'male' || me.role === 'female') fire();
});

socket.on('scatter', (opts) => {
  if (opts && opts.mode === 'align') {
    alignSelf();
  } else {
    scatterSelf();
  }
});

socket.onAny((event, ...args) => { console.log(event, args); });

// ---------------------------------------------------------------------------
// The oscillator
//
// Each firefly free-runs at its own period. When it hears a neighbour it does
// two things: jumps its phase forward a little (Mirollo-Strogatz pulse
// coupling), and retunes its own natural period toward the neighbour's timing.
// Phase coupling alone cannot fully synchronise oscillators whose natural
// periods differ, so the second part is what actually gets them there.
// ---------------------------------------------------------------------------

function onNeighbourPulse(theirPeriod) {
  // 1. Drift our own natural rhythm toward theirs. Each pulse carries the
  //    sender's current period, so we average toward a stated value rather
  //    than estimating it from flash timings. Estimating looks equivalent but
  //    runs away: phase coupling makes a firefly fire early, which shortens
  //    its measured interval, which its neighbour then adopts, and the pair
  //    accelerates into a strobe. Averaging converges on the mean instead.
  if (typeof theirPeriod === 'number' && theirPeriod > 0.2 && theirPeriod < 6) {
    me.period = clamp(me.period + P.periodCoupling * (theirPeriod - me.period), 0.25, 6);
  }

  // 2. Shift when we are next due to flash. The response is biphasic: if the
  //    neighbour flashed while we were overdue we hurry up, and if it flashed
  //    just after we did we hold back. A flat "always hurry up" nudge is
  //    neutrally stable once the periods match, so the pair freezes wherever
  //    it happens to be, often half a cycle apart. This restores toward
  //    flashing together, and is what real fireflies do.
  if (me.phase > REFRACTORY) {
    me.phase = clamp(me.phase - P.coupling * Math.sin(2 * Math.PI * me.phase), 0, 1.2);
    if (me.phase >= 1) fire();
  }
}

function onMaleCall() {
  // A female does not free-run. She waits a species-specific delay and answers.
  if (me.pendingReply) return;                  // already answering this call
  if (performance.now() - me.lastFlashAt < P.responseDelay) return;
  me.pendingReply = setTimeout(() => {
    me.pendingReply = null;
    fire();
  }, P.responseDelay);
}

function fire() {
  me.phase = 0;
  me.lastFlashAt = performance.now();
  me.flashStartedAt = me.lastFlashAt;
  chirp();
  // the period travels with the pulse so neighbours can average toward it
  socket.emit('pulse', { id: me.id, role: me.role, period: me.period });
  updateLabel();
}

// Spread the fireflies deliberately rather than drawing at random. Firefly 1
// takes the fast end of the range, the last one the slow end, and they start
// evenly apart in the cycle. Random starts sometimes handed us two phones that
// were already nearly in step, which locked in a second or two and made it look
// like nothing had to be negotiated. A little jitter keeps it from looking
// mechanically exact.
function scatterSelf() {
  const total = lastRoster.filter((d) => d.role === me.role).length || 1;
  const idx = (me.num || 1) - 1;
  const pos = total > 1 ? idx / (total - 1) : 0;
  const lo = Math.min(P.periodMin, P.periodMax);
  const hi = Math.max(P.periodMin, P.periodMax);
  const base = lo + pos * (hi - lo);
  me.period = clamp(base * (1 + (Math.random() - 0.5) * 0.06), 0.25, 6);
  me.phase = (idx / total + Math.random() * 0.03) % 1;
  updateLabel();
}

function alignSelf() {
  me.period = (P.periodMin + P.periodMax) / 2;
  me.phase = 0.999;
  updateLabel();
}

let lastFrameAt = performance.now();

function loop(now) {
  const dt = Math.min((now - lastFrameAt) / 1000, 0.1); // cap after a tab stall
  lastFrameAt = now;

  // in manual mode a firefly holds still until tapped or fired by the controller
  if (P.running && !P.manual && me.role === 'male') {
    me.phase += dt / me.period;
    if (me.phase >= 1) fire();
  }

  drawGlow(now);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// fast attack, slow decay: reads as a living glow rather than a strobe
function drawGlow(now) {
  if (me.flashStartedAt === null) return;
  const t = (now - me.flashStartedAt) / P.flashDuration;
  if (t >= 1) {
    me.flashStartedAt = null;
    glow.style.opacity = 0;
    return;
  }
  const attack = 0.15;
  const env = t < attack
    ? t / attack
    : Math.pow(1 - (t - attack) / (1 - attack), 1.8);
  glow.style.opacity = env;
}

// ---------------------------------------------------------------------------
// Sound. Synthesized locally rather than fetched, because a flash needs its
// blip within milliseconds and every firefly needs its own pitch. Out of sync
// this is a clatter; in sync it collapses into a single clean pulse.
// ---------------------------------------------------------------------------

let audioCtx;

function ensureAudio() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) audioCtx = new Ctx();
  }
  if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
}

// pentatonic, so a whole field of unsynced fireflies still sounds pleasant
const SCALE = [523.25, 587.33, 698.46, 783.99, 880.0];

function chirp() {
  if (!P.sound || !audioCtx || me.role === 'idle' || me.role === 'controller') return;
  const female = me.role === 'female';
  // keyed to our role number, so Male 1 and Male 2 keep the same two pitches
  // across reconnects and you can hear which is which
  const base = SCALE[(me.num || 1) % SCALE.length];
  const freq = female ? base / 2 : base;
  const dur = female ? 0.26 : 0.13;

  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = female ? 'triangle' : 'sine';
  osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
  // a slight downward slide gives it an insect-like chirp
  osc.frequency.exponentialRampToValueAtTime(freq * 0.82, audioCtx.currentTime + dur);

  gain.gain.setValueAtTime(0.0001, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(female ? 0.18 : 0.25, audioCtx.currentTime + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + dur);

  osc.connect(gain).connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + dur + 0.02);
}

// ---------------------------------------------------------------------------
// Appearance
// ---------------------------------------------------------------------------

function setNight(color) {
  P.nightColor = color;
  document.body.style.backgroundColor = color;
  stage.style.setProperty('--night', color);
}

function applyParams() {
  const isLight = me.role === 'male' || me.role === 'female';
  stage.classList.toggle('on', isLight);
  stage.classList.toggle('decor', !!P.decor);
  stage.classList.toggle('hideLabels', !P.showLabels);
  stage.style.setProperty('--flash', me.role === 'female' ? P.femaleColor : P.flashColor);
  if (isLight) setNight(P.nightColor);

  cardEl.textContent = P.card || '';
  cardEl.classList.toggle('on', !!P.card);

  updateLabel();
}

function updateLabel() {
  if (!me.id) return;
  const n = me.num || 1;
  if (me.role === 'male') {
    // showing the live period makes the gradual retuning visible on camera
    labelEl.textContent = P.manual
      ? `Male Firefly ${n} · tap to flash`
      : `Male Firefly ${n} · ${me.period.toFixed(2)}s`;
  } else if (me.role === 'female') {
    labelEl.textContent = P.manual
      ? `Female Firefly ${n} · tap to flash`
      : `Female Firefly ${n} · answers in ${(P.responseDelay / 1000).toFixed(1)}s`;
  } else {
    labelEl.textContent = '';
  }
}

// tap anywhere on a firefly screen to flash it by hand
stage.onclick = () => {
  if (me.role === 'male' || me.role === 'female') fire();
};

// ---------------------------------------------------------------------------
// Roles
// ---------------------------------------------------------------------------

function setRole(role, announce = true) {
  me.role = role;
  if (announce) socket.emit('setRole', { role });

  const isLight = role === 'male' || role === 'female';
  const panel = document.getElementById('controlPanel');
  panel.classList.toggle('controller', role === 'controller');

  if (isLight) {
    document.getElementById('user').classList.add('fadeOut');
    panel.style.opacity = 0;
    if (pickr) {
      // this is annoying because of the pickr package
      pickr.destroyAndRemove();
      document.querySelector('#classicPanel').append(
        Object.assign(document.createElement('div'), { className: 'pickr' }),
      );
      pickr = undefined;
    }
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch((err) => console.log(err));
    }
    // safari requires playing on input before allowing audio
    audio.muted = true;
    audio.play().then(() => { audio.muted = false; }).catch(() => {});
    scatterSelf();
  } else {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch((err) => console.error(err));
    }
    document.getElementById('user').classList.remove('fadeOut');
    panel.style.opacity = 0.6;
  }

  applyParams();
}

light.onclick = () => { ensureAudio(); setRole('male'); };
femaleBtn.onclick = () => { ensureAudio(); setRole('female'); };

control.onclick = () => {
  ensureAudio();
  setRole('controller');
  buildPickr();
  renderControls();
  renderRoster(lastRoster);
};

// ---------------------------------------------------------------------------
// Controller UI
// ---------------------------------------------------------------------------

const SLIDERS = [
  ['coupling', (v) => v.toFixed(3)],
  ['periodCoupling', (v) => v.toFixed(3)],
  ['periodMin', (v) => `${v.toFixed(1)}s`],
  ['periodMax', (v) => `${v.toFixed(1)}s`],
  ['responseDelay', (v) => `${v}ms`],
  ['flashDuration', (v) => `${v}ms`],
];
const TOGGLES = ['sound', 'decor', 'showLabels', 'manual'];

// push a patch to everyone and apply it here too, since the server relays to
// others only
function emitParams(patch) {
  Object.assign(P, patch);
  socket.emit('params', patch);
  applyParams();
  renderControls();
}

SLIDERS.forEach(([key]) => {
  const el = document.getElementById(key);
  if (el) el.oninput = () => emitParams({ [key]: parseFloat(el.value) });
});

TOGGLES.forEach((key) => {
  const el = document.getElementById(key);
  if (el) el.onchange = () => emitParams({ [key]: el.checked });
});

document.querySelectorAll('#flashColors .swatch').forEach((btn) => {
  btn.onclick = () => emitParams({ flashColor: btn.dataset.color });
});

document.getElementById('runToggle').onclick = () => emitParams({ running: !P.running });
document.getElementById('scatter').onclick = () => socket.emit('scatter', { mode: 'scatter' });
document.getElementById('syncNow').onclick = () => socket.emit('scatter', { mode: 'align' });
document.getElementById('flashAll').onclick = () => socket.emit('flashNow', {});

const cardIn = document.getElementById('cardIn');
document.getElementById('cardPush').onclick = () => emitParams({ card: cardIn.value });
document.getElementById('cardClear').onclick = () => emitParams({ card: '' });
cardIn.onkeyup = (e) => { if (e.keyCode === 13) emitParams({ card: cardIn.value }); };

function renderControls() {
  if (me.role !== 'controller') return;
  SLIDERS.forEach(([key, fmt]) => {
    const el = document.getElementById(key);
    const out = document.getElementById(`${key}Val`);
    if (el && document.activeElement !== el) el.value = P[key];
    if (out) out.textContent = fmt(P[key]);
  });
  TOGGLES.forEach((key) => {
    const el = document.getElementById(key);
    if (el) el.checked = !!P[key];
  });
  document.querySelectorAll('#flashColors .swatch').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.color === P.flashColor);
  });
  document.getElementById('runToggle').textContent = P.running ? 'Pause all' : 'Resume all';
}

const ROLE_NAMES = { male: 'Male', female: 'Female', controller: 'Controller', idle: 'Idle' };

function deviceName(d) {
  if (d.role === 'male') return `Male Firefly ${d.num}`;
  if (d.role === 'female') return `Female Firefly ${d.num}`;
  return `#${d.id}`;
}

function renderRoster(list) {
  const el = document.getElementById('roster');
  if (!el || me.role !== 'controller') return;
  el.innerHTML = '<strong>Connected devices</strong>';
  list.forEach((d) => {
    const row = document.createElement('div');
    row.className = 'device';

    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = deviceName(d) + (d.id === me.id ? ' (this device)' : '');

    const select = document.createElement('select');
    Object.keys(ROLE_NAMES).forEach((role) => {
      const opt = document.createElement('option');
      opt.value = role;
      opt.textContent = ROLE_NAMES[role];
      if (role === d.role) opt.selected = true;
      select.append(opt);
    });
    select.onchange = () => socket.emit('setRole', { id: d.id, role: select.value });

    row.append(name, select);

    // flash this one firefly by hand
    if (d.role === 'male' || d.role === 'female') {
      const flash = document.createElement('button');
      flash.textContent = 'Flash';
      flash.onclick = () => socket.emit('flashNow', { id: d.id });
      row.append(flash);
    }

    el.append(row);
  });
}

// ---------------------------------------------------------------------------
// Classic tinkerbelle: colour picker + freesound audio
// ---------------------------------------------------------------------------

function buildPickr() {
  if (pickr) return;
  // create our color picker. You can change the swatches that appear at the bottom
  pickr = Pickr.create({
    el: '.pickr',
    theme: 'classic',
    showAlways: true,
    swatches: [
      'rgba(5, 11, 5, 1)',
      'rgba(255, 255, 255, 1)',
      'rgba(244, 67, 54, 1)',
      'rgba(233, 30, 99, 1)',
      'rgba(156, 39, 176, 1)',
      'rgba(103, 58, 183, 1)',
      'rgba(63, 81, 181, 1)',
      'rgba(33, 150, 243, 1)',
      'rgba(3, 169, 244, 1)',
      'rgba(0, 188, 212, 1)',
      'rgba(0, 150, 136, 1)',
      'rgba(76, 175, 80, 1)',
      'rgba(139, 195, 74, 1)',
      'rgba(205, 220, 57, 1)',
      'rgba(255, 235, 59, 1)',
      'rgba(255, 193, 7, 1)',
      'rgba(0, 0, 0, 1)',
    ],
    components: {
      preview: false,
      opacity: false,
      hue: true,
    },
  });

  pickr.on('change', (e) => {
    // when pickr color value is changed change background and send message on ws to change background
    const hexCode = e.toHEXA().toString();
    setNight(hexCode);
    socket.emit('hex', hexCode);
  });
}

const getSound = (query, loop = false, random = false) => {
  const url = `https://freesound.org/apiv2/search/text/?query=${query}+"&fields=name,previews&token=U5slaNIqr6ofmMMG2rbwJ19mInmhvCJIryn2JX89&format=json`;
  fetch(url)
    .then((response) => response.clone().text())
    .then((data) => {
      console.log(data);
      data = JSON.parse(data);
      if (data.results.length >= 1) var src = random ? choice(data.results).previews['preview-hq-mp3'] : data.results[0].previews['preview-hq-mp3'];
      audio.src = src;
      audio.play();
      console.log(src);
    })
    .catch((error) => console.log(error));
};

play.onclick = () => {
  socket.emit('audio', audioIn.value)
  getSound(encodeURI(audioIn.value));
};
pause.onclick = () => {
  socket.emit('pauseAudio', audioIn.value)
  audio.pause();
};
audioIn.onkeyup = (e) => { if (e.keyCode === 13) { play.click(); } };
