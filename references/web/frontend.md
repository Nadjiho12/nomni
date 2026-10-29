# Web frontend: HTML5, CSS, JavaScript

*Last updated: 2026-10-13 | Version-sensitive: browser support for newer CSS/JS features; CDN and library versions | Re-check current docs before pinning versions, prices, or API names.*

Use with `scripts/scaffold.py static <dir>` for a working start, and `scripts/lint_html.py` to check the result.

## Contents
1. Decision guide
2. HTML patterns
3. CSS patterns
4. JavaScript patterns
5. PWA / offline
6. Canvas, SVG, animation
7. Common bugs and fixes
8. Verification

## 1. Decision guide

| Situation | Choose |
|---|---|
| Content site, portfolio, landing page | Plain HTML + CSS, JS only for enhancements |
| One interactive tool | Single-file HTML, inline CSS/JS |
| Many views + shared state | Vite + React/Vue/Svelte |
| Needs SEO and server data | Server-rendered (PHP, Next/Nuxt, Astro) |
| Animations that must be smooth | CSS transforms/opacity first; JS (Web Animations API / rAF) second |

## 2. HTML patterns

Accessible disclosure, dialog, and form:

```html
<details><summary>FAQ question</summary><p>Answer.</p></details>

<dialog id="dlg"><form method="dialog"><h2>Title</h2><p>Body</p><button value="ok">OK</button></form></dialog>
<button onclick="document.getElementById('dlg').showModal()">Open</button>

<form id="f" novalidate>
  <label for="email">Email</label>
  <input id="email" type="email" required autocomplete="email" aria-describedby="email-err">
  <p id="email-err" role="alert" hidden>Enter a valid email.</p>
  <button>Send</button>
</form>
```

Head essentials: `lang`, `charset`, viewport, `title`, description, favicon, Open Graph (`og:title`, `og:description`, `og:image`).

## 3. CSS patterns

```css
/* Tokens + dark mode */
:root{--bg:#fff;--fg:#111;--accent:#3b5bfd;--r:12px;--gap:1rem}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#eee}}

/* Responsive grid with no media queries */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:var(--gap)}

/* Center anything */
.center{display:grid;place-items:center;min-height:100dvh}

/* Sticky header + safe scroll targets */
header{position:sticky;top:0;backdrop-filter:blur(8px)} html{scroll-padding-top:4rem;scroll-behavior:smooth}

/* Fluid type */
h1{font-size:clamp(2rem,4vw+1rem,4rem)}

/* Card that reacts to its own width */
.card-wrap{container-type:inline-size}
@container (min-width:30rem){.card{display:flex}}

/* Skeleton loader */
.skel{background:linear-gradient(90deg,#0001,#0003,#0001);background-size:200% 100%;animation:sh 1.2s infinite}
@keyframes sh{to{background-position:-200% 0}}

/* Focus and motion respect */
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
```

Layout picking: Grid for two-dimensional page layout, Flexbox for one-dimensional rows/columns, `position:absolute` only for overlays.

## 4. JavaScript patterns

```js
// Safe fetch wrapper
export async function api(path, { method = 'GET', body } = {}) {
  const res = await fetch(path, { method, headers: body ? { 'Content-Type': 'application/json' } : {},
                                  body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || `HTTP ${res.status}`);
  return res.status === 204 ? null : res.json();
}

// Tiny reactive store: one source of truth, render from state
export function store(initial) {
  let state = initial; const subs = new Set();
  return { get: () => state, set(patch) { state = { ...state, ...patch }; subs.forEach(f => f(state)); },
           sub(f) { subs.add(f); f(state); return () => subs.delete(f); } };
}

// Event delegation (one listener for a dynamic list)
list.addEventListener('click', e => { const btn = e.target.closest('[data-del]'); if (btn) remove(btn.dataset.del); });

// Debounce
export const debounce = (fn, ms = 250) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

// Lazy-reveal on scroll
new IntersectionObserver((es, o) => es.forEach(e => e.isIntersecting && (e.target.classList.add('in'), o.unobserve(e.target))))
  .observe(document.querySelector('.reveal'));

// Theme toggle that persists (guard storage: it can be unavailable)
const setTheme = t => { document.documentElement.dataset.theme = t; try { localStorage.setItem('theme', t); } catch {} };
```

Rendering user text: `el.textContent = value`. If HTML is required, sanitize (DOMPurify) first.

Forms: validate on `submit` with `form.checkValidity()`, show errors next to fields, disable the button while sending, keep typed values on failure.

## 5. PWA / offline

`manifest.webmanifest` (name, icons 192/512, `start_url`, `display: standalone`, `theme_color`) plus a service worker:

```js
// sw.js — cache-first for static assets
const CACHE = 'v1', ASSETS = ['/', '/style.css', '/app.js'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS))));
self.addEventListener('fetch', e => e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))));
// register: if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
```

Bump `CACHE` on each release so old assets are dropped.

## 6. Canvas, SVG, animation

- Canvas for many moving objects or pixels; SVG for crisp icons, charts, and diagrams. Scale canvas by `devicePixelRatio`.
- Animate `transform` and `opacity` only; avoid animating `width`/`top`.
- Web Animations API: `el.animate([{opacity:0},{opacity:1}], {duration:300, easing:'ease-out', fill:'forwards'})`.
- Charts: Chart.js or hand-rolled SVG (`<polyline points="...">`) for small data.
- 3D: Three.js (`WebGLRenderer`, `PerspectiveCamera`, mesh, light, `renderer.setAnimationLoop`).

## 7. Common bugs and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Layout overflows on phone | Missing viewport meta, fixed widths | Add meta, use `max-width:100%`, `minmax()` |
| ES module fails on `file://` | CORS for modules | Serve with `python -m http.server` |
| `100vh` jumps on mobile | Browser chrome | Use `100dvh` |
| Click handler not firing on new items | Listener bound before item existed | Event delegation |
| Fonts flash | Late font load | `font-display:swap`, preload key font |
| Sticky not sticking | Ancestor has `overflow` set | Remove overflow or move the sticky element |

## 8. Verification

Run `python scripts/verify_web.py page.html` (add `--mobile` for a phone check) and `python scripts/lint_html.py page.html`; open at 360 / 768 / 1280 widths; tab through with the keyboard; disable JS once to see what breaks; check console for errors; test empty, loading, and error states.

## 9. Related

Ship it right: `web/production.md` (security headers, caching, Core Web Vitals, accessibility with axe, SEO). Look and feel: `web/design.md`. Verification: `extra/verify.md`.
