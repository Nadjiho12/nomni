"""Functional tests for the bundled scripts: correct outputs, correct exit codes, clean errors."""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import Base, REFS, ROOT, SCRIPTS, have, have_cmd, run  # noqa: E402

CSV_IDEAS = "name,reach,impact,confidence,effort\nA,2000,2,0.5,4\nB,800,3,0.8,3\nC,5000,1,0.9,1\n"
CSV_RISKS = "risk,likelihood,impact,mitigation\nBan,3,5,diversify\nNo demand,4,5,presell\nTypo,2,1,proofread\n"
CSV_OPTS = "option,cost,speed,fit\nStatic,5,5,3\nPHP,3,3,4\nNode,3,4,4\n"


class BizCalc(Base):
    def test_unit_economics_values(self):
        r = run(["biz_calc.py", "unit", "--arpu", "12", "--gross-margin", "0.8", "--churn", "0.05", "--cac", "40"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("LTV              192.00", r.stdout)
        self.assertIn("LTV:CAC          4.80", r.stdout)
        self.assertIn("4.2 months", r.stdout)

    def test_breakeven_and_runway(self):
        r = run(["biz_calc.py", "breakeven", "--fixed", "3000", "--price", "25", "--variable", "6", "--target-profit", "1000"])
        self.assertIn("211", r.stdout)
        r = run(["biz_calc.py", "runway", "--cash", "20000", "--burn", "3500"])
        self.assertIn("5.7 months", r.stdout)

    def test_rice_ranking(self):
        r = run(["biz_calc.py", "rice", "--file", self.f("i.csv", CSV_IDEAS)])
        self.assertEqual(r.returncode, 0)
        order = [m for m in re.findall(r"^\d+\s+(\w+)", r.stdout, re.M)]
        self.assertEqual(order[:3], ["C", "B", "A"])  # 4500, 640, 250

    def test_risk_levels(self):
        r = run(["biz_calc.py", "risk", "--file", self.f("r.csv", CSV_RISKS)])
        self.assertIn("CRITICAL", r.stdout)
        self.assertIn("LOW", r.stdout)

    def test_matrix_orders_options(self):
        r = run(["biz_calc.py", "matrix", "--file", self.f("o.csv", CSV_OPTS), "--weights", "cost=3,speed=2,fit=5"])
        first = re.findall(r"^1\s+(\w+)", r.stdout, re.M)
        self.assertEqual(first, ["Static"])  # weighted: Static 4.0, Node 3.7, PHP 3.5

    def test_pricing_neutral_at_elasticity_minus_one(self):
        r = run(["biz_calc.py", "pricing", "--prices", "5,9,15", "--base-price", "9", "--base-conv", "0.01", "--visitors", "2000",
                 "--ad-spend", "300", "--cpc", "0.8", "--churn", "0.08", "--elasticity", "-1.0"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("No clear winner", r.stdout)

    def test_forecast_reports_lowest_cash_and_breakeven(self):
        r = run(["biz_calc.py", "forecast", "--months", "12", "--new-per-month", "20", "--growth", "0.05", "--churn", "0.05", "--arpu", "12",
                 "--gross-margin", "0.85", "--fixed", "800", "--cac", "25", "--cash", "3000"])
        self.assertIn("Monthly net cash flow turns positive: month 8", r.stdout)
        self.assertIn("Lowest cash balance", r.stdout)

    def test_bad_inputs_are_clean_errors(self):
        for args in (["unit", "--arpu", "9", "--gross-margin", "0.9", "--churn", "0", "--cac", "10"],
                     ["breakeven", "--fixed", "100", "--price", "5", "--variable", "6"],
                     ["rice", "--file", self.f("empty.csv", "")],
                     ["pricing", "--prices", "a,b", "--base-price", "9", "--base-conv", "0.01", "--visitors", "1", "--churn", "0.1"],
                     ["matrix", "--file", self.f("o.csv", CSV_OPTS), "--weights", "cost"]):
            r = run(["biz_calc.py"] + args)
            self.assertNoTraceback(r)
            self.assertNotEqual(r.returncode, 0, args)


class LogTriage(Base):
    F = "Sep 30 10:00:0{i} h sshd[1]: Failed password for root from 9.9.9.9 port 22 ssh2"
    OK = "Sep 30 10:09:00 h sshd[1]: Accepted password for alice from 9.9.9.9 port 22 ssh2"

    def triage(self, lines, thr=5):
        p = self.f("a.log", "\n".join(lines) + "\n")
        r = run(["log_triage.py", "--type", "ssh", "--file", p, "--threshold", str(thr), "--json"])
        self.assertNoTraceback(r)
        return r.returncode, json.loads(r.stdout)

    def test_success_before_failures_is_not_high(self):  # regression: reviewer's reproduction
        code, f = self.triage([self.OK] + [self.F.format(i=i) for i in range(5)])
        self.assertEqual(code, 1)
        self.assertEqual(f[0]["severity"], "MEDIUM")
        self.assertIn("earlier", f[0]["note"])

    def test_success_after_failures_is_high(self):
        code, f = self.triage([self.F.format(i=i) for i in range(5)] + [self.OK])
        self.assertEqual(f[0]["severity"], "HIGH")
        self.assertIn("AFTER 5 failed attempts", f[0]["note"])

    def test_below_threshold_and_clean_logs(self):
        code, f = self.triage([self.F.format(i=i) for i in range(4)])
        self.assertEqual((code, f), (0, []))
        code, f = self.triage([self.OK])
        self.assertEqual((code, f), (0, []))

    def test_web_probes_flagged(self):
        line = '198.51.100.9 - - [30/Sep/2026:10:00:01 +0000] "GET /.env HTTP/1.1" 404 10 "-" "curl"'
        r = run(["log_triage.py", "--type", "web", "--file", self.f("w.log", line + "\n"), "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("/.env", r.stdout)

    def test_errors(self):
        self.assertEqual(run(["log_triage.py", "--type", "ssh", "--file", "/nonexistent.log"]).returncode, 2)
        r = run(["log_triage.py", "--type", "ssh", "--file", self.f("e.log", ""), "--threshold", "0"])
        self.assertEqual(r.returncode, 1)  # sys.exit(message)
        self.assertNoTraceback(r)


class RagLab(Base):
    def corpus(self):
        d = os.path.join(self.tmp, "docs")
        self.f("docs/account.md", "# Account\n\n## Reset password\nOpen Settings then Security and press Reset password. A reset link is emailed and expires in 30 minutes.\n")
        self.f("docs/billing.md", "# Billing\n\n## Refunds\nAnnual plans can be refunded within 30 days. Monthly plans are not refundable.\n")
        self.f("docs/api.md", "# API\n\n## Rate limits\nThe API allows 100 requests per minute. Exceeding it returns HTTP 429.\n")
        return d

    def test_index_search_eval(self):
        d = self.corpus()
        self.assertIn("3 chunks", run(["rag_lab.py", "index", d, "--chunk", "40", "--overlap", "5"]).stdout)
        self.assertIn("billing.md", run(["rag_lab.py", "search", d, "refund annual plan", "-k", "1"]).stdout)
        q = self.f("q.json", json.dumps([{"q": "how do I reset my password", "source": "account.md", "must_contain": "reset link"},
                                          {"q": "what happens when I exceed the rate limit", "source": "api.md", "must_contain": "429"}]))
        r = run(["rag_lab.py", "eval", d, q, "-k", "3"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("recall@3 = 1.00", r.stdout)

    def test_eval_fails_on_unanswerable(self):
        d = self.corpus()
        q = self.f("bad.json", json.dumps([{"q": "quantum chromodynamics lattice", "source": "api.md"}]))
        r = run(["rag_lab.py", "eval", d, q])
        self.assertEqual(r.returncode, 1)
        self.assertIn("MISS", r.stdout)

    def test_invalid_chunk_args_do_not_hang(self):  # regression: --chunk 0 used to loop forever
        d = self.corpus()
        for extra, needle in ((["--chunk", "0"], "--chunk must be"), (["--chunk", "-3"], "--chunk must be"),
                              (["--chunk", "10", "--overlap", "10"], "--overlap must be"), (["--overlap", "500"], "--overlap must be")):
            r = run(["rag_lab.py", "index", d] + extra, timeout=15)
            self.assertEqual(r.returncode, 2, extra)
            self.assertIn(needle, r.stderr, f"{extra}: the error should name the offending option")
            self.assertNoTraceback(r)
        self.assertEqual(run(["rag_lab.py", "search", d, "x", "-k", "0"], timeout=15).returncode, 2)

    def test_bad_question_files(self):
        d = self.corpus()
        for content in ("{bad json", "[]", '{"a":1}', '[{"q":"only q"}]'):
            r = run(["rag_lab.py", "eval", d, self.f("q.json", content)])
            self.assertEqual(r.returncode, 2, content)
            self.assertNoTraceback(r)


@unittest.skipUnless(have("pandas") and have("numpy"), "pandas/numpy not installed")
class DriftCheck(Base):
    def make(self):
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(0)
        n = 2000
        ref = pd.DataFrame({"age": rng.normal(40, 10, n), "income": rng.lognormal(10, .4, n), "plan": rng.choice(["free", "pro", "team"], n, p=[.6, .3, .1])})
        cur = pd.DataFrame({"age": rng.normal(40, 10, n), "income": rng.lognormal(10.6, .4, n), "plan": rng.choice(["free", "pro", "team"], n, p=[.3, .4, .3])})
        same = ref.sample(1500, random_state=1)
        for name, df in (("ref", ref), ("cur", cur), ("same", same)):
            df.to_csv(os.path.join(self.tmp, name + ".csv"), index=False)
        return [os.path.join(self.tmp, n + ".csv") for n in ("ref", "cur", "same")]

    def test_detects_shift_and_accepts_same(self):
        ref, cur, same = self.make()
        r = run(["drift_check.py", ref, cur, "--json"])
        self.assertEqual(r.returncode, 1)
        status = {c["column"]: c["status"] for c in json.loads(r.stdout)["columns"]}
        self.assertEqual(status["income"], "ALERT")
        self.assertEqual(status["plan"], "ALERT")
        self.assertEqual(status["age"], "OK")
        self.assertEqual(run(["drift_check.py", ref, same]).returncode, 0)

    def test_errors_are_clean(self):
        ref = self.make()[0]
        for a, b in (("/nonexistent.csv", ref), (self.f("e.csv", ""), ref), (self.f("h.csv", "a,b\n"), ref)):
            r = run(["drift_check.py", a, b])
            self.assertEqual(r.returncode, 2)
            self.assertNoTraceback(r)
        self.assertEqual(run(["drift_check.py", ref, ref, "--bins", "1"]).returncode, 2)


class WritingLint(Base):
    AI = ("In today's fast-paced digital landscape, it's important to note that time management is not just a skill but a game-changer. "
          "Time management is essential. Time management helps you leverage your potential. Time management can seamlessly elevate productivity. "
          "Moreover, you can really harness the power of planning. Ultimately, a robust solution is very simple.")
    HUMAN = ("I lost most of last year to a calendar I never looked at. The fix was boring. One list, checked every morning, three things on it.\n\n"
             "Some days I only finished one. That was fine. By March the pile of someday tasks had shrunk enough that I stopped dreading Mondays, "
             "and when my sister asked what changed, I could not point to anything dramatic, just a notebook with a coffee ring on the cover.")

    def test_flags_ai_style(self):
        r = run(["writing_lint.py", self.f("a.txt", self.AI), "--json"])
        issues = json.loads(r.stdout)["issues"]
        kinds = {k for k, _ in issues}
        self.assertTrue({"stock", "openers", "filler"} <= kinds, kinds)

    def test_human_style_has_fewer_flags(self):
        ai = json.loads(run(["writing_lint.py", self.f("a.txt", self.AI), "--json"]).stdout)["issues"]
        hu = json.loads(run(["writing_lint.py", self.f("h.txt", self.HUMAN), "--json"]).stdout)["issues"]
        self.assertLess(len(hu), len(ai))
        self.assertFalse([i for i in hu if i[0] == "stock"])

    def test_edge_cases(self):
        self.assertEqual(run(["writing_lint.py", self.f("e.txt", "")]).returncode, 0)
        r = run(["writing_lint.py", "/nonexistent.txt"])
        self.assertEqual(r.returncode, 2)
        self.assertNoTraceback(r)
        self.assertEqual(run(["writing_lint.py", "-"], stdin="Short. Test.").returncode, 0)


class EconomySim(Base):
    def cfg(self, tiers, **extra):
        return self.f("c.json", json.dumps(dict(extra, tiers=tiers)))

    def test_default_runs_and_reports_milestones(self):
        r = run(["economy_sim.py", "--hours", "1", "--milestones", "1e3", "1e4"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("reached at", r.stdout)

    def test_unreachable_milestone_is_flagged(self):
        c = self.cfg([{"name": "A", "base_cost": 10, "growth": 1.5, "income": 0.2}], start_money=10, click_income=1)
        r = run(["economy_sim.py", "--config", c, "--hours", "1", "--milestones", "1e9"])
        self.assertIn("NOT reached", r.stdout)

    def test_invalid_configs_are_clean_errors(self):
        bad = [self.cfg([{"name": "x", "base_cost": 10, "growth": 1.1, "income": 0}]), self.cfg([]), self.cfg([{"name": "x", "base_cost": 10, "growth": 0.5, "income": 1}]),
               self.f("j.json", "{bad"), "/nonexistent.json", self.cfg([{"name": "x", "base_cost": "ten", "growth": 1.1, "income": 1}])]
        for c in bad:
            r = run(["economy_sim.py", "--config", c])
            self.assertEqual(r.returncode, 2, c)
            self.assertNoTraceback(r)
        for extra in (["--hours", "0"], ["--hours", "-1"], ["--milestones", "-5"]):
            self.assertEqual(run(["economy_sim.py"] + extra).returncode, 2)


class LintHtml(Base):
    def test_good_and_bad_pages(self):
        good = self.f("g.html", '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title><meta name="viewport" content="width=device-width"><meta name="description" content="d"></head><body><h1>x</h1><img src="a.png" alt="a"></body></html>')
        self.assertEqual(run(["lint_html.py", good]).returncode, 0)
        bad = self.f("b.html", "<html><body><img src=a.png><h1>a</h1><h1>b</h1><input id=x><a></a></body></html>")
        r = run(["lint_html.py", bad])
        self.assertEqual(r.returncode, 1)
        for needle in ("missing alt", "lang", "viewport", "title"):
            self.assertIn(needle, r.stdout)

    def test_missing_file(self):
        r = run(["lint_html.py", "/nonexistent.html"])
        self.assertEqual(r.returncode, 2)
        self.assertNoTraceback(r)


class Scaffold(Base):
    def make(self, kind):
        d = os.path.join(self.tmp, kind)
        r = run(["scaffold.py", kind, d])
        self.assertEqual(r.returncode, 0, r.stderr)
        return d

    def test_static_and_canvas_game_pass_html_lint(self):
        for kind, page in (("static", "index.html"), ("canvas-game", "index.html")):
            d = self.make(kind)
            self.assertEqual(run(["lint_html.py", os.path.join(d, page)]).returncode, 0, kind)

    def test_py_cli_compiles_and_runs(self):
        d = self.make("py-cli")
        r = run([sys.executable, os.path.join(d, "tool.py"), "count", d, "--glob", "*.py"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("tool.py", r.stdout)

    @unittest.skipUnless(have_cmd("node"), "node not installed")
    def test_node_api_syntax(self):
        d = self.make("node-api")
        self.assertEqual(run(["node", "--check", os.path.join(d, "server.js")]).returncode, 0)

    @unittest.skipUnless(have_cmd("php"), "php not installed")
    def test_php_app_syntax_and_csrf_flow(self):
        import http.cookiejar
        import socket
        import subprocess
        import time
        import urllib.error
        import urllib.parse
        import urllib.request
        d = self.make("php-app")
        for f in ("public/index.php", "src/db.php"):
            self.assertEqual(run(["php", "-l", os.path.join(d, f)]).returncode, 0, f)
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        proc = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}", "-t", "public", "public/index.php"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(50):
                try:
                    urllib.request.urlopen(base + "/", timeout=1); break
                except Exception:  # noqa: BLE001
                    time.sleep(.1)
            jar = http.cookiejar.CookieJar()
            op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            html = op.open(base + "/").read().decode()
            self.assertIn("<h1>Notes</h1>", html)
            token = re.search(r'name="csrf" value="([0-9a-f]+)"', html).group(1)

            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k):
                    return None
            op2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
            with self.assertRaises(urllib.error.HTTPError) as cm:   # no CSRF token -> 403
                op2.open(base + "/add", urllib.parse.urlencode({"title": "x"}).encode())
            self.assertEqual(cm.exception.code, 403)
            with self.assertRaises(urllib.error.HTTPError) as cm:   # valid token -> 303 redirect
                op2.open(base + "/add", urllib.parse.urlencode({"title": "hello <b>world</b>", "csrf": token}).encode())
            self.assertEqual(cm.exception.code, 303)
            page = op.open(base + "/").read().decode()
            self.assertIn("hello &lt;b&gt;world&lt;/b&gt;", page)   # output escaped
            with self.assertRaises(urllib.error.HTTPError) as cm:   # invalid input -> 422
                op2.open(base + "/add", urllib.parse.urlencode({"title": "", "csrf": token}).encode())
            self.assertEqual(cm.exception.code, 422)
        finally:
            proc.terminate(); proc.wait(timeout=5)

    def test_bad_usage(self):
        self.assertEqual(run(["scaffold.py", "nope", "x"]).returncode, 2)
        d = self.make("static")
        self.assertEqual(run(["scaffold.py", "static", d]).returncode, 1)  # non-empty target refused


class Cvss(Base):
    KNOWN = {"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H": 9.8, "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H": 10.0,
             "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N": 6.1, "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N": 5.5,
             "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H": 8.8, "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:N": 0.0,
             "CVSS:3.1/AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N": 1.6}

    def test_known_scores(self):
        for vec, exp in self.KNOWN.items():
            r = run(["cvss_calc.py", "--json", vec])
            self.assertEqual(json.loads(r.stdout)["base_score"], exp, vec)

    def test_severity_labels_and_errors(self):
        self.assertEqual(json.loads(run(["cvss_calc.py", "--json", "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"]).stdout)["severity"], "Critical")
        for bad in ("AV:N/AC:L", "AV:X/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "garbage"):
            r = run(["cvss_calc.py", bad])
            self.assertEqual(r.returncode, 2, bad)
            self.assertNoTraceback(r)


class Subagents(Base):
    READ_ONLY = {"researcher", "reviewer", "security", "verifier"}

    def roles(self):
        sys.path.insert(0, SCRIPTS)
        import specialists_data
        return specialists_data.SPECIALISTS, specialists_data.VALID_TOOLS

    def test_list_show_brief(self):
        roles, _ = self.roles()
        out = run(["subagent_brief.py", "list"]).stdout
        for k in roles:
            self.assertIn(k, out)
        self.assertIn("Mission:", run(["subagent_brief.py", "show", "tester"]).stdout)
        r = run(["subagent_brief.py", "brief", "--role", "builder", "--goal", "Add CSV export", "--context", "Flask app", "--acceptance", "valid CSV", "--files", "a.py", "b.py"])
        for needle in ("**Goal:** Add CSV export", "**Acceptance criteria:** valid CSV", "- a.py", "Report back with", "## Role profile"):
            self.assertIn(needle, r.stdout)

    def test_brief_errors(self):
        self.assertEqual(run(["subagent_brief.py", "brief", "--role", "wizard", "--goal", "x"]).returncode, 2)
        self.assertEqual(run(["subagent_brief.py", "brief", "--role", "builder", "--goal", "  "]).returncode, 2)
        self.assertEqual(run(["subagent_brief.py", "show", "nope"]).returncode, 2)

    def test_specialists_doc_is_in_sync_with_data(self):
        generated = run(["subagent_brief.py", "doc"]).stdout
        with open(os.path.join(REFS, "engineering", "specialists.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), generated, "references/engineering/specialists.md is stale: regenerate with `python scripts/subagent_brief.py doc`")

    def test_every_role_is_well_formed(self):
        roles, tools = self.roles()
        self.assertGreaterEqual(len(roles), 14)
        for k, r in roles.items():
            for field in ("title", "description", "tools", "mission", "mindset", "process", "checklist", "deliverable", "pitfalls", "refs"):
                self.assertTrue(r.get(field), f"{k} missing {field}")
            for t in r["tools"].split(","):
                self.assertIn(t.strip(), tools, k)
            for ref in r["refs"]:
                self.assertTrue(os.path.exists(os.path.join(REFS, ref)), f"{k}: reference {ref} missing")
            if k in self.READ_ONLY:
                self.assertFalse({"Edit", "Write"} & {t.strip() for t in r["tools"].split(",")}, f"{k} must be read-only")

    def test_install_writes_valid_frontmatter_and_respects_existing(self):
        roles, tools = self.roles()
        dest = os.path.join(self.tmp, "agents")
        r = run(["install_subagents.py", "--dest", dest])
        self.assertEqual(r.returncode, 0, r.stderr)
        files = sorted(os.listdir(dest))
        self.assertEqual(len(files), len(roles))
        for fn in files:
            text = open(os.path.join(dest, fn), encoding="utf-8").read()
            m = re.match(r'---\nname: (nos-[\w-]+)\ndescription: "(.+?)"\ntools: ([\w, ]+)\n---\n\n', text)
            self.assertIsNotNone(m, fn)
            self.assertEqual(m.group(1) + ".md", fn)
            self.assertTrue({t.strip() for t in m.group(3).split(",")} <= tools)
        marker = os.path.join(dest, "nos-tester.md")
        open(marker, "w").write("custom")
        run(["install_subagents.py", "--dest", dest])
        self.assertEqual(open(marker).read(), "custom", "must not overwrite without --force")
        run(["install_subagents.py", "--dest", dest, "--force", "--only", "tester"])
        self.assertNotEqual(open(marker).read(), "custom")
        self.assertEqual(run(["install_subagents.py", "--dest", dest, "--only", "wizard"]).returncode, 2)
        self.assertEqual(run(["install_subagents.py", "--dest", os.path.join(self.tmp, "nope"), "--dry-run"]).returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "nope")), "--dry-run must not create files")


@unittest.skipUnless(have_cmd("node") and have_cmd("npm"), "node/npm not installed")
class Multiplayer(Base):
    def test_authoritative_server_behaviour(self):
        d = os.path.join(self.tmp, "mp")
        os.makedirs(d)
        r = run(["npm", "install", "ws", "--silent", "--no-audit", "--no-fund"], cwd=d, timeout=150)
        if r.returncode != 0:
            self.skipTest("could not install the 'ws' package (offline?)")
        env = dict(os.environ, NODE_PATH=os.path.join(d, "node_modules"))
        r = run(["node", os.path.join(ROOT, "tests", "fixtures", "mp_test.js")], timeout=60, env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("MP TEST PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
