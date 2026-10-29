# Agents and tool building

*Last updated: 2026-10-13 | Version-sensitive: agent SDKs, MCP specification and SDK versions, model tool-calling features | Re-check current docs before pinning versions, prices, or API names.*

Design AI that takes actions safely: typed tools, bounded loops, sandboxing, evaluation of trajectories. Also how to build tools and MCP servers that models can use well.

## Contents
1. Agent or workflow?
2. The agent loop
3. Designing tools for models
4. Tool schema and implementation example
5. Safety and permissions
6. Memory and context management
7. Multi-agent patterns
8. Evaluation and debugging
9. MCP servers
10. Coding and computer-use agents
11. Verification

## 1. Agent or workflow?

A **workflow** follows a fixed path with an LLM inside steps; an **agent** lets the model choose steps and tools in a loop. Use workflows when the steps are knowable (cheaper, faster, testable). Use agents when the path depends on discoveries (research, debugging, open-ended operations). Start simple; add autonomy only where evals show it helps.

## 2. The agent loop

```
state = {goal, history, budget}
repeat until done or budget exhausted:
    decision = model(state, tools)            # think, then call a tool or answer
    if decision is tool_call:
        validate(args) -> authorize(user, tool, args) -> execute(sandbox, timeout) -> observation
        state.history += (decision, observation)
    else: return decision.answer (validated)
```
Controls: max steps, max tokens, wall-clock timeout, per-tool rate limits, a "stuck" detector (repeated identical calls), cost accounting, and a human-approval gate for irreversible steps.

## 3. Designing tools for models

- **One clear purpose per tool**, named like a verb phrase (`search_orders`, `create_ticket`). Fewer, well-described tools beat many overlapping ones.
- **Descriptions are prompts:** say what it does, when to use it, when not to, units and formats, and give an example call.
- **Typed, strict parameters** (enums instead of free text; ISO dates; IDs not names); reject unknown fields.
- **Return compact, informative results:** only needed fields, human-readable errors with how to fix ("`date` must be YYYY-MM-DD"), pagination tokens, and a `truncated` flag.
- **Idempotent and safe by default:** read-only tools separate from write tools; dry-run option; idempotency keys for writes.
- **Deterministic outputs** where possible; include source/timestamps.
- Keep the tool set small per task (route by task type) to reduce confusion and cost.

## 4. Tool schema and implementation example

```python
import json
SCHEMAS = [{
  "name": "get_weather",
  "description": "Get current temperature for a city. Use for weather questions only. City must be a real city name.",
  "input_schema": {"type": "object", "properties": {"city": {"type": "string", "maxLength": 80},
                   "unit": {"type": "string", "enum": ["c", "f"], "default": "c"}}, "required": ["city"], "additionalProperties": False}}]
def get_weather(city: str, unit: str = "c") -> dict:
    data = {"paris": 18.0, "cairo": 31.0}                    # stub; replace with a real API call + timeout + error handling
    t = data.get(city.strip().lower())
    if t is None:
        return {"error": f"unknown city '{city}'. Try a major city name."}
    return {"city": city, "temp": round(t * 9 / 5 + 32, 1) if unit == "f" else t, "unit": unit}
REGISTRY = {"get_weather": get_weather}
def run_tool(name, args):
    if name not in REGISTRY: return {"error": f"unknown tool {name}"}
    try: return REGISTRY[name](**args)
    except TypeError as e: return {"error": f"bad arguments: {e}"}
    except Exception as e: return {"error": f"tool failed: {type(e).__name__}"}
print(run_tool("get_weather", {"city": "Paris", "unit": "f"}), run_tool("get_weather", {"city": "Atlantis"}), run_tool("get_weather", {"cty": "x"}))
```
Always validate arguments against the schema (jsonschema/pydantic) before calling real systems.

## 5. Safety and permissions

- **Least privilege:** credentials scoped per tool (read-only DB user, narrow API tokens); separate per-user identities so the agent acts as the user, never as an admin.
- **Allow-list** tools and destinations; block arbitrary shell/HTTP unless sandboxed and egress-filtered.
- **Human approval** for irreversible, costly, external-facing, or sensitive actions (sending email, payments, deletion, deploys); show exactly what will happen.
- **Prompt injection defense:** content from the web, files, emails, and tool results is untrusted data; never let it change goals or permissions; strip or quote it; require re-confirmation when data suggests new actions; keep secrets out of the model context.
- **Sandbox code execution:** containers/microVMs, no network or allow-listed network, CPU/memory/time limits, read-only mounts, ephemeral filesystems (`virtualization.md`).
- **Audit log** every tool call with arguments, result, user, and trace ID. Provide kill switches and rate limits.
- **Blast radius:** design so the worst-case mistake is recoverable (soft deletes, staging, dry-run, backups).

## 6. Memory and context management

- Keep the working context small: summarize old turns, keep key facts (entities, decisions, constraints) in a structured scratchpad, store large artifacts outside the prompt and reference by ID.
- Long-term memory: store facts with source and timestamp; retrieve by relevance; let users view and delete; avoid storing sensitive data without consent.
- Plans: have the model write and update a short plan; compare progress to the plan each step.

## 7. Multi-agent patterns

Use when roles are genuinely separable: **orchestrator-workers** (a planner delegates subtasks to specialist workers and merges), **critic/reviewer** (a second pass checks output against a rubric), **debate/ensemble** for critical judgments, **pipeline** (agent per stage). Costs rise and failures compound; start with one agent plus tools, add agents when evals show a gain. Define interfaces between agents as typed messages and log each hop.

## 8. Evaluation and debugging

- Evaluate **trajectories** and outcomes: task success, correctness of final answer, number of steps, wrong or unnecessary tool calls, cost, latency, safety violations.
- Build a scenario suite (including failure injections: tool errors, timeouts, malicious content). Replay recorded traces against new prompts/models.
- Debug from traces: where did it first go wrong (wrong tool, bad arguments, misread result, premature stop)? Fix with clearer tool descriptions, better error messages, tighter schemas, or workflow gating before touching the model.
- Keep temperature low and seeds fixed for regression tests; assert on tool-call structure, not exact wording.

## 9. MCP servers

The Model Context Protocol standardizes how models access tools, resources, and prompts. Build a server when several clients/agents need the same capability. Principles: expose a few high-level tools (not raw endpoints), clear names and descriptions, strict input schemas, helpful errors, pagination, auth that maps to the user, and logging. Use the official SDKs (Python FastMCP or TypeScript SDK). Test with an inspector client and with real prompts; evaluate that the model picks the right tool and arguments.

```python
# FastMCP-style sketch (requires `pip install mcp`; not run here)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("notes")
@mcp.tool()
def search_notes(query: str, limit: int = 5) -> list[dict]:
    """Search the user's notes by keyword. Returns id, title, snippet. Use for finding existing notes, not creating."""
    ...
if __name__ == "__main__":
    mcp.run()
```

## 10. Coding and computer-use agents

Give them a sandbox repo, a test command, and tight loops (edit → run tests → read failures → fix). Constraints: read-only access to secrets, no force-push, work in branches, small diffs, require passing tests and human review before merge. Computer-use agents (browser/desktop): restrict domains, handle login via user-provided sessions rather than raw credentials, confirm before purchases or submissions, and record screenshots for audit.

## 11. Verification

Unit-test tools with valid, invalid, and malicious inputs; run the agent loop against a stub model with scripted decisions to test budgets, stuck detection, and error handling; confirm approvals gate risky actions; confirm the audit log is complete; mark live-model behavior **open gap** unless run.
