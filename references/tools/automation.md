# Tools: automation

*Last updated: 2026-09-30 | Version-sensitive: library versions (Playwright, requests); OS scheduler details | Re-check current docs before pinning versions, prices, or API names.*

Starter: `scripts/scaffold.py py-cli <dir>`. Principles apply to Python, Bash, PowerShell, and Node.

## Contents
1. Language choice
2. Non-negotiable principles
3. Python recipes
4. Bash and PowerShell recipes
5. Scheduling
6. API clients with retry
7. Web automation (Playwright) and scraping etiquette
8. File and data automation
9. Watchers and pipelines
10. Packaging and distribution
11. Verification

## 1. Language choice

| Need | Pick |
|---|---|
| Glue, files, APIs, data | Python 3 (stdlib first) |
| Linux/macOS one-liners and pipelines | Bash with `set -euo pipefail` |
| Windows admin | PowerShell |
| Web-adjacent CLI, npm ecosystem | Node.js |
| Single distributable binary, speed | Go or Rust |

## 2. Non-negotiable principles

- **Idempotent**: a second run changes nothing. Check state before acting.
- **`--dry-run`** prints intended actions; destructive steps need `--yes`.
- **Fail loudly**: non-zero exit, clear message, no bare `except`.
- **Retry only transient errors** (timeouts, 429, 5xx) with exponential backoff and a cap.
- **Config** via flags/env vars; secrets never in source, logs, or shell history.
- **Atomic writes**: write to a temp file, then rename.
- **Guard deletes**: verify the path is inside the expected root and non-empty before removing.
- **Log** with timestamps and levels; log what changed, not secrets.

## 3. Python recipes

```python
# Organize a folder by file type (dry-run aware, collision-safe)
import shutil, argparse
from pathlib import Path
MAP = {".jpg":"Images",".png":"Images",".pdf":"Docs",".docx":"Docs",".mp3":"Audio",".zip":"Archives"}
def organize(root: Path, dry: bool):
    for p in root.iterdir():
        if not p.is_file() or p.suffix.lower() not in MAP: continue
        dest = root / MAP[p.suffix.lower()] / p.name
        i = 1
        while dest.exists(): dest = dest.with_name(f"{p.stem}_{i}{p.suffix}"); i += 1
        print(("would move " if dry else "moving ") + f"{p} -> {dest}")
        if not dry: dest.parent.mkdir(exist_ok=True); shutil.move(str(p), dest)
```
```python
# Duplicate finder by content hash
import hashlib, collections
def sha(p, n=1<<20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(n): h.update(chunk)
    return h.hexdigest()
def dupes(root):
    seen = collections.defaultdict(list)
    for p in Path(root).rglob("*"):
        if p.is_file(): seen[(p.stat().st_size, sha(p))].append(p)
    return [v for v in seen.values() if len(v) > 1]
```
```python
# Timestamped backup with rotation
import zipfile, time
def backup(src: Path, dst_dir: Path, keep=7):
    dst_dir.mkdir(exist_ok=True); name = dst_dir / f"{src.name}-{time.strftime('%Y%m%d-%H%M%S')}.zip"
    with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
        for p in src.rglob("*"):
            if p.is_file(): z.write(p, p.relative_to(src))
    for old in sorted(dst_dir.glob(f"{src.name}-*.zip"))[:-keep]: old.unlink()
```
```python
# Bulk rename with preview
import re
def rename(root: Path, pattern: str, repl: str, dry=True):
    for p in sorted(root.iterdir()):
        new = re.sub(pattern, repl, p.name)
        if new != p.name: print(f"{p.name} -> {new}"); (not dry) and p.rename(p.with_name(new))
```
Other common jobs: CSV merge/clean (pandas), PDF merge/split (pypdf), image resize (Pillow), email reports (`smtplib` + app password from env), clipboard tools, system info reports (`psutil`), zip/unzip, JSON/YAML conversion.

## 4. Bash and PowerShell recipes

```bash
#!/usr/bin/env bash
set -euo pipefail
DRY=${DRY:-1}
run(){ if [[ $DRY == 1 ]]; then echo "+ $*"; else "$@"; fi; }
# delete files older than 30 days in a specific dir
dir=${1:?usage: $0 DIR}; [[ -d $dir && $dir != / ]] || { echo bad dir; exit 2; }
find "$dir" -type f -mtime +30 -print0 | while IFS= read -r -d '' f; do run rm -- "$f"; done
```
```bash
# Log the top 10 IPs in an access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
# Retry a command 5 times with backoff
for i in {1..5}; do cmd && break || sleep $((2**i)); done
```
```powershell
# PowerShell: find large files, dry-run friendly
Get-ChildItem C:\Data -Recurse -File | Where-Object Length -gt 500MB |
  Sort-Object Length -Descending | Select-Object -First 20 FullName, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}
# Remove old logs with -WhatIf first
Get-ChildItem C:\Logs -Filter *.log | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item -WhatIf
```

## 5. Scheduling

| Platform | How |
|---|---|
| Linux/macOS | `crontab -e` → `30 2 * * * /usr/bin/python3 /opt/job.py >> /var/log/job.log 2>&1` |
| systemd | `job.service` + `job.timer` (`OnCalendar=daily`, `Persistent=true`), `systemctl enable --now job.timer` |
| Windows | Task Scheduler (`schtasks /create /sc daily /st 02:30 /tn Job /tr "python C:\job.py"`) |
| Cloud | GitHub Actions `schedule: cron`, cloud scheduler |

Always: absolute paths, explicit environment (cron has a minimal `PATH`), lock file to prevent overlap (`flock -n /tmp/job.lock cmd`), log to a file, alert on failure.

## 6. API clients with retry

```python
import time, requests
def get_json(url, *, tries=5, timeout=10, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, timeout=timeout, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("Retry-After", 2 ** i)); time.sleep(wait); continue
            r.raise_for_status(); return r.json()
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2 ** i)
    raise RuntimeError(f"gave up on {url}")
# Pagination: loop while response has next cursor/page; respect rate limits (sleep between pages)
```
Auth: API keys from env (`os.environ["API_KEY"]`), OAuth via the provider's library, never commit tokens.

## 7. Web automation (Playwright) and scraping etiquette

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page()
    page.goto("https://example.com"); page.get_by_role("link", name="More").click()
    page.wait_for_load_state("networkidle"); print(page.title()); page.screenshot(path="shot.png"); b.close()
# install: pip install playwright && playwright install chromium
```
Prefer role/test-id selectors and explicit waits over `sleep`. Etiquette: use an official API first; read the site's terms and `robots.txt`; identify your client; rate-limit (1-2 requests/s or slower); cache responses; do not bypass logins, paywalls, CAPTCHAs, or protections; automate only what you are allowed to.

## 8. File and data automation

- CSV/Excel: pandas (`read_csv`, `merge`, `groupby`, `to_excel`), openpyxl for formatting/formulas; keep the original file untouched and write a new output.
- PDF: `pypdf` (merge, split, rotate), `pdfplumber` (text/tables).
- Images: Pillow (`resize`, `thumbnail`, `convert`), batch with `glob`.
- Text: regex extraction with named groups; validate before writing; handle encodings (`utf-8`, `errors="replace"`).
- Reports: generate Markdown/HTML/XLSX summaries with counts and the top N issues.

## 9. Watchers and pipelines

```python
# Poll-based folder watcher (no dependencies); use watchdog for events at scale
import time
seen = set()
while True:
    for p in Path("inbox").glob("*.csv"):
        if p not in seen: process(p); seen.add(p)
    time.sleep(5)
```
Pipeline shape: **read → validate → transform → write**, log row counts at each stage, quarantine bad rows to a separate file, keep raw input immutable, make every stage rerunnable.

## 10. Packaging and distribution

`pyproject.toml` with an entry point (`[project.scripts] mytool = "mytool.cli:main"`), `pipx install .`; single executable with PyInstaller (`pyinstaller --onefile tool.py`); Node: `bin` field + `npm link`; include README with install, usage, examples, and exit codes.

## 11. Verification

Run on a small fixture; run twice and confirm no second-run changes; compare `--dry-run` output to real behavior; force one failure (missing file, bad token, no network) and confirm a clear error and non-zero exit; grep for secrets; list dependencies and Python/Node versions.
