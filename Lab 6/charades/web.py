"""
Telephone Charades: the laptop page. Each Pi serves its own player's page on port 8000.
Standard library only (no Flask), so there is nothing extra to install.

    GET  /                  the page (page.html)
    GET  /api/state         what this player should see right now (only THEIR prompt, not the others')
    GET  /api/clip?key=...  the frames of one clip ("take" = my own take, not sent yet)
    GET  /api/live          the newest webcam frame while counting down / recording (204 otherwise)
    POST /api/action        {"action": "tap" | "hold"}  same as the button
                            {"action": "guess", "text": "..."}  send a typed guess
"""
import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PAGE = pathlib.Path(__file__).resolve().parent / "page.html"


class WebServer:
    def __init__(self, player, port=8000, host="0.0.0.0"):
        self.player, self.port, self.host = player, port, host
        self.httpd = None

    def start(self):
        player = self.player

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code, body, ctype="application/json"):
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                url = urlparse(self.path)
                if url.path in ("/", "/index.html"):
                    return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
                if url.path == "/api/state":
                    return self._send(200, player.view())
                if url.path == "/api/live":
                    jpg = player.live
                    if not jpg:
                        self.send_response(204)
                        self.send_header("Cache-Control", "no-store")
                        self.end_headers()
                        return
                    return self._send(200, jpg, "image/jpeg")
                if url.path == "/api/clip":
                    q = parse_qs(url.query)
                    key = (q.get("key") or [""])[0]
                    game = (q.get("game") or [None])[0]
                    return self._send(200, player.clip_view(key, game))
                return self._send(404, {"error": "not found"})

            def do_POST(self):
                if urlparse(self.path).path != "/api/action":
                    return self._send(404, {"error": "not found"})
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    msg = json.loads(self.rfile.read(n) or b"{}")
                except ValueError:
                    return self._send(400, {"error": "bad json"})
                ok = player.web_action(msg.get("action"), msg.get("text"))
                return self._send(200 if ok else 400, {"ok": ok})

            def log_message(self, *args):
                pass

        try:
            self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError as err:
            raise SystemExit(f"port {self.port} is busy ({err}). Is another player.py running? Try --port 8001")
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self.port

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
