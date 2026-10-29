# Senior engineer mindset

*Last updated: 2026-10-13 | Version-sensitive: none significant (practice) | Re-check current docs before pinning versions, prices, or API names.*

How a talented senior thinks, builds, and communicates. Apply it to every domain: code, games, data, AI, tools, content. The point is not ceremony; it is better outcomes with less waste and fewer surprises.

## Contents
1. The senior loop
2. Framing the problem
3. Simplicity and trade-offs
4. Building: craft and taste
5. Design docs and decision records
6. Risk, failure modes, and operability
7. Review: giving and receiving
8. Estimation, scope, and debt
9. Communication
10. Creativity with discipline
11. Anti-patterns
12. Production-ready checklist
13. Senior self-review before delivering

## 1. The senior loop

**Frame → explore → decide → build thin → verify → harden → hand off.**
- Frame: what outcome, for whom, and what would make this a success or failure.
- Explore: 2-3 viable options, including the boring one and the "do nothing / buy it" one.
- Decide: pick with stated criteria; write down what would change your mind.
- Build thin: smallest end-to-end slice first (a walking skeleton), then widen.
- Verify: tests, runs, measurements, screenshots, simulations. Evidence before claims.
- Harden: errors, limits, security, observability, rollback.
- Hand off: docs, how to run, what is verified, what is not, next steps.

## 2. Framing the problem

- Restate the goal in one sentence a non-expert would accept. If you cannot, you do not understand it yet.
- Separate **requirements** (must), **constraints** (fixed facts: time, budget, platform, skills), **preferences** (nice), and **assumptions** (without evidence). Label assumptions and attach a cheap check to each.
- Ask "what problem is behind this request?" The stated solution is often one of several. Offer a better framing when you see one, briefly and without lecturing.
- Define success measurably (latency under 300 ms, retention above X, "player finishes level 1 in under 3 minutes").
- Identify the **riskiest unknown** and attack it first (the part that could kill the project), not the easiest part.
- Find the real users and their workflow; design for the common path, then the worst path.

## 3. Simplicity and trade-offs

- Prefer the simplest thing that satisfies the requirements and leaves room to grow. Complexity must pay rent.
- Every choice is a trade-off; name the cost: speed vs correctness, flexibility vs simplicity, build vs buy, consistency vs availability, cost vs latency, accuracy vs explainability.
- Use a compact comparison table with weighted criteria for non-trivial choices (`scripts/biz_calc.py matrix`). State the recommendation and the revisit trigger.
- **Reversibility test:** two-way doors (cheap to undo) get decided fast; one-way doors (data models, public APIs, vendor lock-in, security boundaries) get deliberate design.
- Default to boring, well-understood technology for the core; spend novelty budget where it creates real advantage.
- Delete before adding. The best code is the code not written; the best feature is the one cut with no loss.
- YAGNI with foresight: do not build speculative generality, but avoid decisions that make the likely next step expensive.

## 4. Building: craft and taste

- **Make it work, make it right, make it fast, in that order**, and measure before optimizing.
- Names carry meaning; small functions with one job; data structures first (get the data model right and the code follows); pure functions at the core, side effects at the edges.
- Make illegal states unrepresentable (types, enums, validation at boundaries). Validate at the edge, trust inside.
- Explicit over implicit; fail fast and loudly with useful messages; never swallow errors.
- Write the test or the repro first for bugs. Tests describe behavior, not implementation.
- Keep the diff reviewable: small, single-purpose changes, each leaving the system working.
- Instrument as you build: structured logs, a few key metrics, a health check.
- Taste: remove the visual or conceptual noise; consistent patterns beat clever ones; if you need a long comment to explain code, simplify the code.
- Automate the boring and error-prone (formatters, linters, CI, scripts), not the thing you do once.

## 5. Design docs and decision records

For anything that takes more than a few days or is hard to reverse, write a short design note:
```
Context & goal | Non-goals | Requirements & constraints
Options (2-3) with trade-offs | Decision & why | Design (components, data, flow, interfaces)
Risks & mitigations | Rollout & rollback | Testing & observability | Open questions
```
Keep ADRs (architecture decision records): one page each, immutable, with status (proposed/accepted/superseded). They save the team from re-litigating and explain "why" months later. See `engineering/architecture-method.md`.

## 6. Risk, failure modes, and operability

- Ask "how does this fail?" for every component: timeouts, retries storms, partial failure, bad input, duplicate delivery, clock skew, full disk, dependency down, expired credentials.
- Design for graceful degradation: a clear fallback when a dependency fails (cached data, read-only mode, ads-off build, manual path).
- Idempotency for anything that may repeat; timeouts and bounded retries with backoff and jitter; circuit breakers for flaky dependencies; backpressure instead of unbounded queues.
- Data safety: backups you have restored at least once, migrations that can roll back, no destructive operation without a confirmation or dry run.
- Security by default: least privilege, secrets out of code, validated input, dependency hygiene, threat model for anything exposed (STRIDE).
- Operability: you cannot fix what you cannot see. Logs, metrics (RED: rate, errors, duration), traces for distributed flows, alerts tied to user impact, runbooks.
- Rollouts: feature flags, canary, one-command rollback, and a defined "stop" signal.
- Pre-mortem: assume it failed in 3 months; write why; fix the top causes now.

## 7. Review: giving and receiving

Reviewing: understand intent first; look at correctness, edge cases, security, readability, tests, and fit with the design; separate **blocking** issues from **suggestions** and **nits**; explain why, propose an alternative, ask questions instead of decreeing; praise good decisions specifically.
Receiving: separate ego from the work; verify claims before changing code; push back with evidence when you disagree; record decisions.
Self-review: read your own diff as a stranger before sharing.

## 8. Estimation, scope, and debt

- Estimate in ranges with a confidence level; decompose to tasks under a day; add integration and bug-fix time (30-50%); include unknowns explicitly ("spike: 2 days to learn X").
- Slice vertically (a thin working feature across all layers), not horizontally (all DB, then all API, then all UI).
- Cut scope, not quality, when time is short. Keep a visible cut list.
- Technical debt is a loan: take it deliberately, record it with an owner and a trigger, and pay it before it compounds. Refactor continuously in small steps with tests, not in heroic rewrites.
- "Done" includes tests, docs, monitoring, and cleanup, not just "works on my machine".

## 9. Communication

- Lead with the answer or recommendation, then reasons. Short paragraphs, concrete examples, numbers over adjectives.
- Calibrated language: **confirmed**, **likely**, **unknown**, **assumption**. State confidence and what would change it.
- Tailor to the audience: executives want impact, risk, and decision; peers want design and trade-offs; learners want intuition then detail.
- Bad news early with a plan. Disagree and commit once decided.
- Explain without condescension; teach the underlying principle, not only the fix.
- Write things down: decisions, runbooks, "how to run it".

## 10. Creativity with discipline

- Diverge before converging: generate many options, then filter by criteria and evidence (`thinking/ideas-critical.md`).
- Constraints fuel creativity; borrow mechanisms from other fields; combine two ordinary things in an unusual way.
- Prototype to learn: throwaway spikes answer questions quickly; label them as throwaway.
- Taste is trained by studying excellent work in the domain (read great code, play great games, read great writing), then asking why it works.
- Keep a bias to shipping: a good solution this week beats a perfect one next quarter, as long as it is safe and reversible.

## 11. Anti-patterns

Resume-driven technology choices · premature abstraction and microservices for a small app · rewriting instead of refactoring · optimizing without measuring · hiding uncertainty · gold-plating · building without users · no tests on the risky parts · giant pull requests · "it works" with no evidence · skipping the boring parts (migrations, backups, monitoring) · cargo-culting a big company's architecture · treating the first idea as the only idea · ignoring the human and organizational constraints.

## 12. Production-ready checklist

- [ ] Requirements and success metric written; non-goals stated
- [ ] Core flow works end to end; edge cases and error states handled
- [ ] Automated tests on the risky logic; CI green
- [ ] Input validation, authn/authz, secrets handling, dependency scan reviewed
- [ ] Logging, metrics, and an alert for user-impacting failure; health check
- [ ] Performance checked against a stated budget under realistic load
- [ ] Backups and a tested restore; migration and rollback plan
- [ ] Config via environment; no secrets in the repo; `.env.example`
- [ ] Docs: how to run, deploy, operate; ADRs for big decisions
- [ ] Known limitations and next steps listed honestly

## 13. Senior self-review before delivering

1. Did I solve the real problem, not just the stated one?
2. Is there a simpler design that meets the requirements?
3. What is the riskiest assumption, and what evidence do I have?
4. What fails first, and how does the system behave when it does?
5. Could someone else run, debug, and extend this tomorrow?
6. What did I verify, what did I not, and did I say so plainly?
7. What are the next three upgrades, in order?
