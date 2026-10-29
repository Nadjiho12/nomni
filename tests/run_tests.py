#!/usr/bin/env python3
"""Run the N-Omni-Skill regression suite (standard library only; no pytest needed).

  python tests/run_tests.py            # everything the environment can run
  python tests/run_tests.py -v         # verbose
  python tests/run_tests.py scripts    # only tests whose module/class name contains 'scripts' (also: docs, browser)
  python tests/run_tests.py --list-skips

Tests that need something the environment lacks (Chromium, node, php, pandas, network for npm) are SKIPPED with a reason,
never silently passed. Exit code: 0 all run tests passed, 1 failures or errors. Before calling a change "tested",
run this in an environment where the skips you care about are not skipped (see tests/README.md).
"""
import argparse
import os
import sys
import time
import unittest

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pattern", nargs="?", default="", help="substring of the test module or class name")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--list-skips", action="store_true")
    a = ap.parse_args()
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for mod in ("test_scripts", "test_workflow_tools", "test_domain_tools", "test_lab_range", "test_router", "test_docs", "test_browser"):
        if a.pattern and a.pattern not in mod and a.pattern not in "".join(
                n for n in dir(__import__(mod)) if isinstance(getattr(__import__(mod), n), type)):
            continue
        suite.addTests(loader.loadTestsFromName(mod))
    t0 = time.time()
    res = unittest.TextTestRunner(verbosity=2 if a.verbose else 1, stream=sys.stderr).run(suite)
    passed = res.testsRun - len(res.failures) - len(res.errors) - len(res.skipped)
    print(f"\n{passed} passed, {len(res.failures)} failed, {len(res.errors)} errors, {len(res.skipped)} skipped in {time.time() - t0:.0f}s")
    if res.skipped and (a.list_skips or a.verbose or True):
        for t, why in res.skipped:
            print(f"  SKIPPED {t.id().split('.', 1)[-1]}: {why}")
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
