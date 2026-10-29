"""Tests for nos_state.py and workflow_plan.py."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import Base, run  # noqa: E402


class NosState(Base):
    def st(self, *args):
        return run(["nos_state.py", "--file", os.path.join(self.tmp, "NOS-STATE.md")] + list(args))

    def test_lifecycle(self):
        r = self.st("init", "--goal", "Build X", "--constraints", "solo", "--done-when", "users do Y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.st("init", "--goal", "again").returncode, 2, "must refuse to overwrite")
        self.assertEqual(self.st("init", "--goal", "again", "--force").returncode, 0)  # force replaces the goal
        for t in ("Walking skeleton", "Core flow", "Harden"):
            self.assertEqual(self.st("plan", "add", t).returncode, 0)
        self.assertIn("[ ] 2. Core flow", self.st("plan", "list").stdout)
        self.st("plan", "done", "1")
        self.st("plan", "done", "2")
        self.st("plan", "undo", "2")
        lst = self.st("plan", "list").stdout
        self.assertIn("[x] 1. Walking skeleton", lst)
        self.assertIn("[ ] 2. Core flow", lst)
        self.st("set", "gate", "G2 Skeleton")
        self.st("add", "decision", "Chose Postgres over SQLite")
        self.st("add", "checked", "login | ran tests: 12 passed")
        self.st("add", "open-gap", "mobile Safari")
        self.st("add", "assumption", "under 100 users")
        self.st("add", "question", "which host?")
        s = self.st("status").stdout
        for needle in ("Goal:        again", "Gate:        G2 Skeleton", "1/3 steps done; next: 2. Core flow", "1 checked, 1 open gaps, 1 assumptions"):
            self.assertIn(needle, s)
        shown = self.st("show").stdout
        self.assertIn("## Decisions", shown)
        self.assertRegex(shown, r"- \d{4}-\d\d-\d\d: Chose Postgres over SQLite")
        # file survives a round trip: re-adding does not duplicate or lose sections
        self.st("add", "file", "app/main.py")
        again = self.st("show").stdout
        self.assertEqual(again.count("## Goal"), 1)
        self.assertIn("- app/main.py", again)

    def test_errors_are_clean(self):
        self.assertEqual(self.st("status").returncode, 2)                      # no file yet
        self.st("init", "--goal", "G")
        for args in (["plan", "done", "9"], ["plan", "done"], ["plan", "add"], ["add", "decision", "  "], ["set", "goal", ""], ["init", "--goal", " ", "--force"]):
            r = self.st(*args)
            self.assertEqual(r.returncode, 2, args)
            self.assertNotIn("Traceback", r.stderr)


class WorkflowPlan(Base):
    def test_plan_has_five_phases_and_gates(self):
        r = run(["workflow_plan.py", "--task", "Add CSV export", "--domain", "web"])
        self.assertEqual(r.returncode, 0, r.stderr)
        names = re.findall(r"^## Phase \d: (\w+)", r.stdout, re.M)
        self.assertEqual(names, ["Research", "Plan", "Execute", "Optimize", "Review"])
        self.assertEqual(r.stdout.count("**Exit gate:**"), 5)
        self.assertIn("designer", r.stdout)
        self.assertIn("independent", r.stdout)
        self.assertIn("same model", r.stdout)       # honest about shared blind spots

    def test_subagent_mode_emits_runnable_briefs(self):
        r = run(["workflow_plan.py", "--task", "RAG over docs", "--domain", "ai", "--mode", "subagents", "--reviewers", "3"])
        self.assertIn("subagent_brief.py brief --role researcher", r.stdout)
        self.assertIn("data-ml", r.stdout)
        self.assertIn("security, risk, and failure modes", r.stdout)
        cmd = re.search(r"`(python scripts/subagent_brief.py brief --role architect[^`]*)`", r.stdout).group(1)
        self.assertIn("--acceptance", cmd)

    def test_init_state_creates_plan_steps(self):
        state = os.path.join(self.tmp, "S.md")
        r = run(["workflow_plan.py", "--task", "Ship it", "--init-state", state])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = run(["nos_state.py", "--file", state, "status"]).stdout
        self.assertIn("0/5 steps done", out)

    def test_bad_args(self):
        for extra in (["--reviewers", "0"], ["--reviewers", "4"], ["--domain", "cooking"]):
            r = run(["workflow_plan.py", "--task", "x"] + extra)
            self.assertEqual(r.returncode, 2, extra)
        self.assertEqual(run(["workflow_plan.py", "--task", "  "]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
