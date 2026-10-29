# Bundled scripts

*Last updated: 2026-10-21 | Version-sensitive: Python 3.9+ and tool versions listed in tests/README.md | Re-check current docs before pinning versions, prices, or API names.*

Every script lives in `scripts/`, runs on the Python standard library unless its row says otherwise, answers `--help`, and reports bad input with a clear error (exit code 2) instead of a traceback. The regression suite is `python tests/run_tests.py` (see `tests/README.md`). Examples for the harness are in `scripts/examples/`.

| Script | Use |
|---|---|
| `scripts/scaffold.py <static\|canvas-game\|php-app\|node-api\|py-cli> <dir>` | Create a small, runnable starter project |
| `scripts/verify_web.py page.html [--scenario s.json] [--mobile] [--skip-draw] [--axe axe.min.js]` | Headless browser check: errors, blank screen, FPS, accessibility (axe), scripted gameplay assertions, screenshots (examples in `scripts/examples/`) |
| `scripts/lint_html.py page.html ...` | Check lang, title, viewport, h1, alt text, labels, duplicate ids |
| `scripts/economy_sim.py [--config cfg.json]` | Simulate idle/tycoon pacing and milestone times |
| `scripts/log_triage.py --type ssh\|web --file LOG` | Flag brute-force and probing patterns in logs you own |
| `scripts/biz_calc.py rice\|risk\|unit\|pricing\|forecast\|breakeven\|runway\|matrix` | Rank ideas (RICE), score risk registers, unit economics with sensitivity, price-point comparison, 12-month cash forecast, break-even, runway, weighted decisions |
| `scripts/rag_lab.py index\|search\|eval DOCS` | Pure-Python BM25 retrieval baseline with recall@k and MRR evaluation for RAG |
| `scripts/drift_check.py reference.csv current.csv` | PSI/KS data drift report with ALERT/WATCH/OK |
| `scripts/writing_lint.py draft.txt` | Prose signals: rhythm, repeated openers, stock phrases, filler, passive, readability |
| `scripts/ctf_lab.py manifest\|flag\|score\|compose\|coverage` | Build CTF/range infrastructure: challenge manifests, per-team HMAC flags, scoring with first-blood/dedupe, isolated container templates, ATT&CK coverage tracking |
| `scripts/cvss_calc.py "CVSS:3.1/AV:N/..."` | CVSS v3.1 base score for reporting and prioritizing findings |
| `scripts/subagent_brief.py list\|show\|brief\|doc` | Specialist profiles and self-contained subagent briefs |
| `scripts/install_subagents.py [--user] [--only ...]` | Install NOS specialists as Claude Code subagent files |
| `python tests/run_tests.py` | Regression suite for all scripts, docs consistency, snippets (skips what the environment cannot run) |
| `scripts/route_check.py "request" [--explain]` | Which router row/reference matches a request (BM25 over the router table and each reference's headings); a vocabulary check, not a model |
| `scripts/check_freshness.py [stamp FILE]` | Report the age of each reference's last-updated stamp and its version-sensitive facts; stamp after re-verifying |
| `scripts/nos_state.py init\|plan\|set\|add\|status\|show` | Structured project state (anchor, gate, plan checkboxes, decisions, checked items/open gaps) for multi-session Deep work |
| `scripts/workflow_plan.py --task ... --domain ...` | Five-phase workflow plan with specialists, gates, and ready-to-run briefs |
| `scripts/stl_tools.py gen\|check` | Generate simple solids and check STL meshes (watertight, orientation, volume) |
| `scripts/audio_tools.py budget\|vad\|levels\|compose\|wer` | Voice-pipeline latency budget, energy VAD, level/clipping check, test audio, word error rate |
| `scripts/xlsx_model.py build\|verify\|check` | Formula-driven forecast workbook; recalculates in LibreOffice and compares with an independent model; formula error scan |
| `scripts/examples/mp_server.js` | Tested authoritative multiplayer server (Node + `ws`) with speed-hack clamp and rate limits |
