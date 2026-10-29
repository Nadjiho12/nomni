#!/usr/bin/env python3
"""Prose linter: objective signals for human-sounding, clear writing (no dependencies).

Reports sentence-length variety, repeated sentence openers, stock/AI-flavored phrases, filler words,
adverb and passive-voice density, long sentences, and a readability score. Heuristics, not truth:
use them to find places to look, then edit by ear.

  python writing_lint.py draft.txt
  python writing_lint.py draft.md --json
  cat draft.txt | python writing_lint.py -
"""
import argparse
import json
import re
import statistics
import sys

STOCK = [
    "in today's fast-paced", "in today's digital", "it's important to note", "it is important to note", "it's worth noting",
    "delve", "tapestry", "game-changer", "game changer", "unlock the power", "navigate the complexities", "in the realm of",
    "a testament to", "rich tapestry", "ever-evolving", "ever-changing landscape", "at the end of the day", "cutting-edge",
    "seamless", "robust solution", "leverage", "synergy", "paradigm shift", "revolutionize", "elevate your", "dive into",
    "embark on", "harness the power", "i hope this message finds you well", "touch base", "circle back", "moving forward",
    "in conclusion,", "overall,", "ultimately,", "not just", "more than just",
]
FILLER = ["very", "really", "just", "actually", "basically", "literally", "quite", "somewhat", "perhaps", "simply", "totally", "absolutely"]
PASSIVE = re.compile(r"\b(am|is|are|was|were|be|been|being)\s+(\w+ed|written|made|done|given|taken|shown|known|seen|built|found)\b", re.I)


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", re.sub(r"\s+", " ", text.strip()))
    return [p for p in parts if len(p.split()) > 0]


def syllables(w):
    w = w.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def analyze(text):
    sents = sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    lens = [len(re.findall(r"[A-Za-z']+", s)) for s in sents]
    lower = text.lower()
    out = {"words": len(words), "sentences": len(sents), "paragraphs": len([p for p in re.split(r"\n\s*\n", text) if p.strip()])}
    if not sents or not words:
        return out, []
    avg = sum(lens) / len(lens)
    sd = statistics.pstdev(lens) if len(lens) > 1 else 0
    out.update(avg_sentence_words=round(avg, 1), sentence_length_stdev=round(sd, 1), longest_sentence=max(lens))
    syl = sum(syllables(w) for w in words)
    out["flesch_reading_ease"] = round(206.835 - 1.015 * avg - 84.6 * syl / len(words), 1)
    starts = [s.split()[0].lower().strip("\"'(") for s in sents]
    rep = {w: starts.count(w) for w in set(starts) if starts.count(w) >= 3 and starts.count(w) / len(starts) > .15}
    stock = [(p, lower.count(p)) for p in STOCK if p in lower]
    filler = {f: len(re.findall(rf"\b{f}\b", lower)) for f in FILLER}
    filler = {k: v for k, v in filler.items() if v}
    ly = len([w for w in words if w.lower().endswith("ly") and len(w) > 4])
    passive = len(PASSIVE.findall(text))
    out.update(adverb_ly_per_100=round(100 * ly / len(words), 1), passive_per_100_sentences=round(100 * passive / len(sents)), filler_words=sum(filler.values()), stock_phrases=sum(c for _, c in stock))
    issues = []
    if len(sents) >= 6 and sd < 4:
        issues.append(("rhythm", f"sentence lengths are very uniform (stdev {sd:.1f}); mix short and long sentences"))
    if rep:
        issues.append(("openers", "repeated sentence openers: " + ", ".join(f"'{k}' x{v}" for k, v in rep.items())))
    for p, c in stock:
        issues.append(("stock", f"'{p}' x{c}: replace with something specific"))
    if filler:
        issues.append(("filler", "filler words: " + ", ".join(f"{k} x{v}" for k, v in filler.items())))
    if ly / len(words) > .04:
        issues.append(("adverbs", f"{100 * ly / len(words):.1f} -ly words per 100: prefer stronger verbs"))
    if passive / len(sents) > .25:
        issues.append(("passive", f"passive voice in about {100 * passive / len(sents):.0f}% of sentences: name the actor"))
    for s, n in zip(sents, lens):  # noqa: B905 - lens is a list comprehension over sents, same length
        if n > 35:
            issues.append(("long", f"{n}-word sentence: {s[:70]}..."))
    if out["flesch_reading_ease"] < 30:
        issues.append(("readability", f"Flesch {out['flesch_reading_ease']}: very dense; shorten sentences and words (fine only for expert audiences)"))
    if len(re.findall(r"—", text)) / max(1, len(sents)) > .3:
        issues.append(("dashes", "heavy em-dash use"))
    if len(re.findall(r"\bnot (?:just|only|merely)\b.{0,60}\bbut\b", lower)) >= 2:
        issues.append(("pattern", "repeated 'not just X but Y' construction"))
    return out, issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.file == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(a.file, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            print(f"error: cannot read {a.file}: {e.strerror}", file=sys.stderr)
            sys.exit(2)
    stats, issues = analyze(text)
    if a.json:
        print(json.dumps({"stats": stats, "issues": issues}, indent=1))
    else:
        print("stats:", ", ".join(f"{k}={v}" for k, v in stats.items()))
        for k, m in issues:
            print(f"  [{k}] {m}")
        print(f"{len(issues)} flag(s). Heuristics only: read it aloud and keep what sounds right." if issues else "No flags. Read it aloud once anyway.")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # e.g. piped into `head` or `grep -q`
        sys.exit(0)
