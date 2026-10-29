"""End-to-end tests of scripts/verify_web.py. Skipped when no headless Chromium is available (see: verify_web.py --check-env)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import ENV, Base, browser_available, have_cmd, run  # noqa: E402

PAGE = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>{}</body></html>'
GOOD = PAGE.format('<main><h1>Counter</h1><button id="b">add</button> <span id="n">0</span><canvas id="c" width="200" height="100"></canvas>'
                   '<script>let n=0;const c=document.getElementById("c").getContext("2d");'
                   'function draw(){c.fillStyle=n%2?"#1e90ff":"#ff8c00";c.fillRect(0,0,200,100);c.fillStyle="#fff";c.fillRect(10+n*5,10,40,40);c.fillStyle="#000";c.fillRect(100,60,50,20);requestAnimationFrame(draw)}draw();'
                   'document.getElementById("b").onclick=()=>{n++;document.getElementById("n").textContent=n};</script></main>')


class VerifyWebEnvironment(Base):
    def test_missing_browser_is_exit_3_not_a_crash(self):
        env = dict(ENV, PLAYWRIGHT_BROWSERS_PATH=os.path.join(self.tmp, "no-browsers"))
        r = run(["verify_web.py", "--check-env"], env=env, timeout=60)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertNoTraceback(r)
        self.assertIn("unavailable", r.stderr.lower())
        r = run(["verify_web.py", self.f("p.html", GOOD), "--fps-seconds", "0"], env=env, timeout=60)
        self.assertEqual(r.returncode, 3)

    def test_usage_errors_exit_2(self):
        page = self.f("p.html", GOOD)
        self.assertEqual(run(["verify_web.py", "/nonexistent.html"]).returncode, 2)
        for extra in (["--viewport", "abc"], ["--route", "noequals"], ["--route", "a=/nonexistent/file.js"]):
            r = run(["verify_web.py", page, "--fps-seconds", "0"] + extra)
            self.assertEqual(r.returncode, 2, extra)
            self.assertNoTraceback(r)
        self.assertEqual(run(["verify_web.py", page, "--scenario", self.f("bad.json", "{x")]).returncode, 2)


@unittest.skipUnless(browser_available(), "headless Chromium not available (run: python scripts/verify_web.py --check-env)")
class VerifyWebBrowser(Base):
    def verify(self, html, *args, name="page.html", timeout=120):
        path = self.f(name, html)
        out = os.path.join(self.tmp, "out")
        r = run(["verify_web.py", path, "--out", out, "--fps-seconds", "0", "--settle", "300"] + list(args), timeout=timeout)
        self.assertNoTraceback(r)
        report = json.load(open(os.path.join(out, "report.json")))
        return r, report

    def statuses(self, report, name):
        return [x["status"] for x in report if name in x["name"]]

    def test_good_page_passes(self):
        r, rep = self.verify(GOOD)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS", self.statuses(rep, "screen is not blank"))

    def test_js_error_fails(self):
        r, rep = self.verify(PAGE.format("<p>hi</p><script>undefinedFunction()</script>"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.statuses(rep, "uncaught"))

    def test_blank_page_fails(self):
        r, rep = self.verify(PAGE.format('<canvas width="100" height="100"></canvas>').replace("<body>", '<body style="margin:0;background:#000">'))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.statuses(rep, "not blank"))

    def test_missing_local_asset_fails_and_overflow_warns(self):
        r, rep = self.verify(PAGE.format('<script src="missing.js"></script><p>hi</p><div style="width:3000px;height:10px;background:red"></div>'))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.statuses(rep, "failed local requests"))
        self.assertIn("WARN", self.statuses(rep, "horizontal scroll"))

    def test_scenario_assertions_pass_and_negative_control_fails(self):
        steps = [{"do": "shot", "name": "before"}, {"do": "click", "selector": "#b"}, {"do": "click", "selector": "#b"},
                 {"do": "eval", "js": "n", "expect": 2, "label": "counter is 2"}, {"do": "text", "selector": "#n", "contains": "2"},
                 {"do": "wait_for", "js": "n===2", "timeout": 2000}, {"do": "shot", "name": "after"},
                 {"do": "changed", "a": "before", "b": "after", "min": 0.001}]
        sc = self.f("ok.json", json.dumps(steps))
        r, rep = self.verify(GOOD, "--scenario", sc)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS", self.statuses(rep, "counter is 2"))
        bad = self.f("bad.json", json.dumps([{"do": "click", "selector": "#b"}, {"do": "eval", "js": "n", "expect": 99, "label": "wrong expectation"}]))
        r, rep = self.verify(GOOD, "--scenario", bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.statuses(rep, "wrong expectation"))

    def test_mobile_and_skip_draw_flags_run(self):
        r, _ = self.verify(GOOD, "--mobile")
        self.assertEqual(r.returncode, 0, r.stdout)
        r, rep = self.verify(GOOD, "--skip-draw")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_page_url_mode_and_route_override(self):
        page = PAGE.format('<script src="https://cdn.example.invalid/lib.js"></script><p id="x">hi</p><script>window.ok = typeof LIB !== "undefined"</script>')
        lib = self.f("lib.js", "window.LIB = {version: 1};")
        r, rep = self.verify(page, "--route", f"cdn.example.invalid/lib.js={lib}", "--scenario", self.f("s.json", json.dumps([{"do": "eval", "js": "window.ok", "expect": True, "label": "routed library loaded"}])))
        self.assertEqual(r.returncode, 0, r.stdout)

    @unittest.skipUnless(have_cmd("npm"), "npm not installed")
    def test_axe_catches_accessibility_violations(self):
        d = os.path.join(self.tmp, "axe")
        os.makedirs(d)
        r = run(["npm", "install", "axe-core", "--silent", "--no-audit", "--no-fund"], cwd=d, timeout=150)
        axe = os.path.join(d, "node_modules", "axe-core", "axe.min.js")
        if r.returncode != 0 or not os.path.exists(axe):
            self.skipTest("could not install axe-core (offline?)")
        bad = PAGE.format('<h1>Demo</h1><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw="><input type="text"><button></button>')
        r, rep = self.verify(bad, "--axe", axe)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(any(x["name"].startswith("a11y:") and x["status"] == "FAIL" for x in rep))
        good = PAGE.format('<main><h1>Demo</h1><label for="n">Name</label><input id="n" type="text"><button>Save</button></main>')
        r, rep = self.verify(good, "--axe", axe, name="good.html")
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
