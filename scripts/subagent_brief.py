#!/usr/bin/env python3
"""Specialist roles for NOS agentic workflows: list roles, show a profile, build a subagent brief, or generate the specialists doc.

  python subagent_brief.py list
  python subagent_brief.py show tester
  python subagent_brief.py brief --role builder --goal "Add CSV export to the report page" \\
        --context "Flask app in app/, tests in tests/" --constraints "No new dependencies" \\
        --acceptance "Export downloads valid CSV; tests pass" --files app/report.py tests/test_report.py --out brief.md
  python subagent_brief.py doc --out ../references/engineering/specialists.md   # regenerate the reference doc (UTF-8)

A brief is a self-contained task description for a subagent (or for a specialist pass in a single context): goal, context,
inputs, constraints, acceptance criteria, deliverable format, and the role's process and checklist.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specialists_data import LAST_UPDATED, SPECIALISTS  # noqa: E402


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def role(key):
    if key not in SPECIALISTS:
        die(f"unknown role '{key}'. Roles: {', '.join(SPECIALISTS)}")
    return SPECIALISTS[key]


def bullets(items):
    return "\n".join(f"- {x}" for x in items)


def numbered(items):
    return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))


def profile_md(key, heading="##"):
    r = role(key)
    return (f"{heading} {r['title']} (`{key}`)\n\n**Mission:** {r['mission']}\n\n**Use when:** {r['description']}\n\n"
            f"**Mindset**\n{bullets(r['mindset'])}\n\n**Process**\n{numbered(r['process'])}\n\n**Checklist**\n{bullets(['[ ] ' + c for c in r['checklist']])}\n\n"
            f"**Deliverable:** {r['deliverable']}\n\n**Pitfalls:** {'; '.join(r['pitfalls'])}.\n\n"
            f"**Tools (Claude Code):** {r['tools']} | **Load:** {', '.join('`references/' + x + '`' for x in r['refs'])}\n")


def cmd_list(a):
    for k, r in SPECIALISTS.items():
        print(f"{k:18} {r['title']:38} tools: {r['tools']}")


def cmd_show(a):
    print(profile_md(a.role, "#"))


def cmd_brief(a):
    r = role(a.role)
    if not a.goal.strip():
        die("--goal must not be empty")
    parts = [f"# Brief for {r['title']}", "", f"**Goal:** {a.goal.strip()}", ""]
    if a.why:
        parts += [f"**Why it matters:** {a.why.strip()}", ""]
    parts += ["**Context:** " + (a.context.strip() if a.context else "(none given: ask the orchestrator only if blocked, otherwise state assumptions)"), ""]
    if a.files:
        parts += ["**Inputs / files:**", bullets(a.files), ""]
    parts += ["**Constraints and boundaries:** " + (a.constraints.strip() if a.constraints else "Stay within the stated goal; do not touch unrelated files; no secrets in output."), "",
              "**Acceptance criteria:** " + (a.acceptance.strip() if a.acceptance else "(define measurable criteria before starting and state them in your report)"), "",
              f"**Deliverable format:** {r['deliverable']}", "",
              "**Report back with:** what you did; evidence (commands run and their output, or sources); the evidence for each claim; assumptions made; open questions; suggested next step. Treat your own claims as unproven until you show evidence.", "",
              "---", "", "## Role profile", "", profile_md(a.role, "###")]
    text = "\n".join(parts)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"wrote {a.out}")
    else:
        print(text)


def cmd_doc(a):
    out = ["# Specialist roles", "",
           f"*Last updated: {LAST_UPDATED} | Version-sensitive: generated from scripts/specialists_data.py; tool names for Claude Code | Re-check current docs before pinning versions, prices, or API names.*", "",
           "Generated from `scripts/specialists_data.py` (run `python scripts/subagent_brief.py doc --out references/engineering/specialists.md` to regenerate). "
           "Use these profiles for subagents, for Claude Code subagent files (`scripts/install_subagents.py`), and for single-context **specialist passes** (`engineering/agentic-workflows.md`).", "",
           "## Routing table", "", "| Task | Primary specialist | Then |", "|---|---|---|",
           "| New feature or system | architect → builder | tester → reviewer → verifier |",
           "| Bug or failing test | debugger | tester → verifier |",
           "| Is this true / does this exist? | researcher | reviewer (critic) |",
           "| Page, UI, landing page | designer → builder | tester (axe, screenshots) → verifier |",
           "| Game | game-dev | tester (harness, simulation) → reviewer |",
           "| Data analysis, ML, RAG, pipelines | data-ml | reviewer → verifier |",
           "| Business plan, pricing, forecast | business-analyst | researcher (facts) → reviewer |",
           "| Writing, editing, docs | writer | reviewer |",
           "| Security review (authorized) | security | reviewer → verifier |",
           "| Deploy, CI, infra, reliability | devops | tester → verifier |", "",
           "## Contents", ""]
    out += [f"- {r['title']} (`{k}`)" for k, r in SPECIALISTS.items()]
    out.append("")
    for k in SPECIALISTS:
        out += [profile_md(k, "##")]
    text = "\n".join(out).rstrip() + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("show"); p.add_argument("role"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("brief")
    p.add_argument("--role", required=True); p.add_argument("--goal", required=True); p.add_argument("--why"); p.add_argument("--context")
    p.add_argument("--constraints"); p.add_argument("--acceptance"); p.add_argument("--files", nargs="*"); p.add_argument("--out")
    p.set_defaults(fn=cmd_brief)
    d = sub.add_parser("doc"); d.add_argument("--out", help="write UTF-8 to this file instead of stdout"); d.set_defaults(fn=cmd_doc)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
