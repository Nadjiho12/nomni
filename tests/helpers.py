"""Shared helpers for the N-Omni-Skill regression tests."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
REFS = os.path.join(ROOT, "references")
import shutil
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")


def run(args, cwd=None, timeout=90, env=None, stdin=None):
    """Run a script (path relative to scripts/) or a command list. Returns CompletedProcess (never raises on non-zero)."""
    if isinstance(args, (list, tuple)) and args and args[0].endswith(".py") and not os.path.isabs(args[0]):
        cmd = [sys.executable, os.path.join(SCRIPTS, args[0])] + list(args[1:])
    else:
        cmd = list(args)
        found = shutil.which(cmd[0])          # resolves npm.cmd / node.exe on Windows
        if found:
            cmd[0] = found
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, env=env or ENV, input=stdin)


def have(module):
    try:
        __import__(module)
        return True
    except Exception:  # noqa: BLE001
        return False


def have_cmd(name):
    return shutil.which(name) is not None


def tmpdir():
    d = tempfile.mkdtemp(prefix="nos-test-")
    return d


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def f(self, name, text=""):
        return write(os.path.join(self.tmp, name), text)

    def assertNoTraceback(self, r):
        self.assertNotIn("Traceback", r.stderr, f"script crashed instead of reporting a clean error:\n{r.stderr[-400:]}")


def browser_available():
    r = run(["verify_web.py", "--check-env"], timeout=120)
    return r.returncode == 0
