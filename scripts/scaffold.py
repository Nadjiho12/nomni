#!/usr/bin/env python3
"""Project scaffolder. Creates a small, runnable starter so work begins from a
working foundation instead of a blank file.

Usage:
  python scaffold.py static      my-site
  python scaffold.py canvas-game my-game
  python scaffold.py php-app     my-php
  python scaffold.py node-api    my-api
  python scaffold.py py-cli      my-tool

Each template prints run instructions when done.
"""
import pathlib
import sys

T = {}

T["static"] = {
    "index.html": """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Site title</title>
  <meta name="description" content="One-sentence description for search results.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="wrap"><a class="brand" href="/">Brand</a>
    <nav aria-label="Main"><a href="#work">Work</a> <a href="#contact">Contact</a></nav></header>
  <main class="wrap">
    <h1>Headline that states the value</h1>
    <p class="lead">One supporting sentence.</p>
    <a class="btn" href="#contact">Primary action</a>
    <section id="work"><h2>Work</h2></section>
    <section id="contact"><h2>Contact</h2></section>
  </main>
  <footer class="wrap"><small>&copy; 2026</small></footer>
  <script src="app.js" type="module"></script>
</body>
</html>
""",
    "style.css": """:root{--bg:#fff;--fg:#14161a;--muted:#5b6470;--accent:#3b5bfd;--radius:12px;--s1:.5rem;--s2:1rem;--s3:2rem;--s4:4rem}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#eceff4;--muted:#9aa3b0;--accent:#7c93ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:1rem/1.6 system-ui,sans-serif}
.wrap{max-width:60rem;margin-inline:auto;padding:var(--s2)}
header.wrap{display:flex;justify-content:space-between;align-items:center}
h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.1}.lead{color:var(--muted);font-size:1.2rem}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:.7rem 1.2rem;border-radius:var(--radius);text-decoration:none}
a:focus-visible,.btn:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
""",
    "app.js": "console.log('ready');\n",
    "_run": "Open index.html, or: python -m http.server 8000",
}

T["canvas-game"] = {
    "index.html": """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Game</title>
<style>html,body{margin:0;height:100%;background:#0b0d12;overflow:hidden;touch-action:none}
canvas{display:block;margin:auto;image-rendering:pixelated;max-width:100vw;max-height:100vh}</style></head>
<body><canvas id="c" width="320" height="180"></canvas><script type="module" src="game.js"></script></body></html>
""",
    "game.js": """// Minimal fixed-timestep game: move a square with arrows/WASD/touch, collect coins.
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const W = cv.width, H = cv.height, STEP = 1 / 60;
const keys = new Set();
addEventListener('keydown', e => keys.add(e.key.toLowerCase()));
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
const touch = { x: null, y: null };
cv.addEventListener('pointerdown', e => setTouch(e)); cv.addEventListener('pointermove', e => e.buttons && setTouch(e));
cv.addEventListener('pointerup', () => { touch.x = touch.y = null; });
function setTouch(e){ const r = cv.getBoundingClientRect(); touch.x = (e.clientX - r.left) / r.width * W; touch.y = (e.clientY - r.top) / r.height * H; }
const rng = (() => { let s = 12345; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32; })();
const state = { player: { x: W / 2, y: H / 2, s: 10, v: 90 }, coins: [], score: 0, mode: 'play' };
function spawn(){ state.coins.push({ x: 10 + rng() * (W - 20), y: 10 + rng() * (H - 20), r: 4 }); }
for (let i = 0; i < 5; i++) spawn();
function update(dt){
  const p = state.player; let dx = 0, dy = 0;
  if (keys.has('arrowleft') || keys.has('a')) dx--; if (keys.has('arrowright') || keys.has('d')) dx++;
  if (keys.has('arrowup') || keys.has('w')) dy--; if (keys.has('arrowdown') || keys.has('s')) dy++;
  if (touch.x !== null) { dx = Math.sign(touch.x - p.x) * (Math.abs(touch.x - p.x) > 3); dy = Math.sign(touch.y - p.y) * (Math.abs(touch.y - p.y) > 3); }
  const len = Math.hypot(dx, dy) || 1;
  p.x = Math.min(W - p.s, Math.max(0, p.x + dx / len * p.v * dt));
  p.y = Math.min(H - p.s, Math.max(0, p.y + dy / len * p.v * dt));
  state.coins = state.coins.filter(c => {
    const hit = Math.abs(c.x - (p.x + p.s / 2)) < p.s / 2 + c.r && Math.abs(c.y - (p.y + p.s / 2)) < p.s / 2 + c.r;
    if (hit) { state.score++; spawn(); }
    return !hit;
  });
}
function draw(){
  ctx.fillStyle = '#0b0d12'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#ffd34d'; state.coins.forEach(c => { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, 6.283); ctx.fill(); });
  ctx.fillStyle = '#6ee7b7'; const p = state.player; ctx.fillRect(p.x | 0, p.y | 0, p.s, p.s);
  ctx.fillStyle = '#fff'; ctx.font = '10px monospace'; ctx.fillText('Score ' + state.score, 6, 12);
}
let last = performance.now(), acc = 0;
function frame(now){
  acc += Math.min(0.05, (now - last) / 1000); last = now;   // clamp: tab switches must not explode physics
  while (acc >= STEP) { update(STEP); acc -= STEP; }
  draw(); requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
""",
    "_run": "python -m http.server 8000  ->  http://localhost:8000  (modules need a server, not file://)",
}

T["php-app"] = {
    "public/index.php": """<?php
declare(strict_types=1);
session_start();
require __DIR__ . '/../src/db.php';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
if (empty($_SESSION['csrf'])) { $_SESSION['csrf'] = bin2hex(random_bytes(32)); }
function e(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
if ($path === '/' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $rows = db()->query('SELECT id, title FROM notes ORDER BY id DESC')->fetchAll();
    ?><!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Notes</title><h1>Notes</h1>
    <form method="post" action="/add"><input type="hidden" name="csrf" value="<?= e($_SESSION['csrf']) ?>">
      <label for="t">New note</label> <input id="t" name="title" maxlength="120" required> <button>Add</button></form>
    <ul><?php foreach ($rows as $r): ?><li><?= e($r['title']) ?></li><?php endforeach; ?></ul></html><?php
    exit;
}
if ($path === '/add' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!hash_equals($_SESSION['csrf'], (string)($_POST['csrf'] ?? ''))) { http_response_code(403); exit('Bad CSRF token'); }
    $title = trim((string)($_POST['title'] ?? ''));
    $len = function_exists('mb_strlen') ? mb_strlen($title, 'UTF-8') : strlen($title);   // mbstring is not guaranteed on minimal PHP builds
    if ($title === '' || $len > 120) { http_response_code(422); exit('Invalid title'); }
    db()->prepare('INSERT INTO notes (title) VALUES (?)')->execute([$title]);
    header('Location: /', true, 303); exit;
}
http_response_code(404); echo 'Not found';
""",
    "src/db.php": """<?php
declare(strict_types=1);
function db(): PDO {
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data.sqlite', null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $pdo->exec('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)');
    }
    return $pdo;
}
""",
    "_run": "php -S localhost:8000 -t public public/index.php   (front controller routes every URL)",
}

T["node-api"] = {
    "package.json": """{"name":"api","version":"1.0.0","type":"module","scripts":{"start":"node server.js"},"dependencies":{}}
""",
    "server.js": """// Zero-dependency REST API (Node 18+). Swap for Express/Fastify when you need middleware.
import http from 'node:http';
const items = new Map(); let nextId = 1;
const send = (res, code, body) => { res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(body)); };
const readJson = req => new Promise((ok, bad) => { let b = ''; req.on('data', c => { b += c; if (b.length > 1e6) req.destroy(); });
  req.on('end', () => { try { ok(b ? JSON.parse(b) : {}); } catch { bad(new Error('invalid json')); } }); });
http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x'); const m = url.pathname.match(/^\\/items(?:\\/(\\d+))?$/);
  try {
    if (!m) return send(res, 404, { error: 'not found' });
    const id = m[1] && Number(m[1]);
    if (req.method === 'GET' && !id) return send(res, 200, [...items.values()]);
    if (req.method === 'GET') return items.has(id) ? send(res, 200, items.get(id)) : send(res, 404, { error: 'not found' });
    if (req.method === 'POST' && !id) {
      const { name } = await readJson(req);
      if (typeof name !== 'string' || !name.trim() || name.length > 100) return send(res, 422, { error: 'name required (<=100 chars)' });
      const item = { id: nextId++, name: name.trim() }; items.set(item.id, item); return send(res, 201, item);
    }
    if (req.method === 'DELETE' && id) return items.delete(id) ? send(res, 204, {}) : send(res, 404, { error: 'not found' });
    send(res, 405, { error: 'method not allowed' });
  } catch (e) { send(res, 400, { error: e.message }); }
}).listen(process.env.PORT || 3000, () => console.log('listening'));
""",
    "_run": "node server.js ; curl -X POST localhost:3000/items -d '{\"name\":\"a\"}' ; curl localhost:3000/items",
}

T["py-cli"] = {
    "tool.py": '''#!/usr/bin/env python3
"""Tool template: subcommands, dry-run, logging, exit codes."""
import argparse
import logging
import sys
from pathlib import Path

log = logging.getLogger("tool")


def cmd_count(args):
    files = [p for p in Path(args.path).rglob(args.glob) if p.is_file()]
    log.info("matched %d files", len(files))
    for p in files[: args.limit]:
        print(p)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="show actions without changing anything")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("count", help="list files matching a glob")
    c.add_argument("path")
    c.add_argument("--glob", default="*")
    c.add_argument("--limit", type=int, default=20)
    c.set_defaults(fn=cmd_count)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        log.error("%s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
''',
    "_run": "python tool.py count . --glob '*.py'",
}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=sorted(T), help="template to create")
    ap.add_argument("dest", help="new (or empty) directory")
    args = ap.parse_args()
    kind, name = args.kind, pathlib.Path(args.dest)
    if name.exists() and any(name.iterdir()):
        print(f"error: {name} exists and is not empty", file=sys.stderr)
        sys.exit(1)
    for rel, content in T[kind].items():
        if rel == "_run":
            continue
        p = name / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print("created", p)
    print("run:", T[kind]["_run"])


if __name__ == "__main__":
    main()
