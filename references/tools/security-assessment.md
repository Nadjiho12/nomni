# Authorized security assessment (penetration testing, validation, labs)

*Last updated: 2026-10-14 | Version-sensitive: OWASP list versions, CVSS version, legal rules by country, scanner versions | Re-check current docs before pinning versions, prices, or API names.*

Scope of this file: security testing that is **authorized, scoped, documented, and aimed at fixing**. It covers planning, methodology, safe verification, scoring, reporting, retesting, purple-team detection validation, and lab learning (CTF, HackTheBox, TryHackMe). It does not cover attacking systems without permission. Companion: `defense.md` (hardening, detection, IR), `ai/virtualization.md` (labs and isolation), `scripts/cvss_calc.py` (scoring).

## Contents
1. Boundary: what NOS does and does not do
2. Authorization and rules of engagement
3. Assessment lifecycle
4. Web application checklist (OWASP-mapped)
5. API checklist
6. Network and infrastructure review
7. Cloud and configuration review
8. AI/LLM application assessment
9. Safe verification and evidence handling
10. Scoring and prioritization
11. Reporting template
12. Retest and remediation tracking
13. Purple teaming: validating detections
14. Labs, CTFs, and learning paths
15. Ethics, disclosure, and law
16. Verification

## 1. Boundary: what NOS does and does not do

**Does (with authorization and scope):** plan and scope assessments; build test plans and checklists; run standard, rate-limited discovery and vulnerability scanning with established tools; review configurations and code; reason about attack paths at the level needed to prioritize and fix; verify findings with **minimal, non-destructive evidence** (versions, misconfigurations, harmless canary markers, screenshots, logs); score and report; verify fixes; validate detections with benign emulation in an isolated lab; teach concepts, methodology, and tool output interpretation for CTFs and labs.

**Does not:** access, probe, or disrupt systems without permission; write or optimize weaponized exploits, malware, ransomware, or phishing kits; steal, harvest, or crack credentials of real accounts; build stealth, persistence, or detection-evasion tooling; run denial-of-service; exfiltrate data beyond the minimum proof; social-engineer real people without written approval and an approved platform. If the platform, the model's own policy, or the law is stricter than this file, the stricter rule wins. For active CTF challenges, give hints and methodology rather than full solutions unless the platform allows write-ups.

## 2. Authorization and rules of engagement

No authorization, no testing. Before any active step confirm in writing:
- [ ] **Owner/authorizer** with authority over every in-scope asset (not just a colleague's say-so)
- [ ] **Scope:** exact hosts/IP ranges/domains/apps/APIs/cloud accounts, environments (prod vs staging), and **explicit exclusions** (third-party services, shared hosting, payment providers)
- [ ] **Time window** and blackout periods; contacts for emergencies; stop conditions
- [ ] **Allowed techniques** and forbidden ones (no DoS, no destructive tests, no real-user data access, no social engineering unless approved)
- [ ] **Data handling:** what may be viewed or stored, how evidence is protected and destroyed
- [ ] **Credentials and test accounts** provided (prefer test accounts over real users)
- [ ] **Reporting:** format, severity scheme, disclosure and confidentiality terms
- [ ] **Third-party/cloud provider rules** reviewed (many allow testing your own resources under policy)
Rules of engagement (ROE) one-pager: parties · scope in/out · window · techniques allowed/forbidden · contacts · data handling · reporting · signatures/date. Stop and call the contact if you hit something out of scope, a production impact, or sensitive data.

## 3. Assessment lifecycle

1. **Plan:** objectives (compliance? pre-launch? incident follow-up?), scope, ROE, threat model (STRIDE), test plan with time budget.
2. **Discover (within scope):** asset inventory, technology fingerprinting, exposed services, DNS and certificate review, content/endpoint mapping at low rate. Prefer passive sources first.
3. **Identify:** automated scanning with approved profiles, configuration and dependency review, manual testing by checklist (sections 4-8). Keep a log of every command, time, and target.
4. **Validate:** confirm candidate issues with the least invasive evidence; eliminate false positives; record exact repro conditions.
5. **Assess impact:** what could an attacker reach? Combine findings into realistic attack paths for prioritization, without exploiting beyond proof.
6. **Report:** findings with evidence, risk rating, and fixes (section 11).
7. **Retest:** verify remediation (section 12) and close the loop.
Keep notes continuously (what, when, tool, result) in a structured file; screenshots with timestamps; redact secrets.

## 4. Web application checklist (OWASP-mapped)

Use OWASP Web Security Testing Guide (WSTG) and ASVS as the master checklists; Top 10 categories below with what to verify and the usual fix.
| Area | What to check (non-destructively) | Typical fix |
|---|---|---|
| Access control | Can user A reach user B's objects by changing IDs? Missing function-level checks on admin routes? | Server-side ownership checks on every request; deny by default |
| Cryptographic failures | TLS versions/ciphers, HSTS, cookie flags, sensitive data in URLs/logs, weak password hashing | TLS 1.2+, `Secure/HttpOnly/SameSite`, argon2/bcrypt, no secrets in URLs |
| Injection | Input reaching SQL/OS/LDAP/templates: does malformed input change behavior or produce errors? (use canary strings and error-based observation) | Parameterized queries, allow-list validation, output encoding |
| Insecure design | Business-logic abuse: skipped steps, race conditions, price/quantity tampering, missing rate limits | Threat-model flows; server-side state machines; limits |
| Security misconfiguration | Default creds, debug pages, directory listing, verbose errors, open storage, missing headers | Hardened baselines, remove defaults, headers (`web/production.md`) |
| Vulnerable components | Outdated frameworks/libraries/plugins (version evidence + advisories) | Patch, pin, SCA in CI |
| Authentication | Brute-force protection, lockouts, reset flows, MFA, session fixation, weak password policy | Rate limits, MFA, rotate session IDs, secure reset tokens |
| Integrity failures | Unsigned updates, insecure deserialization indicators, CI/CD trust | Signing, integrity checks, locked pipelines |
| Logging/monitoring | Are failed logins, access-control failures, and admin actions logged and alerted? | Structured security logs, alerts, retention |
| SSRF/redirects | Does the server fetch user-supplied URLs; open redirect behavior | Allow-list destinations, block internal ranges, metadata service protection |
| Client side | XSS indicators (is input reflected unencoded in a harmless marker test?), CSP quality, clickjacking, CORS | Context-aware encoding, CSP, `frame-ancestors`, strict CORS |
Tooling: browser dev tools, an intercepting proxy (Burp Community, OWASP ZAP baseline scan), `curl`, header scanners, dependency scanners (`npm audit`, `pip-audit`, `osv-scanner`), Nuclei with reviewed templates. Respect rate limits; scan staging when possible.

## 5. API checklist

OWASP API Security Top 10 themes: broken object-level authorization (IDOR across tenants), broken authentication (token handling, weak JWT validation: algorithm, expiry, audience), excessive data exposure (fields returned vs needed), lack of resource/rate limiting, broken function-level authorization (admin endpoints), mass assignment (unexpected fields accepted), security misconfiguration (CORS, verbose errors, stale versions), unsafe consumption of third-party APIs, improper inventory (shadow/old API versions), SSRF. Verify with two test accounts in different roles/tenants, malformed and oversized inputs, expired/forged tokens (against your own test tokens), and schema comparison (OpenAPI vs actual behavior).

## 6. Network and infrastructure review

Inventory exposed services and compare with expectations: `nmap -sV` on **authorized ranges** at polite timing; verify only intended ports are open; TLS configuration review; management interfaces not exposed (SSH/RDP/DB/admin panels); segmentation and egress rules; default or weak service configurations; patch levels from banners and package inventories (with credentials where permitted: authenticated scans are more accurate and less intrusive); Active Directory/identity hygiene (privileged groups, stale accounts, delegation, password policy) via read-only enumeration and configuration review; wireless and physical only if explicitly in scope. Use CIS benchmarks and vendor hardening guides as pass/fail baselines.

## 7. Cloud and configuration review

IAM: least privilege, no long-lived keys, MFA on root/admin, role trust policies, unused credentials. Storage: public buckets/containers, encryption, versioning, access logs. Network: security groups open to the world, exposed databases, metadata service protections (IMDSv2). Secrets: in code, env, images, CI logs. Logging: audit trails enabled and protected. Posture tools (open-source scanners and native posture services) give broad coverage quickly; validate their findings manually and prioritize by exposure plus data sensitivity. Infrastructure as code: scan templates (Checkov/tfsec-style) in CI.

## 8. AI/LLM application assessment

Test **your own or authorized** AI systems for: prompt injection via user input and via retrieved documents/web pages/tool results (use canary instructions such as "reply with CANARY-123" and check whether it is obeyed); system-prompt and data leakage (can another user's data or hidden instructions be extracted?); tool abuse and over-permissioned agents (can a model-triggered action exceed the user's rights?); insecure output handling (model output rendered as HTML or executed); retrieval access control (does RAG respect per-user permissions?); excessive resource use and cost abuse; training/data poisoning paths; supply chain (model and package provenance). Build a regression suite of canary tests and run it in CI (`ai/architecture.md` section 9, `ai/agents-tools.md` section 5). Report impact in terms of data exposure, unauthorized actions, and cost.

## 9. Safe verification and evidence handling

- Prove with the **minimum**: a version string plus advisory, a configuration screenshot, a response header, a harmless canary reflected in output, a read of a single non-sensitive test record you own. Stop at proof; do not pivot deeper than needed to show impact.
- Never alter or delete production data; never keep credentials or personal data longer than needed; mask sensitive values in the report.
- Log timestamps, source IP, tool, and parameters so the client can correlate with their logs.
- Store evidence encrypted; share through agreed channels; destroy per the ROE.
- If you discover a critical issue or evidence of an ongoing compromise, notify the contact immediately instead of waiting for the final report.

## 10. Scoring and prioritization

Score technical severity with CVSS (`python scripts/cvss_calc.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"`), then adjust for context: asset criticality, data sensitivity, internet exposure, compensating controls, known exploitation in the wild (CISA KEV) and exploit likelihood (EPSS). Rank by **risk = likelihood x impact** and by effort to fix. Present quick wins separately. Do not inflate severity to look important or deflate it to avoid conflict; state assumptions.

## 11. Reporting template

```
1. Executive summary (non-technical, one page): scope, overall risk, top 3 issues, recommended next steps
2. Scope and methodology: assets, dates, tools, limitations, what was not tested
3. Findings summary table: ID | title | severity | CVSS | affected asset | status
4. Detailed findings (one per issue):
   Title / ID / Severity (CVSS vector) / Affected asset
   Description (what and why it matters) | Evidence (steps, screenshots, logs; redacted)
   Impact (business terms) | Likelihood and context
   Remediation (specific, ordered, with owner suggestion and effort) | References (CWE, OWASP, advisories)
5. Positive observations (controls that worked)
6. Remediation roadmap (quick wins, 30/60/90 days)
7. Appendix: tool output, test accounts used, glossary
```
Write findings so a developer can reproduce and fix without a meeting. Keep language precise and neutral.

## 12. Retest and remediation tracking

Track each finding: status (open, in progress, fixed, accepted risk, false positive), owner, due date. Retest within the agreed window using the same evidence method; confirm no regression and no new issue introduced by the fix; update the report with retest results. Fix classes, not instances (a missing authorization check pattern usually exists in several endpoints). Add automated regression tests and CI checks (`engineering/architecture-method.md` fitness functions).

## 13. Purple teaming: validating detections

Goal: prove your detections fire. In an **isolated lab or an explicitly authorized environment**: pick behaviors from MITRE ATT&CK relevant to your threat model, run **benign emulation tests** from established open frameworks (documented, reversible test cases), confirm the telemetry is collected, the detection rule fires, the alert reaches the queue, and the response runbook works. Record per technique: coverage (none/partial/full), data source gaps, false-positive notes, and fixes. Re-run after tuning. Keep a coverage matrix and a backlog of new detections (`defense.md` section 3). Never use real malware, never test on production endpoints without written approval, and never leave test artifacts behind.

## 14. Labs, CTFs, and learning paths

- Build an isolated lab (`ai/virtualization.md` section 7): host-only networks, snapshots, a tooling VM, intentionally vulnerable targets (DVWA, OWASP Juice Shop, Metasploitable-style images, platform-provided machines).
- Learn the methodology first: scoping → enumeration → hypothesis → minimal test → record. Enumeration is most of the work; take structured notes (target, service, version, finding, next step).
- For each technique you study, also write the **detection and the mitigation** (blue-team pairing). That is how defenders and good testers think.
- Certifications and paths (for planning): eJPT, PNPT, Security+, CySA+, OSCP, GIAC; choose by role. Practice platforms: HackTheBox, TryHackMe, PortSwigger Web Security Academy, picoCTF, OverTheWire. Follow each platform's rules (no solution sharing for active challenges; no attacking the platform).
- Build a portfolio from legal work: write-ups of retired challenges, tools you built, detection rules, a home lab diagram, a sample assessment report with fictional data.

## 15. Ethics, disclosure, and law

Only test what you are authorized to test. For bug bounties, read the program scope and safe-harbor terms; stay inside them. For accidental discovery of someone else's vulnerability: stop, do not exploit, document minimally, and report through the owner's security contact or a coordinator (coordinated disclosure with a reasonable fix window). Laws on computer misuse differ by country and can criminalize even "harmless" access; when in doubt, get written permission or consult a lawyer. Protect any personal data you encounter.

## 16. Verification

Confirm the authorization checklist exists before any active step; run scans only against in-scope targets (compare target lists to scope programmatically); score at least one finding with `scripts/cvss_calc.py` and sanity-check the vector; produce the report from the template and have a developer reproduce one finding from it alone; mark live-target results **open gap** when no authorized environment was available.
