# Planning, review, and project-state templates

*Last updated: 2026-10-13 | Version-sensitive: none significant (templates) | Re-check current docs before pinning versions, prices, or API names.*

## Contents
1. NOS-STATE (anchor file for long tasks)
2. Requirements upgrade checklist ("make it better")
3. One-page PRD
4. One-page GDD
5. Tech design note and decision record
6. Task breakdown and estimation
7. Review mode (audit existing work)
8. Handoff summary
9. Prompt to self before finishing

## 1. NOS-STATE (anchor file for long tasks)

For Deep-mode projects, keep this block current (in a file such as `NOS-STATE.md` or restated in the chat at each checkpoint):

```
# NOS-STATE
Goal: <one sentence>
Constraints: <platform, versions, style, deadlines, must-not>
Done-when: <observable criteria>
Assumptions: <choices made for the user>
Plan: [x] 1 scaffold  [x] 2 core loop  [ ] 3 UI  [ ] 4 save  [ ] 5 polish  [ ] 6 test
Now: step 3, building the HUD
Decisions: <date/short: chose X over Y because Z>
Open questions: <only those that block progress>
Files: <path: purpose>
Verified: <what was actually run and how>
Open gaps: <what could not be checked here>
```
Update after each step. When the user changes direction, rewrite Goal/Constraints/Done-when first, then the Plan.

## 2. Requirements upgrade checklist

Turn the literal request into the better version. Scan these and add what is cheap and clearly wanted; list the rest as optional upgrades.

- **Users and context:** who uses it, on what device, with what skill level?
- **States:** empty, loading, error, offline, first-run, success.
- **Edge cases:** bad input, very long or very large data, zero items, double-click, refresh mid-action, no permission.
- **Quality:** responsive, accessible, fast, secure by default, readable code, comments where non-obvious.
- **Feel (games/UI):** feedback on every action (sound, motion, numbers), sensible defaults, undo, pause.
- **Persistence:** save/load, export/import, versioned data.
- **Configuration:** constants or a settings object instead of magic numbers.
- **Docs:** how to run, controls, how to extend.
- **Growth:** the next three features the structure should make easy.
Rule: raise quality, not scope. If an addition changes the deliverable's size, ask or list it.

## 3. One-page PRD

```
Problem: who hurts, how, evidence
Goal & success metric: measurable
Users & scenarios: 2-3 concrete stories
Requirements: Must / Should / Could (prioritized)
Out of scope: explicit
UX notes: flows, key screens
Technical notes: data, integrations, constraints
Risks & mitigations
Milestones: v0 (proof) / v1 (usable) / v2 (polish)
Open questions
```

## 4. One-page GDD

```
Title / Genre / Platform / Engine
Pitch (2 sentences) and player fantasy
Core loop: verb -> reward -> upgrade -> new challenge
Controls
Systems: movement, combat, economy, progression, AI, UI (one line each)
Content plan: levels/enemies/items counts for v1
Progression & difficulty curve
Art direction (palette, references, resolution) and audio direction
Monetization/distribution (if any)
Scope: v1 must-have / cut list
Technical risks and prototype plan
Playtest plan: who, what to watch
```

## 5. Tech design note and decision record

```
Context: what problem and constraints
Options: A / B / C with pros, cons, cost
Decision: chosen option and why
Consequences: what gets easier, harder, and risks
Revisit when: trigger to reconsider
```
For non-trivial choices (framework, engine, database, hosting), present a compact comparison table and a recommendation. Label facts, inferences, and unknowns separately.

## 6. Task breakdown and estimation

Split into vertical slices that each end in something runnable (`walk around → collect coin → score shows → save`). Order: risky/unknown first, foundation, core loop, secondary systems, polish. For each task write the acceptance check ("done when ..."). Estimate in ranges (best/likely/worst) and add 30-50% for integration and bugs. Keep a visible cut list.

## 7. Review mode (audit existing work)

Use when the user provides code, a design, a document, or a game to critique or improve.

1. **Restate** what it is meant to do (anchor).
2. **Run or read** it: reproduce issues with evidence (error text, screenshot, failing input).
3. **Rate** by severity:
   - **Blocker:** breaks the main use (crash, data loss, security hole).
   - **Major:** wrong or confusing behavior in common paths.
   - **Minor:** polish, style, small inefficiency.
4. **Root cause** for each issue, not just the symptom.
5. **Fix** with minimal `find → replace` pairs (or a short patch) for each, in priority order.
6. **Verify** the fix by running the same repro.
7. **Summarize**: what was wrong, what changed, what remains, and next upgrades.

Code review rubric: correctness · security · error handling · readability · structure · performance · tests · docs. Design review rubric: hierarchy · consistency · contrast/accessibility · spacing · copy · states · responsiveness. Writing review rubric: audience fit · clarity · structure · voice · concision · accuracy.

## 8. Handoff summary

At the end of substantial work:
```
Built: <what exists>
Run/use: <exact steps or commands>
Structure: <key files/sections and their roles>
Checked: <checks that ran>   Open gaps: <gaps>
Assumptions: <list>
Next upgrades (max 3): <concrete, ordered>
```

## 9. Prompt to self before finishing

- Does the output match the **Goal** and **Done-when** in the anchor?
- Did I answer what was asked, in the requested format and length?
- Is anything claimed as working that I did not run?
- Are assumptions and limits stated?
- Is the first thing the user sees the result they wanted?

## 10. Stage gates in NOS-STATE

Add a `Gate:` line to NOS-STATE and update it as work advances: `G0 Frame → G1 Design → G2 Skeleton → G3 Core → G4 Harden → G5 Launch → G6 Operate` (checks in `engineering/architecture-method.md`; AI projects use A0-A5 in `ai/architecture.md`; games use the production stages in `games/production.md`). At each gate write: evidence collected, decisions made (ADR ids), what changed in the plan, and the progress-fit verdict (continue / adjust / stop).
