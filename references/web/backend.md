# Web backend and full stack

*Last updated: 2026-10-13 | Version-sensitive: framework, library, and runtime LTS versions; hosting terms and prices | Re-check current docs before pinning versions, prices, or API names.*

Starters: `scripts/scaffold.py php-app <dir>` and `scripts/scaffold.py node-api <dir>`.

## Contents
1. Architecture and stack choice
2. REST API design
3. PHP (plain PDO)
4. Node.js (Express)
5. Python (FastAPI)
6. SQL and data modeling
7. Authentication and sessions
8. File uploads
9. Security checklist
10. Deployment
11. Debugging playbook
12. Verification

## 1. Architecture and stack choice

Flow: **route → validate → service (business rules) → data access → response**. Keep handlers thin.

| Constraint | Pick |
|---|---|
| Cheap shared hosting | PHP + MySQL |
| Fast JSON API, real-time | Node (Express/Fastify) |
| Data/ML-adjacent | Python FastAPI |
| Prototype | SQLite (zero setup) |
| Multi-user production | PostgreSQL or MySQL |

## 2. REST API design

- Nouns for resources: `GET /items`, `POST /items`, `GET /items/{id}`, `PATCH /items/{id}`, `DELETE /items/{id}`.
- Status codes: 200 OK, 201 Created, 204 No Content, 400 malformed, 401 not logged in, 403 not allowed, 404 missing, 409 conflict, 422 validation, 429 rate limited, 500 server bug.
- Errors: `{"error":"human message","code":"machine_code","fields":{"email":"invalid"}}`.
- Paginate lists (`?limit=20&cursor=...`), version breaking changes (`/v1/`), return `Location` on create.
- Document with a curl example per endpoint.

## 3. PHP (plain PDO)

```php
<?php declare(strict_types=1);
// Register
$hash = password_hash($_POST['password'], PASSWORD_DEFAULT);
$stmt = db()->prepare('INSERT INTO users (email, pass_hash) VALUES (?, ?)');
$stmt->execute([$email, $hash]);            // UNIQUE index on email; catch PDOException code 23000

// Login
$u = db()->prepare('SELECT id, pass_hash FROM users WHERE email = ?'); $u->execute([$email]); $u = $u->fetch();
if ($u && password_verify($_POST['password'], $u['pass_hash'])) {
    session_regenerate_id(true); $_SESSION['uid'] = $u['id'];
}

// Session cookie hardening (before session_start)
session_set_cookie_params(['httponly' => true, 'secure' => true, 'samesite' => 'Lax']);

// JSON endpoint
header('Content-Type: application/json');
$in = json_decode(file_get_contents('php://input'), true) ?? [];
echo json_encode(['ok' => true]);

// Auth guard
function require_login(): int { if (empty($_SESSION['uid'])) { http_response_code(401); exit(json_encode(['error'=>'login required'])); } return (int)$_SESSION['uid']; }
```

Rules: prepared statements only; escape output with `htmlspecialchars`; CSRF token on every POST form; config outside web root; `display_errors=0` in production; log errors. Routing on Apache: `.htaccess` with `RewriteRule ^ index.php [L]` for non-file requests.

## 4. Node.js (Express)

```js
import express from 'express'; import helmet from 'helmet'; import rateLimit from 'express-rate-limit';
const app = express(); app.use(helmet(), express.json({ limit: '100kb' }), rateLimit({ windowMs: 60_000, max: 100 }));
const wrap = fn => (req, res, next) => fn(req, res, next).catch(next);          // async errors → error handler
app.post('/items', wrap(async (req, res) => {
  const { name } = req.body; if (typeof name !== 'string' || !name.trim()) return res.status(422).json({ error: 'name required' });
  res.status(201).json(await db.insert(name.trim()));
}));
app.use((err, _req, res, _next) => { console.error(err); res.status(500).json({ error: 'server error' }); });
app.listen(process.env.PORT || 3000);
```

Use `zod` or `joi` for schemas; `better-sqlite3` or `pg` with parameter placeholders (`$1`); `dotenv` for config; `jsonwebtoken`/session cookies for auth.

## 5. Python (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
app = FastAPI(); DB = {}
class ItemIn(BaseModel): name: str = Field(min_length=1, max_length=100)
@app.post("/items", status_code=201)
def create(i: ItemIn): id = len(DB) + 1; DB[id] = {"id": id, **i.model_dump()}; return DB[id]
@app.get("/items/{id}")
def read(id: int):
    if id not in DB: raise HTTPException(404, "not found")
    return DB[id]
# run: uvicorn main:app --reload    docs auto-generated at /docs
```

## 6. SQL and data modeling

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, pass_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_posts_user ON posts(user_id, created_at DESC);
-- Many-to-many: junction table with composite primary key
CREATE TABLE post_tags (post_id INTEGER REFERENCES posts(id), tag_id INTEGER REFERENCES tags(id), PRIMARY KEY (post_id, tag_id));
```

Model entities, then relations, then indexes for the queries you actually run. Use transactions for multi-step writes; migrations as numbered files; `EXPLAIN` slow queries; avoid `SELECT *` in APIs.

## 7. Authentication and sessions

- Server-rendered app: session cookie (HttpOnly, Secure, SameSite) + CSRF token.
- SPA + API: same-site cookie session is simplest and safest; JWTs need refresh, revocation, and careful storage, so use them only when required.
- Passwords: bcrypt/argon2 (`password_hash`, `bcrypt`, `argon2-cffi`). Never store or log plaintext.
- Add login rate limiting, generic error text ("email or password incorrect"), and password reset via single-use, expiring tokens.
- Authorization: check ownership on every read/write (`WHERE id = ? AND user_id = ?`), never trust IDs or roles from the client.

## 8. File uploads

Allow-list extensions and MIME (check the real content, not the name), cap size, generate a random filename, store outside the web root or in object storage, serve through a handler that sets `Content-Type` and `X-Content-Type-Options: nosniff`, and never execute uploads.

## 9. Security checklist

Parameterized queries · output encoding · CSRF protection · secure cookies · hashed passwords · rate limits · HTTPS · security headers (CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`) · least-privilege DB user · no secrets in git · dependency updates · error messages that do not leak internals. State which are covered in your delivery.

## 10. Deployment

- Static: GitHub Pages (push to `gh-pages`/`main` + Pages setting), Netlify, Cloudflare Pages.
- PHP shared host: upload via SFTP, set document root to `public/`, import SQL, set config outside web root.
- Node/Python: small VPS or PaaS (Render, Railway, Fly), process manager (systemd/pm2), reverse proxy (nginx/Caddy) with automatic HTTPS, environment variables for secrets, health endpoint, log rotation.
- Always: backups, a rollback plan, and a `.env.example` listing required variables.

## 11. Debugging playbook

Reproduce → read the actual error (logs, network tab, stack trace) → isolate (which layer: browser, network, server, DB) → form one hypothesis → change one thing → verify. Typical culprits: CORS (missing `Access-Control-Allow-Origin` on the API), wrong content type, cookie not sent (`SameSite`/`Secure`/domain), off-by-one in pagination, timezone mismatches, missing DB index causing timeouts.

## 12. Verification

Hit every endpoint with `curl` (happy path plus a bad input and an unauthorized call); check status codes and error shapes; confirm a second user cannot read the first user's data; restart the server and confirm data persists; grep the repo for secrets.

## 13. Related

Production readiness (headers, caching, performance, accessibility, operations): `web/production.md`. System design method, NFRs, ADRs, scaling path: `engineering/architecture-method.md`. Observability and SLOs: `extra/devops-testing.md` section 9. AI features in web apps: `ai/rag-llm.md`, `ai/agents-tools.md`.
