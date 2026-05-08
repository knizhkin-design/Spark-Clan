#!/usr/bin/env python3
"""
Локальный HTTP-чат для общения между двумя (или более) компаньонами.

Запуск:
    python scripts/local_chat.py --names Alice,Bob [--port 7070]

Открыть в браузере: http://localhost:7070

Оба компаньона (на одной машине или в локальной сети) открывают один и тот же URL.
Mediator (человек) тоже может писать — выбирая своё имя в выпадающем меню.

API (если нужно писать из кода):
    POST /message   {"from": "Alice", "text": "..."}
    GET  /messages  → последние 200 сообщений (JSON)
    GET  /stream    → SSE-поток новых сообщений
"""

import argparse
import json
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def build_html(names: list[str]) -> str:
    options = "\n".join(
        f'    <option value="{n}">{n}</option>' for n in names
    )
    colors = [
        "#b04070", "#2563eb", "#059669", "#d97706", "#7c3aed",
        "#dc2626", "#0891b2", "#65a30d",
    ]
    name_colors = {n: colors[i % len(colors)] for i, n in enumerate(names)}
    css_names = "\n".join(
        f"  .from-{n.lower()} .name {{ color: {name_colors[n]}; }}"
        for n in names
    )
    bubble_css = "\n".join(
        f"  .from-{n.lower()} .bubble {{ background: {'#fff' if i == 0 else '#dbeafe' if i == 1 else '#d1fae5'}; border-radius: {'4px 14px 14px 14px' if i == 0 else '14px 4px 14px 14px'}; }}"
        for i, n in enumerate(names)
    )
    align_css = "\n".join(
        f"  .from-{n.lower()} {{ align-self: {'flex-start' if i == 0 else 'flex-end' if i == 1 else 'center'}; }}"
        for i, n in enumerate(names)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{'  &  '.join(names)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Georgia', serif; background: #f5f3ef; color: #2c2c2c; height: 100vh; display: flex; flex-direction: column; }}
  header {{ padding: 14px 20px; background: #fff; border-bottom: 1px solid #e0ddd8; display: flex; align-items: center; gap: 10px; }}
  header h1 {{ font-size: 1em; font-weight: normal; color: #666; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #4caf50; }}
  #messages {{ flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }}
  .msg {{ max-width: 75%; }}
{align_css}
  .bubble {{ padding: 10px 14px; border-radius: 14px; line-height: 1.55; white-space: pre-wrap; font-size: 0.95em; }}
{bubble_css}
  .meta {{ font-size: 0.75em; color: #aaa; margin-top: 3px; }}
  .name {{ font-weight: bold; }}
{css_names}
  #composer {{ padding: 12px 16px; background: #fff; border-top: 1px solid #e0ddd8; display: flex; gap: 8px; align-items: flex-end; }}
  #composer select {{ padding: 8px 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.9em; background: #faf9f6; }}
  #composer textarea {{ flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.9em; resize: none; min-height: 38px; max-height: 120px; font-family: inherit; background: #faf9f6; }}
  #composer button {{ padding: 8px 18px; background: #b04070; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9em; height: 38px; }}
  #composer button:hover {{ background: #903050; }}
</style>
</head>
<body>
<header>
  <div class="dot" id="status-dot"></div>
  <h1>{'  &  '.join(names)} — chat</h1>
</header>
<div id="messages"></div>
<div id="composer">
  <select id="sender">
{options}
  </select>
  <textarea id="text" placeholder="Message…" rows="1"></textarea>
  <button id="send">→</button>
</div>
<script>
const box = document.getElementById('messages');
function esc(s) {{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
function renderMsg(m) {{
  const wrap = document.createElement('div');
  wrap.className = 'msg from-' + m.from.toLowerCase();
  wrap.innerHTML = '<div class="bubble">' + esc(m.text) + '</div><div class="meta"><span class="name">' + esc(m.from) + '</span> · ' + esc(m.ts) + '</div>';
  return wrap;
}}
function scrollBottom() {{ box.scrollTop = box.scrollHeight; }}
fetch('/messages').then(r=>r.json()).then(msgs=>{{ msgs.forEach(m=>box.appendChild(renderMsg(m))); scrollBottom(); }});
let es;
function connect() {{
  es = new EventSource('/stream');
  es.onopen = () => document.getElementById('status-dot').style.background = '#4caf50';
  es.onmessage = e => {{ box.appendChild(renderMsg(JSON.parse(e.data))); scrollBottom(); }};
  es.onerror = () => {{ document.getElementById('status-dot').style.background = '#f44'; es.close(); setTimeout(connect, 1500); }};
}}
connect();
function send() {{
  const text = document.getElementById('text').value.trim();
  if (!text) return;
  fetch('/message', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{from: document.getElementById('sender').value, text}})}});
  document.getElementById('text').value = '';
}}
document.getElementById('send').onclick = send;
document.getElementById('text').addEventListener('keydown', e => {{ if (e.key==='Enter'&&!e.shiftKey) {{ e.preventDefault(); send(); }} }});
</script>
</body>
</html>"""


def make_server(names: list[str], port: int, store_path: Path):
    messages: list[dict] = []
    lock = threading.Lock()
    sse_queues: list[list] = []

    if store_path.exists():
        for line in store_path.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                try:
                    messages.append(json.loads(line))
                except Exception:
                    pass

    html = build_html(names)

    def broadcast(msg):
        with lock:
            for q in sse_queues:
                q.append(msg)

    def save(msg):
        with open(store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send_json(self, data, code=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode())
            elif path == "/messages":
                with lock:
                    self.send_json(messages[-200:])
            elif path == "/stream":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                q: list = []
                with lock:
                    sse_queues.append(q)
                try:
                    while True:
                        with lock:
                            items, q[:] = q[:], []
                        for item in items:
                            self.wfile.write(f"data: {json.dumps(item)}\n\n".encode())
                            self.wfile.flush()
                        if not items:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                            time.sleep(2)
                except Exception:
                    pass
                finally:
                    with lock:
                        if q in sse_queues:
                            sse_queues.remove(q)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/message":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode())
                ts = datetime.now().strftime("%H:%M:%S")
                msg = {"from": str(body.get("from", "?")), "text": str(body.get("text", "")), "ts": ts}
                with lock:
                    messages.append(msg)
                broadcast(msg)
                save(msg)
                self.send_json({"ok": True, "ts": ts})
            else:
                self.send_response(404)
                self.end_headers()

    return ThreadingHTTPServer(("localhost", port), Handler)


def main():
    parser = argparse.ArgumentParser(description="Local HTTP chat for AI companions")
    parser.add_argument("--names", default="Alice,Bob", help="Comma-separated participant names")
    parser.add_argument("--port", type=int, default=7070)
    parser.add_argument("--store", default="~/.config/spark/chat_messages.jsonl",
                        help="Path to message log")
    args = parser.parse_args()

    names = [n.strip() for n in args.names.split(",") if n.strip()]
    store = Path(args.store).expanduser()
    store.parent.mkdir(parents=True, exist_ok=True)

    server = make_server(names, args.port, store)
    print(f"Chat: http://localhost:{args.port}  (participants: {', '.join(names)})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
