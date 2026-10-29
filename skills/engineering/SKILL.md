---
name: engineering
description: "Software engineering judgment: senior-level design review, system architecture and ADRs, the five-phase research-plan-execute-optimize-review workflow, specialist roles, agentic and subagent work, and DevOps/testing/debugging. Use for architecture decisions, code or design reviews, and any multi-step engineering project."
---

# N-Omni: engineering

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| Senior-level thinking: design reviews, trade-offs, failure modes, estimation, production-ready checklist | `references/engineering/senior-mindset.md` |
| System design method: architecture, NFRs, reference architectures, ADR (architecture decision record), stage gates, scaling path | `references/engineering/architecture-method.md` |
| Agentic work: subagents, split a task across specialists, briefs, routing, verifying delegated work | `references/engineering/agentic-workflows.md` |
| Five-phase pipeline for Deep work: research, plan, execute, optimize, independent review (`NOS workflow`) | `references/engineering/multi-phase-workflow.md` |
| Specialist roles (researcher, architect, builder, tester, reviewer, security, debugger, writer, data-ml, game-dev, business, devops, designer, verifier): which specialist should do what | `references/engineering/specialists.md` |
| Git, Docker, CI (GitHub Actions), tests, debugging a failing test, SLOs/alerts/observability, profiling | `references/extra/devops-testing.md` |
| Plans, PRD, one-page GDD (game design document), decision records, review mode, handoffs, NOS-STATE | `references/extra/planning.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
