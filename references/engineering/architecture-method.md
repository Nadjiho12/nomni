# Architecture method (real-world quality, checked at every stage)

*Last updated: 2026-10-13 | Version-sensitive: cloud service names and limits | Re-check current docs before pinning versions, prices, or API names.*

A repeatable way to design and build systems that fit the project's real stage and constraints, with a progress-fit check at each gate so the work never drifts from the best result.

## Contents
1. Principles
2. The design process
3. Non-functional requirements (NFRs)
4. Reference architectures by project type
5. Data and API design
6. Scaling path by stage
7. Stage gates and progress-fit checks
8. Architecture decision records
9. Fitness functions (automated checks)
10. Common failure patterns
11. Architecture review checklist

## 1. Principles

- **Fit the stage.** A prototype, an MVP, a growing product, and a platform need different architectures. Over-building early and under-building late are both failures.
- **Start with a monolith, modularize inside it**, split into services only when a clear force demands it (independent scaling, team boundaries, different runtimes, fault isolation).
- **Make boundaries explicit** (modules, interfaces, data ownership) so splitting later is cheap.
- **Data outlives code.** Design the data model, migrations, and retention first; it is the hardest thing to change.
- **Design for observability and rollback from day one**, not after the first outage.
- **Choose boring technology** for the core; novelty where it differentiates.
- **Cost is a requirement.** Estimate run cost per user or per request early.
- **Security and privacy are architectural**, not a final pass.
- **Evidence over opinion.** Prototype the risky part, measure it, then commit.

## 2. The design process

1. **Understand**: users, jobs-to-be-done, goals, constraints, scale today and in 12 months (ranges), team skills, budget, deadlines, compliance.
2. **List NFRs** (section 3) with numbers.
3. **Identify the riskiest parts** (new tech, scale, integrations, unclear requirements, model quality). Plan spikes.
4. **Sketch the context diagram** (system and external actors), then containers/components, then the main flows (sequence diagrams for 2-3 key use cases).
5. **Generate 2-3 candidate architectures** that differ in a meaningful way (for example monolith vs modular monolith + worker vs services; hosted API vs local model).
6. **Evaluate** against NFRs and risks with a weighted matrix; pick; record an ADR.
7. **Define the walking skeleton**: the thinnest end-to-end slice through every layer (deployed, monitored). Build it first.
8. **Plan increments** as vertical slices with acceptance checks; review the architecture at each gate (section 7).
9. **Operate and learn**: metrics, incidents, cost; feed back into the design.

Deliver diagrams as text (Mermaid or ASCII) so they live next to the code.

## 3. Non-functional requirements (NFRs)

Quantify each; unquantified NFRs are wishes.

| NFR | Questions | Example target |
|---|---|---|
| Performance | p50/p95/p99 latency? throughput? | p95 < 300 ms at 50 req/s |
| Scalability | users, data volume, growth rate? | 10k MAU, 50 GB, 3x/year |
| Availability | tolerable downtime? | 99.5% monthly |
| Reliability/durability | what must never be lost? | no loss of paid orders; RPO 15 min |
| Security | data classes, threat model, authn/authz, compliance | PII encrypted; MFA for admins |
| Privacy | retention, deletion, residency | delete on request in 30 days |
| Cost | cost per user/request, budget | < $0.02 per request |
| Maintainability | team size, onboarding time, change frequency | new dev ships in a week |
| Observability | what must be seen, how fast? | alert within 5 min of error spike |
| Usability/accessibility | devices, WCAG level | WCAG 2.1 AA, works on low-end phones |
| Portability | lock-in tolerance | can move hosts in a week |
| Quality (AI/ML) | accuracy, groundedness, fairness, drift | recall@5 ≥ 0.85; hallucination rate < 3% on eval set |

## 4. Reference architectures by project type

**Web SaaS (MVP → growth)**
```
Browser/SPA --> CDN --> App server (modular monolith) --> Postgres
                           |--> Cache (Redis, later)
                           |--> Job queue --> Workers (emails, exports, AI jobs)
                           |--> Object storage (uploads)
Observability: logs + metrics + error tracking | CI/CD | staging env
```
Split out services later: auth, billing, search, heavy workers.

**Real-time game / multiplayer**
```
Clients --WebSocket/UDP--> Gateway --> Authoritative game server (tick loop)
                                   |--> Matchmaking --> Session allocator
                                   |--> Persistence (accounts, progress) --> DB
                                   |--> Telemetry --> analytics
```
Server authoritative; client prediction and interpolation; anti-cheat by validation (`games/multiplayer.md`).

**Data/ML pipeline**
```
Sources --> Ingest (batch/stream) --> Raw store --> Validate --> Transform --> Feature/curated store
        --> Train (tracked experiments) --> Evaluate --> Registry --> Serve (batch/online)
        --> Monitor (data + model drift) --> Retrain trigger
```
See `ai/pipelines-mlops.md`.

**RAG / LLM application**
```
Docs --> Parse --> Chunk --> Embed --> Index (vector + keyword)
Query --> Rewrite --> Retrieve (hybrid) --> Rerank --> Prompt assembly --> LLM --> Guardrails --> Answer + citations
Eval set + tracing + feedback loop + cost/latency budgets
```
See `ai/rag-llm.md` and `ai/architecture.md`.

**Automation/tooling platform**: scheduler/trigger → job runner with idempotent tasks → state store → notifications → audit log; secrets via manager; dry-run and rollback.

**Security monitoring (defensive)**: collectors → normalization → detection rules/ML → alert triage queue → case management → response playbooks; retention and integrity of logs; least-privilege collectors.

**Mobile app + backend**: app (offline-first local DB) ↔ sync API ↔ backend; push notifications; feature flags; crash reporting.

## 5. Data and API design

- Model entities, relationships, and ownership; add constraints in the database (unique, foreign keys, checks), not only in code.
- Every table: primary key, created/updated timestamps; consider soft delete only when needed; plan retention.
- Migrations: forward-only files, backward-compatible steps (expand → migrate → contract) for zero-downtime.
- APIs: resource-oriented, consistent errors, pagination, idempotency keys for unsafe operations, versioning for breaking changes, rate limits, clear auth model. Document with examples.
- Events: define schemas, make consumers idempotent, include a correlation ID, plan for replay and dead-letter handling.
- Caching: cache reads with explicit invalidation or TTL; never the source of truth.
- Multi-tenancy: tenant ID on every row and in every query path; test isolation explicitly.

## 6. Scaling path by stage

| Stage | Typical architecture | Add when |
|---|---|---|
| Prototype | Single process, SQLite or files, one host | now |
| MVP | Modular monolith, managed Postgres, one environment + staging | first real users |
| Growth | Cache, job queue + workers, read replica, CDN, autoscaling, feature flags | latency/queue pain, > a few hundred concurrent |
| Scale | Service split by bottleneck, search/analytics store, partitioning, multi-region | measured limits, team boundaries |
| Platform | Internal platform team, multi-tenant isolation, SLOs, cost governance | many teams/products |

Scale by **measurement**: profile, find the bottleneck, fix the largest one, re-measure.

## 7. Stage gates and progress-fit checks

At each gate ask the same questions and write the answers down (in `NOS-STATE` or the design note). If the answers are weak, change course before building more.

| Gate | Check |
|---|---|
| G0 Frame | Is the problem real and the goal measurable? Who is the user? What is the riskiest assumption? |
| G1 Design | Do the options cover the NFRs? Is there a simpler option? Is the riskiest part spiked? ADR written? |
| G2 Skeleton | Does the walking skeleton run end to end, deployed, with logs and a test? |
| G3 Core | Does the core flow meet the success metric on real data/users? What did we learn that changes the plan? |
| G4 Harden | Failure modes, security, performance budget, backup/restore, rollback verified? |
| G5 Launch | Production-ready checklist passed; monitoring and alerts live; support path defined? |
| G6 Operate | Are metrics, cost, and incidents telling us to change the architecture? |

**Progress-fit check (run continuously):** Is the current architecture still the best fit for *this* stage, *these* users, and *this* evidence? Are we building something the data does not justify? Is any part now a bottleneck, a cost problem, or unnecessary? If yes, record the change as an ADR and adjust the plan. Always compare the current result with the success metric, not with how much has been built.

## 8. Architecture decision records

```
# ADR-007: Use PostgreSQL full-text search before adding Elasticsearch
Status: Accepted (2026-10-05)
Context: 20k documents, p95 target 300 ms, team of 2, no search ops experience.
Options: (A) Postgres FTS (B) Elasticsearch (C) Managed search API
Decision: A. Meets target in a spike (p95 90 ms at 50k docs); zero new infra.
Consequences: Ranking is basic; revisit if > 1M docs or relevance complaints > X.
Revisit when: p95 > 300 ms or product asks for typo tolerance/faceting.
```
Keep ADRs in the repo (`docs/adr/`), numbered, never edited after acceptance (supersede instead).

## 9. Fitness functions (automated checks)

Turn architectural intent into tests that run in CI: dependency rules (module A must not import module B), p95 latency check on a benchmark, bundle-size budget, migration safety lint, license check, secret scan, SLO burn alert, cost-per-request report, retrieval recall on the eval set (AI), data-quality checks (pipelines). Fail the build when a rule breaks.

## 10. Common failure patterns

Distributed monolith (services that must deploy together) · shared database across services · no walking skeleton, big-bang integration · no monitoring until the first incident · unbounded queues and retries · synchronous chains of many services · cache as source of truth · no migration plan · security bolted on · architecture sized for hypothetical scale · no cost model · vendor lock-in discovered at renewal · missing ownership of data and on-call.

## 11. Architecture review checklist

- [ ] Goals, constraints, NFRs quantified
- [ ] Context diagram and key flows drawn
- [ ] Options compared; simpler alternative considered; ADR recorded
- [ ] Data model, ownership, retention, backups, migrations covered
- [ ] Failure modes and degradation behavior listed
- [ ] Security/privacy threat model done for exposed surfaces
- [ ] Observability and SLOs defined; runbooks for top failures
- [ ] Cost estimate per unit; scaling path and triggers defined
- [ ] Deployment, environments, CI/CD, rollback defined
- [ ] Riskiest assumptions spiked or scheduled
- [ ] Progress-fit check for the current gate answered honestly
