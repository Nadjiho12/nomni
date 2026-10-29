#!/usr/bin/env python3
"""Headless browser verification for web pages and browser games (Playwright + Chromium).

Turns "Verified" into evidence: loads the page, records console errors, uncaught exceptions,
failed requests, checks the canvas is not blank, samples FPS, and runs an optional scripted
scenario (clicks, keys, assertions on page state, screenshots, change detection).

Setup (once):  pip install playwright pillow && playwright install chromium
Usage:
  python verify_web.py --check-env                  # is a usable headless browser available here?
  python verify_web.py game.html
  python verify_web.py game.html --mobile --out shots
  python verify_web.py game.html --scenario scenario.json
  python verify_web.py page.html --route "cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js=./three.min.js"

Options:
  --viewport 1280x720     --mobile (touch, 2x DPR, 390x844 unless --viewport given)
  --route SUBSTR=FILE     answer any request whose URL contains SUBSTR from a local FILE (repeatable);
                          use when the network is blocked or to pin a library version
  --settle MS             wait after load before checks (default 1500)
  --fps-seconds S         FPS sampling window (default 2, 0 disables)
  --skip-draw             logic-only fast mode: WebGL draw calls become no-ops, so game logic runs at CPU
                          speed instead of ~1 fps under software GL. Screenshots are not meaningful in this
                          mode; use a normal run for visuals and a --skip-draw run for gameplay assertions
  --axe PATH              run the axe-core accessibility audit (PATH to axe.min.js, e.g. node_modules/axe-core/axe.min.js
                          after `npm i axe-core`); critical/serious violations FAIL, moderate/minor WARN
  --out DIR               screenshots + report.json (default ./verify-out)

Scenario JSON = list of steps:
  {"do":"wait","ms":500}
  {"do":"click","selector":"button#start"}            or {"do":"click","x":200,"y":300}
  {"do":"tap","x":200,"y":300}                        touch tap (use with --mobile)
  {"do":"press","key":"KeyW","hold":800}              hold a key (KeyboardEvent.code names)
  {"do":"mouse","x":300,"y":200,"down":true}          move, optional down/up
  {"do":"drag","from":[100,300],"to":[250,300]}
  {"do":"eval","js":"A.length","expect":10,"label":"ten actors"}
      expect: literal, or {"gt":n,"gte":n,"lt":n,"lte":n,"eq":v,"contains":s,"truthy":true}
  {"do":"wait_for","js":"mode==='play'","timeout":8000}
  {"do":"text","selector":"#msg","contains":"WIN"}
  {"do":"shot","name":"menu"}
  {"do":"changed","a":"menu","b":"play","min":0.01}   fraction of pixels that differ between two shots
Top-level lexical globals (let/const in a classic <script>) are readable from "eval" by name.
Exit codes: 0 all checks passed; 1 at least one FAIL; 2 usage/input error; 3 browser unavailable (Chromium or Playwright not
installed or cannot launch: run with --check-env to diagnose). WARN and INFO never fail the run.
"""
import argparse
import functools
import http.server
import io
import json
import mimetypes
import os
import re
import sys
import threading

try:
    from PIL import Image, ImageChops
except ImportError:  # pixel checks degrade to INFO
    Image = ImageChops = None

RESULTS = []


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def unavailable(msg):
    print("error: browser unavailable: " + msg, file=sys.stderr)
    print("Verification could not run here. Record browser behavior as an open gap, or install Chromium and re-run. Static checks still work: scripts/lint_html.py.", file=sys.stderr)
    sys.exit(3)


def rec(status, name, detail=""):
    RESULTS.append({"status": status, "name": name, "detail": detail})
    print(f"[{status:4}] {name}" + (f"  -  {detail}" if detail else ""))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=directory))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def stats(png):
    """(unique colors in a 64x64 downsample) for blank-screen detection."""
    if Image is None:
        return None
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((64, 64))
    return len(im.getcolors(maxcolors=64 * 64) or [])


def diff_fraction(p1, p2):
    a = Image.open(io.BytesIO(p1)).convert("L").resize((96, 96))
    b = Image.open(io.BytesIO(p2)).convert("L").resize((96, 96))
    d = ImageChops.difference(a, b)
    hist = d.histogram()
    return sum(hist[17:]) / (96 * 96)


def check_expect(val, exp):
    if isinstance(exp, dict):
        ok = True
        if "gt" in exp: ok &= val > exp["gt"]
        if "gte" in exp: ok &= val >= exp["gte"]
        if "lt" in exp: ok &= val < exp["lt"]
        if "lte" in exp: ok &= val <= exp["lte"]
        if "eq" in exp: ok &= val == exp["eq"]
        if "contains" in exp: ok &= exp["contains"] in str(val)
        if "truthy" in exp: ok &= bool(val) == bool(exp["truthy"])
        return ok
    if isinstance(exp, bool):
        return bool(val) == exp
    return val == exp


def run_step(page, st, shots, out):
    do = st["do"]
    label = st.get("label") or do
    if do == "wait":
        page.wait_for_timeout(st.get("ms", 500))
    elif do == "click":
        if "selector" in st:
            page.click(st["selector"], timeout=st.get("timeout", 5000))
        else:
            page.mouse.click(st["x"], st["y"])
    elif do == "tap":
        page.touchscreen.tap(st["x"], st["y"])
    elif do == "press":
        page.keyboard.down(st["key"])
        page.wait_for_timeout(st.get("hold", 100))
        page.keyboard.up(st["key"])
    elif do == "mouse":
        page.mouse.move(st["x"], st["y"])
        if st.get("down") is True: page.mouse.down()
        if st.get("down") is False: page.mouse.up()
    elif do == "drag":
        (x1, y1), (x2, y2) = st["from"], st["to"]
        page.mouse.move(x1, y1); page.mouse.down(); page.mouse.move(x2, y2, steps=8); page.mouse.up()
    elif do == "eval":
        val = page.evaluate(st["js"])
        if "expect" in st:
            rec("PASS" if check_expect(val, st["expect"]) else "FAIL", label, f"{st['js']} = {val!r}, expected {st['expect']!r}")
        else:
            rec("INFO", label, f"{st['js']} = {val!r}")
    elif do == "wait_for":
        try:
            page.wait_for_function(st["js"], timeout=st.get("timeout", 8000), polling=100)
            rec("PASS", label if "label" in st else "wait_for", st["js"])
        except Exception:
            rec("FAIL", label if "label" in st else "wait_for", f"timed out: {st['js']}")
    elif do == "text":
        t = page.inner_text(st["selector"], timeout=st.get("timeout", 3000))
        rec("PASS" if st["contains"] in t else "FAIL", label if "label" in st else "text", f"{st['selector']} = {t!r}, expected to contain {st['contains']!r}")
    elif do == "shot":
        png = page.screenshot(path=os.path.join(out, st["name"] + ".png"))
        shots[st["name"]] = png
        u = stats(png)
        rec("INFO", f"shot {st['name']}", f"{u} distinct colors (64x64 sample)" if u is not None else "saved")
    elif do == "changed":
        if Image is None:
            rec("WARN", "changed", "Pillow missing; pip install pillow")
        else:
            f = diff_fraction(shots[st["a"]], shots[st["b"]])
            rec("PASS" if f >= st.get("min", 0.01) else "FAIL", label if "label" in st else f"changed {st['a']}->{st['b']}", f"{f:.1%} of pixels differ (min {st.get('min', 0.01):.1%})")
    else:
        rec("FAIL", "step", f"unknown step {do!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?")
    ap.add_argument("--check-env", action="store_true", help="only check that Playwright + Chromium (and WebGL) work")
    ap.add_argument("--viewport")
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--route", action="append", default=[])
    ap.add_argument("--settle", type=int, default=1500)
    ap.add_argument("--fps-seconds", type=float, default=2)
    ap.add_argument("--skip-draw", action="store_true")
    ap.add_argument("--axe")
    ap.add_argument("--scenario")
    ap.add_argument("--out", default="verify-out")
    a = ap.parse_args()
    LAUNCH_ARGS = ["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader",
                   "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        unavailable("Python package 'playwright' is not installed: pip install playwright pillow && playwright install chromium")

    if a.check_env:
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(args=LAUNCH_ARGS)
                pg = b.new_page()
                pg.set_content("<canvas id=c></canvas>")
                gl = pg.evaluate("!!document.getElementById('c').getContext('webgl')")
                ver = b.version
                b.close()
        except Exception as e:  # noqa: BLE001
            unavailable(f"Chromium cannot launch: {str(e).splitlines()[0][:160]}")
        print(f"OK: Chromium {ver} launches headless; WebGL {'available' if gl else 'NOT available (3D pages will not render)'}; Pillow {'available' if Image else 'missing (pixel checks degrade): pip install pillow'}")
        sys.exit(0)
    if not a.target:
        die("give a page/folder/URL to verify (or --check-env)")
    if a.settle < 0 or a.fps_seconds < 0:
        die("--settle and --fps-seconds must be >= 0")
    os.makedirs(a.out, exist_ok=True)

    srv = None
    if a.target.startswith(("http://", "https://")):
        url = a.target
    else:
        path = os.path.abspath(a.target)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if not os.path.exists(path):
            die(f"{path} not found")
        srv = serve(os.path.dirname(path))
        url = f"http://127.0.0.1:{srv.server_address[1]}/{os.path.basename(path)}"

    routes = []
    for r in a.route:
        sub, sep, f = r.partition("=")
        if not sep or not sub or not f:
            die(f"--route must look like SUBSTR=FILE, got {r!r}")
        if not os.path.exists(f):
            die(f"route file {f} not found")
        routes.append((sub, f))

    vw, vh = (390, 844) if a.mobile else (1280, 720)
    if a.viewport:
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", a.viewport.lower())
        if not m:
            die(f"--viewport must look like 1280x720, got {a.viewport!r}")
        vw, vh = int(m[1]), int(m[2])

    logs, errors, failed, bad = [], [], [], []
    shots = {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=LAUNCH_ARGS)
        except Exception as e:  # noqa: BLE001
            unavailable(f"Chromium cannot launch: {str(e).splitlines()[0][:160]}")
        ctx = browser.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=2 if a.mobile else 1,
                                  is_mobile=a.mobile, has_touch=a.mobile)
        if a.skip_draw:
            ctx.add_init_script("""for (const C of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) { if (!C) continue;
              for (const f of ['drawElements','drawArrays','drawElementsInstanced','drawArraysInstanced','drawRangeElements','clear'])
                if (C.prototype[f]) C.prototype[f] = function(){}; }""")
        page = ctx.new_page()
        page.on("console", lambda m: logs.append((m.type, m.text)))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append((r.url, r.failure)))
        page.on("response", lambda r: bad.append((r.url, r.status)) if r.status >= 400 else None)

        def handler(route):
            u = route.request.url
            for sub, f in routes:
                if sub in u:
                    ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
                    return route.fulfill(status=200, body=open(f, "rb").read(), content_type=ctype)
            route.continue_()
        if routes:
            page.route("**/*", handler)

        try:
            page.goto(url, wait_until="load", timeout=30000)
            rec("PASS", "page loads", url)
        except Exception as e:
            rec("FAIL", "page loads", str(e).splitlines()[0])
            browser.close()
            finish(a.out)
        page.wait_for_timeout(a.settle)

        if a.scenario:
            try:
                steps = json.load(open(a.scenario, encoding="utf-8"))
            except (OSError, ValueError) as e:
                die(f"cannot read scenario: {e}")
            if not isinstance(steps, list) or not all(isinstance(x, dict) and "do" in x for x in steps):
                die("scenario must be a JSON list of objects, each with a 'do' key")
            for i, st in enumerate(steps):
                try:
                    run_step(page, st, shots, a.out)
                except Exception as e:
                    rec("FAIL", f"step {i + 1} ({st.get('do')})", str(e).splitlines()[0][:200])

        # automatic checks
        png = page.screenshot(path=os.path.join(a.out, "final.png"))
        u = stats(png)
        if a.skip_draw:
            rec("INFO", "blank-screen check", "skipped in --skip-draw mode")
        elif u is None:
            rec("WARN", "blank-screen check", "Pillow missing; pip install pillow")
        else:
            rec("PASS" if u > 2 else "FAIL", "screen is not blank", f"{u} distinct colors in final screenshot (a uniform or 2-color screen is treated as blank)")
        for i, c in enumerate(page.query_selector_all("canvas")):
            bb = c.bounding_box()
            if not bb or bb["width"] < 50 or bb["height"] < 50:
                rec("WARN", f"canvas #{i}", "tiny or hidden")
        if a.axe:
            if not os.path.exists(a.axe):
                rec("WARN", "accessibility (axe)", f"{a.axe} not found; npm i axe-core")
            else:
                try:
                    page.add_script_tag(path=a.axe)
                    res = page.evaluate("axe.run().then(r => r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, sample: v.nodes[0].target.join(' ')})))")
                    for v in res:
                        rec("FAIL" if v["impact"] in ("critical", "serious") else "WARN", f"a11y: {v['id']} ({v['impact']})", f"{v['help']}; {v['nodes']} element(s), e.g. {v['sample']}")
                    if not res:
                        rec("PASS", "accessibility (axe)", "no automated violations (automation finds only part of real issues; also test with a keyboard)")
                except Exception as e:
                    rec("WARN", "accessibility (axe)", str(e).splitlines()[0][:150])
        over = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        rec("PASS" if over <= 1 else "WARN", "no horizontal scroll", f"overflow {over}px" if over > 1 else "")
        if a.fps_seconds > 0:
            r = page.evaluate("""d => new Promise(res => { let n=0, s=performance.now(), last=s, mx=0;
                function f(t){ n++; mx=Math.max(mx,t-last); last=t; if (t-s < d*1000) requestAnimationFrame(f); else res({n, ms:t-s, mx}); }
                requestAnimationFrame(f); })""", a.fps_seconds)
            fps = r["n"] / (r["ms"] / 1000)
            rec("PASS" if fps >= 20 else "WARN", "frame rate", f"{fps:.0f} fps avg, worst frame {r['mx']:.0f} ms (software rendering is slower than a real GPU)")
        browser.close()

    errs = [t for k, t in logs if k == "error"]
    rec("PASS" if not errors else "FAIL", "no uncaught exceptions", "; ".join(errors[:3]))
    rec("PASS" if not errs else "FAIL", "no console.error", "; ".join(errs[:3]))
    warns = [t for k, t in logs if k == "warning"]
    if warns:
        rec("INFO", "console warnings", f"{len(warns)}: {warns[0][:140]}")
    ext = [(u, s) for u, s in bad if not u.startswith("http://127.0.0.1")]
    loc = [(u, s) for u, s in bad if u.startswith("http://127.0.0.1")]
    rec("PASS" if not loc else "FAIL", "no failed local requests", "; ".join(f"{s} {u}" for u, s in loc[:3]))
    fext = [u for u, _ in failed if not u.startswith("http://127.0.0.1")]
    if ext or fext:
        rec("WARN", "external requests failed", "; ".join([f"{s} {u}" for u, s in ext[:2]] + fext[:2]) + "  (blocked network? map them with --route SUBSTR=FILE)")
    finish(a.out)


def finish(out):
    json.dump(RESULTS, open(os.path.join(out, "report.json"), "w"), indent=1)
    c = {k: sum(1 for r in RESULTS if r["status"] == k) for k in ("PASS", "FAIL", "WARN", "INFO")}
    print(f"\n{c['PASS']} pass, {c['FAIL']} fail, {c['WARN']} warn, {c['INFO']} info. Screenshots and report.json in {out}/")
    sys.exit(1 if c["FAIL"] else 0)


if __name__ == "__main__":
    main()
