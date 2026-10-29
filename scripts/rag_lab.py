#!/usr/bin/env python3
"""RAG retrieval lab (pure Python, no dependencies): chunk documents, BM25 search, and measure retrieval quality.

Use it to get a retrieval baseline and an evaluation harness BEFORE adding embeddings or an LLM.

  python rag_lab.py index docs/ --chunk 120 --overlap 20          # build and print stats
  python rag_lab.py search docs/ "how do I reset my password" -k 3 # search
  python rag_lab.py eval docs/ questions.json -k 3                 # recall@k and MRR

questions.json: [{"q": "question text", "source": "file.md", "must_contain": "optional phrase the right chunk contains"}]
A hit means a top-k chunk comes from `source` (and contains `must_contain` if given).
Swap `bm25_scores` for an embedding or hybrid scorer to compare against this baseline.
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

TOK = re.compile(r"[a-z0-9]+")
STOP = set("a an the of to in on for and or is are was were be by with as at it this that from how do i you what when where which".split())


def tokenize(t):
    return [w for w in TOK.findall(t.lower()) if w not in STOP]


def chunk_text(text, size, overlap):
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("size must be >= 1 and 0 <= overlap < size")
    """Structure-aware: split on blank lines/headings first, then pack paragraphs into ~size-word chunks with word overlap."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], []
    for p in paras:
        w = p.split()
        if cur and len(cur) + len(w) > size:
            chunks.append(" ".join(cur))
            cur = cur[-overlap:] if overlap else []
        cur += w
        while len(cur) > size * 2:  # very long paragraph
            chunks.append(" ".join(cur[:size])); cur = cur[size - overlap:]
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def load(folder, size, overlap):
    items = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.lower().endswith((".md", ".txt")):
                path = os.path.join(root, f)
                text = open(path, encoding="utf-8", errors="replace").read()
                for i, c in enumerate(chunk_text(text, size, overlap)):
                    items.append({"source": os.path.relpath(path, folder), "id": f"{f}#{i}", "text": c, "tokens": tokenize(c)})
    return items


class BM25:
    def __init__(self, items, k1=1.5, b=0.75):
        self.items, self.k1, self.b = items, k1, b
        self.N = len(items)
        self.avg = sum(len(i["tokens"]) for i in items) / max(1, self.N)
        df = Counter()
        for i in items:
            df.update(set(i["tokens"]))
        self.idf = {t: math.log(1 + (self.N - n + .5) / (n + .5)) for t, n in df.items()}
        self.tf = [Counter(i["tokens"]) for i in items]

    def scores(self, query):
        q = tokenize(query)
        out = []
        for i, it in enumerate(self.items):
            s, dl = 0.0, len(it["tokens"])
            for t in q:
                f = self.tf[i].get(t, 0)
                if f:
                    s += self.idf.get(t, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
            out.append(s)
        return out

    def search(self, query, k=5):
        sc = self.scores(query)
        order = sorted(range(self.N), key=lambda i: -sc[i])[:k]
        return [(self.items[i], sc[i]) for i in order if sc[i] > 0]


def evaluate(bm, qs, k):
    hits, rr = 0, 0.0
    misses = []
    for q in qs:
        res = bm.search(q["q"], k)
        rank = None
        for r, (it, _) in enumerate(res, 1):
            if it["source"] == q["source"] and (not q.get("must_contain") or q["must_contain"].lower() in it["text"].lower()):
                rank = r
                break
        if rank:
            hits += 1
            rr += 1 / rank
        else:
            misses.append(q["q"])
    n = len(qs)
    return hits / n, rr / n, misses


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def load_questions(path):
    try:
        with open(path, encoding="utf-8") as f:
            qs = json.load(f)
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    except ValueError as e:
        die(f"{path} is not valid JSON: {e}")
    if not isinstance(qs, list) or not qs:
        die("questions file must be a non-empty JSON list")
    for i, q in enumerate(qs):
        if not isinstance(q, dict) or "q" not in q or "source" not in q:
            die(f"question {i} needs 'q' and 'source' keys")
    return qs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["index", "search", "eval"])
    ap.add_argument("folder")
    ap.add_argument("arg", nargs="?")
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--chunk", type=int, default=120)
    ap.add_argument("--overlap", type=int, default=20)
    a = ap.parse_args()
    if a.chunk < 1:
        die("--chunk must be >= 1 (words per chunk)")
    if a.overlap < 0 or a.overlap >= a.chunk:
        die("--overlap must be >= 0 and smaller than --chunk")
    if a.k < 1:
        die("-k must be >= 1")
    if not os.path.isdir(a.folder):
        die(f"{a.folder} is not a folder")
    items = load(a.folder, a.chunk, a.overlap)
    if not items:
        die("no .md/.txt files found")
    bm = BM25(items)
    if a.cmd == "index":
        print(f"{len(items)} chunks from {len({i['source'] for i in items})} files; avg {bm.avg:.0f} tokens/chunk")
    elif a.cmd == "search":
        if not a.arg:
            die("give a query")
        for it, s in bm.search(a.arg, a.k):
            print(f"{s:6.2f}  {it['id']}  {it['text'][:110]}...")
    else:
        if not a.arg:
            die("give questions.json")
        qs = load_questions(a.arg)
        rec, mrr, miss = evaluate(bm, qs, a.k)
        print(f"recall@{a.k} = {rec:.2f}   MRR = {mrr:.2f}   ({len(qs)} questions)")
        for m in miss:
            print("  MISS:", m)
        print("Next: inspect misses (chunking? vocabulary mismatch -> add embeddings/query rewriting?), then compare a hybrid scorer on the same file.")
        sys.exit(0 if rec >= .8 else 1)


if __name__ == "__main__":
    main()
