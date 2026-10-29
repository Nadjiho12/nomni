---
name: web
description: "Build and ship websites and web apps: HTML/CSS/JS, responsive layout, PWA, PHP/Node/Python backends, APIs, databases, design systems, landing pages, and production readiness (security headers, caching, Core Web Vitals, accessibility, SEO). Use for any web frontend, full-stack, or site-launch request."
---

# N-Omni: web

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| HTML5, CSS, JavaScript, responsive layout, grid/flexbox, navbar, dark mode toggle, forms, PWA/service worker offline, animation, canvas/SVG | `references/web/frontend.md` |
| PHP, Node, Python APIs, REST, SQL databases, login/auth/sessions/password hashing, file uploads, full-stack backend, deployment | `references/web/backend.md` |
| Look and feel, UI/UX aesthetic, landing pages, dashboards, design systems, colors, typography, layout | `references/web/design.md` |
| Production readiness: security headers, caching, performance/Core Web Vitals, accessibility, SEO, monitoring, launch checklist | `references/web/production.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
