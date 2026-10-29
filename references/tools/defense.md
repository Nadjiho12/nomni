# Tools: defending (blue team, hardening, secure engineering)

*Last updated: 2026-10-14 | Version-sensitive: CIS benchmark versions; tool names; OS hardening defaults | Re-check current docs before pinning versions, prices, or API names.*

Defensive and authorized only. Analyze logs and configurations of systems the user owns or is authorized to review. Helper: `scripts/log_triage.py` (SSH and web log triage).

## Contents
1. Scope and boundaries
2. Log analysis workflow
3. Detection engineering
4. Linux hardening checklist
5. Windows hardening checklist
6. Network and web hardening
7. Secrets and dependency hygiene
8. Threat modeling (STRIDE)
9. Incident response runbook
10. Secure code review checklists
11. Monitoring and alerting design
12. Backup and recovery
13. Learning labs (CTF, HackTheBox, TryHackMe)
14. Verification

## 1. Scope and boundaries

In scope: detection, hardening, monitoring, incident response, secure code review, threat modeling, awareness material, defensive scripts and dashboards. Authorized testing and validation workflows (scoping, rules of engagement, standard scanning, safe verification, scoring, reporting, retest, purple-team detection checks, CTF/lab learning) are covered in `tools/security-assessment.md`. Out of scope everywhere: malware, ransomware, weaponized exploit development, credential harvesting of real accounts, phishing kits, stealth/persistence/evasion tooling, DoS tools, and any unauthorized scanning or access. For questions about how attacks work, explain the concept, the detection, and the defense; do not produce working attack tooling. If a platform or law is stricter, follow the stricter rule.

## 2. Log analysis workflow

1. **Scope**: which system, which time window, what question (brute force? data exfil? privilege change?).
2. **Collect**: auth logs (`/var/log/auth.log`, `secure`, Windows Security 4624/4625/4720/4728/4672), web access/error logs, application logs, DNS, firewall.
3. **Normalize**: timestamps to UTC, parse into fields (time, source IP, user, action, result).
4. **Baseline**: what is normal for this host (hours, IP ranges, users).
5. **Hunt for patterns**: many failures from one IP; failures then success; one IP many usernames (spraying); one username many IPs; logins at odd hours; new admin/sudoers; impossible travel; 4xx floods; probes for `/.env`, `/wp-login.php`, `/phpmyadmin`, `/.git/`; unusual user-agents; spikes in outbound bytes.
6. **Correlate** across sources and build a timeline.
7. **Report**: findings ranked by severity with evidence, likely cause, and specific fix.

Quick shell triage:
```bash
grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head      # top failing IPs
grep "Accepted" /var/log/auth.log | tail -20                                                              # recent successes
last -a | head -20; lastb | head                                                                          # login history / failed
awk '$9 ~ /^4/ {print $1}' access.log | sort | uniq -c | sort -rn | head                                  # 4xx by IP
```

## 3. Detection engineering

Write detections as clear logic with false-positive notes so they port to any SIEM (Sigma-style):
```yaml
title: SSH brute force (many failures from one source)
logsource: { product: linux, service: auth }
detection:
  selection: { message|contains: "Failed password" }
  condition: selection | count() by src_ip > 10 within 5m
falsepositives: [ misconfigured automation, password managers with stale creds ]
level: medium
response: block/rate-limit source, check for later "Accepted" from same IP
```
Method: pick behavior (not indicator) → define the data source → write the condition → test on known-good and known-bad samples → tune thresholds → document the response step. Prefer behavior-based rules over IP blocklists.

## 4. Linux hardening checklist

- SSH: `PasswordAuthentication no`, `PermitRootLogin no`, key-only, `AllowUsers`, non-default port optional, `MaxAuthTries 3`; fail2ban or `sshguard`.
- Updates: unattended security upgrades; reboot policy.
- Firewall: default deny inbound (`ufw default deny incoming`, allow only needed ports).
- Accounts: no shared accounts, least-privilege `sudo`, lock unused users, strong password policy or SSO.
- Services: disable/remove what is not needed (`ss -tulpn` to review listeners).
- Files: correct permissions (`chmod 600` for keys, no world-writable), `noexec` on `/tmp` where possible, check SUID files (`find / -perm -4000 -type f 2>/dev/null`) against expectations.
- Logging: remote log shipping, `auditd` for sensitive files, time sync.
- Kernel/sysctl basics: `net.ipv4.conf.all.rp_filter=1`, `kernel.kptr_restrict=2`, ignore ICMP redirects.
- Baselines: CIS Benchmarks; audit with Lynis (`lynis audit system`).

## 5. Windows hardening checklist

BitLocker; automatic updates; local admin removed from daily accounts; LAPS for local admin passwords; SMBv1 off; RDP behind VPN/NLA with MFA; Defender + ASR rules on; PowerShell logging (Script Block, Module) enabled; audit policy for logon, process creation (4688), account management; disable legacy protocols (NTLMv1, LLMNR/NBT-NS where feasible); application control (WDAC/AppLocker) for sensitive machines. Review with CIS/Microsoft security baselines.

## 6. Network and web hardening

- Segmentation: separate user, server, and management networks; least-privilege firewall rules; egress filtering.
- DNS: filtered resolver, DoT/DoH policy, logging.
- TLS: modern versions only (1.2+, prefer 1.3), automatic renewal, HSTS.
- Headers: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`.
- WAF/rate limits on login and API endpoints; separate admin panels from public access (VPN/IP allow-list/MFA).
- Web app: parameterized queries, output encoding, CSRF tokens, secure cookies, upload validation (see `web/backend.md`).

## 7. Secrets and dependency hygiene

- Secrets: environment variables or a secrets manager; never in git; rotate on exposure. Scan history (`gitleaks detect`, `trufflehog`), add a pre-commit hook.
- Dependencies: pin versions, lockfiles, audit (`pip-audit`, `npm audit`, `osv-scanner`), automated update PRs (Dependabot/Renovate), remove unused packages.
- Supply chain: verify publishers, prefer well-maintained packages, review install scripts for critical projects.
- Containers: minimal base images, non-root user, read-only filesystems, scan images (`trivy image`).

## 8. Threat modeling (STRIDE)

Steps: (1) diagram the system (actors, processes, data stores, data flows, trust boundaries); (2) for each element ask STRIDE: **S**poofing, **T**ampering, **R**epudiation, **I**nformation disclosure, **D**enial of service, **E**levation of privilege; (3) list threats with likelihood × impact; (4) choose mitigations (authn, integrity checks, logging, encryption, rate limits, least privilege); (5) record residual risk and owners. Output a table: `Element | Threat | Impact | Mitigation | Status`.

## 9. Incident response runbook

1. **Prepare**: contacts, log retention, backups, playbooks.
2. **Identify**: confirm it is real; scope affected hosts/accounts; record start time and indicators.
3. **Contain**: isolate the host (network quarantine), disable compromised accounts, revoke tokens/keys, block indicators; preserve evidence first when feasible (memory/disk snapshot, log copies with hashes).
4. **Eradicate**: remove persistence, patch the entry point, rebuild from known-good images where trust is lost.
5. **Recover**: restore from clean backups, rotate all credentials, monitor closely.
6. **Lessons learned**: blameless timeline, root cause, detection gaps, action items with owners and dates.
Keep a timeline document (`time UTC | who | action | evidence`). Communicate with a single incident lead and a clear status cadence.

## 10. Secure code review checklists

General: authentication and authorization on every route; input validation at trust boundaries; output encoding; secrets not in code; safe error messages; logging without sensitive data; dependency risk.

| Language | Look for |
|---|---|
| PHP | string-built SQL, `include` with user input, missing `htmlspecialchars`, `unserialize` on user data, weak `md5`/`sha1` passwords, file upload flaws |
| Python | `eval/exec`, `pickle.loads` untrusted, `subprocess(..., shell=True)` with user input, SQL f-strings, `yaml.load` without SafeLoader, path traversal in file handlers |
| JavaScript/Node | `innerHTML` with user data, `eval`, prototype pollution in deep merges, `child_process.exec` with input, missing CSRF/CORS limits, JWT `none`/weak secrets |
| C/C++ | unchecked buffer sizes, format strings, integer overflow, use-after-free; prefer bounded APIs and sanitizers (`-fsanitize=address,undefined`) |
| Java/C# | deserialization of untrusted data, XXE (disable DTDs), SQL concatenation, missing authz attributes |

For each finding give: location, risk, minimal fixed code, and a test that would have caught it. Static tools: Semgrep, Bandit (Python), ESLint security plugins, CodeQL.

## 11. Monitoring and alerting design

Decide what matters (auth anomalies, privilege changes, new services, outbound spikes, integrity changes) → collect → threshold with baselines → route alerts by severity (page, channel, ticket) → dedupe/rate-limit → attach the first response step to every alert. Alert fatigue is a vulnerability: remove alerts nobody acts on. Test alerts with a controlled event.

File integrity monitoring (concept script):
```python
import hashlib, json, sys
from pathlib import Path
def snap(root): return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(root).rglob("*") if p.is_file()}
# baseline: json.dump(snap("/etc"), open("base.json","w")); check: diff current vs base, report added/removed/changed
```

## 12. Backup and recovery

3-2-1 (three copies, two media, one offsite/offline); immutable or versioned backups against ransomware; encrypt at rest; **test restores on a schedule** and record the time; document RTO/RPO; keep backup credentials separate from production credentials.

## 13. Learning labs (CTF, HackTheBox, TryHackMe)

Support learning without doing the challenge for the user or breaching platform rules: explain concepts (how a class of vulnerability works and how to detect and fix it), teach methodology (scoping, enumeration, note-taking, hypothesis → test → record), explain tool output (what an Nmap result means, how to read a log), help write clean notes and reports (finding, evidence, impact, remediation), and build study plans and cheat sheets. Follow each platform's rules on sharing solutions; keep active-challenge walkthroughs to hints unless the challenge is retired and the platform allows write-ups. Build defensive skills in parallel: for every attack technique studied, write the detection and the mitigation.

Report template: Title · Severity · Affected asset · Description · Evidence (steps, screenshots, logs) · Impact · Remediation · References.

## 14. Verification

Run `scripts/log_triage.py` on a fixture with a planted brute-force pattern and confirm it flags it; confirm hardening commands are read-only unless clearly labeled as changes; give rollback steps for every configuration change; list what was **open gap** (for example live systems, vendor-specific UI).

## 15. Labs, isolation, and ML-assisted detection

Build isolated analysis and training labs with VMs and containers: `ai/virtualization.md` (isolation spectrum, snapshots, host-only networks, sandboxing untrusted code). ML for detection (anomaly detection, alert triage) with evaluation discipline and drift monitoring: `ai/ml-dl.md` (section 12), `ai/pipelines-mlops.md`, `scripts/drift_check.py`. AI systems that handle untrusted input (prompt injection, tool abuse): `ai/architecture.md` section 9 and `ai/agents-tools.md` section 5.
