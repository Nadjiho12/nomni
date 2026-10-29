# Multi-phase workflow: Research, Plan, Execute, Optimize, Review

*Last updated: 2026-10-18 | Version-sensitive: none significant (process) | Re-check current docs before pinning versions, prices, or API names.*

A five-phase pipeline for substantial work, with an exit gate and an artifact per phase and independent review at the end. It is the NOS version of the common research/plan/execute/optimize/review pattern used by multi-model development workflows. The external ECC multi-workflow skill was not available when this was written, so none of its specifics are reproduced: this file describes what NOS does itself. Tools: `scripts/workflow_plan.py` (generates the plan and briefs), `scripts/nos_state.py` (tracks state across sessions), `scripts/subagent_brief.py` (briefs), and the roles in `engineering/specialists.md`.

## Contents
1. When to use it
2. The five phases at a glance
3. Phase details
4. Cross-validation and multiple models
5. Artifacts and NOS-STATE
6. Gates and loop-backs
7. Anti-patterns
8. Worked example
9. Checklist

## 1. When to use it

Use for **Deep** work: multi-file features, new systems, migrations, AI or data projects, business plans with numbers, anything where a wrong turn is costly. Skip it for Quick and most Standard tasks (the mode contract in `SKILL.md` decides). Command: `NOS workflow`. Start with `python scripts/workflow_plan.py --task "..." --domain web|game|ai|business|writing|security|devops|general [--mode subagents] [--reviewers 2] [--init-state NOS-STATE.md]`.

## 2. The five phases at a glance

| Phase | Specialists | Artifact | Exit gate |
|---|---|---|---|
| 1 Research | researcher (+ security for security tasks) | `research.md` | Facts sourced or labeled; riskiest unknown named; scope and non-goals written |
| 2 Plan | architect | `plan.md`, ADR if hard to reverse | One plan chosen with reasons; acceptance criteria per increment; progress-fit check passed |
| 3 Execute | builder (+ domain specialist), tester | change set, test report | Acceptance criteria met with evidence; tests pass; gaps listed |
| 4 Optimize | builder, debugger (or devops) | `optimization.md` (before/after) | Measured improvement or a documented decision to stop; behavior unchanged; tests pass |
| 5 Review | reviewer(s), security, verifier | `review.md`, handoff summary | No open blockers; every claim mapped to evidence; list of open gaps honest |

## 3. Phase details

**1. Research (context first).** Restate the goal and the decision it feeds. Read the existing code, docs, and data before proposing anything. Search for what already exists and cite it (uniqueness and prior art). List requirements, constraints, assumptions, and unknowns; resolve what you can by looking, and keep at most one question for the user. Identify the riskiest unknown and a cheap test for it. Output: `research.md` with a claim | source | confidence table, the assumptions ledger, and non-goals.

**2. Plan (options before commitment).** Write NFRs with numbers. Produce two or three candidate plans that differ meaningfully (including the simplest and "do not build"). Compare them with a weighted matrix (`scripts/biz_calc.py matrix`) and pick one; record an ADR when the choice is hard to reverse (`engineering/architecture-method.md`). Define the walking skeleton and the increments with acceptance checks. Update NOS-STATE (plan steps, gate, assumptions). Ask: is this the simplest design that meets the requirements for this stage?

**3. Execute (thin, verified increments).** Build the walking skeleton first, then widen. For fixes write the failing test or repro first. One writer per file; small diffs; run everything you claim; keep evidence (commands and output). The tester specialist adds edge cases, negative controls, and for web/games runs the headless harness (`extra/verify.md`).

**4. Optimize (measure, then change).** Only after the behavior is correct. Measure first (profile, benchmark, bundle size, complexity, cost); pick the largest cost; change one thing; re-measure; keep only what helps. Typical targets: hot paths, queries, payload size, startup time, memory, dead code, duplicated logic, error handling, security basics, logging. Behavior must not change: the existing tests are the guard. Record before/after numbers. Stop when the gain is below the cost or the budget is met.

**5. Review (independent, several angles).** Run one to three review passes, each with a different focus: correctness and tests; security, risk, and failure modes; readability, maintainability, and fit with the design. Reviewers see the change and the acceptance criteria, not each other's conclusions. Compare findings; resolve disagreements with a test or evidence, not a vote. Finish with the verifier: re-run checks from a clean state and map each claim to evidence. Write `review.md` with the verdict, blockers, majors, minors, verified vs open gap.

## 4. Cross-validation and multiple models

Independent review catches errors the author is blind to. Ways to get independence, strongest first:
1. **A different model or tool** reviewing a compact summary and the diff (if the user has one available). Only with the user's consent for any code or data that leaves the machine; strip secrets and personal data; treat the output as advice and verify every claim yourself.
2. **A fresh-context subagent** with the reviewer role (real subagents).
3. **A separate specialist pass** in the same context with a different mindset and checklist.
When only option 3 is possible, say so plainly: "reviewed by separate passes of the same model", which reduces but does not remove shared blind spots, and compensate with executable checks (tests, linters, the harness, negative controls). Never present agreement between passes as proof; proof is a passing check.

## 5. Artifacts and NOS-STATE

Keep the artifacts next to the work (for example `docs/workflow/<task>/research.md`, `plan.md`, `optimization.md`, `review.md`). Track state with `python scripts/nos_state.py`: `init`, `plan add/done`, `set gate`, `add decision|verified|not-verified|assumption|question|file`, `status`. A new session resumes by running `status` and reading the latest artifact; nothing depends on chat memory.

## 6. Gates and loop-backs

Do not enter a phase until the previous gate is met. Loop back to the phase that can fix the problem: failing acceptance tests go to Execute (debugger first); a flawed design goes to Plan; missing facts go to Research. Cap loops (for example three Execute-Review rounds) and then stop and report what blocks. At every gate answer the progress-fit question: is this still the best result for this stage, these users, and the evidence so far?

## 7. Anti-patterns

Skipping Research and building from assumptions · one plan presented as the only option · optimizing before correctness · reviewers who only see the author's summary · "review" passes that never run anything · treating a second model's opinion as a test · sending proprietary code to another service without consent · phases without artifacts · endless loops with no cap · using the full pipeline for a one-line fix.

## 8. Worked example

Task: "Add CSV export to the reports page." Deep mode is warranted only if the data volume or security is non-trivial; otherwise Standard. Suppose it is (large tables, per-tenant data):
- **Research:** read the reports code and tests; check streaming vs in-memory export; note tenant-isolation requirements; riskiest unknown: memory use on a 1M-row export (cheap test: generate a fixture and measure).
- **Plan:** options (synchronous download, streamed response, background job + link); matrix on memory, complexity, UX; choose streaming; ADR; skeleton = endpoint streaming 10 rows with auth and tenant filter.
- **Execute:** failing test for tenant isolation first; implement; tests for escaping (commas, quotes, newlines, formula injection prefixes), empty result, large result.
- **Optimize:** measure memory and time on 1M rows; change chunk size; re-measure; record before/after.
- **Review:** correctness pass (encoding, headers), security pass (authorization, CSV injection), maintainability pass; verifier re-runs the tests and the 1M-row measurement from a clean checkout.
Generate the scaffold: `python scripts/workflow_plan.py --task "Add CSV export to the reports page" --domain web --reviewers 3 --init-state NOS-STATE.md`.

## 9. Checklist

- [ ] Mode justified (Deep); anchor and NOS-STATE created
- [ ] Research artifact with sources and the riskiest unknown
- [ ] Two or more plans compared; ADR for hard-to-reverse choices
- [ ] Increments verified with evidence before moving on
- [ ] Optimization measured before and after
- [ ] Independent review passes with different focus; verifier re-ran checks
- [ ] Independence level stated honestly (other model, subagent, or separate pass)
- [ ] open gaps and next steps listed in the handoff
