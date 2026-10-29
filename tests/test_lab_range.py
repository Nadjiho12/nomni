"""Tests for scripts/ctf_lab.py: manifests, HMAC flags, scoring (dedupe/first-blood/rejection), compose templates, ATT&CK coverage."""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import REFS, Base, run  # noqa: E402


def newman(d, fname="c.json", **kw):
    args = {"name": "Baby SQLi", "category": "web", "points": "100", "difficulty": "easy", "description": "find it", "flag_secret": "seed-" + fname}
    args.update(kw)
    p = os.path.join(d, fname)
    r = run(["ctf_lab.py", "manifest", "new", "--out", p] + sum(([f"--{k.replace('_', '-')}", str(v)] for k, v in args.items()), []))
    return p, r


class Manifest(Base):
    def test_new_then_validate_requires_review_flag(self):
        p, r = newman(self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        m = json.load(open(p))
        self.assertEqual(m["id"], "baby-sqli")
        self.assertEqual(m["flag_format"], "WEB{TOKEN}")
        self.assertFalse(m["unintended_solution_review"])
        bad = run(["ctf_lab.py", "manifest", "validate", p])
        self.assertEqual(bad.returncode, 1, "a fresh manifest must fail validation until a second solver confirms it")
        self.assertIn("unintended_solution_review", bad.stdout)
        m["unintended_solution_review"] = True
        json.dump(m, open(p, "w"))
        self.assertEqual(run(["ctf_lab.py", "manifest", "validate", p]).returncode, 0)

    def test_bad_category_points_name(self):
        for kw in (dict(category="bogus"), dict(points="9999"), dict(points="0"), dict(name="")):
            r = newman(self.tmp, fname=f"x{hash(frozenset(kw.items())) & 0xffff}.json", **kw)[1]
            self.assertEqual(r.returncode, 2, kw)
            self.assertNoTraceback(r)

    def test_flag_format_must_place_braces_correctly(self):
        # manifest new validates at creation time too, so a bad flag_format never even gets written
        r = newman(self.tmp, flag_format="noplaceholder")[1]
        self.assertEqual(r.returncode, 1)
        self.assertIn("{TOKEN}", r.stderr)
        # edit a previously-valid manifest to a bad format and confirm `manifest validate` catches it standalone
        p, _ = newman(self.tmp, fname="ok.json")
        m = json.load(open(p)); m["unintended_solution_review"] = True; m["flag_format"] = "noplaceholder"
        json.dump(m, open(p, "w"))
        r = run(["ctf_lab.py", "manifest", "validate", p])
        self.assertEqual(r.returncode, 1)
        self.assertIn("{TOKEN}", r.stdout)

    def test_hints_cannot_zero_out_points(self):
        p, _ = newman(self.tmp, points="50")
        m = json.load(open(p))
        m["unintended_solution_review"] = True
        m["hints"] = [{"cost": 50, "text": "too expensive"}]
        json.dump(m, open(p, "w"))
        r = run(["ctf_lab.py", "manifest", "validate", p])
        self.assertEqual(r.returncode, 1)
        self.assertIn("hint cost", r.stdout)

    def test_missing_and_malformed_files(self):
        self.assertEqual(run(["ctf_lab.py", "manifest", "validate", "/nonexistent.json"]).returncode, 2)
        bad = self.f("bad.json", "{not json")
        r = run(["ctf_lab.py", "manifest", "validate", bad])
        self.assertEqual(r.returncode, 2)
        self.assertNoTraceback(r)


class Flags(Base):
    def setUp(self):
        super().setUp()
        self.chal, _ = newman(self.tmp)
        m = json.load(open(self.chal)); m["unintended_solution_review"] = True
        json.dump(m, open(self.chal, "w"))

    def test_flag_shape_and_roundtrip(self):
        r = run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "alice"])
        self.assertEqual(r.returncode, 0, r.stderr)
        flag = r.stdout.strip()
        self.assertRegex(flag, r"^WEB\{[0-9a-f]{24}\}$")
        self.assertEqual(run(["ctf_lab.py", "flag", "check", self.chal, "--team", "alice", flag]).returncode, 0)

    def test_different_team_or_forged_flag_rejected(self):
        flag = run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "alice"]).stdout.strip()
        self.assertEqual(run(["ctf_lab.py", "flag", "check", self.chal, "--team", "bob", flag]).returncode, 1)
        self.assertEqual(run(["ctf_lab.py", "flag", "check", self.chal, "--team", "alice", "WEB{deadbeef}"]).returncode, 1)

    def test_same_team_is_deterministic_different_teams_differ(self):
        a1 = run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "alice"]).stdout.strip()
        a2 = run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "alice"]).stdout.strip()
        b1 = run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "bob"]).stdout.strip()
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, b1)

    def test_empty_team_rejected(self):
        self.assertEqual(run(["ctf_lab.py", "flag", "gen", self.chal, "--team", "  "]).returncode, 2)


class Scoring(Base):
    def setUp(self):
        super().setUp()
        self.c1, _ = newman(self.tmp, fname="c1.json")
        self.c2, _ = newman(self.tmp, fname="c2.json", name="Crypto Warmup", category="crypto", points="200", difficulty="medium", flag_secret="seed2")
        for p in (self.c1, self.c2):
            m = json.load(open(p)); m["unintended_solution_review"] = True
            json.dump(m, open(p, "w"))

    def flag(self, chal, team):
        return run(["ctf_lab.py", "flag", "gen", chal, "--team", team]).stdout.strip()

    def test_dedupe_first_blood_rejection(self):
        a1, b1, a2 = self.flag(self.c1, "alice"), self.flag(self.c1, "bob"), self.flag(self.c2, "alice")
        csv_text = ("team,challenge_id,flag,timestamp_iso\n"
                    f"alice,baby-sqli,{a1},2026-01-01T10:00:00Z\n"
                    f"bob,baby-sqli,{b1},2026-01-01T10:05:00Z\n"
                    f"alice,crypto-warmup,{a2},2026-01-01T10:10:00Z\n"
                    f"alice,baby-sqli,{a1},2026-01-01T10:11:00Z\n"           # duplicate: must not double-count
                    "mallory,baby-sqli,FORGED{nope},2026-01-01T10:12:00Z\n"  # forged: rejected
                    f"alice,nope-chal,{a1},2026-01-01T10:13:00Z\n")          # unknown challenge: rejected
        subs = self.f("subs.csv", csv_text)
        out = os.path.join(self.tmp, "board.json")
        r = run(["ctf_lab.py", "score", "--manifests", self.c1, self.c2, "--submissions", subs, "--out", out])
        self.assertEqual(r.returncode, 0, r.stderr)
        board = json.load(open(out))
        self.assertEqual(board["rejected_submissions"], 2)
        self.assertEqual(board["accepted_solves"], 3)
        by_team = {r["team"]: r for r in board["scoreboard"]}
        self.assertAlmostEqual(by_team["alice"]["score"], 100 * 1.1 + 200 * 1.1, places=3)  # first blood on both
        self.assertAlmostEqual(by_team["bob"]["score"], 100.0, places=3)                     # second solve, no bonus
        self.assertEqual(by_team["alice"]["solved"], 2)
        self.assertEqual(board["first_blood"], {"baby-sqli": "alice", "crypto-warmup": "alice"})

    def test_bad_submissions_file(self):
        self.assertEqual(run(["ctf_lab.py", "score", "--manifests", self.c1, "--submissions", "/nonexistent.csv"]).returncode, 2)
        badcols = self.f("bad.csv", "a,b,c\n1,2,3\n")
        r = run(["ctf_lab.py", "score", "--manifests", self.c1, "--submissions", badcols])
        self.assertEqual(r.returncode, 2)
        self.assertNoTraceback(r)


class Compose(Base):
    def test_isolation_properties_present(self):
        p, _ = newman(self.tmp)
        m = json.load(open(p)); m["unintended_solution_review"] = True
        json.dump(m, open(p, "w"))
        out = run(["ctf_lab.py", "compose", p, "--port", "9090"]).stdout
        for needle in ("internal: true", "cap_drop: [ALL]", "read_only: true", "127.0.0.1:0:9090", "vulnerability code"):
            self.assertIn(needle, out)

    def test_bad_port(self):
        p, _ = newman(self.tmp)
        m = json.load(open(p)); m["unintended_solution_review"] = True
        json.dump(m, open(p, "w"))
        self.assertEqual(run(["ctf_lab.py", "compose", p, "--port", "0"]).returncode, 2)
        self.assertEqual(run(["ctf_lab.py", "compose", p, "--port", "70000"]).returncode, 2)


class Coverage(Base):
    def techfile(self):
        return self.f("t.txt", "T1110.001 Password Guessing\nT1059 Command and Scripting Interpreter\n# a comment\n\nT1021.001 RDP\n")

    def test_marks_and_summary(self):
        out = os.path.join(self.tmp, "cov.json")
        r = run(["ctf_lab.py", "coverage", "--techniques", self.techfile(), "--mark", "T1110.001=detected", "T1059=gap", "--out", out])
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.load(open(out))
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["summary"], {"detected": 1, "gap": 1, "untested": 1})
        by_id = {t["id"]: t["status"] for t in data["techniques"]}
        self.assertEqual(by_id["T1021.001"], "untested")

    def test_bad_inputs(self):
        self.assertEqual(run(["ctf_lab.py", "coverage", "--techniques", "/nonexistent.txt"]).returncode, 2)
        bad = self.f("bad.txt", "NOTATECHNIQUE something\n")
        r = run(["ctf_lab.py", "coverage", "--techniques", bad])
        self.assertEqual(r.returncode, 2)
        self.assertNoTraceback(r)
        self.assertEqual(run(["ctf_lab.py", "coverage", "--techniques", self.techfile(), "--mark", "nocolon"]).returncode, 2)
        self.assertEqual(run(["ctf_lab.py", "coverage", "--techniques", self.techfile(), "--mark", "T1059=bogus"]).returncode, 2)


class DocCrossCheck(unittest.TestCase):
    def test_lab_range_doc_mentions_the_cli_and_the_safety_boundary(self):
        text = open(os.path.join(REFS, "tools", "lab-range-design.md"), encoding="utf-8").read()
        for needle in ("scripts/ctf_lab.py", "unintended_solution_review", "SKILL.md` safety boundary", "## Contents", "internal: true"):
            self.assertIn(needle, text)

    def test_commands_in_the_doc_are_runnable_shapes(self):
        text = open(os.path.join(REFS, "tools", "lab-range-design.md"), encoding="utf-8").read()
        for cmd in re.findall(r"python scripts/ctf_lab\.py (\S+)", text):
            self.assertIn(cmd, ("manifest", "flag", "score", "compose", "coverage"))


if __name__ == "__main__":
    unittest.main()
