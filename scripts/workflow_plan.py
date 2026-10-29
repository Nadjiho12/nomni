#!/usr/bin/env python3
"""Generate a five-phase NOS workflow plan: Research -> Plan -> Execute -> Optimize -> Review.

Each phase gets specialists, objectives, artifacts, an exit gate, and (in subagent mode) ready-to-run brief commands.
Optionally initializes NOS-STATE with the phases as plan steps.

  python workflow_plan.py --task "Add CSV export to the reports page" --domain web
  python workflow_plan.py --task "RAG assistant over our docs" --domain ai --mode subagents --reviewers 2 --out plan.md
  python workflow_plan.py --task "Launch plan for my game" --domain game --init-state NOS-STATE.md
Domains: web, game, ai, business, writing, security, devops, general. Modes: passes (single context, sequential roles) or subagents.
Reviewers: 1-3 independent review passes with different focus (correctness, security/risk, maintainability).
See references/engineering/multi-phase-workflow.md.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAIN_ROLE = {"web": "designer", "game": "game-dev", "ai": "data-ml", "business": "business-analyst", "writing": "writer",
               "security": "security", "devops": "devops", "general": None}
FOCUS = ["correctness and tests", "security, risk, and failure modes", "readability, maintainability, and fit with the design"]


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def build(task, domain, mode, reviewers):
    dom = DOMAIN_ROLE[domain]
    build_roles = ["builder"] + ([dom] if dom and dom != "security" else [])
    phases = [
        dict(key="research", name="Research", roles=["researcher"] + (["security"] if domain == "security" else []),
             goal=f"Establish the facts, constraints, and prior art for: {task}",
             actions=["Restate the goal and success measure; list assumptions and unknowns.", "Read the existing code/docs/data; search for what already exists (sourced).",
                      "Identify the riskiest unknown and how to test it cheaply.", "Capture findings in research.md (claim | source | confidence)."],
             artifacts=["research.md"], gate="Facts sourced or labeled; riskiest unknown named; scope and non-goals written."),
        dict(key="plan", name="Plan", roles=["architect"],
             goal="Choose the design and break the work into verifiable increments.",
             actions=["Write NFRs with numbers; draft 2-3 candidate plans including the simplest.", "Compare with a weighted matrix; choose; record an ADR if the choice is hard to reverse.",
                      "Define the walking skeleton and increments with acceptance checks.", "Update NOS-STATE: plan steps, gate, assumptions."],
             artifacts=["plan.md", "ADR (if needed)"], gate="One plan chosen with reasons; acceptance criteria per increment; progress-fit check passed."),
        dict(key="execute", name="Execute", roles=build_roles + ["tester"],
             goal="Implement in thin verified increments.",
             actions=["Build the walking skeleton first, then widen.", "Write the failing test or repro first for fixes; run everything you claim.",
                      "Keep diffs small; one writer per file.", "Record evidence (commands and output) per increment."],
             artifacts=["working change set", "test report"], gate="Acceptance criteria met with evidence; tests pass; known gaps listed."),
        dict(key="optimize", name="Optimize", roles=["builder", "debugger"] if domain != "devops" else ["devops", "debugger"],
             goal="Improve speed, size, clarity, and robustness without changing behavior.",
             actions=["Measure first (profile, benchmark, size, complexity); pick the biggest cost.", "Simplify and remove dead code; harden errors, limits, and security basics.",
                      "Re-run all tests and re-measure; keep only changes that help.", "Record before/after numbers in optimization.md."],
             artifacts=["optimization.md (before/after)"], gate="Measured improvement or documented decision to stop; behavior unchanged; tests still pass."),
        dict(key="review", name="Review", roles=["reviewer"] + (["security"] if domain != "security" else []) + ["verifier"],
             goal="Independently confirm quality before reporting done.",
             actions=[f"Run {reviewers} independent review pass(es), each with a different focus: " + "; ".join(FOCUS[:reviewers]) + ".",
                      "Compare findings; resolve disagreements with a test or evidence, not a vote.", "Verifier re-runs the checks from a clean state and compares to the acceptance criteria.",
                      "Write review.md: verdict, blockers, majors, checked items and open gaps."],
             artifacts=["review.md", "handoff summary"], gate="No open blockers; every claim mapped to evidence; list of open gaps honest."),
    ]
    return phases


def render(task, domain, mode, reviewers, phases):
    out = ["# NOS workflow plan", "", f"**Task:** {task}", f"**Domain:** {domain} | **Mode:** {'real subagents' if mode == 'subagents' else 'specialist passes (single context)'} | **Independent reviewers:** {reviewers}", "",
           "Run the phases in order. Do not start a phase until the previous exit gate is met; if a gate fails, loop back to the phase that can fix it. "
           "Update NOS-STATE after each phase (`python scripts/nos_state.py ...`).", ""]
    for i, p in enumerate(phases, 1):
        out += [f"## Phase {i}: {p['name']}", "", f"**Specialists:** {', '.join(p['roles'])}", f"**Objective:** {p['goal']}", "", "**Actions**"] + [f"{j}. {a}" for j, a in enumerate(p["actions"], 1)]
        out += ["", f"**Artifacts:** {', '.join(p['artifacts'])}", f"**Exit gate:** {p['gate']}", ""]
        if mode == "subagents":
            out.append("**Briefs to dispatch**")
            for r in p["roles"]:
                goal_text = f"{p['name']} phase for: {task}"
                out.append(f"- `python scripts/subagent_brief.py brief --role {r} --goal \"{goal_text}\" --acceptance \"{p['gate']}\" --out brief-{p['key']}-{r}.md`")
            out.append("")
        else:
            out += ["**Specialist-pass headers**", ""] + [f"- `[PASS: {r}]`" for r in p["roles"]] + [""]
    out += ["## Cross-validation", "",
            "Reviews are independent: each reviewer sees the change and the acceptance criteria but not the other reviewers' conclusions. "
            "If other models or tools are available, use them only as additional independent reviewers on a compact summary, with the user's consent for any code or data that leaves the machine; "
            "treat their output as advice and verify every claim. If not, say plainly that review was done by separate passes of the same model, which reduces but does not remove shared blind spots.", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True)
    ap.add_argument("--domain", default="general", choices=sorted(DOMAIN_ROLE))
    ap.add_argument("--mode", default="passes", choices=["passes", "subagents"])
    ap.add_argument("--reviewers", type=int, default=2)
    ap.add_argument("--out")
    ap.add_argument("--init-state", metavar="FILE", help="create a NOS-STATE file with the phases as plan steps")
    a = ap.parse_args()
    if not a.task.strip():
        die("--task must not be empty")
    if not 1 <= a.reviewers <= 3:
        die("--reviewers must be 1, 2, or 3")
    phases = build(a.task.strip(), a.domain, a.mode, a.reviewers)
    text = render(a.task.strip(), a.domain, a.mode, a.reviewers, phases)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"wrote {a.out}")
    else:
        print(text)
    if a.init_state:
        st = os.path.join(HERE, "nos_state.py")
        r = subprocess.run([sys.executable, st, "--file", a.init_state, "init", "--goal", a.task.strip(), "--gate", "G0 Frame", "--force"], capture_output=True, text=True)
        if r.returncode:
            die(r.stderr.strip() or "could not create NOS-STATE")
        for p in phases:
            subprocess.run([sys.executable, st, "--file", a.init_state, "plan", "add", f"{p['name']}: {p['gate']}"], capture_output=True, text=True)
        print(f"initialized {a.init_state} with {len(phases)} plan steps")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
