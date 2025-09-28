// ~/vlt/fastvlm_server.mjs
//
// FastVLM HTTP server (localhost only) using @huggingface/transformers + onnxruntime-web (WASM).
// - HTTP API: GET /health, POST /infer, POST /shutdown
// - Accepts local file paths and file:// URLs (reads via fs), or http(s) URLs.
// - Clean 200/4xx/5xx responses; no stdin/stdout protocols.
//
// Setup (in project dir):
//   npm uninstall onnxruntime-node @xenova/transformers
//   npm install @huggingface/transformers onnxruntime-web
//
// Run (usually spawned by Python):
//   node fastvlm_server.mjs
//
// Env:
//   VLM_MODEL=onnx-community/FastVLM-0.5B-ONNX
//   VLM_PORT=17860
//   VLM_CLEAR_CACHE=1
//   HF_HOME=...

import http from 'node:http';
import process from 'node:process';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { URL, fileURLToPath } from 'node:url';

function ts() { return new Date().toISOString(); }
const QUIET = /^(1|true|yes)$/i.test(process.env.VLM_QUIET ?? '');
const DEBUG = /^(1|true|yes)$/i.test(process.env.VLM_DEBUG ?? '');
function log(...args)   { if (!QUIET) console.error(`[${ts()}]`, ...args); }
function warn(...args)  { if (!QUIET) console.error(`[${ts()}] WARN:`, ...args); }
function debug(...args) { if (DEBUG && !QUIET) console.error(`[${ts()}] DEBUG:`, ...args); }
function fatal(...args) { console.error(`[${ts()}] FATAL:`, ...args); process.exit(1); }

const IS_TTY = !!process.stderr.isTTY && !QUIET;


// ---------------- deps ----------------
try { await import('onnxruntime-web'); }
catch (e) {
  const msg = String(e?.message || e);
  if (msg.includes("Cannot find package 'onnxruntime-web'")) {
    fatal(
      'Missing dependency "onnxruntime-web". Fix with:\n' +
      '  npm uninstall onnxruntime-node @xenova/transformers\n' +
      '  npm install @huggingface/transformers onnxruntime-web'
    );
  }
  fatal('Failed loading onnxruntime-web:', e?.stack || e);
}

let AutoProcessor, AutoModelForImageTextToText, RawImage, env;
try {
  ({ AutoProcessor, AutoModelForImageTextToText, RawImage, env } =
    await import('@huggingface/transformers'));
} catch (e) {
  const msg = String(e?.message || e);
  if (msg.includes("Cannot find package '@huggingface/transformers'")) {
    fatal(
      'Missing dependency "@huggingface/transformers". Fix with:\n' +
      '  npm uninstall onnxruntime-node @xenova/transformers\n' +
      '  npm install @huggingface/transformers onnxruntime-web'
    );
  }
  fatal('Failed to import @huggingface/transformers:', e?.stack || e);
}

// Soft-warn if native addon lingers
try {
  await import('onnxruntime-node').then(() => {
    warn('"onnxruntime-node" is installed. We do not use it; remove to avoid conflicts:\n  npm uninstall onnxruntime-node');
  }).catch(() => {});
} catch {}

// ---------------- runtime config ----------------
try {
  env.backends.onnx.backend = 'wasm';
  const cpuCount = (os.cpus()?.length ?? 4);
  const threadsEnv = parseInt(process.env.VLM_THREADS || '', 10);
  const threads = Number.isFinite(threadsEnv) && threadsEnv > 0
    ? threadsEnv
    : Math.max(1, Math.min(3, Math.floor(cpuCount / 2))); // gentler default
  env.backends.onnx.wasm.numThreads = threads;
  env.useBrowserCache = false;
  env.allowRemoteModels = true;
  log(`Backend configured: backend=wasm threads=${env.backends.onnx?.wasm?.numThreads ?? 'n/a'} cpus=${cpuCount}`);
} catch (e) {
  warn('Failed to set WASM backend params:', e?.message ?? e);
}


const MODEL_ID = process.env.VLM_MODEL ?? 'onnx-community/FastVLM-0.5B-ONNX';
const PORT     = parseInt(process.env.VLM_PORT || '17860', 10);
const HOST     = '127.0.0.1';
const dtype    = { embed_tokens: 'fp32', vision_encoder: 'fp32', decoder_model_merged: 'fp32' };

// ---------------- helpers ----------------
function startProgress(label = 'Loading', tickMs = 200) {
  // Disable the spinner if not a TTY or if VLM_PROGRESS=0
  if (!IS_TTY || /^(0|false|no)$/i.test(process.env.VLM_PROGRESS ?? '1')) {
    const t0 = Date.now();
    return { stop() {}, elapsedMs() { return Date.now() - t0; } };
  }
  let dots = 0;
  const start = Date.now();
  const timer = setInterval(() => {
    dots = (dots + 1) % 10;
    const bar = '█'.repeat(dots) + '-'.repeat(10 - dots);
    const secs = ((Date.now() - start) / 1000).toFixed(1);
    process.stderr.write(`\r[${ts()}] [${label}] [${bar}] ${secs}s elapsed`);
  }, tickMs);
  return { stop() { clearInterval(timer); process.stderr.write('\n'); },
           elapsedMs() { return Date.now() - start; } };
}


async function purgeModelCacheIfRequested(modelId) {
  if (!process.env.VLM_CLEAR_CACHE) return false;

  const hfHome =
    process.env.HF_HOME
      || (process.env.HOME && path.join(process.env.HOME, '.cache', 'huggingface'))
      || path.join(os.homedir(), '.cache', 'huggingface');

  const bases = [
    path.join(hfHome, 'transformers'),
    path.join(process.cwd(), 'node_modules', '@huggingface', 'transformers', '.cache'),
  ];
  let removed = false;
  for (const base of bases) {
    const p1 = path.join(base, modelId.replaceAll('/', path.sep));
    const p2 = path.join(p1, 'onnx');
    for (const p of [p1, p2]) {
      try { await fs.rm(p, { recursive: true, force: true }); removed = true; log('Purged cache:', p); }
      catch {}
    }
  }
  return removed;
}

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
    'Cache-Control': 'no-store',
    'Connection': 'close',
    'X-Server': 'fastvlm-http',
  });
  res.end(payload);
}

async function readJsonBody(req, limit = 2 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > limit) { reject(Object.assign(new Error('payload too large'), { code: 'ETOOBIG' })); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')); }
      catch { reject(Object.assign(new Error('invalid JSON'), { code: 'EBADJSON' })); }
    });
    req.on('error', reject);
  });
}

function isHttpUrl(s) { return /^https?:\/\//i.test(s); }
function isFileUrl(s) { return /^file:\/\//i.test(s); }
function isLikelyPath(s) { return !/^[a-z]+:\/\//i.test(s); }

async function loadRawImage(input) {
  // Accept: http(s) URL, file:// URL, or plain filesystem path
  try {
    if (typeof input !== 'string') throw new Error('image must be a string');

    if (isHttpUrl(input)) {
      debug('[image] from HTTP(S) URL:', input);
      return await RawImage.fromURL(input);
    }

    if (isFileUrl(input)) {
      const p = fileURLToPath(input);
      debug('[image] from file URL:', p);
      return await RawImage.fromURL(p);
    }

    if (isLikelyPath(input)) {
      const abs = path.resolve(input);
      debug('[image] from path:', abs);
      try { await fs.access(abs); } catch { throw new Error(`file not accessible: ${abs}`); }
      return await RawImage.fromURL(abs);
    }

    debug('[image] from fallback URL-ish:', input);
    return await RawImage.fromURL(input);
  } catch (e) {
    const msg = e?.message ?? String(e);
    throw new Error(`loadRawImage failed: ${msg}`);
  }
}




// ---------------- model globals ----------------
let processor, model;
let ready = false;
let readyAt = null;
let busy = false;
let isShuttingDown = false;
globalThis.__fatalLoadError = null;

// ---------------- model load ----------------
async function loadModel() {
  log(`Boot: model="${MODEL_ID}" deviceWanted=cpu backend=wasm (pure JS via HF)`);
  if (process.env.VLM_CLEAR_CACHE) {
    const purged = await purgeModelCacheIfRequested(MODEL_ID);
    if (purged) log('Note: cache purge requested and completed.');
  }

  const pb = startProgress('Loading');
  try {
    log('Stage 1: Loading processor...');
    processor = await AutoProcessor.from_pretrained(MODEL_ID);
    log('Stage 1: Processor loaded OK.');

    log('Stage 2: Loading model (fp32, wasm backend, pure JS)...');
    model = await AutoModelForImageTextToText.from_pretrained(MODEL_ID, { dtype, device: 'cpu' });

    ready = true;
    readyAt = new Date().toISOString();
    pb.stop();
    log(`Model ready on device=cpu backend=wasm in ${(pb.elapsedMs()/1000).toFixed(2)}s.`);
  } catch (err) {
    pb.stop();
    const msg = String(err || '');
    warn('Model load failed:', msg);
    ready = false; readyAt = null;
    globalThis.__fatalLoadError = msg;
  }
}

// ---------------- HTTP server ----------------
const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, `http://${req.headers.host}`);
    if (u.hostname !== 'localhost' && u.hostname !== '127.0.0.1') {
      return sendJson(res, 403, { ok: false, error: 'forbidden' });
    }

    // Health
    if (req.method === 'GET' && u.pathname === '/health') {
      if (isShuttingDown) return sendJson(res, 503, { ok: false, ready: false, shutting_down: true });
      if (ready) return sendJson(res, 200, { ok: true, ready: true, model: MODEL_ID, backend: 'wasm', device: 'cpu', ready_at: readyAt });
      if (globalThis.__fatalLoadError) return sendJson(res, 500, { ok: false, ready: false, error: globalThis.__fatalLoadError });
      return sendJson(res, 503, { ok: false, ready: false, stage: 'loading' });
    }

    // Inference
    if (req.method === 'POST' && u.pathname === '/infer') {
    if (isShuttingDown) return sendJson(res, 503, { ok: false, error: 'shutting down' });
    if (!ready) return sendJson(res, 503, { ok: false, error: 'model not ready' });

    let body;
    try { body = await readJsonBody(req); }
      catch (e) {
        const code = e?.code === 'ETOOBIG' ? 413 : 400;
        return sendJson(res, code, { ok: false, error: e?.message || 'bad request' });
      }

    const image = body?.image;
    const prompt = (body?.prompt ?? 'Describe the image.');
    const max_new_tokens_req = parseInt(body?.max_new_tokens || '', 10);
    const max_new_tokens = Math.max(1, Math.min(256, Number.isFinite(max_new_tokens_req) ? max_new_tokens_req : 12));

    if (!image || typeof image !== 'string') return sendJson(res, 400, { ok: false, error: 'image (string) is required' });
    if (busy) return sendJson(res, 409, { ok: false, error: 'busy, try again' });

    busy = true;

    const marks = [];
    const mark = (label) => marks.push([label, Date.now()]);
    mark('start');

    try {
      debug('[infer] start', { image, max_new_tokens });

      const imageObj = await loadRawImage(image);
      mark('image_loaded');

      const chat = [{ role: 'user', content: `<image>${prompt}` }];
      const templ = processor.apply_chat_template(chat, { add_generation_prompt: true });
      mark('templated');

      const inputs = await processor(imageObj, templ, { add_special_tokens: false });
      mark('inputs_ready');

      const outputs = await model.generate({
        ...inputs,
        max_new_tokens,
        do_sample: false,
      });
      mark('generated');

      const text = processor.batch_decode(
        outputs.slice(null, [inputs.input_ids.dims.at(-1), null]),
        { skip_special_tokens: true }
      )?.[0] ?? '';
      mark('decoded');

      const dt_ms = marks.at(-1)[1] - marks[0][1];
      debug('[infer] timings(ms):', Object.fromEntries(
        marks.slice(1).map((m, i) => [m[0], m[1] - marks[i][1]])
      ));

      return sendJson(res, 200, { ok: true, text: String(text).trim(), dt_ms });
    } catch (e) {
      const emsg = String(e?.message || e);
      if (/ENOENT|not exist|no such file/i.test(emsg)) {
        return sendJson(res, 404, { ok: false, error: 'image not found' });
      }
      warn('INFER error:', e?.stack || e);
      return sendJson(res, 500, { ok: false, error: emsg });
    } finally {
      busy = false;
    }
  }


    // Shutdown
    if (req.method === 'POST' && u.pathname === '/shutdown') {
      isShuttingDown = true;
      sendJson(res, 200, { ok: true, message: 'shutting down' });
      setTimeout(() => server.close(() => process.exit(0)), 50);
      return;
    }

    // Not found
    return sendJson(res, 404, { ok: false, error: 'not found' });
  } catch (e) {
    warn('Request handling error:', e?.stack || e);
    try { sendJson(res, 500, { ok: false, error: 'internal error' }); } catch {}
  }
});

server.listen(PORT, HOST, () => {
  log(`HTTP server listening on http://${HOST}:${PORT}`);
  loadModel().catch((e) => warn('loadModel top-level error:', e?.stack || e));
});

process.on('SIGINT',  () => { log('SIGINT');  server.close(() => process.exit(0)); });
process.on('SIGTERM', () => { log('SIGTERM'); server.close(() => process.exit(0)); });
process.on('uncaughtException', (e) => { console.error(e); process.exit(1); });
process.on('unhandledRejection', (e) => { console.error(e); process.exit(1); });
