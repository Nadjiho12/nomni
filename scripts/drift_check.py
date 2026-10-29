#!/usr/bin/env python3
"""Data drift check between a reference CSV (training/baseline) and a current CSV (live/new).

Numeric columns: PSI over reference quantile bins + KS statistic. Categorical columns: PSI over category frequencies.
Also reports missing-rate change. Thresholds (rules of thumb, verify for your data): PSI < 0.1 OK, 0.1-0.25 WATCH, > 0.25 ALERT.

  python drift_check.py reference.csv current.csv
  python drift_check.py reference.csv current.csv --bins 10 --json
Requires: pandas, numpy. Exit code 1 if any ALERT.
"""
import argparse
import json
import sys

try:
    import numpy as np
    import pandas as pd
except ImportError:          # --help still works; main() reports the missing dependency
    np = pd = None


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def read(path):
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        die(f"{path} not found")
    except pd.errors.EmptyDataError:
        die(f"{path} is empty (no columns)")
    except Exception as e:  # noqa: BLE001
        die(f"cannot parse {path}: {e}")
    if len(df) == 0:
        die(f"{path} has a header but no rows")
    return df


def psi(ref_p, cur_p, eps=1e-4):
    ref_p, cur_p = np.clip(ref_p, eps, None), np.clip(cur_p, eps, None)
    return float(np.sum((cur_p - ref_p) * np.log(cur_p / ref_p)))


def num_psi(ref, cur, bins):
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref)
    c = np.histogram(cur, edges)[0] / len(cur)
    return psi(r, c)


def ks(ref, cur):
    allv = np.sort(np.concatenate([ref, cur]))
    cdf = lambda x: np.searchsorted(np.sort(x), allv, side="right") / len(x)
    return float(np.max(np.abs(cdf(ref) - cdf(cur))))


def cat_psi(ref, cur):
    cats = sorted(set(ref.astype(str)) | set(cur.astype(str)))
    r = ref.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0).values
    c = cur.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0).values
    return psi(r, c)


def status(v):
    return "ALERT" if v > .25 else "WATCH" if v > .1 else "OK"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("current")
    ap.add_argument("--bins", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if pd is None:
        print("error: drift_check needs pandas and numpy: pip install pandas numpy", file=sys.stderr)
        sys.exit(3)
    if a.bins < 2:
        die("--bins must be >= 2")
    ref, cur = read(a.reference), read(a.current)
    rows = []
    for col in ref.columns:
        if col not in cur.columns:
            rows.append({"column": col, "type": "-", "psi": None, "ks": None, "missing_delta": None, "status": "ALERT", "note": "column missing in current data"})
            continue
        r, c = ref[col], cur[col]
        md = float(c.isna().mean() - r.isna().mean())
        if pd.api.types.is_numeric_dtype(r):
            rv, cv = r.dropna().to_numpy(float), c.dropna().to_numpy(float)
            if len(rv) == 0 or len(cv) == 0:
                continue
            p, k = num_psi(rv, cv, a.bins), ks(rv, cv)
            rows.append({"column": col, "type": "num", "psi": round(p, 4), "ks": round(k, 3), "missing_delta": round(md, 3), "status": status(p), "note": ""})
        else:
            p = cat_psi(r.dropna(), c.dropna())
            rows.append({"column": col, "type": "cat", "psi": round(p, 4), "ks": None, "missing_delta": round(md, 3), "status": status(p), "note": ""})
        if abs(md) > .05:
            rows[-1]["note"] = "missing rate changed by more than 5 points"
            if rows[-1]["status"] == "OK":
                rows[-1]["status"] = "WATCH"
    new = [c for c in cur.columns if c not in ref.columns]
    if a.json:
        print(json.dumps({"columns": rows, "new_columns": new}, indent=1))
    else:
        print(f"{'column':<18}{'type':<5}{'PSI':>8}{'KS':>7}{'miss+':>8}  status  note")
        for r in rows:
            print(f"{r['column']:<18}{r['type']:<5}{str(r['psi']):>8}{str(r['ks']):>7}{str(r['missing_delta']):>8}  {r['status']:<6}  {r['note']}")
        if new:
            print("new columns not in reference:", ", ".join(new))
        print("Thresholds are rules of thumb. Confirm drift matters by checking model performance on recent labeled data.")
    sys.exit(1 if any(r["status"] == "ALERT" for r in rows) else 0)


if __name__ == "__main__":
    main()
