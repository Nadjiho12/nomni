#!/usr/bin/env python3
"""Router check: which reference file does a request map to? Scores a prompt against the SKILL.md router table (BM25, no dependencies).

  python route_check.py "build a RAG chatbot over my PDFs"
  python route_check.py "my print keeps warping" --top 5 --explain
  python route_check.py --list                    # show the parsed router rows
It tests the VOCABULARY of the router table (does the table text contain the words people use?), not how a model reads it.
A prompt that scores 0 for every row has no vocabulary overlap: add its words to the right router row.
tests/test_router.py runs a corpus of sample prompts through this and fails if routing accuracy drops.
"""
import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set("a an the of to in on for and or is are was were be by with as at it this that from how do i you my me what when where which can should would about into your our we they them".split())


def stem(w):
    for suf in ("ations", "ation", "ings", "ing", "ies", "ied", "es", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            base = w[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
            if suf in ("ing", "ings", "ed") and len(base) > 3 and base[-1] == base[-2] and base[-1] not in "aeiouls":
                base = base[:-1]                       # overfitting -> overfit, planning -> plan
            return base
    return w


# Query expansion: everyday words mapped to the vocabulary the reference files use. Generic domain knowledge, not per-prompt tuning.
SYNONYMS = {
    "slow": "performance cache speed", "lag": "performance latency multiplayer", "laggy": "performance latency", "fast": "performance speed", "speed": "performance",
    "phone": "mobile android ios app", "iphone": "mobile ios", "ios": "mobile app", "android": "mobile apk", "tablet": "mobile",
    "signup": "registration login auth password session", "register": "registration auth login", "account": "auth login session", "password": "auth hashing login",
    "website": "web site frontend page", "webpage": "web frontend", "site": "web website",
    "enemy": "ai enemy pathfinding", "zombie": "enemy ai pathfinding game", "npc": "ai enemy game", "chase": "pathfinding enemy ai steering", "obstacle": "pathfinding collision",
    "sfx": "sound audio effect", "footstep": "sound audio effect", "music": "audio chiptune", "sound": "audio sfx",
    "print": "3d printing fdm", "printer": "3d printing", "printable": "3d printing stl", "stand": "3d printing design", "model": "cad design mesh machine learning",
    "excel": "spreadsheet formula model", "sheet": "spreadsheet", "spreadsheet": "excel formula model", "total": "formula check spreadsheet",
    "money": "cash finance runway budget", "cash": "finance runway forecast", "spend": "budget cost finance", "ads": "marketing paid channel budget", "budget": "finance forecast",
    "customer": "marketing go-to-market sales acquisition", "customers": "marketing go-to-market", "pricing": "price marketing saas", "subscription": "saas pricing business model",
    "agent": "agent llm tool", "assistant": "llm agent voice tool", "chatbot": "llm rag conversation", "wiki": "document rag retrieval", "pdf": "document rag ocr", "document": "rag retrieval chunking",
    "semantic": "embedding retrieval rag vector", "embed": "embedding retrieval vector rag", "search": "retrieval rag index",
    "reward": "reinforcement learning policy", "learn": "machine learning training", "overfit": "machine learning validation regularization",
    "photo": "vision image detection ocr", "image": "vision detection ocr", "camera": "vision video detection", "picture": "vision image", "plate": "ocr vision",
    "container": "docker virtualization isolation", "gpu": "container docker virtualization", "isolate": "sandbox virtualization isolation vm", "sandbox": "isolation virtualization",
    "novel": "fiction chapter story outline", "chapter": "fiction novel story", "thriller": "fiction novel story character", "antagonist": "fiction character story", "story": "fiction novel",
    "newsletter": "writing style email voice", "paragraph": "writing style voice edit", "natural": "human voice writing style", "email": "writing style professional", "blog": "writing style",
    "idea": "ideas brainstorming unique startup", "brainstorm": "ideas unique", "unusual": "unique ideas creative", "creative": "ideas unique", "startup": "business ideas strategy",
    "rewrite": "refactor senior design review", "refactor": "senior review design tradeoff", "senior": "senior review trade-off design",
    "parallel": "subagent agentic specialist delegate", "specialist": "agentic subagent role", "delegate": "subagent agentic",
    "sensor": "embedded arduino iot", "humidity": "sensor embedded arduino", "temperature": "sensor embedded arduino", "motion": "sensor embedded raspberry", "display": "embedded arduino screen",
    "speech": "voice asr tts", "voice": "speech asr tts latency", "recognizer": "asr speech voice", "talk": "voice speech", "noisy": "noise audio voice asr", "call": "telephony voice phone",
    "test": "testing ci verify", "tests": "testing ci", "ci": "devops testing github-actions", "crash": "verify testing debug", "testable": "testing verify simulation", "repo": "git ci testing",
    "spec": "prd planning requirements", "milestone": "plan planning roadmap", "criterion": "acceptance planning prd", "plan": "planning prd roadmap",
    "monolith": "architecture microservices design", "microservice": "architecture design", "architecture": "design nfr adr system",
    "dataset": "data pipeline versioning mlops", "version": "pipeline mlops registry", "retrain": "mlops pipeline drift",
    "hacker": "security", "ssh": "security hardening logs", "guessing": "brute force logs security", "pentest": "penetration test assessment security report", "finding": "report vulnerability assessment",
    "analytics": "telemetry metrics production", "track": "telemetry analytics", "player": "game multiplayer", "players": "game multiplayer", "websocket": "multiplayer netcode realtime",
    "clicker": "idle incremental game economy", "upgrade": "idle economy progression", "offline": "idle progress", "hit": "shooter game", "recoil": "shooter weapon game", "fps": "shooter game",
    "lowpoly": "blender model mesh", "low-poly": "blender model mesh", "export": "build release", "ship": "release build publish",
    "backup": "automation script cron", "rename": "automation script files", "folder": "automation files script", "nightly": "cron schedule automation",
    "welcome": "bot discord", "member": "bot discord", "slack": "bot",
}


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def doc_vocabulary(path):
    """Title, the scope paragraph, and all headings of a reference file."""
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return ""
    out, para = [], 0
    for i, l in enumerate(lines):
        if l.startswith("#"):
            out.append(re.sub(r"^#+\s*\d*\.?\s*", "", l))
        elif 0 < i < 8 and l.strip() and para < 3:
            out.append(l)
            para += 1
    return " ".join(out)


def router_rows(skill_path=None):
    path = skill_path or os.path.join(ROOT, "SKILL.md")
    text = open(path, encoding="utf-8").read()
    start = text.index("## Domain router")
    end = text.index("\n## ", start + 5)
    rows = []
    for line in text[start:end].splitlines():
        m = re.match(r"^\|\s*(.+?)\s*\|\s*`(references/[^`]+)`\s*\|\s*$", line)
        if m:
            rel = m.group(2)
            words = rel.replace("references/", "").replace("/", " ").replace("-", " ").replace(".md", "")
            doc = doc_vocabulary(os.path.join(os.path.dirname(path), rel))
            # router text counts three times; the reference's own title, scope and headings add generalizing vocabulary
            rows.append({"file": rel, "desc": m.group(1), "tokens": tokens(m.group(1) + " " + words) * 3 + tokens(doc)})
    return rows


class BM25:
    def __init__(self, rows, k1=1.2, b=0.75):
        self.rows, self.k1, self.b = rows, k1, b
        self.avg = sum(len(r["tokens"]) for r in rows) / max(1, len(rows))
        df = {}
        for r in rows:
            for t in set(r["tokens"]):
                df[t] = df.get(t, 0) + 1
        n = len(rows)
        self.idf = {t: math.log(1 + (n - c + .5) / (c + .5)) for t, c in df.items()}

    def score(self, query):
        q = tokens(query)
        extra = []
        for t in q:
            extra += tokens(SYNONYMS.get(t, "")) if t in SYNONYMS else []
        q = q + extra
        out = []
        for r in self.rows:
            tf = {}
            for t in r["tokens"]:
                tf[t] = tf.get(t, 0) + 1
            s, hits, dl = 0.0, [], len(r["tokens"])
            for t in set(q):
                f = tf.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
                    hits.append(t)
            out.append((s, r["file"], hits))
        return sorted(out, key=lambda x: -x[0])


def route(prompt, skill_path=None):
    return BM25(router_rows(skill_path)).score(prompt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    rows = router_rows()
    if not rows:
        print("error: no router rows found in SKILL.md", file=sys.stderr)
        sys.exit(2)
    if a.list:
        for r in rows:
            print(f"{r['file']:55} {r['desc'][:90]}")
        return
    if not a.prompt or not a.prompt.strip():
        print("error: give a prompt (or --list)", file=sys.stderr)
        sys.exit(2)
    if a.top < 1:
        print("error: --top must be >= 1", file=sys.stderr)
        sys.exit(2)
    res = route(a.prompt)[: a.top]
    if res[0][0] == 0:
        print("no vocabulary overlap with any router row: use the default (NOS loop + closest reference) or extend the router")
        sys.exit(1)
    if a.json:
        print(json.dumps([{"file": f, "score": round(s, 3), "matched": h} for s, f, h in res], indent=1))
    else:
        for s, f, h in res:
            print(f"{s:6.2f}  {f}" + (f"   matched: {', '.join(h)}" if a.explain else ""))


if __name__ == "__main__":
    main()
