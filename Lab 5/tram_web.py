"""
tram_web.py: a tiny live web app for the tram watcher, served from the Pi.

    python tram_web.py                 # http://<pi-address>:8080  (run next to tram_watch.py)
    python tram_web.py --port 9000

Phones on a network that can reach the Pi open http://<pi-address>:8080. To share it with
anyone, anywhere, put a free tunnel in front of it (no router changes), for example:
    cloudflared tunnel --url http://localhost:8080      # prints a public https://...trycloudflare.com link
or Tailscale Funnel. Put that link in tram_config.json as "public_url" and tram_notify.py makes
every notification open it.

Endpoints:
    /            the page (updates itself every 2 s)
    /api/state   the live JSON (position, speed, ETAs, last pass, next-pass prediction)
    /api/passes  the last 20 passes
    /api/recent  recent passes with estimated vs true times
    /api/accuracy  how close estimates have been to the truth
    POST /api/truth?key=...&kind=arrival|departure   "I saw it arrive / leave just now"

Your private link (printed at start) adds ?key=..., which shows the "I saw it arrive / leave"
buttons. Share the link WITHOUT the key with other people.
Only numbers are served, never camera images. It is labeled as an unofficial estimate.
"""
import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import tram_accuracy
from tram_common import EVENTS, STATE, load_config, save_config

TRUTH_KEY = None             # set in main(); only links with ?key=<this> show the "I saw it" buttons

PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Island Tram Watch</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--fg:#1d1d1f;--dim:#6b6b70;--line:#d9d6cf;--accent:#c8102e;--ok:#1f8a4c;--warn:#b26b00}
@media (prefers-color-scheme:dark){:root{--bg:#121214;--card:#1c1c1f;--fg:#f2f2f2;--dim:#9a9aa0;--line:#333338;--accent:#ff4d5e;--ok:#4cc27e;--warn:#e0a03a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 -apple-system,system-ui,Segoe UI,Roboto,sans-serif}
main{max-width:520px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--dim);font-size:13px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.status{font-size:22px;font-weight:700}.big{font-size:40px;font-weight:800;letter-spacing:-1px;font-variant-numeric:tabular-nums}
.dim{color:var(--dim);font-size:14px}.row{display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-top:1px solid var(--line)}
.row:first-child{border-top:0}
.track{position:relative;height:44px;margin:14px 6px 4px}
.route{position:relative;height:74px;margin:22px 20px 6px}
.rope{position:absolute;left:0;right:0;top:14px;height:2px;background:var(--dim);opacity:.6}
.station{position:absolute;top:6px;width:12px;height:18px;margin-left:-6px;border-radius:3px;background:var(--line);border:1px solid var(--dim)}
.viewzone{position:absolute;top:2px;height:40px;border-radius:8px;background:var(--accent);opacity:.08}
.viewzone span{position:absolute;top:-15px;right:2px;font-size:10px;color:var(--dim)}
.rend{position:absolute;top:50px;font-size:12px;color:var(--dim);width:50%}
.gondola{position:absolute;top:14px;width:30px;margin-left:-15px;transition:left 2s linear,opacity .6s;display:none}
.gondola i{display:block;width:2px;height:9px;margin:0 auto;background:var(--fg);opacity:.7}
.gondola b{display:block;height:17px;border-radius:5px;background:var(--accent);color:#fff;font:700 12px/17px system-ui;text-align:center}
.gondola.ghost b{background:transparent;border:2px dashed var(--accent);color:var(--accent);line-height:13px;animation:breathe 3s ease-in-out infinite}
.gondola.ghost i{opacity:.35}
.gondola.seen b{animation:pulse 1.6s ease-in-out infinite}
@keyframes breathe{0%,100%{opacity:.45}50%{opacity:.85}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(200,16,46,.5)}50%{box-shadow:0 0 0 7px rgba(200,16,46,0)}}
@media (prefers-reduced-motion:reduce){.gondola{transition:none}.gondola b{animation:none!important}}
.legend{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);margin:6px 0 2px;flex-wrap:wrap}
.lg{display:inline-block;width:16px;height:10px;border-radius:3px;margin-left:6px}.lg.solid{background:var(--accent)}.lg.ghost{border:2px dashed var(--accent)}
.cable{position:absolute;left:0;right:0;top:20px;height:2px;background:var(--line)}
.end{position:absolute;top:28px;font-size:12px;color:var(--dim)}
.cab{position:absolute;top:12px;width:18px;height:18px;margin-left:-9px;border-radius:50%;color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:18px;background:var(--accent);transition:left 1s linear;display:none}
.pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:13px;font-weight:600;background:var(--line)}
.live{background:var(--accent);color:#fff}.foot{color:var(--dim);font-size:12px;margin-top:18px}
.band{position:absolute;top:10px;height:22px;border-radius:11px;background:var(--accent);opacity:.22;display:none;transition:all 1s linear}
.cab{opacity:.85}.tag{position:absolute;top:-6px;left:0;font-size:11px;color:var(--dim)}
.btns{display:flex;gap:8px;margin-top:10px}.btns button{flex:1;padding:12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);font-size:15px;font-weight:600}
.err{font-variant-numeric:tabular-nums}.good{color:var(--ok)}.meh{color:var(--warn)}
.small{font-size:13px}
</style></head><body><main>
<h1>Island Tram Watch</h1>
<div class="sub">Live estimates from a window camera. Unofficial; check posted schedules.</div>

<div class="card">
  <div id="pill" class="pill">loading…</div>
  <div id="status" class="status" style="margin-top:8px">&nbsp;</div>
  <div id="detail" class="dim">&nbsp;</div>
  <div class="route" id="route">
    <div class="rope"></div>
    <div class="station" style="left:0"></div><div class="station" style="left:100%"></div>
    <div id="viewzone" class="viewzone"><span>camera</span></div>
    <div class="gondola" id="g0"><i></i><b></b></div><div class="gondola" id="g1"><i></i><b></b></div>
    <div class="rend" style="left:0">Manhattan</div><div class="rend" style="right:0;text-align:right">Roosevelt Island</div>
  </div>
  <div class="legend"><span class="lg solid"></span>seen by the camera <span class="lg ghost"></span>estimated position</div>
  <div id="cablist" class="small dim"></div>
</div>

<div class="card">
  <div class="dim">Next tram expected</div>
  <div id="next" class="big">–</div>
  <div id="nextd" class="dim">&nbsp;</div>
  <div id="nextdirs" class="small" style="margin-top:10px"></div>
</div>

<div class="card" id="recent"><div class="dim">Recent trams: estimated vs true</div></div>
<div class="card" id="acc"><div class="dim">How accurate has it been?</div><div id="accbody" class="small" style="margin-top:6px">no checks yet</div></div>
<div class="card" id="truth" style="display:none">
  <div class="dim">Saw the tram yourself? Tap the moment it happens:</div>
  <div class="btns"><button onclick="truth('arrival')">It arrived at the island</button><button onclick="truth('departure')">It left the island</button></div>
  <div id="truthmsg" class="dim small" style="margin-top:6px">&nbsp;</div>
</div>
<div class="foot" id="foot"></div>
</main>
<script>
const $ = id => document.getElementById(id);
const KEY = new URLSearchParams(location.search).get("key");
const hm = iso => iso ? iso.slice(11,16) : "–";
const when = iso => { if (!iso) return "–"; const d = new Date(iso), t = new Date();
  const days = Math.round((new Date(t.toDateString()) - new Date(d.toDateString())) / 864e5);
  return days === 0 ? hm(iso) : days === 1 ? "yesterday " + hm(iso) :
    d.toLocaleDateString(undefined, {weekday: "short"}) + " " + hm(iso); };
const hms = iso => iso ? iso.slice(11,19) : "–";
const secs = iso => iso ? Math.round((new Date(iso) - new Date()) / 1000) : null;
const mmss = s => s == null ? "" : (s < 0 ? "now" : (s >= 60 ? Math.floor(s/60) + " min " : "") + (s % 60) + " s");
const pct = p => Math.round(p * 100) + "%";
const sgn = s => (s > 0 ? "+" : s < 0 ? "−" : "±") + Math.abs(s);
const errtxt = s => Math.abs(s) >= 90 ? sgn(Math.round(s / 60)) + " min" : sgn(s) + " s";
const errword = e => { const a = Math.abs(e), amt = a >= 90 ? Math.round(a / 60) + " min" : a + " s";
  return e === 0 ? "spot on" : "estimate " + amt + (e < 0 ? " early" : " late"); };
const errcls = s => Math.abs(s) <= 15 ? "good" : "meh";
if (KEY) $("truth").style.display = "block";

async function tick(){
  try{
    const st = await (await fetch("api/state", {cache:"no-store"})).json();
    const age = (new Date() - new Date(st.time)) / 1000;
    const cabins = (st.cabins && st.cabins.length) ? st.cabins : (st.live ? [st.live] : []);
    const fresh = age <= 20;
    const toIsland = c => c.heading === "station", leaving = c => c.heading === "tower";
    const line = c => toIsland(c)
      ? "Heading to the island: est. arrival ~" + hms(c.eta_station) + (c.eta_station ? (secs(c.eta_station) > 0 ? " (in " + mmss(secs(c.eta_station)) + ")" : " (due now)") : "") +
        (c.eta_station_low ? " · 80% likely " + hms(c.eta_station_low) + "–" + hms(c.eta_station_high) : "") +
        (c.eta_station_p30 != null ? " · " + pct(c.eta_station_p30) + " chance within ±30 s" : "")
      : leaving(c) ? "Left the island, heading to Manhattan" : "Stopped or slow";
    if (!fresh){ $("pill").textContent = "offline"; $("pill").className = "pill";
      $("status").textContent = "Tracker not running"; $("detail").textContent = "Last update " + hm(st.time); }
    else if (st.tram_in_view && cabins.length){
      $("pill").textContent = cabins.length > 1 ? "BOTH CABINS IN VIEW" : "TRAM IN VIEW"; $("pill").className = "pill live";
      if (cabins.length > 1){ $("status").textContent = "Two cabins passing";
        $("detail").innerHTML = cabins.map((c, i) => "<b>Cabin " + (i + 1) + ":</b> " + line(c)).join("<br>"); }
      else { const c = cabins[0];
        $("status").textContent = toIsland(c) ? "Heading to the island" : leaving(c) ? "Leaving the island" : "Tram in view";
        $("detail").textContent = toIsland(c) ? line(c).replace("Heading to the island: ", "") : leaving(c) ? "Heading to Manhattan" : "Stopped or slow"; }
    } else if (st.tram_in_view){ $("pill").textContent = "TRAM IN VIEW"; $("pill").className = "pill live";
      $("status").textContent = "Tram in view"; $("detail").textContent = ""; }
    else if (!st.in_service){ $("pill").textContent = "closed"; $("pill").className = "pill";
      $("status").textContent = "Not running now"; $("detail").textContent = st.next && st.next.opens ? "Opens " + hm(st.next.opens) : ""; }
    else { $("pill").textContent = "waiting"; $("pill").className = "pill";
      const lp = st.last_pass; $("status").textContent = lp ? "Last tram " + when(lp.start) : "No tram yet today";
      $("detail").textContent = lp ? (lp.direction || "") +
        (lp.est_station_arrival ? " · reached the island ~" + hms(lp.est_station_arrival) + " (estimated)" : "") +
        (lp.est_station_departure ? " · left the island ~" + hms(lp.est_station_departure) + " (estimated)" : "") : ""; }
    drawRoute(fresh ? st.route : null);
    const n = st.next || {};
    const dirName = d => /island/i.test(d || "") ? "arrival at the island" : /manhattan/i.test(d || "") ? "departure from the island" : "tram";
    if (n.status === "ok" && n.eta){ $("next").textContent = "~" + hm(n.eta);
      $("nextd").textContent = (n.direction ? "next " + dirName(n.direction) + " · " : "") + "estimated, in about " + mmss(secs(n.eta)) +
        (n.low && n.high ? " · 80% likely " + hm(n.low) + "–" + hm(n.high) : "") +
        (n.p_within_5min != null ? " · " + pct(n.p_within_5min) + " chance within 5 min" : ""); }
    else if (n.status === "overdue"){ $("next").textContent = "any moment"; $("nextd").textContent = "later than usual"; }
    else if (n.status === "closed"){ $("next").textContent = hm(n.opens); $("nextd").textContent = "first tram"; }
    else if (n.status === "waiting"){ $("next").textContent = "–";
      $("nextd").textContent = "Waiting to see a tram first" + (n.typical_gap_s ? " · they usually run every ~" + Math.round(n.typical_gap_s / 60) + " min now" : ""); }
    else { $("next").textContent = "–"; $("nextd").textContent = n.status || ""; }
    const by = st.next_by_direction || {};
    $("nextdirs").innerHTML = Object.keys(by).sort().map(d => { const p = by[d];
      const txt = p.status === "ok" && p.eta ? "~" + hm(p.eta) + (p.low && p.high ? " (80%: " + hm(p.low) + "–" + hm(p.high) + ")" : "")
                : p.status === "overdue" ? "any moment" : p.status === "waiting" ? "after the next tram" : (p.status || "–");
      return "<div class='row'><span>Next " + dirName(d) + "</span><span class='dim'>" + txt + "</span></div>"; }).join("") +
      (Object.keys(by).length && Object.values(by)[0].based_on ? "<div class='dim small' style='margin-top:4px'>from " + Object.values(by)[0].based_on + "</div>" : "");
    $("foot").textContent = "Updated " + st.time.slice(11,19) + " · " + (st.passes_today || 0) + " trams seen today";
  }catch(e){ $("pill").textContent = "no connection"; }
}
const Z80 = 1.2816;

function drawRoute(route){
  const vz = $("viewzone"), list = $("cablist");
  const cabins = route && route.cabins ? route.cabins : [];
  if (route){ vz.style.display = "block"; vz.style.left = (route.view_start * 100) + "%"; vz.style.width = ((1 - route.view_start) * 100) + "%"; }
  else vz.style.display = "none";
  [0, 1].forEach(i => {
    const g = $("g" + i), c = cabins[i];
    if (!c){ g.style.display = "none"; return; }
    g.style.display = "block";
    g.className = "gondola " + (c.seen ? "seen" : "ghost");
    g.style.left = (Math.max(0, Math.min(1, c.pos)) * 100) + "%";
    g.title = c.label;
    const h = (c.heading || "").toLowerCase();
    g.querySelector("b").textContent = h.includes("island") && !h.includes("at ") ? "→" : h.includes("manhattan") && !h.includes("at ") ? "←" : "";
  });
  list.innerHTML = cabins.map(c => "<div class='row'><span>" + (c.seen ? "● seen" : "◌ estimated") +
    "</span><span>" + c.label + "</span></div>").join("") ||
    (route ? "<div style='margin-top:4px'>No cabins placed yet: the route fills in after the camera sees a tram each way.</div>" : "");
}

async function recent(){
  try{
    const rows = await (await fetch("api/recent", {cache:"no-store"})).json();
    const box = $("recent"); box.innerHTML = '<div class="dim">Recent trams: estimated vs true</div>';
    rows.slice(0, 8).forEach(p => {
      const parts = [];
      if (p.est_arrival) parts.push("arrived island: est " + hms(p.est_arrival) +
        (p.true_arrival ? " · true " + hms(p.true_arrival) + " <span class='err " + errcls(p.arrival_error_s) + "'>(" + errword(p.arrival_error_s) + ")</span>" : " · true: not timed"));
      if (p.est_departure) parts.push("left island: est " + hms(p.est_departure) +
        (p.true_departure ? " · true " + hms(p.true_departure) + " <span class='err " + errcls(p.departure_error_s) + "'>(" + errword(p.departure_error_s) + ")</span>" : " · true: not timed"));
      if (p.predicted_start) parts.push("predicted ~" + hm(p.predicted_start) + " · came " + hm(p.start) +
        " <span class='err " + (Math.abs(p.prediction_error_s) <= 120 ? "good" : "meh") + "'>(" + errword(p.prediction_error_s) + ")</span>");
      if (!parts.length) parts.push(p.direction || "passed");
      const r = document.createElement("div"); r.className = "row";
      r.innerHTML = "<span>" + hm(p.start) + "</span><span class='dim small' style='text-align:right'>" + parts.join("<br>") + "</span>";
      box.appendChild(r);
    });
    if (!rows.length) box.innerHTML += '<div class="dim" style="margin-top:6px">none yet</div>';
  }catch(e){}
}

async function accuracy(){
  try{
    const a = await (await fetch("api/accuracy", {cache:"no-store"})).json();
    const lines = [];
    if (a.next_tram) lines.push("<b>Next-tram predictions</b> (" + a.next_tram.n + " checked): typically off by " +
      errtxt(a.next_tram.median_abs_error_s).replace(/^[+−±]/, "") + "; within 2 min " + pct(a.next_tram.within_2_min) +
      " of the time" + (a.next_tram.inside_range != null ? "; inside the 80% range " + pct(a.next_tram.inside_range) + " of the time" : ""));
    [["arrival", "Island arrival"], ["departure", "Island departure"]].forEach(([k, name]) => {
      if (a[k]) lines.push("<b>" + name + " estimates</b> vs " + a[k].n + " hand-timed: typically off by " + a[k].median_abs_error_s + " s" +
        (a[k].bias_s != null ? " (now corrected for a " + Math.abs(a[k].bias_s) + " s " + (a[k].bias_s < 0 ? "early" : "late") + " bias)" : " (5+ timings needed to self-correct)"));
    });
    $("accbody").innerHTML = lines.length ? lines.join("<br><br>") : "No checks yet. Next-tram predictions are checked automatically; island times need a few hand-timed taps.";
  }catch(e){}
}

async function truth(kind){
  try{
    const r = await fetch("api/truth?key=" + encodeURIComponent(KEY) + "&kind=" + kind, {method:"POST"});
    const j = await r.json();
    $("truthmsg").textContent = r.ok ? "Logged true " + kind + " at " + j.t.slice(11,19) + ". Thanks!" : "Not logged: " + (j.error || r.status);
    recent(); accuracy();
  }catch(e){ $("truthmsg").textContent = "Not logged: no connection"; }
}
tick(); recent(); accuracy(); setInterval(tick, 2000); setInterval(recent, 15000); setInterval(accuracy, 30000);
</script></body></html>
"""


def recent_passes(n=20):
    out = []
    try:
        with open(EVENTS) as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("event") == "pass":
                    out.append(e)
    except OSError:
        pass
    return out[-n:]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")      # so other apps can read the API
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/state":
            try:
                with open(STATE) as f:
                    self._send(200, f.read(), "application/json")
            except OSError:
                self._send(503, json.dumps({"error": "tram_watch.py is not running"}), "application/json")
        elif path == "/api/passes":
            self._send(200, json.dumps(recent_passes()), "application/json")
        elif path == "/api/recent":
            self._send(200, json.dumps(tram_accuracy.recent()), "application/json")
        elif path == "/api/accuracy":
            self._send(200, json.dumps(tram_accuracy.summary()), "application/json")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path.rstrip("/") != "/api/truth":
            return self._send(404, "not found", "text/plain")
        if not TRUTH_KEY or not secrets.compare_digest(q.get("key", ""), TRUTH_KEY):
            return self._send(403, json.dumps({"error": "wrong key"}), "application/json")
        if q.get("kind") not in ("arrival", "departure"):
            return self._send(400, json.dumps({"error": "kind must be arrival or departure"}),
                              "application/json")
        entry = tram_accuracy.log_truth(q["kind"])
        print(f"true {entry['kind']} logged at {entry['t'][11:]}", flush=True)
        self._send(200, json.dumps(entry), "application/json")

    def log_message(self, *args):          # keep the terminal quiet
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    global TRUTH_KEY
    cfg = load_config()                    # fail early with a clear message if not set up
    if not cfg.get("truth_key"):
        cfg["truth_key"] = secrets.token_urlsafe(8)
        save_config(cfg)
    TRUTH_KEY = cfg["truth_key"]
    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"serving on http://0.0.0.0:{args.port}  (Ctrl-C to stop)\n"
          f"your private link (with the 'I saw it' buttons): add ?key={TRUTH_KEY} to the address",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
