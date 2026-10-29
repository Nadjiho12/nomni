# Game production: pipeline, QA, analytics, release

*Last updated: 2026-10-13 | Version-sensitive: store requirements, fees, and platform policies | Re-check current docs before pinning versions, prices, or API names.*

How shipped games get finished: scope control, pipelines, performance budgets, playtesting, telemetry, store presence, and post-launch.

## Contents
1. Production stages and gates
2. Scope control
3. Asset and build pipeline
4. Performance budgets
5. QA and playtesting
6. Telemetry and analytics
7. Level and content production
8. Release: stores and platforms
9. Post-launch and live operations
10. Checklist

## 1. Production stages and gates

Concept (pitch, core loop) → **Prototype** (is the core verb fun? days) → **Vertical slice** (one polished level with final art, audio, UI, systems) → **Production** (content at scale) → **Alpha** (feature complete) → **Beta** (content complete, bug fixing) → **Release candidate** → **Launch** → **Live**. Gate each stage with evidence: playtest results for the prototype, performance and fun in the slice, bug counts and crash rates in beta. Cut or pivot at the prototype and slice gates; they are cheap.

## 2. Scope control

Write the one-page GDD (`extra/planning.md`) with a **cut list** ordered by value per effort. Use MoSCoW: Must (loop works), Should, Could, Won't. Time-box features, review burn-down weekly, and ship the smallest complete game first. Estimate content in units (levels, enemies) with measured per-unit cost from the first few.

## 3. Asset and build pipeline

- Version control with large-file support (Git LFS, Perforce, Plastic) and engine `.gitignore`s; lock binary assets while editing.
- Naming conventions and folders per asset type; source files (PSD/blend/aseprite) stored separately from exported runtime assets.
- Automated import settings (texture compression, sprite atlases, audio formats) and a one-command build; CI builds nightly on every target; automated smoke test (launch, load main scene, run 60 seconds, assert no exceptions and a stable frame time) using the headless harness for browser builds (`extra/verify.md`).
- Content validation scripts: missing references, oversized textures, duplicate IDs, unreferenced assets.
- Save-data versioning and migrations from day one.

## 4. Performance budgets

Set budgets at the start and test on the lowest target device.
| Metric | Typical target |
|---|---|
| Frame time | 16.6 ms (60 fps) or 33 ms (30 fps) |
| Draw calls | PC 1-3k, mobile 100-300 |
| Memory | mobile 300-800 MB total; textures dominate |
| Load time | under 10 s to interactive on target |
| Download size | web under 10-20 MB initial; mobile under store limits |
| Battery/thermals | stable 15-20 minute sessions without throttling |
Profile before optimizing (engine profilers, browser Performance tab); fix the largest cost; re-measure. Techniques: batching and atlases, object pooling, LOD, occlusion culling, baked lighting, compressed textures, audio streaming, simplified physics, spreading work across frames.

## 5. QA and playtesting

- **Playtest early and often** with people who did not build it. Watch silently; note where they hesitate, die repeatedly, or quit. Ask what they thought was happening, not what they liked.
- 5 players find most major usability problems; test each build milestone. Record sessions where allowed.
- Test matrix: devices, resolutions, input methods, languages, save/load, interruptions (calls, backgrounding), low storage/offline, first-time vs returning player.
- Bug triage: severity (crash/data loss > progression blocker > wrong behavior > cosmetic) and frequency; fix blockers first; track in an issue tracker with repro steps and build number.
- Soak and fuzz tests: run the game for hours with random inputs to find leaks and crashes.
- Playtest report template: build, tester profile, session length, objectives completed, confusion points, bugs, quotes, top 3 changes.

## 6. Telemetry and analytics

Instrument the funnel: install → first session → tutorial complete → level N reached → day-1/7/30 retention → purchase. Events carry player ID (anonymous), session ID, timestamp, build, and context. Useful metrics: retention (D1/D7/D30), session length and count, level completion and fail rates, time-to-first-fail, economy sinks/sources, ARPDAU and conversion for monetized games, crash-free sessions. Respect privacy: disclose collection, minimize data, honor opt-outs and children's data rules. Use analytics to find where players leave, then playtest those spots.

## 7. Level and content production

Process: paper layout → blockout with gray boxes → playtest → add gameplay beats and pacing (tension/release) → art pass → audio → polish. Teach one mechanic per level section: safe introduction, test, twist, combination. Use data tables for waves, items, and quests; validate difficulty with simulation (`scripts/economy_sim.py`, balance sims). Keep a content tracker with status per asset.

## 8. Release: stores and platforms

- **Web/itch.io:** HTML5 zip build, set viewport and fullscreen, test in multiple browsers; page with GIF/trailer, clear controls, devlog.
- **Steam:** store page early (wishlists), capsule art, trailer in the first 10 seconds shows gameplay, demo/next-fest, achievements, cloud saves, Steamworks integration.
- **Android/iOS:** store listing assets (icons, screenshots, short video), age rating, privacy policy and data safety forms, signing keystore backup, staged rollout, crash reporting.
- **Consoles:** platform holder approval, certification requirements, dev kits.
Marketing runs from the start: devlogs, short clips, community (Discord), press kit, keyword research for titles/tags. See `business/marketing-products.md`.

## 9. Post-launch and live operations

Monitor crash rate and reviews daily at launch; hotfix process ready; patch cadence and changelogs; communicate known issues; update content on a schedule; events and seasons for live games with a content pipeline sized to cadence; community management and moderation tools; plan end-of-life (offline mode, refunds policy, server shutdown notice).

## 10. Checklist

- [ ] Core loop prototyped and playtested; fun proven before content
- [ ] Vertical slice at target quality; performance budget met on the lowest device
- [ ] Cut list maintained; scope matches remaining time
- [ ] CI builds and smoke tests on every target; content validation in place
- [ ] Save versioning, crash reporting, and telemetry (with privacy handling)
- [ ] Playtest reports from outside testers at each milestone
- [ ] Store pages, ratings, privacy policy, and legal assets ready
- [ ] Launch-week monitoring and hotfix plan
