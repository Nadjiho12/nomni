#!/usr/bin/env python3
"""NOS-STATE: a small structured project-state file for long, multi-session (Deep mode) work.

Keeps the anchor (goal, constraints, done-when), the current stage gate, the plan with checkboxes, decisions, assumptions,
what was checked, open gaps, open questions, files, and a short log, so work can resume without re-explaining.

  python nos_state.py init --goal "Build X" --constraints "solo, 2 weeks" --done-when "users can Y"
  python nos_state.py plan add "Walking skeleton deployed"      # also: plan done 1 | plan undo 1 | plan list
  python nos_state.py set gate "G2 Skeleton"                   # also: set goal|constraints|done-when TEXT
  python nos_state.py add decision "Chose Postgres over SQLite: multi-user writes"
  python nos_state.py add checked "login flow | ran tests/test_login.py: 12 passed"
  python nos_state.py add open-gap "mobile Safari rendering"
  python nos_state.py status                                   # compact summary
  python nos_state.py show                                     # whole file
Sections for `add`: decision, assumption, checked, open-gap, question, file, log. Default file: ./NOS-STATE.md (use --file).
"""
import argparse
import datetime
import os
import re
import sys

TEXT_SECTIONS = ["Goal", "Constraints", "Done-when", "Gate"]
LIST_SECTIONS = ["Plan", "Decisions", "Assumptions", "Checked", "Open gaps", "Open questions", "Files", "Log"]
ORDER = TEXT_SECTIONS + LIST_SECTIONS
ADD_MAP = {"decision": "Decisions", "assumption": "Assumptions", "checked": "Checked", "open-gap": "Open gaps",
           "question": "Open questions", "file": "Files", "log": "Log"}
SET_MAP = {"goal": "Goal", "constraints": "Constraints", "done-when": "Done-when", "gate": "Gate"}


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def today():
    return datetime.date.today().isoformat()


def load(path):
    if not os.path.exists(path):
        die(f"{path} not found; run `nos_state.py init --goal ...` first")
    data = {s: [] for s in ORDER}
    cur = None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            m = re.match(r"^## (.+?)\s*$", line)
            if m:
                cur = m.group(1) if m.group(1) in data else None
                continue
            if cur and line.strip():
                data[cur].append(line.rstrip())
    return data


def save(path, data):
    out = ["# NOS-STATE", ""]
    for s in ORDER:
        out.append(f"## {s}")
        out += data[s] if data[s] else ["(none yet)" if s in LIST_SECTIONS else "(not set)"]
        out.append("")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip() + "\n")
    os.replace(tmp, path)


def clean(data):
    for s in ORDER:
        data[s] = [l for l in data[s] if l.strip() not in ("(none yet)", "(not set)")]
    return data


def steps(data):
    items = []
    for l in data["Plan"]:
        m = re.match(r"^- \[( |x)\] (\d+)\. (.*)$", l)
        if m:
            items.append((m.group(1) == "x", int(m.group(2)), m.group(3)))
    return items


def cmd_init(a):
    if os.path.exists(a.file) and not a.force:
        die(f"{a.file} already exists (use --force to overwrite)")
    if not a.goal.strip():
        die("--goal must not be empty")
    data = {s: [] for s in ORDER}
    data["Goal"] = [a.goal.strip()]
    if a.constraints:
        data["Constraints"] = [a.constraints.strip()]
    if a.done_when:
        data["Done-when"] = [a.done_when.strip()]
    data["Gate"] = [a.gate]
    data["Log"] = [f"- {today()}: state created"]
    save(a.file, data)
    print(f"created {a.file}")


def cmd_set(a):
    if not a.text.strip():
        die("text must not be empty")
    data = clean(load(a.file))
    data[SET_MAP[a.field]] = [a.text.strip()]
    data["Log"].append(f"- {today()}: set {a.field}")
    save(a.file, data)
    print(f"{a.field} updated")


def cmd_add(a):
    if not a.text.strip():
        die("text must not be empty")
    data = clean(load(a.file))
    sec = ADD_MAP[a.section]
    data[sec].append(f"- {today()}: {a.text.strip()}" if a.section in ("decision", "log") else f"- {a.text.strip()}")
    save(a.file, data)
    print(f"added to {sec}")


def cmd_plan(a):
    data = clean(load(a.file))
    items = steps(data)
    if a.action == "add":
        if not a.arg or not a.arg.strip():
            die("give the step text")
        n = max([i[1] for i in items], default=0) + 1
        data["Plan"].append(f"- [ ] {n}. {a.arg.strip()}")
        save(a.file, data)
        print(f"step {n} added")
    elif a.action in ("done", "undo"):
        try:
            n = int(a.arg)
        except (TypeError, ValueError):
            die("give the step number")
        if n not in [i[1] for i in items]:
            die(f"no step {n}")
        data["Plan"] = [re.sub(r"^- \[( |x)\]", "- [x]" if a.action == "done" else "- [ ]", l) if l.startswith("- [") and re.match(rf"^- \[( |x)\] {n}\. ", l) else l for l in data["Plan"]]
        data["Log"].append(f"- {today()}: step {n} {'done' if a.action == 'done' else 'reopened'}")
        save(a.file, data)
        print(f"step {n} {a.action}")
    else:
        for done, n, t in items:
            print(f"[{'x' if done else ' '}] {n}. {t}")


def cmd_status(a):
    data = clean(load(a.file))
    items = steps(data)
    done = sum(1 for i in items if i[0])
    nxt = next((f"{n}. {t}" for d, n, t in items if not d), "none (all done)" if items else "no plan yet")
    one = lambda s: data[s][0] if data[s] else "(not set)"
    print(f"Goal:        {one('Goal')}")
    print(f"Done-when:   {one('Done-when')}")
    print(f"Gate:        {one('Gate')}")
    print(f"Plan:        {done}/{len(items)} steps done; next: {nxt}")
    print(f"Evidence:    {len(data['Checked'])} checked, {len(data['Open gaps'])} open gaps, {len(data['Assumptions'])} assumptions")
    print(f"Open items:  {len(data['Open questions'])} questions, {len(data['Decisions'])} decisions recorded")


def cmd_show(a):
    load(a.file)
    print(open(a.file, encoding="utf-8").read(), end="")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default="NOS-STATE.md")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--goal", required=True); p.add_argument("--constraints"); p.add_argument("--done-when")
    p.add_argument("--gate", default="G0 Frame"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("set"); p.add_argument("field", choices=sorted(SET_MAP)); p.add_argument("text"); p.set_defaults(fn=cmd_set)
    p = sub.add_parser("add"); p.add_argument("section", choices=sorted(ADD_MAP)); p.add_argument("text"); p.set_defaults(fn=cmd_add)
    p = sub.add_parser("plan"); p.add_argument("action", choices=["add", "done", "undo", "list"]); p.add_argument("arg", nargs="?"); p.set_defaults(fn=cmd_plan)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("show").set_defaults(fn=cmd_show)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
