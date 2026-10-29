#!/usr/bin/env python3
"""Idle / tycoon economy simulator.

Simulates a player who always buys the generator with the best payback time
and reports when milestones are reached. Use it to balance cost curves BEFORE
shipping numbers into a game.

Usage:
  python economy_sim.py                      # built-in 5-tier example
  python economy_sim.py --config game.json   # your own tiers
  python economy_sim.py --hours 6 --milestones 1e3 1e6 1e9

Config JSON:
{
  "start_money": 10,
  "click_income": 1,
  "tiers": [
    {"name": "Lemonade", "base_cost": 10,   "growth": 1.10, "income": 0.5},
    {"name": "Cart",     "base_cost": 150,  "growth": 1.12, "income": 6}
  ]
}
"""
import argparse
import json
import sys

DEFAULT = {
    "start_money": 10,
    "click_income": 1,
    "tiers": [
        {"name": "Lemonade", "base_cost": 10, "growth": 1.10, "income": 0.5},
        {"name": "Cart", "base_cost": 150, "growth": 1.12, "income": 6},
        {"name": "Shop", "base_cost": 2200, "growth": 1.13, "income": 70},
        {"name": "Factory", "base_cost": 35000, "growth": 1.14, "income": 900},
        {"name": "Empire", "base_cost": 600000, "growth": 1.15, "income": 14000},
    ],
}


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def load_config(path):
    if not path:
        return DEFAULT
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    except ValueError as e:
        die(f"{path} is not valid JSON: {e}")
    tiers = cfg.get("tiers") if isinstance(cfg, dict) else None
    if not isinstance(tiers, list) or not tiers:
        die("config needs a non-empty 'tiers' list")
    for i, t in enumerate(tiers):
        if not isinstance(t, dict):
            die(f"tier {i} must be an object")
        for k in ("name", "base_cost", "growth", "income"):
            if k not in t:
                die(f"tier {i} is missing '{k}'")
        if not (num(t["base_cost"]) and num(t["growth"]) and num(t["income"])):
            die(f"tier '{t['name']}': base_cost, growth, income must be numbers")
        if t["base_cost"] <= 0 or t["income"] <= 0:
            die(f"tier '{t['name']}': base_cost and income must be > 0")
        if t["growth"] < 1:
            die(f"tier '{t['name']}': growth must be >= 1.0 (cost multiplier per unit owned)")
    for k in ("start_money", "click_income"):
        if k in cfg and (not num(cfg[k]) or cfg[k] < 0):
            die(f"'{k}' must be a number >= 0")
    return cfg


def fmt(x):
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if x >= size:
            return f"{x / size:.2f}{unit}"
    return f"{x:.1f}"


def simulate(cfg, hours, milestones, clicks_per_sec):
    tiers = cfg["tiers"]
    owned = [0] * len(tiers)
    money = float(cfg.get("start_money", 0))
    total = money
    t = 0.0
    dt = 1.0
    end = hours * 3600
    hit = {}
    pending = sorted(milestones)
    log = []
    while t < end and pending:
        income = cfg.get("click_income", 0) * clicks_per_sec + sum(
            o * tr["income"] for o, tr in zip(owned, tiers)  # noqa: B905 - owned has one entry per tier by construction
        )
        money += income * dt
        total += income * dt
        t += dt
        # buy best payback while affordable
        while True:
            best, best_payback = None, None
            for i, tr in enumerate(tiers):
                cost = tr["base_cost"] * tr["growth"] ** owned[i]
                if cost <= money:
                    payback = cost / tr["income"]
                    if best is None or payback < best_payback:
                        best, best_payback = i, payback
            if best is None:
                break
            cost = tiers[best]["base_cost"] * tiers[best]["growth"] ** owned[best]
            money -= cost
            owned[best] += 1
            if owned[best] == 1:
                log.append((t, f"first {tiers[best]['name']}"))
        while pending and total >= pending[0]:
            hit[pending[0]] = t
            pending.pop(0)
    return hit, log, owned, total, t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config")
    ap.add_argument("--hours", type=float, default=4)
    ap.add_argument("--milestones", type=float, nargs="*", default=[1e3, 1e4, 1e5, 1e6, 1e7, 1e8])
    ap.add_argument("--clicks-per-sec", type=float, default=2)
    a = ap.parse_args()
    if a.hours <= 0:
        die("--hours must be > 0")
    if a.clicks_per_sec < 0:
        die("--clicks-per-sec must be >= 0")
    if any(m <= 0 for m in a.milestones):
        die("--milestones must all be > 0")
    cfg = load_config(a.config)
    hit, log, owned, total, t = simulate(cfg, a.hours, a.milestones, a.clicks_per_sec)
    print("== First purchases ==")
    for when, what in log:
        print(f"  {when/60:7.1f} min  {what}")
    print("== Milestones (total earned) ==")
    for m in sorted(a.milestones):
        if m in hit:
            print(f"  {fmt(m):>8}  reached at {hit[m]/60:7.1f} min")
        else:
            print(f"  {fmt(m):>8}  NOT reached in {a.hours} h  <- tune growth/income")
    print("== End state ==")
    print("  owned:", {tr["name"]: n for tr, n in zip(cfg["tiers"], owned)})  # noqa: B905 - same
    print(f"  total earned: {fmt(total)} after {t/60:.1f} min simulated")


if __name__ == "__main__":
    main()
