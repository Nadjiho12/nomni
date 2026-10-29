# N-Omni

N-Omni is a Claude Code plugin for building, designing, researching, and writing. It groups nine domain skills, 25 specialist agents, and 17 connector definitions into one installable package.

## Status

The plugin's 117 automated tests pass on Linux. The plugin is not yet installed in Claude Code.

## What is included

| Part | Count | Location |
|---|---|---|
| Domain skills | 9 | `skills/` |
| Specialist agents | 25 | `agents/` |
| Connector definitions | 17 | `.mcp.json` |
| Reference files | 47 | `references/` |
| Scripts | 20+ | `scripts/` |
| Tests | 117 passing | `tests/` |

## Skills

Each skill is a short entry point with its own description and links to the references it needs.

- `web`: websites and web apps, frontend, backend, design, and production readiness
- `games`: browser, mobile, and engine games, genres, multiplayer, and release
- `tools`: automation, bots, defensive security, authorized assessments, and lab design
- `writing`: prose, editing, documentation, fiction, and nonfiction
- `ai`: AI system design, machine learning, RAG, agents, reinforcement learning, vision, and pipelines
- `business`: business models, pricing, forecasting, marketing, and operations
- `engineering`: architecture, reviews, the five-phase workflow, specialists, and DevOps
- `thinking`: idea generation, critical review, and decision support
- `extras`: mobile, embedded and IoT, CAD and 3D printing, audio, data recipes, and browser verification

## Agents

Agents are specialist roles. Read-only agents cannot edit the work they judge.

| Group | Agents |
|---|---|
| Build | builder, mobile-dev, embedded-dev, game-dev, ui-builder |
| Check | tester, reviewer, verifier, security-auditor, debugger |
| Design | architect, designer, ux-designer |
| Plan and manage | planner, manager, release-manager |
| Research and analysis | researcher, analyzer, data-analyst, data-ml, business-analyst |
| Write and document | writer, documentation, content-strategist |
| Operate | devops |

The manager writes assignments and routes outputs. It does not start other agents by itself, because I could not confirm how Claude Code delegation works in this setup.

## Connectors

The connectors are remote HTTP endpoints taken from the connector registry. Each one requires you to sign in with your own account before it works.

| Area | Connectors |
|---|---|
| Design | Figma, Lovable, Adobe, Gamma, Moda, Send |
| Email, files, and calendar | Gmail, Google Drive, Google Docs, Google Sheets, Google Slides, Google Calendar |
| Knowledge and audit | Rockhopper |
| Finance | Aleph |
| Marketing and video | vidIQ, Orshot |
| Usability testing | TheySaid |

Not yet included: Higgsfield (not found in the registry) and an automation service (needs a specific product name and endpoint).

## Using the plugin

Skills are intended to be invoked with the plugin namespace, for example `/n-omni:web` or `/n-omni:business`. Claude can also choose a skill from a plain request. Neither behavior has been tested yet.

## Safety

N-Omni builds, defends, and supports authorized security work only. It does not produce malware, exploit tooling, credential theft, phishing material, or denial-of-service tools. Security testing must be scoped and authorized, as described in `references/tools/security-assessment.md`.

## Development

Run the test suite from the plugin root:

```
python tests/run_tests.py
```

Tests that need a missing tool, such as PHP or Chromium, are reported as skipped with the reason.

## License

UNLICENSED. A license has not been chosen.
