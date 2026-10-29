# DevOps, testing, and debugging

*Last updated: 2026-10-13 | Version-sensitive: GitHub Actions, Docker, and tool versions | Re-check current docs before pinning versions, prices, or API names.*

## Contents
1. Git workflow
2. Docker and compose
3. CI with GitHub Actions
4. Testing strategy and examples
5. Debugging protocol
6. Performance profiling
7. Project hygiene
8. Verification

## 1. Git workflow

```bash
git init && git add -A && git commit -m "feat: initial scaffold"
git switch -c feature/save-system          # one branch per change
git commit -m "fix: clamp delta time to avoid physics explosion"
git fetch origin && git rebase origin/main  # or merge; pick one convention
git push -u origin HEAD                      # then open a pull request
git restore --staged file; git restore file  # unstage / discard local changes
git stash push -m wip; git stash pop
git log --oneline --graph -20; git bisect start; git bisect bad; git bisect good <sha>   # find the commit that broke things
git revert <sha>                              # safe undo on shared branches
```
Commit messages: `type: summary` (feat, fix, docs, refactor, test, chore), imperative, under 72 characters, body explains why. Keep `.gitignore` current (`node_modules`, `.env`, build output, engine folders like Unity `Library/`, Unreal `Intermediate/`). Never commit secrets; if leaked, rotate first, then clean history.

## 2. Docker and compose

```dockerfile
# Node API, small and non-root
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules node_modules
COPY . .
USER node
EXPOSE 3000
HEALTHCHECK CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "server.js"]
```
```yaml
# docker-compose.yml: app + database
services:
  app:
    build: .
    ports: ["3000:3000"]
    env_file: .env
    depends_on: [db]
    restart: unless-stopped
  db:
    image: postgres:16-alpine
    environment: { POSTGRES_PASSWORD: "${DB_PASSWORD}" }
    volumes: [dbdata:/var/lib/postgresql/data]
volumes: { dbdata: {} }
```
Commands: `docker compose up -d --build`, `docker compose logs -f app`, `docker compose down`. Add `.dockerignore`. Pin image versions, run as non-root, do not bake secrets into images.

## 3. CI with GitHub Actions

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run lint --if-present
      - run: npm test --if-present
```
Add matrix builds for multiple versions, `pip-audit`/`npm audit` for dependency checks, secret scanning, and a deploy job gated on the main branch with environment secrets.

## 4. Testing strategy and examples

Pyramid: many fast unit tests, fewer integration tests, few end-to-end tests. Test behavior, not implementation. Write the failing test first for bugs, then fix.

```python
# pytest
import pytest
from mymod import parse_price
def test_parses_plain(): assert parse_price("$1,234.50") == 1234.50
def test_rejects_garbage():
    with pytest.raises(ValueError): parse_price("abc")
@pytest.mark.parametrize("raw,exp", [("10", 10.0), ("0.5", 0.5), ("1,000", 1000.0)])
def test_table(raw, exp): assert parse_price(raw) == exp
```
```js
// Node built-in test runner (node --test)
import test from 'node:test'; import assert from 'node:assert/strict'; import { clamp } from './math.js';
test('clamp', () => { assert.equal(clamp(5, 0, 3), 3); assert.equal(clamp(-1, 0, 3), 0); });
```
API tests: start the server, call endpoints with `fetch`/`requests`, assert status and body, including one invalid input and one unauthorized call. UI/E2E: Playwright (`page.getByRole(...)`, assertions with auto-waiting). Game logic: pure functions with seeded RNG, simulation tests for balance (win rate, time-to-milestone). Edge cases checklist: empty, one, many, max, negative, unicode, very long, duplicate, concurrent, offline.

## 5. Debugging protocol

1. **Reproduce** reliably; write the smallest failing case.
2. **Read the evidence**: full error, stack trace, logs, network tab, inputs. Quote it exactly.
3. **Isolate**: which layer (input, logic, data, environment)? Bisect: comment out half, `git bisect`, binary-search the input.
4. **Hypothesize** one cause and predict what you will see if it is true.
5. **Test the hypothesis** with a print, breakpoint, or assertion; change one thing at a time.
6. **Fix the root cause**, not the symptom; explain why it happened.
7. **Verify**: the repro passes, related cases still pass, add a regression test.
8. **Report** the confirmed cause separately from guesses.

Common cause table: off-by-one, null/undefined, async race (missing `await`), stale closure, wrong units or time zones, mutated shared state, encoding, path or working-directory differences, environment variable missing, version mismatch, cache serving old files.

## 6. Performance profiling

Measure before optimizing. Python: `cProfile` (`python -m cProfile -s cumtime script.py`), `timeit`. Node: `node --prof` or `--inspect` with Chrome DevTools. Browser: Performance tab, Lighthouse. Databases: `EXPLAIN` / `EXPLAIN ANALYZE`, add indexes for filtered/sorted columns. Games: frame time budget (16.6 ms at 60 fps), engine profilers (Unity Profiler, Unreal Insights), reduce allocations, batching, pooling, LOD. Fix the biggest measured cost first; re-measure.

## 7. Project hygiene

README (what, run, test, deploy) · `.env.example` · consistent formatter and linter (Prettier/ESLint, Black/Ruff, `dotnet format`) · dependency lockfile · license · CHANGELOG for releases · semantic versioning · issue/PR templates · small pull requests.

## 8. Verification

Run the test suite and paste the result line; run the linter; build the Docker image or explain why it could not be built here; show the command used to reproduce and confirm each bug fix.

## 9. Observability, SLOs, and incident readiness

- **Signals:** logs (structured, with request IDs), metrics (RED for services: rate, errors, duration; USE for resources: utilization, saturation, errors), traces for multi-service flows. Instrument before launch, not after the first outage.
- **SLIs and SLOs:** pick user-facing indicators (availability of the key request, latency percentile, freshness) and targets (for example 99.5% of checkouts succeed, p95 under 400 ms). The **error budget** (1 − SLO) decides whether to ship features or fix reliability. Alert on budget burn rate, not on every blip.
- **Alerts:** page only for user-impacting problems that need a human now; everything else goes to a ticket or dashboard; each alert links a runbook with first checks and rollback steps.
- **Incidents:** declare early, one incident lead, a timeline, a status update cadence, mitigate first (rollback, feature flag off, scale), diagnose later; blameless postmortem with root cause, contributing factors, and dated action items (see `tools/defense.md` for the security variant).
- **Chaos and drills:** practice restores, failovers, and rollbacks on a schedule; an untested runbook is a guess.
- **Cost observability:** tag resources, track cost per request/user, alert on budget anomalies.
- **Capacity:** load test the critical path to the next order of magnitude and write down the first bottleneck.
- Cross-references: production readiness for web (`web/production.md`), pipeline monitoring (`ai/pipelines-mlops.md`), stage gates and ADRs (`engineering/architecture-method.md`).
