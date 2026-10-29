"""Router vocabulary tests: does the SKILL.md router table (plus each reference's headings) contain the words people use?

These are REGRESSION GUARDS for a lexical proxy, not a measure of how well a model routes (a model reads semantically).
Corpora: route_prompts.json (A: router vocabulary was tuned on it), route_prompts_heldout.json (B: seen when choosing synonyms),
route_prompts_heldout2.json (C: written before any tuning and measured once; the honest generalization estimate).
Thresholds sit below the last measured values so refactors that hurt routing fail, while normal edits do not.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import ROOT, Base, run  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import route_check  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
BM = route_check.BM25(route_check.router_rows())


def load(name):
    return json.load(open(os.path.join(FIX, name), encoding="utf-8"))


def accuracy(corpus):
    t1 = t3 = 0
    misses = []
    for c in corpus:
        res = BM.score(c["prompt"])
        files = [f for _, f, _ in res]
        ok1 = res[0][0] > 0 and files[0] in c["expect"]
        t1 += ok1
        t3 += res[0][0] > 0 and any(f in c["expect"] for f in files[:3])
        if not ok1:
            misses.append((c["prompt"], c["expect"], files[:2]))
    return t1 / len(corpus), t3 / len(corpus), misses


class RouterAccuracy(unittest.TestCase):
    def check(self, name, min1, min3):
        corpus = load(name)
        t1, t3, misses = accuracy(corpus)
        self.assertGreaterEqual(t1, min1, f"{name}: top-1 {t1:.0%} < {min1:.0%}; misses: {misses[:5]}")
        self.assertGreaterEqual(t3, min3, f"{name}: top-3 {t3:.0%} < {min3:.0%}; misses: {misses[:5]}")

    def test_tuned_corpus(self):
        self.check("route_prompts.json", 0.88, 0.95)

    def test_seen_heldout_corpus(self):
        self.check("route_prompts_heldout.json", 0.78, 0.80)

    def test_fresh_corpus(self):
        self.check("route_prompts_heldout2.json", 0.72, 0.90)

    def test_every_router_row_has_a_sample_prompt(self):
        covered = {e for c in load("route_prompts.json") for e in c["expect"]}
        self.assertEqual(sorted({r["file"] for r in BM.rows} - covered), [], "add a sample prompt for each new router row to route_prompts.json")

    def test_router_rows_are_exactly_the_reference_files(self):
        import glob
        refs = {os.path.relpath(p, ROOT).replace(os.sep, "/") for p in glob.glob(os.path.join(ROOT, "references", "**", "*.md"), recursive=True)}
        rows = [r["file"] for r in BM.rows]
        self.assertEqual(len(rows), len(set(rows)), "duplicate router rows")
        self.assertEqual(sorted(refs - set(rows)), [], "reference files without a router row (the router table is how a reference gets found)")
        self.assertEqual(sorted(set(rows) - refs), [], "router rows pointing at missing files")

    def test_expected_files_exist(self):
        for name in ("route_prompts.json", "route_prompts_heldout.json", "route_prompts_heldout2.json"):
            for c in load(name):
                for e in c["expect"]:
                    self.assertTrue(os.path.exists(os.path.join(ROOT, e)), f"{name}: {e} does not exist")


class RouteCheckCli(Base):
    def test_list_json_and_explain(self):
        out = run(["route_check.py", "--list"]).stdout
        self.assertGreaterEqual(len(out.strip().splitlines()), 45)
        r = run(["route_check.py", "build a RAG chatbot over my PDFs", "--json", "--top", "2"])
        data = json.loads(r.stdout)
        self.assertEqual(data[0]["file"], "references/ai/rag-llm.md")
        self.assertIn("rag", data[0]["matched"])
        self.assertIn("matched:", run(["route_check.py", "debounce a button on Arduino", "--explain"]).stdout)

    def test_errors_and_no_overlap(self):
        self.assertEqual(run(["route_check.py"]).returncode, 2)
        self.assertEqual(run(["route_check.py", "   "]).returncode, 2)
        self.assertEqual(run(["route_check.py", "x", "--top", "0"]).returncode, 2)
        r = run(["route_check.py", "zzzz qqqq xxxx"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("no vocabulary overlap", r.stdout)


if __name__ == "__main__":
    unittest.main()
