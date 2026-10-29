#!/usr/bin/env python3
"""Fast HTML sanity linter (no dependencies).

Checks: <html lang>, <title>, viewport meta, meta description, exactly one <h1>,
heading order, <img alt>, form controls with labels, duplicate ids, empty links,
buttons without text, inline event handlers count.

Usage:
  python lint_html.py index.html [more.html ...]
Exit code 1 if any ERROR is found.
"""
import sys
from html.parser import HTMLParser


class Linter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.issues = []
        self.ids = {}
        self.h1 = 0
        self.last_h = 0
        self.has_title = False
        self.has_viewport = False
        self.has_desc = False
        self.has_lang = False
        self.label_for = set()
        self.controls = []
        self.stack = []
        self.text_buf = []
        self.inline_handlers = 0

    def add(self, level, msg):
        self.issues.append((level, msg))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "title":
            self.has_title = True
        if tag == "meta":
            if a.get("name") == "viewport":
                self.has_viewport = True
            if a.get("name") == "description" and a.get("content"):
                self.has_desc = True
        if tag == "h1":
            self.h1 += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = int(tag[1])
            if self.last_h and lvl > self.last_h + 1:
                self.add("WARN", f"line {line}: heading jumps from h{self.last_h} to h{lvl}")
            self.last_h = lvl
        if tag == "img" and "alt" not in a:
            self.add("ERROR", f"line {line}: <img> missing alt")
        if "id" in a:
            if a["id"] in self.ids:
                self.add("ERROR", f"line {line}: duplicate id '{a['id']}' (first at line {self.ids[a['id']]})")
            self.ids[a["id"]] = line
        if tag == "label" and a.get("for"):
            self.label_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit", "button"):
            self.controls.append((line, a.get("id"), a.get("aria-label") or a.get("aria-labelledby")))
        if any(k.startswith("on") for k in a):
            self.inline_handlers += 1
        if tag in ("a", "button"):
            self.stack.append((tag, line, a))
            self.text_buf.append("")

    def handle_data(self, data):
        if self.text_buf:
            self.text_buf[-1] += data.strip()

    def handle_endtag(self, tag):
        if tag in ("a", "button") and self.stack:
            t, line, a = self.stack.pop()
            txt = self.text_buf.pop()
            if not txt and not a.get("aria-label") and not a.get("title"):
                self.add("WARN", f"line {line}: <{t}> has no visible text or aria-label")
            if t == "a" and not a.get("href"):
                self.add("WARN", f"line {line}: <a> without href")

    def finish(self):
        if not self.has_lang:
            self.add("ERROR", "<html> missing lang attribute")
        if not self.has_title:
            self.add("ERROR", "missing <title>")
        if not self.has_viewport:
            self.add("ERROR", "missing viewport meta (mobile layout will break)")
        if not self.has_desc:
            self.add("WARN", "missing meta description (SEO)")
        if self.h1 != 1:
            self.add("WARN", f"expected exactly one <h1>, found {self.h1}")
        for line, cid, aria in self.controls:
            if not (cid and cid in self.label_for) and not aria:
                self.add("WARN", f"line {line}: form control without <label for> or aria-label")
        if self.inline_handlers > 5:
            self.add("INFO", f"{self.inline_handlers} inline event handlers; consider addEventListener")


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="HTML files to check")
    args = ap.parse_args()
    bad = False
    for path in args.files:
        lin = Linter()
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lin.feed(f.read())
        except OSError as e:
            print(f"error: cannot read {path}: {e.strerror}", file=sys.stderr)
            sys.exit(2)
        lin.finish()
        print(f"== {path}: {len(lin.issues)} issue(s)")
        for level, msg in lin.issues:
            print(f"  [{level}] {msg}")
            bad = bad or level == "ERROR"
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
