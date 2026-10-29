# N-Omni-Skill tests

Run everything the environment can run:

    python tests/run_tests.py          # add -v for verbose, or a filter: scripts | docs | browser

The suite uses only the standard library (`unittest`). It never passes silently: tests that need a missing tool (Chromium, Node, PHP, pandas, network access for `npm`) are reported as **SKIPPED with the reason**. A change counts as tested only when the relevant tests ran, not when they were skipped.

## What is covered

| Module | Covers |
|---|---|
| `test_scripts.py` | Correct outputs and exit codes for `biz_calc`, `log_triage` (including the order-aware SSH compromise logic), `rag_lab` (including invalid chunk settings), `drift_check`, `writing_lint`, `economy_sim`, `lint_html`, `scaffold` (PHP app run over HTTP with a CSRF flow when PHP exists), `cvss_calc` (published scores), `subagent_brief`, `install_subagents`, the multiplayer server example; clean errors instead of tracebacks for bad input |
| `test_workflow_tools.py` | `nos_state.py` lifecycle and errors; `workflow_plan.py` phases, gates, briefs, state initialization |
| `test_domain_tools.py` | `stl_tools` (exact volumes, defect detection), `audio_tools` (VAD boundaries, clipping, latency budget, WER), `xlsx_model` (LibreOffice recalculation equals an independent Python model and `biz_calc`; tampered formulas and formula errors are caught), C++ sketches compiled against an Arduino stub, runnable snippets (PID simulation, CAD calculations, WER, openpyxl) |
| `test_router.py` | Router vocabulary regression guards over three prompt corpora (see below) and the `route_check.py` CLI |
| `test_docs.py` | Frontmatter and naming rules, every referenced path exists, router lists every reference and script, Contents lists, freshness stamps, Python/JS snippets parse, selected snippets execute and give expected results, every script has `--help` |
| `test_browser.py` | `verify_web.py` end to end: good page passes; JS errors, blank canvas, missing assets fail; scenario assertions and negative controls; mobile and `--skip-draw`; `--route`; `--axe`; exit code 3 when no browser exists |

### About the router tests

`scripts/route_check.py` scores a request against the SKILL.md router table (plus each reference's headings) with BM25 and a small synonym list. It measures **vocabulary coverage**, not how a model routes. Three corpora: A (`route_prompts.json`) was used to tune the router wording, so its score is optimistic; B (`route_prompts_heldout.json`) was used to choose the synonyms; C (`route_prompts_heldout2.json`) was written before any tuning and measured once, so it is the honest generalization estimate. The thresholds in `test_router.py` sit below the last measured values and exist to catch regressions.

## Running on Windows

- Run from the plugin root: `python tests\run_tests.py` (or `pytest tests` from the root). The suite decodes all subprocess output as UTF-8.
- Each skipped test names the tool it needs. For full coverage on Windows install: Node.js (provides `npm`), PHP with `pdo_sqlite`, LibreOffice (for `soffice`), a C++ compiler such as MinGW `g++` (for the embedded sketch checks), and `pip install pandas numpy openpyxl pillow`.
- Regenerate the specialists reference with `python scripts\subagent_brief.py doc --out references\engineering\specialists.md` (avoid `>` in PowerShell, which writes UTF-16).

## Dependencies and tested versions

Requires Python 3.9+. Install: `pip install -r tests/requirements.txt && playwright install chromium`. Also useful: Node.js >= 18 with npm, PHP >= 8.1 with pdo_sqlite.

| Component | Version used in the last full run |
|---|---|
| Python | 3.12.3 |
| Node.js | v22.22.2 |
| PHP (CLI + pdo_sqlite) | 8.3.6 |
| numpy | 2.4.4 |
| pandas | 3.0.2 |
| scikit-learn | 1.8.0 |
| scipy | 1.17.1 |
| Pillow | 12.1.1 |
| opencv-python-headless | 4.13.0.92 |
| opencv-python | 4.13.0.92 |
| playwright | 1.56.0 |

## Exit codes of `verify_web.py`

0 all checks passed · 1 at least one FAIL · 2 usage or input error · 3 browser unavailable (run `python scripts/verify_web.py --check-env` to diagnose).

## Release rule

Describe a release as tested only after `python tests/run_tests.py` has passed in an environment where Chromium, Node, and PHP are available (use `tests/ci/github-actions.yml` as a starting point; it has not been executed yet). If any of those were skipped, say which, and label the affected behavior **open gap**.

## Adding tests

Fix a bug → add a regression test in the same change. New script → add functional tests, a bad-input test (no traceback, exit code 2), and a mention in `SKILL.md` (the docs test enforces it).
