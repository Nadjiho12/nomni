# Building labs, challenges, and machines for blue and red team training

*Last updated: 2026-10-23 | Version-sensitive: CTFd/DetectionLab/GOAD/CloudGoat/Atomic Red Team/CALDERA versions and setup steps; MITRE ATT&CK technique IDs | Re-check current docs before pinning versions, prices, or API names.*

Design and operate training infrastructure: CTF-style challenges, intentionally vulnerable practice machines, detection (blue team) labs, adversary-emulation (red team) ranges, and purple-team exercises that connect the two. This is about **building the range**, not attacking anyone's systems: every exercise described here runs in an isolated lab you own, against targets you built or deployed for that purpose. Companion: `tools/security-assessment.md` (authorized assessment of real systems), `tools/defense.md` (hardening and detection), `ai/virtualization.md` (isolation mechanics). Tool: `scripts/ctf_lab.py` (challenge manifests, signed per-team flags, scoring, isolated-container templates, ATT&CK coverage tracking).

## Contents
1. What this file does and does not cover
2. Range topology and isolation
3. Vulnerable machines: sourcing vs building
4. CTF challenge design
5. Challenge infrastructure: flags, scoring, isolation
6. Blue team labs: detection engineering ranges
7. Red team labs: adversary emulation ranges
8. Purple team: connecting the two
9. Platforms and open-source building blocks
10. CI for ranges: does the challenge actually work?
11. Running the exercise: team formats and scoring
12. Legal, ethical, and access boundaries
13. Checklist
14. Verification

## 1. What this file does and does not cover

Covers: how to plan, structure, and automate a training range; where to source or how to compose vulnerable machines; how to design CTF challenges with working, fair flags; how to build detection (blue) and adversary-emulation (red) exercises; how to score and run the event; how to keep it safe and legal.

Does not cover: writing new exploit code, vulnerability research, or weaponizing a technique against a system you do not control — that is out of scope everywhere in this skill (`SKILL.md` safety boundary). When a challenge needs a vulnerable application, this file points to established open-source training apps or to the same documented vulnerability classes already in `tools/security-assessment.md` and `web/backend.md` — it does not generate new injectable application code. Red-team exercises here mean **benign, documented technique emulation** (the same framing as the purple-team section of `security-assessment.md`), not novel attack development.

## 2. Range topology and isolation

Every range, whatever its purpose, has the same shape:

```
[Internet]                         (usually: none — ranges are isolated)
     |
[Management network] -- admin access, scoring server, logging collector
     |
[Range network(s)] -- internal only, no egress unless a specific exercise needs it
     |-- target/vulnerable hosts
     |-- attacker/tooling hosts (red exercises)
     |-- sensor/SIEM hosts (blue exercises)
```

Rules, regardless of scale:
- **No route to production or the real internet** unless one exercise explicitly needs outbound access (e.g., testing DNS exfil detection), and then only through an allow-listed, logged egress point.
- **Per-team or per-instance network isolation** in multi-team events: teams must not be able to see or interfere with each other's instances. Separate VLANs/networks or separate container/VM stacks per team.
- **Golden images and snapshots**: build once, snapshot, redeploy fresh for every run; never hand-patch a live range between teams.
- **Out-of-band management**: the scoring server and admin access should not be reachable from inside the range network a participant could compromise.
- **Resource limits** on every target: CPU/memory/pid caps and a wall-clock timeout, so a crashed or abused machine does not take down the event.
- Build the topology as code (Vagrant, Packer, Terraform, docker-compose, cloud-init, Ansible) so it is reproducible and destroyable (`ai/virtualization.md` section 7-8 for the isolation mechanics and reproducible-environment tooling).

## 3. Vulnerable machines: sourcing vs building

**Prefer established, maintained training apps and images** — they are reviewed, documented, and already safe to run in a lab:

| Need | Use |
|---|---|
| Web vulnerabilities (general) | OWASP Juice Shop, DVWA, WebGoat, bWAPP |
| Full vulnerable Linux hosts, varied services | Metasploitable 2/3, VulnHub images, HTB/TryHackMe-style retired boxes |
| Active Directory attack paths | GOAD (Game of Active Directory), DetectionLab's AD portion |
| Cloud misconfiguration | CloudGoat (AWS), a dedicated sandbox cloud account/project with strict budget alerts |
| Container/Kubernetes | Kubernetes Goat, a disposable kind/minikube cluster |
| Reverse engineering / pwn | crackmes.one-style binaries, pwn.college-style curated binary sets |

**Building your own machine or web challenge:** inject **one documented weakness class per machine/challenge**, drawn from the checklists already in this skill (`tools/security-assessment.md` sections 4-7, `web/backend.md` section 6) — for example a missing authorization check on an object ID (IDOR), a default credential, an exposed `.git` directory, a misconfigured S3-style bucket, a weak JWT secret. Document the intended vulnerability, the intended path to exploit it, and the intended fix in a private answer key before you ship the challenge (section 10 covers verifying there is no unintended shortcut). Keep the "intentional weakness" principle explicit in your own documentation so nobody mistakes a lab machine for a hardening reference.

**Never** base a training machine on a real production system, real customer data, or a copy of a real breach — scrub or synthesize all data.

## 4. CTF challenge design

Standard categories and what they test:

| Category | Tests | Typical difficulty levers |
|---|---|---|
| Web | Auth, access control, injection classes, logic flaws | Number of steps, obfuscation, red herrings |
| Crypto | Identifying and breaking weak constructions, encoding vs encryption | Known-weakness vs research-level |
| Forensics | Log/packet/memory/file analysis, artifact recovery | Data volume, noise, format obscurity |
| Reversing | Reading disassembly/bytecode, defeating simple obfuscation | Language/architecture, anti-analysis tricks |
| Pwn/binary exploitation | Memory safety bugs, exploit primitives in a controlled binary | Mitigations enabled (ASLR, stack canaries, etc.) |
| Network | Protocol analysis, packet crafting, sniffing | Protocol obscurity, traffic volume |
| OSINT | Finding and correlating public information (about fictional targets you control) | Breadth of sources, correlation depth |
| Misc | Logic puzzles, esoteric formats, steganography | Varies |

Design process: write the **solution first** (the intended solve path, step by step), then build the challenge backward from it so you know exactly what is required to reach the flag. Write a difficulty rating and expected solve time. Always provide 1-3 priced hints (cost deducted from points, never below zero) rather than leaving teams stuck with no signal. Playtest with someone who did not build it before the event (section 10).

## 5. Challenge infrastructure: flags, scoring, isolation

Use `scripts/ctf_lab.py` so the infrastructure is consistent and testable rather than hand-rolled per event:

```
python scripts/ctf_lab.py manifest new --out chal.json --name "Baby SQLi" --category web \
    --points 100 --difficulty easy --description "Find the admin password." --flag-secret <private-seed>
python scripts/ctf_lab.py manifest validate chal.json
python scripts/ctf_lab.py flag gen chal.json --team alice          # CATEGORY{hmac-derived-token}, per team
python scripts/ctf_lab.py compose chal.json --out docker-compose.yml   # isolation shape; you supply the app image
```
Design choices and why:
- **Per-team flags** (HMAC of challenge id + team name, keyed by a private seed) mean a leaked or shared flag only works for the team it was issued to, and a leak is attributable.
- **The private seed is never stored in plaintext** — the manifest stores only its SHA-256 hash, and the seed itself lives wherever you keep secrets for the event.
- **Manifests are validated before use**: id format, category, points range, flag format shape, hint costs, and (deliberately) a required `unintended_solution_review` flag that starts `false` and must be flipped to `true` only after a second person has solved the challenge the intended way — a cheap, enforced check against unintended shortcuts.
- **Scoring** (`ctf_lab.py score`) reads a CSV of submissions, verifies each flag with constant-time comparison, de-duplicates repeat-solves, rejects forged or malformed submissions, and applies a first-blood bonus — all auditable from the inputs.
- **Compose templates** give the isolation shape (internal-only network, read-only filesystem, dropped capabilities, resource limits, loopback-only binding) for whatever application image you plug in; they contain no application code.

## 6. Blue team labs: detection engineering ranges

Goal: give defenders real telemetry to hunt in and real detections to write and tune, without live attackers.

- **Baseline environment**: a small domain or host set with realistic, boring activity (Windows/Linux hosts, a domain controller if AD is in scope, normal logins, normal file access) so trainees learn to find the signal in noise, not just stare at an empty log.
- **Log pipeline**: forward Sysmon/auditd/firewall/application logs to a central collector (ELK/OpenSearch, Splunk free tier, Wazuh, or a simple syslog + grep setup for a small lab). DetectionLab is a maintained, scriptable starting point for a Windows+Sysmon+ELK lab.
- **Inject activity**: replay captured benign and malicious *sample* traffic (publicly available pcap/log datasets built for training), or run the red-team emulation from section 7 against the same environment and have blue team hunt the result.
- **Exercise format**: give trainees a scenario brief (not the answer), a time box, and a specific question ("was there lateral movement, and from where?"). Grade against a rubric: correct detection, correct timeline, correct scope, proposed containment.
- **Build the detection**, not just find the incident: have trainees write the actual rule (Sigma-style, as in `tools/defense.md` section 3) and then prove it fires on a replay, using `scripts/ctf_lab.py coverage` to track which ATT&CK techniques in the scenario now have a working, verified detection (status `detected`) versus still a `gap`.

## 7. Red team labs: adversary emulation ranges

Goal: practice recognizing and chaining attacker *techniques* in a safe target, using documented, benign emulation — not novel exploit development.

- **Target**: the vulnerable machines from section 3 (VulnHub/HTB-style boxes, GOAD for AD attack paths, CloudGoat for cloud).
- **Technique source**: MITRE ATT&CK for the technique catalog; emulate with established, open benign-emulation tools built for exactly this (Atomic Red Team, CALDERA) rather than hand-written exploit code. These run documented, reversible test actions (e.g., "simulate credential dumping via a benign test artifact") designed for defensive validation, matching the purple-teaming guidance already in `tools/security-assessment.md` section 13.
- **Scenario, not toolkit dump**: give trainees an objective ("reach domain admin", "exfiltrate the flag file from the finance host") and a scope, and let them chain reconnaissance → initial access → privilege escalation → lateral movement → objective using the lab's intentionally-built weaknesses, writing notes at each step (same methodology discipline as `tools/security-assessment.md` section 3).
- **Capture the chain, not just the flag**: require a short attack-path writeup (what was exploited, in what order, why it worked) in addition to the flag — this is what makes the exercise transfer to real assessment skills, and it is what `tools/security-assessment.md` section 11's report template is for.
- Track technique coverage across your challenge set with `scripts/ctf_lab.py coverage` so the range exercises a deliberate spread of ATT&CK techniques rather than the same three repeatedly.

## 8. Purple team: connecting the two

Run red and blue in the same range, in either order:
- **Red-then-blue**: red team (or the instructor, using Atomic Red Team/CALDERA) runs a scenario; blue team hunts it afterward from logs; compare blue's findings to the known-truth attack path.
- **Live purple**: red and blue run concurrently with a referee; red announces each technique just after executing it; blue confirms detection in real time or logs a gap; both sides fix immediately (red clarifies the technique, blue writes the missing rule) and re-test. This is the fastest way to close detection gaps because the feedback loop is minutes, not a report read weeks later.
- Track results the same way as an authorized purple-team engagement (`tools/security-assessment.md` section 13): a coverage matrix per technique (none/partial/full), data-source gaps, false-positive notes, and a backlog of new detections — generate it with `scripts/ctf_lab.py coverage`.

## 9. Platforms and open-source building blocks

| Purpose | Options |
|---|---|
| CTF hosting platform (challenges, scoreboard, users) | CTFd (self-hosted, widely used), rCTF, FBCTF |
| Dynamic per-team challenge deployment | CTFd's ctfd-chall-manager, Kubernetes + a scheduler, or plain docker-compose per team as in section 5 |
| Blue-team log/detection lab | DetectionLab, a self-managed ELK/OpenSearch + Sysmon stack |
| Red-team benign emulation | Atomic Red Team, MITRE CALDERA |
| AD attack-path lab | GOAD |
| Cloud misconfiguration lab | CloudGoat (keep it in a dedicated, budget-capped cloud account) |
| Vulnerable web apps | OWASP Juice Shop, DVWA, WebGoat, bWAPP |
| Vulnerable hosts/VMs | Metasploitable, VulnHub, retired HTB/THM boxes |
Pick platforms with active maintenance; pin versions; keep them inside the isolated range network (section 2), not internet-facing, unless you have specifically hardened and are prepared to operate a public-facing instance.

## 10. CI for ranges: does the challenge actually work?

Treat challenges like code: broken or unfair challenges waste an event and erode trust.
- **Solvability**: every challenge must be solved end-to-end by someone other than the author before it ships (`unintended_solution_review` in the manifest enforces this as a gate, not just a reminder).
- **No unintended shortcuts**: a second solver's job is specifically to look for an easier, unintended path (a debug endpoint left open, a predictable flag before you added the per-team HMAC, a misconfigured permission that bypasses the intended puzzle) — not just to confirm the intended path works.
- **Automated smoke test**: script a known-good solve (hit the expected endpoint, submit the expected flag) and run it whenever the challenge's container image changes; this catches "the app updated and the bug moved" before event day.
- **Manifest and flag validation in CI**: `python scripts/ctf_lab.py manifest validate *.json` over every challenge in the repo, as a pre-event gate.
- **Load test** dynamically-deployed challenges at expected concurrent-team count before the event, not during it.

## 11. Running the exercise: team formats and scoring

Formats: **jeopardy** (independent challenges, points per category/difficulty — most common and easiest to score fairly), **attack-defense** (each team runs the same vulnerable services and must patch while attacking others — needs strong per-team isolation per section 2), **king-of-the-hill** (control of a shared resource scored over time), **red-vs-blue** (section 8, scored by technique coverage rather than flags). Jeopardy is the simplest to run well; attack-defense is the most realistic but the most operationally demanding (isolation failures are not just annoying, they invalidate the event). Score jeopardy events with `scripts/ctf_lab.py score`; score red-vs-blue with the coverage tracker plus a judged rubric for detection quality and writeup quality. Decide and publish scoring rules (first-blood bonus, hint costs, tie-breaks) before the event starts, not during it.

## 12. Legal, ethical, and access boundaries

Everything in this file assumes the range is **yours**: your hardware or cloud account, your isolated network, participants who agreed to the rules, and no route to systems you do not own or have not been authorized to include. The same boundary as the rest of this skill applies: build and defend, never attack without authorization (`SKILL.md` safety boundary; `tools/security-assessment.md` section 15). Specific points for ranges:
- Get explicit opt-in from participants (what will be logged, what skills are tested, any recording).
- If the range touches a cloud account, cap spend and alert on anomalies — a misconfigured CloudGoat-style lab can rack up real charges if left running.
- If a "capture the flag" style public-facing event is ever hosted outside a fully isolated lab, that is a different risk class (real internet exposure, real abuse potential) and needs its own threat model, rate limiting, and legal review — treat it as a production system, not a lab.
- Never point red-team tooling (even benign emulation tools) at anything outside the declared range scope.
- Retired/public vulnerable images and CTF archives still carry their own licenses and usage terms; follow them.

## 13. Checklist

- [ ] Topology diagrammed; range network has no route to production or the real internet (or a specific, logged exception)
- [ ] Per-team/per-instance isolation verified, not assumed
- [ ] Machines/challenges sourced from maintained training apps, or built with one documented weakness each
- [ ] Every challenge solved end-to-end by someone other than the author (`unintended_solution_review = true`)
- [ ] Flags are per-team and signed (`ctf_lab.py flag`), not shared static strings
- [ ] Scoring rules published before the event; `ctf_lab.py manifest validate` run in CI
- [ ] Blue-team telemetry pipeline tested with a known-signature replay before relying on it
- [ ] Red-team activity uses documented benign emulation (Atomic Red Team/CALDERA), scoped to the range only
- [ ] ATT&CK coverage tracked (`ctf_lab.py coverage`) so the exercise set is deliberate, not accidental
- [ ] Participant rules, logging disclosure, and (for cloud labs) a spend cap are all in place

## 14. Verification

Run `python scripts/ctf_lab.py manifest validate` on every challenge and confirm it fails on a manifest missing `unintended_solution_review=true`; generate a flag, verify it round-trips (`flag gen` then `flag check`) and that a different team's or a forged flag is rejected; run `score` against a small submissions CSV and confirm duplicate solves are not double-counted and forged flags are rejected; confirm the compose template binds to loopback and sets `internal: true`. Mark **open gap**: actual deployment on Docker/Kubernetes/cloud (no container runtime in this environment — see `ai/virtualization.md` section 11 for what to check on your own machine), and the named third-party platforms (CTFd, DetectionLab, GOAD, CloudGoat, Atomic Red Team, CALDERA), which were not installed or run here.
