"""Documentation and package consistency tests: frontmatter, links, router completeness, snippets, CLI help."""
import ast
import glob
import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import ENV, REFS, ROOT, SCRIPTS, Base, have, have_cmd, run  # noqa: E402

SKILL = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
HELPERS = {"specialists_data.py"}


def md_files():
    return sorted(glob.glob(os.path.join(REFS, "**", "*.md"), recursive=True))


class Frontmatter(unittest.TestCase):
    def test_name_and_description(self):
        m = re.match(r'---\nname: (.+)\ndescription: "(.*)"\n---\n', SKILL)
        self.assertIsNotNone(m, "SKILL.md frontmatter malformed")
        self.assertEqual(m.group(1), "n-omni-skill")
        self.assertLessEqual(len(m.group(2)), 1024)
        for domain in ("WEB", "GAMES", "TOOLS", "WRITING", "AI", "BUSINESS", "ENGINEERING", "THINKING"):
            self.assertIn(domain, m.group(2))

    def test_naming_and_scope_rules(self):
        self.assertTrue(SKILL.startswith("---\nname: n-omni-skill"))
        self.assertNotRegex(SKILL, r"(?i)\bv2\b", "the skill must not be named or versioned 'v2'")
        for path in [os.path.join(ROOT, "SKILL.md")] + md_files():
            self.assertNotIn("Roblox", open(path, encoding="utf-8").read(), path)

    def test_skill_md_size(self):
        self.assertLess(SKILL.count("\n"), 500)


class Links(unittest.TestCase):
    PATH = re.compile(r"(?:references|scripts|tests)/[A-Za-z0-9_./-]+\.(?:md|py|json|js|txt|yml)")

    def test_every_referenced_path_exists(self):
        files = [os.path.join(ROOT, "SKILL.md")] + md_files() + glob.glob(os.path.join(ROOT, "tests", "*.md"))
        missing = []
        for path in files:
            text = open(path, encoding="utf-8").read()
            for rel in set(self.PATH.findall(text)):
                if "/" not in rel or "*" in rel:
                    continue
                candidates = [os.path.join(ROOT, rel)]
                if rel.startswith("references/"):
                    candidates.append(os.path.join(REFS, rel[len("references/"):]))
                if not any(os.path.exists(c) for c in candidates) and not os.path.exists(os.path.join(REFS, rel)):
                    # also allow short references used inside reference files, e.g. `ai/rag-llm.md`
                    missing.append((os.path.relpath(path, ROOT), rel))
        self.assertEqual(missing, [])

    def test_short_reference_links_resolve(self):
        pat = re.compile(r"`((?:web|games|tools|writing|ai|business|engineering|thinking|extra)/[a-z0-9-]+\.md)`")
        bad = []
        for path in md_files() + [os.path.join(ROOT, "SKILL.md")]:
            for rel in set(pat.findall(open(path, encoding="utf-8").read())):
                if not os.path.exists(os.path.join(REFS, rel)):
                    bad.append((os.path.relpath(path, ROOT), rel))
        self.assertEqual(bad, [])

    def test_router_lists_every_reference_and_script(self):
        for path in md_files():
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            self.assertIn(rel, SKILL, f"{rel} is not listed in the SKILL.md router")
        catalog = SKILL + open(os.path.join(REFS, "scripts.md"), encoding="utf-8").read()
        for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
            name = os.path.basename(path)
            if name not in HELPERS:
                self.assertIn(name, SKILL, f"scripts/{name} is not named in SKILL.md")
                self.assertIn(name, catalog.split("## Bundled scripts")[0] + open(os.path.join(REFS, "scripts.md"), encoding="utf-8").read(), name)
                self.assertIn(f"scripts/{name}", open(os.path.join(REFS, "scripts.md"), encoding="utf-8").read(), f"scripts/{name} missing from references/scripts.md")

    def test_long_references_have_contents(self):
        for path in md_files():
            lines = open(path, encoding="utf-8").read().splitlines()
            if len(lines) > 90 and not path.endswith("specialists.md"):
                self.assertTrue(any(l.strip() == "## Contents" for l in lines), f"{os.path.relpath(path, ROOT)} needs a '## Contents' list")


class Snippets(unittest.TestCase):
    def blocks(self, lang):
        out = []
        for path in md_files():
            for i, m in enumerate(re.finditer(r"```" + lang + r"\n(.*?)```", open(path, encoding="utf-8").read(), re.S)):
                out.append((os.path.relpath(path, ROOT), i, m.group(1)))
        return out

    def test_python_blocks_parse(self):
        bad = []
        for rel, i, code in self.blocks("python"):
            try:
                ast.parse(code)
            except SyntaxError as e:
                bad.append((rel, i, e.msg, e.lineno))
        self.assertEqual(bad, [])

    @unittest.skipUnless(have_cmd("node"), "node not installed")
    def test_js_blocks_parse(self):
        bad = []
        for rel, i, code in self.blocks("js") + self.blocks("javascript"):
            with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as tf:
                tf.write(code)
            r = subprocess.run(["node", "--check", tf.name], capture_output=True, text=True, encoding="utf-8", errors="replace")
            os.unlink(tf.name)
            if r.returncode:
                bad.append((rel, i, r.stderr.strip().splitlines()[-1][:100]))
        self.assertEqual(bad, [])

    RUNNABLE = [  # (reference, a marker inside the block, modules needed)
        ("ai/ml-dl.md", "make_classification", ["sklearn", "pandas", "numpy"]),
        ("ai/ml-dl.md", "np.tanh", ["numpy"]),
        ("ai/ml-dl.md", "def attention", ["numpy"]),
        ("ai/ml-dl.md", "IsolationForest", ["sklearn", "numpy"]),
        ("ai/rl.md", "def step(s, a)", ["numpy"]),
        ("ai/vision.md", "import cv2", ["cv2", "numpy"]),
        ("ai/vision.md", "def nms", ["numpy"]),
        ("ai/rag-llm.md", "def rrf", []),
        ("ai/agents-tools.md", "REGISTRY = ", []),
        ("games/blender-art-vfx.md", "SPRITE = ", ["PIL"]),
    ]

    def test_runnable_snippets_execute(self):
        for ref, marker, mods in self.RUNNABLE:
            if not all(have(m) for m in mods):
                continue
            text = open(os.path.join(REFS, ref), encoding="utf-8").read()
            code = [b for b in re.findall(r"```python\n(.*?)```", text, re.S) if marker in b]
            self.assertTrue(code, f"{ref}: block with {marker!r} not found")
            with tempfile.TemporaryDirectory() as d:
                r = subprocess.run([sys.executable, "-c", code[0]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, cwd=d, env=ENV)
            self.assertEqual(r.returncode, 0, f"{ref} [{marker}] failed:\n{r.stderr[-500:]}")

    def test_rl_snippet_learns_to_reach_the_goal(self):
        if not have("numpy"):
            self.skipTest("numpy not installed")
        text = open(os.path.join(REFS, "ai", "rl.md"), encoding="utf-8").read()
        code = [b for b in re.findall(r"```python\n(.*?)```", text, re.S) if "def step(s, a)" in b][0]
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, env=ENV)
        self.assertIn("reached goal True", r.stdout)
        self.assertIn("touched pit False", r.stdout)

    @unittest.skipUnless(have_cmd("node"), "node not installed")
    def test_reconciliation_snippet(self):
        text = open(os.path.join(REFS, "games", "multiplayer.md"), encoding="utf-8").read()
        code = re.search(r"```js\n(const SPEED = 6[\s\S]*?)```", text).group(1)
        r = subprocess.run(["node", "-e", code], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(r.stdout.strip(), "reconciled")


class CliHelp(unittest.TestCase):
    def test_every_script_documents_itself_and_exits_zero_on_help(self):
        for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
            name = os.path.basename(path)
            if name in HELPERS:
                continue
            src = open(path, encoding="utf-8").read()
            self.assertTrue(ast.get_docstring(ast.parse(src)), f"{name} needs a module docstring")
            r = run([name, "--help"], timeout=30)
            self.assertEqual(r.returncode, 0, f"{name} --help failed: {r.stderr[-300:]}")
            self.assertIn("usage", r.stdout.lower(), name)

    def test_scripts_compile(self):
        for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.join(SCRIPTS, "examples", "*.py"))):
            with open(path, encoding="utf-8") as f:
                ast.parse(f.read(), path)


class Freshness(Base):
    def test_every_reference_has_a_valid_stamp(self):
        import datetime
        pat = re.compile(r"^\*Last updated: (\d{4}-\d{2}-\d{2}) \| Version-sensitive: (.+?) \| Re-check current docs before pinning versions, prices, or API names\.\*$")
        for path in md_files():
            lines = open(path, encoding="utf-8").read().splitlines()[:7]
            m = next((pat.match(l) for l in lines if pat.match(l)), None)
            self.assertIsNotNone(m, f"{os.path.relpath(path, ROOT)} needs a freshness line under its title (see scripts/check_freshness.py)")
            datetime.date.fromisoformat(m.group(1))

    def test_tool_reports_ok_now_and_stale_in_the_future(self):
        self.assertEqual(run(["check_freshness.py"]).returncode, 0)
        r = run(["check_freshness.py", "--today", "2030-01-01"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("STALE", r.stdout)
        self.assertEqual(run(["check_freshness.py", "--max-days", "0"]).returncode, 2)
        self.assertEqual(run(["check_freshness.py", "--today", "not-a-date"]).returncode, 2)

    def test_stamp_command(self):
        import shutil
        src = os.path.join(REFS, "extra", "audio.md")
        dst = os.path.join(self.tmp, "audio.md")
        shutil.copy(src, dst)
        r = run(["check_freshness.py", "--today", "2031-02-03", "stamp", dst])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Last updated: 2031-02-03", open(dst, encoding="utf-8").read())
        plain = self.f("plain.md", "# no stamp here\n")
        self.assertEqual(run(["check_freshness.py", "stamp", plain]).returncode, 2)
        self.assertEqual(run(["check_freshness.py", "stamp", "/nonexistent.md"]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
