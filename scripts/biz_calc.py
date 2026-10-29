#!/usr/bin/env python3
"""Business and decision calculators (no dependencies).

Subcommands:
  rice       Rank ideas by RICE = reach * impact * confidence / effort
  risk       Score a risk register (likelihood x impact) and rank it
  unit       Unit economics: LTV, LTV:CAC, payback, with +/-30% sensitivity
  breakeven  Break-even units and revenue
  runway     Months of cash left
  matrix     Weighted decision matrix
  pricing    Compare price points: conversion (via assumed elasticity), CAC, LTV, 12-month profit
  forecast   Monthly subscription forecast: customers, MRR, costs, cash balance, break-even month

CSV formats (header row required):
  rice:   name,reach,impact,confidence,effort        confidence 0-1 (or 0-100), effort in person-weeks
  risk:   risk,likelihood,impact,mitigation          likelihood and impact 1-5
  matrix: option,<criterion1>,<criterion2>,...       scores 1-5, higher is better (invert cost-like criteria first)

Examples:
  python biz_calc.py rice --file ideas.csv
  python biz_calc.py risk --file risks.csv
  python biz_calc.py unit --arpu 12 --gross-margin 0.8 --churn 0.05 --cac 40
  python biz_calc.py breakeven --fixed 3000 --price 25 --variable 6
  python biz_calc.py runway --cash 20000 --burn 3500
  python biz_calc.py forecast --months 12 --new-per-month 20 --growth 0.05 --churn 0.05 --arpu 12 --gross-margin 0.85 --fixed 800 --cac 25 --cash 3000
  python biz_calc.py matrix --file options.csv --weights "cost=3,speed=2,fit=5"
  python biz_calc.py pricing --prices 5,9,15,19 --base-price 9 --base-conv 0.01 --visitors 2000 \
      --ad-spend 300 --cpc 0.8 --churn 0.08 --gross-margin 0.9 --elasticity -1.0
Every output number is only as good as its inputs: label assumptions.
"""
import argparse
import csv
import math
import sys


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"error: {path} has no data rows (expected a header row plus at least one row)")
    return rows


def table(rows, headers):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h)) for i, h in enumerate(headers)]
    line = "  ".join(str(h).ljust(w) for h, w in zip(headers, widths))  # noqa: B905 - built together, always equal length (Python 3.9+ target)
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))  # noqa: B905 - rows are constructed with one value per header


def cmd_rice(a):
    out = []
    for r in read_rows(a.file):
        conf = float(r["confidence"])
        conf = conf / 100 if conf > 1 else conf
        effort = float(r["effort"])
        if effort <= 0:
            sys.exit(f"error: effort must be > 0 for '{r['name']}'")
        score = float(r["reach"]) * float(r["impact"]) * conf / effort
        out.append((r["name"], r["reach"], r["impact"], f"{conf:.2f}", r["effort"], round(score, 2)))
    out.sort(key=lambda x: -x[5])
    table([(i + 1, *o) for i, o in enumerate(out)], ["#", "name", "reach", "impact", "conf", "effort", "RICE"])
    if out:
        print(f"\nTop: {out[0][0]}. Low-confidence items (conf < 0.5) deserve a cheap test before building.")


def level(score):
    return "CRITICAL" if score >= 15 else "HIGH" if score >= 10 else "MEDIUM" if score >= 5 else "LOW"


def cmd_risk(a):
    out = []
    for r in read_rows(a.file):
        l, i = int(r["likelihood"]), int(r["impact"])
        if not (1 <= l <= 5 and 1 <= i <= 5):
            sys.exit(f"error: likelihood/impact must be 1-5 for '{r['risk']}'")
        out.append((r["risk"], l, i, l * i, level(l * i), r.get("mitigation", "")))
    out.sort(key=lambda x: -x[3])
    table([(i + 1, *o) for i, o in enumerate(out)], ["#", "risk", "L", "I", "score", "level", "mitigation"])
    crit = [o for o in out if o[4] in ("CRITICAL", "HIGH")]
    print(f"\n{len(crit)} high/critical risk(s). Each needs an owner, an early-warning trigger, and a contingency.")


def ltv_calc(arpu, gm, churn, cac):
    ltv = arpu * gm / churn
    return ltv, ltv / cac, cac / (arpu * gm)


def cmd_unit(a):
    if a.churn <= 0 or a.cac <= 0 or a.arpu <= 0 or a.gross_margin <= 0:
        sys.exit("error: arpu, gross-margin, churn, cac must all be > 0")
    ltv, ratio, payback = ltv_calc(a.arpu, a.gross_margin, a.churn, a.cac)
    print(f"LTV              {ltv:,.2f}")
    print(f"LTV:CAC          {ratio:.2f}   (rule of thumb >= 3; verify for your model)")
    print(f"CAC payback      {payback:.1f} months   (rule of thumb < 12; verify)")
    print(f"Customer lifetime ~{1 / a.churn:.1f} months")
    print("Sensitivity (churn and CAC each +/-30%):")
    rows = []
    for cm in (0.7, 1.0, 1.3):
        for km in (0.7, 1.0, 1.3):
            l, r, p = ltv_calc(a.arpu, a.gross_margin, a.churn * cm, a.cac * km)
            rows.append((f"{cm:.1f}x", f"{km:.1f}x", f"{r:.2f}", f"{p:.1f}"))
    table(rows, ["churn", "CAC", "LTV:CAC", "payback_mo"])
    if ratio < 3 or payback > 12:
        print("Flag: economics are weak under these inputs; test price, churn drivers, or cheaper channels before scaling spend.")


def cmd_breakeven(a):
    margin = a.price - a.variable
    if margin <= 0:
        sys.exit("error: price must exceed variable cost per unit")
    units = (a.fixed + a.target_profit) / margin
    print(f"Contribution margin/unit  {margin:,.2f}")
    print(f"Break-even units          {math.ceil(units):,}")
    print(f"Break-even revenue        {math.ceil(units) * a.price:,.2f}")


def cmd_runway(a):
    if a.burn <= 0:
        sys.exit("error: burn must be > 0")
    m = a.cash / a.burn
    print(f"Runway: {m:.1f} months at a burn of {a.burn:,.2f}/month")
    if m < 6:
        print("Flag: under 6 months. Cut burn or secure revenue/funding now; decisions get worse as runway shrinks.")


def cmd_matrix(a):
    weights = {}
    for part in a.weights.split(","):
        k, v = part.split("=")
        weights[k.strip()] = float(v)
    total = sum(weights.values())
    out = []
    for r in read_rows(a.file):
        missing = [c for c in weights if c not in r]
        if missing:
            sys.exit(f"error: criteria not in CSV header: {missing}")
        s = sum(float(r[c]) * w for c, w in weights.items()) / total
        out.append((r["option"], round(s, 2), *(r[c] for c in weights)))
    out.sort(key=lambda x: -x[1])
    table([(i + 1, *o) for i, o in enumerate(out)], ["#", "option", "weighted(1-5)", *weights.keys()])
    if len(out) > 1 and out[0][1] - out[1][1] <= 0.3 + 1e-9:
        print("\nNote: top two are within 0.3. Treat as a tie and decide on reversibility, risk, or a cheap test.")


def cmd_pricing(a):
    prices = [float(x) for x in a.prices.split(",")]
    if a.churn <= 0 or a.base_price <= 0 or a.base_conv <= 0 or a.cpc <= 0 or min(prices) <= 0 or a.gross_margin <= 0:
        sys.exit("error: churn, base-price, base-conv, cpc, gross-margin and every price must be > 0")
    if a.elasticity > 0:
        sys.exit("error: elasticity must be <= 0 (higher price should not raise conversion)")
    paid_visitors = a.ad_spend / a.cpc if a.cpc > 0 else 0
    print(f"Assumptions: base price {a.base_price}, base conversion {a.base_conv:.2%}, elasticity {a.elasticity}, "
          f"organic visitors {a.visitors:.0f}, ad spend {a.ad_spend:.0f} at CPC {a.cpc} -> {paid_visitors:.0f} paid visitors, "
          f"churn {a.churn:.0%}, gross margin {a.gross_margin:.0%}")
    rows = []
    for p in prices:
        conv = min(1.0, a.base_conv * (p / a.base_price) ** a.elasticity)
        org_new, paid_new = a.visitors * conv, paid_visitors * conv
        cac = a.ad_spend / paid_new if paid_new > 0 else float("inf")
        ltv = p * a.gross_margin / a.churn
        payback = cac / (p * a.gross_margin) if cac != float("inf") else float("inf")
        active, profit = 0.0, 0.0
        for _ in range(12):
            active = active * (1 - a.churn) + org_new + paid_new
            profit += active * p * a.gross_margin - a.ad_spend
        rows.append((f"{p:g}", f"{conv:.2%}", f"{org_new + paid_new:.1f}", f"{cac:.0f}", f"{ltv:.0f}", f"{ltv / cac:.2f}" if cac else "n/a",
                     f"{payback:.1f}", f"{profit:,.0f}"))
    table(rows, ["price", "conv", "new/mo", "paid_CAC", "LTV", "LTV:CAC", "payback_mo", "12mo_profit_after_ads"])
    profits = sorted(((float(r[7].replace(",", "")), r[0]) for r in rows), reverse=True)
    if len(profits) > 1 and profits[0][0] - profits[1][0] <= 0.01 * abs(profits[0][0]):
        print("\nNo clear winner: profits are within 1%. At this elasticity the price change is revenue-neutral, so the answer depends on whether "
              "real elasticity is above or below this value. Rerun with -0.5 and -1.5, then run a real price test.")
    else:
        print(f"\nHighest 12-month profit under these assumptions: price {profits[0][1]}. Elasticity is the weakest input: rerun with -0.5 and -1.5, "
              "then run a real price test (new visitors see different prices) before changing anything.")


def cmd_forecast(a):
    cust, cash, rows, be, broke = a.start_customers, a.cash, [], None, None
    low = (a.cash, 0)
    for m in range(1, a.months + 1):
        new = a.new_per_month * (1 + a.growth) ** (m - 1)
        lost = cust * a.churn
        cust = cust - lost + new
        mrr = cust * a.arpu
        gp = mrr * a.gross_margin
        spend = new * a.cac
        net = gp - spend - a.fixed
        cash += net
        if cash < low[0]:
            low = (cash, m)
        if be is None and net >= 0:
            be = m
        if broke is None and cash < 0:
            broke = m
        rows.append((m, f"{new:.1f}", f"{cust:.0f}", f"{mrr:,.0f}", f"{gp:,.0f}", f"{spend:,.0f}", f"{a.fixed:,.0f}", f"{net:,.0f}", f"{cash:,.0f}"))
    table(rows, ["month", "new", "customers", "MRR", "gross_profit", "acq_spend", "fixed", "net_cash", "cash_balance"])
    print(f"\nMonthly net cash flow turns positive: {'month ' + str(be) if be else 'not within ' + str(a.months) + ' months'}.")
    print(f"Lowest cash balance: {low[0]:,.0f} at month {low[1]}" + (" (funding or savings needed to bridge this gap)." if low[0] < 0 else "."))
    print(f"Cash runs out: {'month ' + str(broke) + '. Reduce fixed cost or CAC, raise price, or secure funding before then.' if broke else 'not within the horizon.'}")
    print("Steady-state customers if growth stopped: new_per_month/churn = %.0f. Every input is an assumption: rerun with worse churn and CAC." % (a.new_per_month / a.churn if a.churn else float('inf')))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("rice", cmd_rice), ("risk", cmd_risk)):
        p = sub.add_parser(name); p.add_argument("--file", required=True); p.set_defaults(fn=fn)
    p = sub.add_parser("unit")
    for k in ("arpu", "gross-margin", "churn", "cac"):
        p.add_argument(f"--{k}", type=float, required=True)
    p.set_defaults(fn=cmd_unit)
    p = sub.add_parser("breakeven")
    p.add_argument("--fixed", type=float, required=True); p.add_argument("--price", type=float, required=True)
    p.add_argument("--variable", type=float, default=0.0); p.add_argument("--target-profit", type=float, default=0.0)
    p.set_defaults(fn=cmd_breakeven)
    p = sub.add_parser("runway"); p.add_argument("--cash", type=float, required=True); p.add_argument("--burn", type=float, required=True); p.set_defaults(fn=cmd_runway)
    p = sub.add_parser("pricing")
    p.add_argument("--prices", required=True, help="comma-separated price points")
    p.add_argument("--base-price", type=float, required=True); p.add_argument("--base-conv", type=float, required=True, help="visitor->paid conversion at base price (0.01 = 1%%)")
    p.add_argument("--visitors", type=float, required=True, help="organic visitors per month")
    p.add_argument("--ad-spend", type=float, default=0.0); p.add_argument("--cpc", type=float, default=0.8)
    p.add_argument("--churn", type=float, required=True); p.add_argument("--gross-margin", type=float, default=0.9)
    p.add_argument("--elasticity", type=float, default=-1.0, help="conversion ~ (price/base)^elasticity; assumption, keep <= 0")
    p.set_defaults(fn=cmd_pricing)
    p = sub.add_parser("forecast")
    p.add_argument("--months", type=int, default=12); p.add_argument("--start-customers", type=float, default=0.0)
    p.add_argument("--new-per-month", type=float, required=True); p.add_argument("--growth", type=float, default=0.0, help="monthly growth of new customers (0.05 = 5%%)")
    p.add_argument("--churn", type=float, required=True); p.add_argument("--arpu", type=float, required=True)
    p.add_argument("--gross-margin", type=float, default=0.85); p.add_argument("--fixed", type=float, default=0.0)
    p.add_argument("--cac", type=float, default=0.0); p.add_argument("--cash", type=float, default=0.0)
    p.set_defaults(fn=cmd_forecast)
    p = sub.add_parser("matrix"); p.add_argument("--file", required=True); p.add_argument("--weights", required=True); p.set_defaults(fn=cmd_matrix)
    a = ap.parse_args()
    try:
        a.fn(a)
    except (KeyError, ValueError, FileNotFoundError) as e:
        sys.exit(f"error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
