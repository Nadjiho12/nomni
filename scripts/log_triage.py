#!/usr/bin/env python3
"""Defensive log triage: find brute-force and scanning patterns in your own logs.

Supports:
  --type ssh    auth.log style lines ("Failed password for X from IP"); HIGH only when a successful login from the same IP
                FOLLOWS at least --threshold failures from it (log order matters); otherwise MEDIUM
  --type web    nginx/apache combined logs (flags 4xx floods and probe paths)

Usage:
  python log_triage.py --type ssh --file /var/log/auth.log --threshold 5
  python log_triage.py --type web --file access.log --threshold 30
  python log_triage.py --type ssh --file auth.log --json > report.json

Log lines must be in chronological order. Only analyze logs from systems you own or are authorized to review.
"""
import argparse
import collections
import json
import re
import sys

SSH_FAIL = re.compile(r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)")
SSH_OK = re.compile(r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)")
WEB = re.compile(r'^(?P<ip>\S+) \S+ \S+ \[[^\]]+\] "(?P<method>\S+) (?P<path>\S+)[^"]*" (?P<status>\d{3})')
PROBES = ("/.env", "/wp-login.php", "/phpmyadmin", "/.git/", "/admin", "/xmlrpc.php", "/etc/passwd", "/cgi-bin/")


def triage_ssh(lines, threshold):
    """Lines must be in chronological order (normal for syslog/auth.log).
    HIGH only if a successful login from the same IP occurs AFTER at least `threshold` failures from it."""
    fails = collections.Counter()
    users = collections.defaultdict(collections.Counter)
    success_after = {}      # ip -> (user, failures_before_success)
    success_before = set()  # ip had a success while below the threshold (earlier legitimate use)
    for line in lines:
        m = SSH_FAIL.search(line)
        if m:
            fails[m["ip"]] += 1
            users[m["ip"]][m["user"]] += 1
            continue
        m = SSH_OK.search(line)
        if m:
            ip = m["ip"]
            if fails[ip] >= threshold:
                success_after.setdefault(ip, (m["user"], fails[ip]))
            else:
                success_before.add(ip)
    findings = []
    for ip, n in fails.most_common():
        if n < threshold:
            continue
        f = {"ip": ip, "failures": n, "distinct_users": len(users[ip]), "top_users": users[ip].most_common(3)}
        if ip in success_after:
            user, nb = success_after[ip]
            f.update(severity="HIGH", note=f"successful login for '{user}' AFTER {nb} failed attempts from this IP: investigate as possible compromise")
        else:
            extra = "; a successful login from this IP appeared earlier, before the failures" if ip in success_before else ""
            f.update(severity="MEDIUM", note="repeated failed logins; no successful login from this IP after the failures" + extra)
        findings.append(f)
    return findings


def triage_web(lines, threshold):
    errs = collections.Counter()
    probes = collections.defaultdict(set)
    for line in lines:
        m = WEB.match(line)
        if not m:
            continue
        if m["status"].startswith("4"):
            errs[m["ip"]] += 1
        for p in PROBES:
            if p in m["path"]:
                probes[m["ip"]].add(p)
    findings = []
    for ip in set(errs) | set(probes):
        if errs[ip] >= threshold or probes[ip]:
            findings.append({"ip": ip, "client_errors": errs[ip], "probe_paths": sorted(probes[ip]),
                             "severity": "MEDIUM" if probes[ip] else "LOW",
                             "note": "probing sensitive paths" if probes[ip] else "high 4xx rate"})
    return sorted(findings, key=lambda f: (f["severity"] != "MEDIUM", -f["client_errors"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", choices=["ssh", "web"], required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--threshold", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.threshold < 1:
        sys.exit("error: --threshold must be >= 1")
    try:
        lines = open(a.file, encoding="utf-8", errors="replace").read().splitlines()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
    findings = triage_ssh(lines, a.threshold) if a.type == "ssh" else triage_web(lines, a.threshold)
    if a.json:
        print(json.dumps(findings, indent=2))
    else:
        print(f"{len(findings)} finding(s) in {len(lines)} lines")
        for f in findings:
            print(" ", f)
        if findings:
            if a.type == "ssh":
                print("Next: rate-limit or block offenders (fail2ban/firewall), enforce key-only SSH, review any HIGH item.")
            else:
                print("Next: rate-limit or block offenders (WAF/firewall), make sure probed paths are not exposed, review origin of 4xx floods.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
