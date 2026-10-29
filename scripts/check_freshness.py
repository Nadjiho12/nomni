#!/usr/bin/env python3
"""Freshness tracker for the reference files. Each reference carries a line under its title:

  *Last updated: YYYY-MM-DD | Version-sensitive: <items that go stale> | Re-check current docs before pinning versions, prices, or API names.*

  python check_freshness.py                       # report age per file; exit 1 if a stamp is missing or older than --max-days
  python check_freshness.py --max-days 90 --json
  python check_freshness.py --list-volatile       # which facts to re-verify first (files with version-sensitive content)
  python check_freshness.py stamp references/ai/rag-llm.md [more files]    # set the stamp to today after you edited/re-verified a file
The date means "last edited or re-verified by a maintainer", not "every fact was checked on that date".
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"^\*Last updated: (\d{4}-\d{2}-\d{2}) \| Version-sensitive: (.+?) \| Re-check current docs before pinning versions, prices, or API names\.\*\s*$")


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def files():
    return sorted(glob.glob(os.path.join(ROOT, "references", "**", "*.md"), recursive=True))


def stamp_of(path):
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i > 6:
                break
            m = PAT.match(line)
            if m:
                return m.group(1), m.group(2)
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", choices=["stamp"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--max-days", type=int, default=180)
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-volatile", action="store_true")
    a = ap.parse_args()
    try:
        today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    except ValueError:
        die("--today must be YYYY-MM-DD")
    if a.max_days < 1:
        die("--max-days must be >= 1")
    if a.cmd == "stamp":
        if not a.paths:
            die("give at least one reference file to stamp")
        for p in a.paths:
            if not os.path.exists(p):
                die(f"{p} not found")
            lines = open(p, encoding="utf-8").read().split("\n")
            for i, line in enumerate(lines[:7]):
                m = PAT.match(line)
                if m:
                    lines[i] = line.replace(m.group(1), today.isoformat(), 1)
                    break
            else:
                die(f"{p} has no freshness line to update")
            open(p, "w", encoding="utf-8").write("\n".join(lines))
            print(f"stamped {p} {today.isoformat()}")
        return
    rows, bad = [], 0
    for p in files():
        d, vol = stamp_of(p)
        rel = os.path.relpath(p, ROOT)
        if d is None:
            rows.append({"file": rel, "status": "MISSING", "age_days": None, "volatile": None})
            bad += 1
            continue
        age = (today - datetime.date.fromisoformat(d)).days
        st = "STALE" if age > a.max_days else "ok"
        bad += st == "STALE"
        rows.append({"file": rel, "status": st, "age_days": age, "updated": d, "volatile": vol})
    if a.json:
        print(json.dumps(rows, indent=1))
    elif a.list_volatile:
        for r in rows:
            if r["volatile"] and not r["volatile"].lower().startswith("none"):
                print(f"{r['file']:50} {r['volatile']}")
    else:
        for r in rows:
            print(f"{r['status']:8} {r['file']:50} " + (f"{r['age_days']} days old" if r["age_days"] is not None else "no freshness line"))
        print(f"{len(rows)} files, {bad} need attention (max {a.max_days} days)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
