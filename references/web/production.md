# Web production readiness

*Last updated: 2026-10-13 | Version-sensitive: security header best practices; Core Web Vitals thresholds; browser behavior | Re-check current docs before pinning versions, prices, or API names.*

What turns a working site into a dependable one: security headers, caching, performance, accessibility, SEO, reliability, and operations. Test with `scripts/verify_web.py` (add `--axe` for accessibility).

## Contents
1. Security headers and cookies
2. HTTP caching and CDN
3. Performance budget
4. Accessibility
5. SEO and sharing
6. Reliability and operations
7. Privacy and compliance basics
8. Deployment and rollback
9. Production checklist

## 1. Security headers and cookies

```
Content-Security-Policy: default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
```
Start CSP in report-only mode, fix violations, then enforce. Avoid inline scripts (or use nonces). Cookies: `HttpOnly; Secure; SameSite=Lax` (or `Strict`), short lifetimes, rotate on login. Node: `helmet()`. nginx: `add_header ... always;`. PHP: `header()` before output. Verify headers with `curl -I` and a scanner (securityheaders.com style checks).

## 2. HTTP caching and CDN

- Static assets with content hashes in filenames: `Cache-Control: public, max-age=31536000, immutable`.
- HTML: `Cache-Control: no-cache` (revalidate) or short max-age; use ETag/Last-Modified.
- APIs: `Cache-Control: private` for user data; `no-store` for sensitive data; cache public GETs at the CDN with explicit keys.
- Compression: Brotli/gzip for text; modern images (AVIF/WebP); serve responsive sizes (`srcset`).
- CDN in front of static content; purge on deploy; use HTTP/2 or HTTP/3.

## 3. Performance budget

Targets (mobile, mid-range): LCP under 2.5 s, INP under 200 ms, CLS under 0.1, JS under 170 KB compressed for content sites, total page weight under 1.5 MB. Tactics: ship less JS, defer non-critical scripts, preload the LCP image and key font, `loading="lazy"` below the fold, set image width/height, avoid layout shift, use `font-display: swap`, inline critical CSS, code-split routes, cache API responses, optimize database queries. Measure with Lighthouse/WebPageTest and real-user monitoring; budget in CI (fail on regression).

## 4. Accessibility

Automated: `python scripts/verify_web.py page.html --axe node_modules/axe-core/axe.min.js` (finds a portion of issues). Manual: keyboard-only walkthrough (tab order, visible focus, no traps, skip link), zoom to 200%/400%, screen reader smoke test (NVDA/VoiceOver) on key flows, color contrast 4.5:1, text alternatives, form labels and error messages tied to inputs, captions for media, respect `prefers-reduced-motion`. Target WCAG 2.1/2.2 AA; document known gaps.

## 5. SEO and sharing

Unique `<title>` and meta description per page, one `h1`, semantic headings, canonical URLs, `robots.txt` and `sitemap.xml`, structured data (JSON-LD) where relevant, Open Graph/Twitter cards with an image, fast and mobile-friendly pages, clean URLs, 301 redirects for moved pages, descriptive link text and image alt text. Server-render or pre-render content that must be indexed.

## 6. Reliability and operations

- Health endpoint (`/health`) for load balancers; graceful shutdown; timeouts everywhere; retries with backoff only for idempotent calls.
- Observability: structured logs with request IDs, error tracking (Sentry-style), uptime checks, basic metrics (rate, errors, duration), alerts to a channel with runbooks.
- Backups: automated, encrypted, offsite; **restore tested** on a schedule.
- Rate limiting and abuse protection on login, signup, search, and expensive endpoints; CAPTCHA only where needed.
- Background jobs for slow work (emails, exports); queue with retries and a dead-letter store.
- Capacity: load-test the critical path (k6, Locust) to the next order of magnitude; find the bottleneck first.
- Status page and incident process for customer-facing services.

## 7. Privacy and compliance basics

Collect the minimum; cookie consent where required for non-essential cookies/analytics; privacy policy and terms matching reality; data export and deletion paths; encrypt in transit and at rest; log access to sensitive data; vendor/subprocessor list; age-gating rules if children may use it. Confirm legal requirements for your region and your users' regions with a qualified professional.

## 8. Deployment and rollback

CI builds, tests, and scans; deploy to staging, run smoke tests (`verify_web.py` scenarios); roll out gradually (canary/blue-green); database migrations in expand → migrate → contract steps; feature flags for risky changes; one-command rollback; post-deploy checks and alerts watching error rate and latency for 15-30 minutes.

## 9. Production checklist

- [ ] HTTPS everywhere, HSTS, security headers, secure cookies; CSP enforced
- [ ] Inputs validated, outputs encoded, auth/authorization tested for horizontal access
- [ ] Caching headers and CDN configured; compression on
- [ ] Core Web Vitals within budget on a mid-range phone
- [ ] Axe clean (no critical/serious) and a keyboard walkthrough passed
- [ ] Titles, descriptions, canonical, sitemap, robots; OG image
- [ ] Logs, error tracking, uptime checks, alerts, runbook for top failures
- [ ] Backups with a tested restore; migration rollback plan
- [ ] Rate limits on abuse-prone endpoints; secrets in a manager
- [ ] Privacy policy, consent, deletion path; dependency scan clean
