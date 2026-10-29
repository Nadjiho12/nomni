#!/usr/bin/env python3
"""CVSS v3.1 base score calculator for vulnerability REPORTING and prioritization (defensive; no dependencies).

  python cvss_calc.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"      # -> 9.8 Critical
  python cvss_calc.py AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N                  # prefix optional
  python cvss_calc.py --json "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H"

Metrics: AV (N,A,L,P) AC (L,H) PR (N,L,H) UI (N,R) S (U,C) C/I/A (H,L,N). Formulas follow the FIRST CVSS v3.1 specification.
Use it to score findings from authorized assessments and to rank remediation. Scores are a starting point: add business context.
"""
import argparse
import json
import math
import sys

AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
AC = {"L": 0.77, "H": 0.44}
PR_U = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_C = {"N": 0.85, "L": 0.68, "H": 0.5}
UI = {"N": 0.85, "R": 0.62}
CIA = {"H": 0.56, "L": 0.22, "N": 0.0}


def roundup(x):
    i = int(round(x * 100000))
    return i / 100000.0 if i % 10000 == 0 else (math.floor(i / 10000) + 1) / 10.0


def parse(vec):
    parts = [p for p in vec.strip().split("/") if p]
    if parts and parts[0].upper().startswith("CVSS:"):
        if parts[0].upper() != "CVSS:3.1" and parts[0].upper() != "CVSS:3.0":
            raise ValueError(f"unsupported version {parts[0]} (this tool implements v3.0/v3.1 base metrics)")
        parts = parts[1:]
    m = {}
    for p in parts:
        if ":" not in p:
            raise ValueError(f"bad metric '{p}'")
        k, v = p.split(":", 1)
        m[k.upper()] = v.upper()
    need = {"AV": AV, "AC": AC, "PR": PR_U, "UI": UI, "S": {"U": 0, "C": 0}, "C": CIA, "I": CIA, "A": CIA}
    for k, allowed in need.items():
        if k not in m:
            raise ValueError(f"missing metric {k}")
        if m[k] not in allowed:
            raise ValueError(f"invalid value {m[k]} for {k} (allowed: {','.join(allowed)})")
    return m


def score(m):
    changed = m["S"] == "C"
    iss = 1 - (1 - CIA[m["C"]]) * (1 - CIA[m["I"]]) * (1 - CIA[m["A"]])
    impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15 if changed else 6.42 * iss
    pr = (PR_C if changed else PR_U)[m["PR"]]
    expl = 8.22 * AV[m["AV"]] * AC[m["AC"]] * pr * UI[m["UI"]]
    if impact <= 0:
        base = 0.0
    elif changed:
        base = roundup(min(1.08 * (impact + expl), 10))
    else:
        base = roundup(min(impact + expl, 10))
    sev = "None" if base == 0 else "Low" if base < 4 else "Medium" if base < 7 else "High" if base < 9 else "Critical"
    return base, sev, round(impact, 1), round(expl, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vector")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        m = parse(a.vector)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
    base, sev, imp, expl = score(m)
    if a.json:
        print(json.dumps({"vector": a.vector, "base_score": base, "severity": sev, "impact_subscore": imp, "exploitability_subscore": expl}))
    else:
        print(f"CVSS v3.1 base score {base} ({sev})   impact {imp}, exploitability {expl}")
        print("Add context: asset value, exposure, compensating controls, exploit maturity. Prioritize remediation by risk, not score alone.")


if __name__ == "__main__":
    main()
