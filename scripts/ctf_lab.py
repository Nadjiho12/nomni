#!/usr/bin/env python3
"""Build and operate training ranges: CTF challenge manifests, signed flags, a scoreboard engine,
isolated-container compose templates, and an ATT&CK-style detection-coverage tracker for purple-team exercises.

For your own authorized lab/training use (see references/tools/lab-range-design.md). This tool generates
infrastructure (manifests, flags, scoring, isolation templates, coverage tracking) — never vulnerability or
exploit code. Populate challenges from established open-source training apps (DVWA, Juice Shop, WebGoat,
Metasploitable, VulnHub/HTB-style boxes) or your own app with ONE documented weakness per challenge, built
from the vulnerability classes already in tools/security-assessment.md and web/backend.md.

  python ctf_lab.py manifest new --out chal.json --name "Baby SQLi" --category web --points 100 --difficulty easy \\
      --description "Find the admin password." --flag-secret mysecretseed
  python ctf_lab.py manifest validate chal.json [more.json ...]       # schema + solvability shape check
  python ctf_lab.py flag gen chal.json --team alice                   # deterministic per-team flag (HMAC)
  python ctf_lab.py flag check chal.json --team alice "CHAL{...}"     # verify a submission
  python ctf_lab.py score --manifests dir/*.json --submissions subs.csv --out scoreboard.json
      submissions.csv: team,challenge_id,flag,timestamp_iso
  python ctf_lab.py compose chal.json --out docker-compose.yml        # isolated per-challenge template (no egress, limits)
  python ctf_lab.py coverage --techniques techniques.txt [--mark T1110.001=tested,T1059=planned] --out coverage.json
      techniques.txt: one ATT&CK technique ID (and optional name) per line, e.g. "T1110.001 Password Guessing"
Exit codes: 0 ok; 1 validation/check failed; 2 usage error.
"""
import argparse
import csv
import hashlib
import hmac
import json
import re
import sys
from datetime import datetime, timezone

CATEGORIES = {"web", "crypto", "forensics", "reversing", "pwn", "misc", "network", "cloud", "mobile", "osint", "hardware"}
DIFFICULTIES = ["easy", "medium", "hard", "insane"]
FLAG_RE = re.compile(r"^[A-Za-z0-9_.-]{1,40}\{[\x20-\x7e]{1,300}\}$")


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    except ValueError as e:
        die(f"{path} is not valid JSON: {e}")


def validate_manifest(m, path="(manifest)"):
    errs = []
    req = ["id", "name", "category", "points", "difficulty", "description", "flag_format", "flag_secret_hash"]
    for k in req:
        if k not in m:
            errs.append(f"missing '{k}'")
    if errs:
        return errs
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,49}", m["id"]):
        errs.append("id must be 3-50 chars: lowercase letters, digits, _ or -")
    if m["category"] not in CATEGORIES:
        errs.append(f"category must be one of {sorted(CATEGORIES)}")
    if m["difficulty"] not in DIFFICULTIES:
        errs.append(f"difficulty must be one of {DIFFICULTIES}")
    if not isinstance(m["points"], int) or not (1 <= m["points"] <= 1000):
        errs.append("points must be an integer 1-1000")
    if not m["name"].strip() or len(m["name"]) > 80:
        errs.append("name must be 1-80 characters")
    if not m["description"].strip():
        errs.append("description must not be empty")
    if "{TOKEN}" not in m["flag_format"]:
        errs.append("flag_format must contain the literal placeholder {TOKEN} (braces are literal flag syntax; TOKEN is replaced)")
    else:
        sample = m["flag_format"].replace("TOKEN", "a" * 24)
        if not FLAG_RE.match(sample):
            errs.append(f"flag_format does not produce a CATEGORY{{token}}-shaped flag (got e.g. {sample!r}); "
                        "use ascii letters/digits/_.- before '{', and printable ascii inside the braces")
    hints = m.get("hints", [])
    if not isinstance(hints, list) or any(not isinstance(h, dict) or "cost" not in h or "text" not in h for h in hints):
        errs.append("hints must be a list of {cost, text} objects")
    elif any(h["cost"] < 0 or h["cost"] >= m.get("points", 0) for h in hints):
        errs.append("every hint cost must be >= 0 and less than the challenge's points (a hint must not zero out the reward)")
    if "unintended_solution_review" not in m:
        errs.append("missing 'unintended_solution_review' (bool: has someone other than the author solved this and confirmed no shortcut exists?)")
    elif m["unintended_solution_review"] is not True:
        errs.append("unintended_solution_review must be true before the challenge ships (get a second solver)")
    return errs


def derive_flag(secret_hash_hex, chal_id, team, flag_format):
    # HMAC-SHA256(per-challenge secret, team) -> short token. Per-team flags make shared/leaked flags attributable
    # and stop one team's solve from trivially solving it for everyone.
    key = bytes.fromhex(secret_hash_hex)
    token = hmac.new(key, f"{chal_id}:{team}".encode(), hashlib.sha256).hexdigest()[:24]
    return flag_format.replace("TOKEN", token)  # braces in flag_format are literal; only the bare TOKEN word is substituted


def secret_hash(secret):
    return hashlib.sha256(secret.encode()).hexdigest()


def cmd_manifest_new(a):
    if not a.name.strip():
        die("--name must not be empty")
    if len(a.name) > 80:
        die("--name must be 80 characters or fewer")
    if a.category not in CATEGORIES:
        die(f"--category must be one of {sorted(CATEGORIES)}")
    if a.difficulty not in DIFFICULTIES:
        die(f"--difficulty must be one of {DIFFICULTIES}")
    if not (1 <= a.points <= 1000):
        die("--points must be 1-1000")
    if not a.description.strip():
        die("--description must not be empty")
    cid = re.sub(r"[^a-z0-9]+", "-", a.name.lower()).strip("-")[:40] or "challenge"
    m = {
        "id": cid, "name": a.name, "category": a.category, "points": a.points, "difficulty": a.difficulty,
        "description": a.description, "flag_format": a.flag_format or f"{a.category.upper()}{{{{TOKEN}}}}".replace("{{", "{").replace("}}", "}"),
        "flag_secret_hash": secret_hash(a.flag_secret), "hints": [], "author": a.author or "", "unintended_solution_review": False,
        "created": datetime.now(timezone.utc).date().isoformat(),
    }
    errs = validate_manifest(m)
    errs = [e for e in errs if "unintended_solution_review" not in e]  # expected false on creation
    if errs:
        die("generated manifest failed its own validation: " + "; ".join(errs), 1)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1)
    print(f"wrote {a.out} (id={cid}). Keep --flag-secret private: it is hashed into the manifest, not stored in plain text. "
          f"Set unintended_solution_review to true only after a second person solves it.")


def cmd_manifest_validate(a):
    bad = 0
    for path in a.files:
        m = load_json(path)
        errs = validate_manifest(m, path)
        if errs:
            bad += 1
            print(f"INVALID {path}")
            for e in errs:
                print("  -", e)
        else:
            print(f"ok      {path}  [{m['id']}] {m['points']}pt {m['category']}/{m['difficulty']}")
    print(f"{len(a.files)} manifest(s), {bad} invalid")
    sys.exit(1 if bad else 0)


def cmd_flag_gen(a):
    m = load_json(a.manifest)
    if not validate_manifest(m) == [] and set(validate_manifest(m)) - {"unintended_solution_review"}:
        die(f"{a.manifest} fails validation; run `manifest validate` first")
    if not a.team.strip():
        die("--team must not be empty")
    print(derive_flag(m["flag_secret_hash"], m["id"], a.team.strip(), m["flag_format"]))


def cmd_flag_check(a):
    m = load_json(a.manifest)
    if not a.team.strip():
        die("--team must not be empty")
    expected = derive_flag(m["flag_secret_hash"], m["id"], a.team.strip(), m["flag_format"])
    ok = hmac.compare_digest(expected, a.flag.strip())
    print("VALID" if ok else "INVALID")
    sys.exit(0 if ok else 1)


def cmd_score(a):
    manifests = {}
    for p in a.manifests:
        m = load_json(p)
        errs = validate_manifest(m)
        if set(errs) - {"unintended_solution_review"}:
            die(f"{p} fails validation: {errs}")
        manifests[m["id"]] = m
    if not manifests:
        die("no manifests given")
    try:
        with open(a.submissions, newline="", encoding="utf-8") as f:
            subs = list(csv.DictReader(f))
    except OSError as e:
        die(f"cannot read {a.submissions}: {e.strerror}")
    need = {"team", "challenge_id", "flag", "timestamp_iso"}
    if subs and not need <= set(subs[0]):
        die(f"{a.submissions} must have columns: {sorted(need)}")
    solved = {}        # (team, chal_id) -> timestamp, for dedupe (only the first correct submission counts)
    first_blood = {}   # chal_id -> (team, timestamp)
    rejected = 0
    for row in subs:
        cid, team = row["challenge_id"], row["team"].strip()
        if cid not in manifests or not team:
            rejected += 1
            continue
        if (team, cid) in solved:
            continue  # duplicate submission for an already-solved challenge: ignore, do not re-score
        m = manifests[cid]
        expected = derive_flag(m["flag_secret_hash"], cid, team, m["flag_format"])
        if not hmac.compare_digest(expected, row["flag"].strip()):
            rejected += 1
            continue
        try:
            ts = datetime.fromisoformat(row["timestamp_iso"].replace("Z", "+00:00"))
        except ValueError:
            rejected += 1
            continue
        solved[(team, cid)] = ts
        if cid not in first_blood or ts < first_blood[cid][1]:
            first_blood[cid] = (team, ts)
    totals = {}
    for (team, cid), ts in solved.items():
        bonus = 1.10 if first_blood.get(cid, (None,))[0] == team else 1.0
        totals[team] = totals.get(team, 0.0) + manifests[cid]["points"] * bonus
    board = sorted(({"team": t, "score": round(s, 1), "solved": sum(1 for (tt, _) in solved if tt == t)} for t, s in totals.items()), key=lambda r: -r["score"])
    out = {"scoreboard": board, "first_blood": {cid: team for cid, (team, _) in first_blood.items()}, "rejected_submissions": rejected, "accepted_solves": len(solved)}
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)
        print(f"wrote {a.out}: {len(board)} team(s), {len(solved)} accepted solve(s), {rejected} rejected")
    else:
        print(json.dumps(out, indent=1))
    sys.exit(0)


COMPOSE_TMPL = """# Isolated template for challenge '{cid}' ({name}). Fill in `image`/`build` with YOUR OWN training application
# (an established vulnerable app such as DVWA/Juice Shop/WebGoat, or your own app with one documented weakness
# from tools/security-assessment.md's checklists). This file only provides the isolation shape; it contains no
# application or vulnerability code.
services:
  {cid}:
    # image: your-registry/{cid}:latest        # or: build: ./{cid}
    networks: [{cid}_net]
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 128
    mem_limit: 512m
    cpus: "1.0"
    restart: "no"               # training instances should not silently respawn mid-attempt
    ports:
      - "127.0.0.1:0:{port}"    # bind to loopback only; put a reverse proxy with auth in front for remote teams
networks:
  {cid}_net:
    internal: true               # no outbound internet from the challenge container
"""


def cmd_compose(a):
    m = load_json(a.manifest)
    errs = validate_manifest(m)
    if set(errs) - {"unintended_solution_review"}:
        die(f"{a.manifest} fails validation: {errs}")
    if not (1 <= a.port <= 65535):
        die("--port must be 1-65535")
    text = COMPOSE_TMPL.format(cid=m["id"], name=m["name"], port=a.port)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.out}")
    else:
        print(text, end="")


def cmd_coverage(a):
    try:
        lines = [l.strip() for l in open(a.techniques, encoding="utf-8") if l.strip() and not l.startswith("#")]
    except OSError as e:
        die(f"cannot read {a.techniques}: {e.strerror}")
    techs = []
    for line in lines:
        parts = line.split(None, 1)
        tid = parts[0]
        if not re.fullmatch(r"T\d{4}(\.\d{3})?", tid):
            die(f"not an ATT&CK technique id: {line!r}")
        techs.append((tid, parts[1] if len(parts) > 1 else ""))
    marks = {}
    for pair in a.mark or []:
        if "=" not in pair:
            die(f"--mark must look like T1110.001=tested, got {pair!r}")
        tid, status = pair.split("=", 1)
        if status not in ("untested", "planned", "tested", "detected", "gap"):
            die(f"--mark status must be one of untested|planned|tested|detected|gap, got {status!r}")
        marks[tid] = status
    rows = [{"id": tid, "name": name, "status": marks.get(tid, "untested")} for tid, name in techs]
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out = {"techniques": rows, "summary": counts, "total": len(rows)}
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)
        print(f"wrote {a.out}: {len(rows)} techniques, {counts}")
    else:
        for r in rows:
            print(f"{r['status']:10} {r['id']:14} {r['name']}")
        print(counts)
    detected = counts.get("detected", 0)
    tested = detected + counts.get("tested", 0) + counts.get("gap", 0)
    if tested and detected / tested < 0.5:
        print(f"Note: only {detected}/{tested} tested techniques show a confirmed detection. Prioritize 'gap' entries.")
    sys.exit(0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    mp = sub.add_parser("manifest")
    msub = mp.add_subparsers(dest="mcmd", required=True)
    n = msub.add_parser("new")
    n.add_argument("--out", required=True); n.add_argument("--name", required=True); n.add_argument("--category", required=True)
    n.add_argument("--points", type=int, required=True); n.add_argument("--difficulty", required=True)
    n.add_argument("--description", required=True); n.add_argument("--flag-secret", required=True)
    n.add_argument("--flag-format"); n.add_argument("--author", default="")
    n.set_defaults(fn=cmd_manifest_new)
    v = msub.add_parser("validate"); v.add_argument("files", nargs="+"); v.set_defaults(fn=cmd_manifest_validate)

    fp = sub.add_parser("flag")
    fsub = fp.add_subparsers(dest="fcmd", required=True)
    g = fsub.add_parser("gen"); g.add_argument("manifest"); g.add_argument("--team", required=True); g.set_defaults(fn=cmd_flag_gen)
    c = fsub.add_parser("check"); c.add_argument("manifest"); c.add_argument("--team", required=True); c.add_argument("flag"); c.set_defaults(fn=cmd_flag_check)

    s = sub.add_parser("score")
    s.add_argument("--manifests", nargs="+", required=True); s.add_argument("--submissions", required=True); s.add_argument("--out")
    s.set_defaults(fn=cmd_score)

    cp = sub.add_parser("compose"); cp.add_argument("manifest"); cp.add_argument("--out"); cp.add_argument("--port", type=int, default=8080)
    cp.set_defaults(fn=cmd_compose)

    cov = sub.add_parser("coverage")
    cov.add_argument("--techniques", required=True); cov.add_argument("--mark", nargs="*"); cov.add_argument("--out")
    cov.set_defaults(fn=cmd_coverage)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
