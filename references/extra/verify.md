# Verification harness (headless browser)

*Last updated: 2026-10-14 | Version-sensitive: Playwright and Chromium versions; sandbox network rules | Re-check current docs before pinning versions, prices, or API names.*

`scripts/verify_web.py` turns "Verified" into evidence for any web page or browser game: Playwright + Chromium, console errors, failed requests, blank-screen check, FPS, scripted scenarios, screenshots. It was used to find and fix real bugs in a shooter that had been shipped untested.

## Contents
1. Check the environment first
2. Quick use
3. Scenarios
4. Games: logic mode, balance simulation, visuals
5. Negative controls
6. Limits
7. Verification checklist for deliverables

## 1. Check the environment first
Do not assume a browser is missing, and do not assume it is present. Run `python scripts/verify_web.py --check-env`: exit 0 means Chromium launches (and reports whether WebGL works); exit 3 means it is unavailable, in which case say **open gap** for browser behavior, run the static checks (`scripts/lint_html.py`, JS syntax checks), and give the user the exact command to run. Where it works, Chromium with software WebGL (SwiftShader) is usually enough for games. Setup elsewhere: `pip install playwright pillow && playwright install chromium`. The network may be blocked (CDNs return 403): download the library with npm (`npm i three@0.128.0`) and map it with `--route "cdn-url-substring=/local/file.js"`.

## 2. Quick use
```
python scripts/verify_web.py page.html                      # load, errors, blank check, fps
python scripts/verify_web.py game.html --mobile --out shots  # touch, 390x844, 2x DPR
python scripts/verify_web.py game.html --scenario s.json
```
Exit codes: 0 all checks passed; 1 a FAIL (uncaught exception, console.error, failed local request, blank screen, failed assertion); 2 usage or input error; 3 browser unavailable. WARN (overflow, blocked external request, low FPS) never fails the run. Always view at least one screenshot with the image viewer; pixel checks prove it renders, not that it looks right.

## 3. Scenarios
JSON list of steps: `wait`, `click` (selector or x,y), `tap`, `press` (hold a key), `mouse`, `drag`, `eval` (JS expression plus `expect`), `wait_for` (poll an expression), `text`, `shot`, `changed` (two shots differ by at least a fraction). Examples: `scripts/examples/mobile-canvas-game.scenario.json`, `scripts/examples/threejs-shooter-logic.scenario.json`. Top-level `let/const` globals in a classic `<script>` are readable from `eval` by name; code inside an IIFE is not, so for testable games expose state (`window.__game = {...}`) or keep it top-level.

Assert state, not only pixels: actor counts, finite positions, bounds, score changes after an action, mode transitions, round end and restart.

## 4. Games
- **Software rendering is slow (about 1 fps for a 3D shooter).** Use two modes. `--skip-draw` turns WebGL draw calls into no-ops so game logic runs at CPU speed; use it for gameplay assertions and simulations. A normal run at a small viewport (for example 640x360) is for screenshots. A 1280x720 screenshot of a heavy scene can time out.
- **Balance by simulation.** Put every tuning number in one `TUNE` object. In an `eval` step, loop the game's own `update` functions with fixed `dt` for many rounds, with AI driving the player too, and report win rates, round length and "fizzle" rate. See `scripts/examples/balance_sim_generator.py`. Run sweeps in the background (`setsid nohup ... &`) with 16-24 rounds per config and poll; a single command is limited to about 5 minutes.
- **Find root causes with traces.** When a rate looks wrong, log one entity's state over time (position, hp, target, stuck timer) before changing numbers. Example finding: knockback per hit exceeded zombie speed, so one infected player could not advance, and the first zombie lost its bonus HP on respawn. Both were invisible without a trace.
- **Report results honestly.** AI-vs-AI simulations show relative balance, not human feel.

## 5. Negative controls
Prove the harness can fail: run it on a page with a JS error, a blank canvas, a missing script and horizontal overflow, and confirm the expected FAIL/WARN lines. Do this once per new environment.

## 6. Limits
Not covered: real GPU performance, touch feel on devices, audio quality, pointer lock behavior in sandboxed iframes, Android APK builds (SDK downloads are usually blocked in the sandbox; build in CI instead and mark **open gap**).

## 7. Verification checklist for deliverables

The harness itself is covered by `tests/test_browser.py` (run `python tests/run_tests.py browser`).
- [ ] `verify_web.py` exit 0 on the real file, mobile and desktop viewport if relevant
- [ ] At least one gameplay or interaction scenario passes with state assertions
- [ ] One screenshot viewed and described honestly
- [ ] Balance or logic simulations run for games with economies, rounds or AI
- [ ] Remaining gaps listed as open gaps

## 8. More checks

- **Accessibility:** `python scripts/verify_web.py page.html --axe node_modules/axe-core/axe.min.js` (`npm i axe-core`). Critical/serious violations fail the run; automation finds only part of real issues, so also walk the page with a keyboard.
- **Multiplayer:** run `scripts/examples/mp_server.js` with scripted clients to assert tick rate, input clamping, and rate limits (`games/multiplayer.md`).
- **Data and AI:** `scripts/drift_check.py` (data drift), `scripts/rag_lab.py eval` (retrieval recall@k and MRR).
- **Prose:** `scripts/writing_lint.py` for rhythm, stock phrases, and readability.
