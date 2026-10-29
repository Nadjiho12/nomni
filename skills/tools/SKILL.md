---
name: tools
description: "Automation scripts, scheduled jobs, Discord/Telegram/Slack bots, CLI tools, and authorized defensive security: log analysis, hardening, detection, incident response, authorized assessments with rules of engagement, CVSS scoring, and lab/CTF/range design. Use for any automation or security-related request within the authorized scope."
---

# N-Omni: tools

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| Automation scripts: organize files, cron/scheduled nightly backup, APIs with retry, scraping etiquette, Playwright, CLI tools, data jobs | `references/tools/automation.md` |
| Discord, Telegram, Slack bots: slash commands, reminders, moderation, hosting | `references/tools/bots.md` |
| Defensive security: log analysis (brute force, auth logs), hardening (SSH, Linux, Windows), detection rules, incident response runbook, secure code review, backups | `references/tools/defense.md` |
| Authorized security assessment: scope an authorized penetration test, rules of engagement, safe verification, CVSS scoring, vulnerability reports, retest, purple team, CTF/lab learning | `references/tools/security-assessment.md` |
| Building training labs, CTF challenges, vulnerable machines, blue-team detection ranges, red-team emulation ranges, scoring and flags | `references/tools/lab-range-design.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
