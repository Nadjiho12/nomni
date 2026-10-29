# AI system architecture

*Last updated: 2026-10-13 | Version-sensitive: model names, prices, serving tools, provider features | Re-check current docs before pinning versions, prices, or API names.*

How to design AI systems the way production teams do: pick the simplest approach that works, define quality with an evaluation set before building, budget cost and latency, and design for failure, safety, and change. Companion files: `rag-llm.md`, `agents-tools.md`, `ml-dl.md`, `rl.md`, `vision.md`, `pipelines-mlops.md`, `virtualization.md`, and `engineering/architecture-method.md` (stage gates, ADRs).

## Contents
1. First question: do you need AI at all?
2. Choosing the approach (decision ladder)
3. Evaluation-first development
4. Reference architectures
5. Cross-cutting design: quality, cost, latency, safety
6. Model selection: hosted vs local vs fine-tuned
7. Serving and performance
8. Observability for AI
9. Security and privacy for AI
10. Human in the loop and fallbacks
11. Failure modes
12. Stage gates for AI projects
13. Design review checklist

## 1. First question: do you need AI at all?

Use the cheapest solution that meets the requirement. Order of preference: **rules/regex/SQL → classic algorithm → classical ML → pretrained model/API → fine-tuned model → custom training**. Reasons to climb: rules cannot capture the variation; labeled data and an evaluation set exist; the value justifies the cost; errors are tolerable or reviewed.
Write the baseline first (even keyword search or a majority-class predictor). If an AI approach cannot beat the baseline on the evaluation set by a margin that matters, do not ship it.

## 2. Choosing the approach (decision ladder)

| Problem | First try | Escalate to |
|---|---|---|
| Structured prediction (churn, price, fraud score) | Logistic regression / gradient boosting | Feature engineering, ensembles, deep tabular only if justified |
| Text classification / extraction | Rules + TF-IDF + linear model | Small fine-tuned encoder, then LLM with schema |
| Question answering over documents | Search + extractive answer | RAG with hybrid retrieval and reranking |
| Generation (drafts, summaries) | Hosted LLM with a good prompt and examples | Fine-tune/distill for cost, latency, or style |
| Images (classify/detect/read) | Pretrained model + transfer learning | Fine-tune detector/segmenter, VLM for open-ended |
| Anomalies (logs, sensors, security) | Statistical baselines, isolation forest | Autoencoders/sequence models with labeled review |
| Sequential decisions (control, games, bidding) | Heuristics, search (A*/MCTS), bandits | Reinforcement learning with a simulator |
| Recommendations | Popularity + co-occurrence | Matrix factorization / two-tower models |
| Speech/voice | Managed ASR/TTS | Streaming pipelines with interruption handling |
| Workflows needing tools | Deterministic orchestration with LLM at decision points | Agent loop with guardrails (`agents-tools.md`) |

Prefer **workflows over free-roaming agents**: fixed steps with an LLM inside are cheaper, faster, testable, and safer.

## 3. Evaluation-first development

1. Define the task and the failure that hurts most.
2. Build an **eval set** (30-200 real, diverse examples; include edge cases and adversarial ones) with expected outputs or grading rubrics. Keep a hidden test slice.
3. Choose metrics: classification (precision/recall/F1, PR-AUC), retrieval (recall@k, MRR, nDCG), generation (rubric score, groundedness/citation accuracy, hallucination rate, format validity), latency (p50/p95), cost per request, refusal/safety rate.
4. Establish baselines, then iterate one change at a time; keep a results table.
5. Automate evals in CI (`fitness functions`); fail the build on regressions.
6. Add LLM-as-judge only with calibration against human labels; spot-check by hand.
7. After launch, sample production traffic into the eval set (with privacy controls).
Never tune on the test set; never trust a single aggregate number, slice by category.

## 4. Reference architectures

**A. Document Q&A / knowledge assistant (RAG)**
```
Ingest: files/web -> parse -> clean -> chunk (structure-aware) -> embed -> vector index + BM25 index (+ metadata)
Serve:  query -> (rewrite/expand) -> hybrid retrieve (k=20) -> rerank (k=5) -> prompt (context + rules) -> LLM
        -> validate (schema, citations, safety) -> answer with sources -> log trace + feedback
Ops:    eval set, retrieval recall dashboard, freshness job, cost/latency budget, access control per document
```
**B. Document processing pipeline (invoices, forms, reports)**
```
Upload -> OCR/layout parse -> classify doc type -> extract fields (LLM/schema or model) -> validate (rules, totals, formats)
       -> confidence routing: high -> auto-accept, low -> human review queue -> export to system of record -> audit log
```
**C. Agent platform (tool-using assistant)**
```
Request -> planner/router -> tool registry (typed schemas, permissions) -> sandboxed executors -> result validation
        -> memory (short summary + key facts) -> response; budgets: steps, tokens, time; human approval for risky actions
Observability: full trace per run, tool-call audit, replay for debugging
```
**D. Vision inspection / detection service**
```
Camera/upload -> preprocess -> detector/segmenter (GPU or edge) -> post-process (NMS, thresholds, tracking)
             -> rules (defect size, zone) -> decision + evidence image -> storage -> feedback labeling loop -> retrain
```
**E. Anomaly and threat analytics (security-style)**
```
Collectors -> normalize schema -> feature builder (rolling windows) -> detectors (rules + statistical + ML)
           -> scoring + dedupe -> triage queue with explanations -> analyst feedback -> labels -> retrain/tune
```
**F. Recommendation / ranking**
```
Events -> feature pipeline -> candidate generation (popular, similar, collaborative) -> ranker -> business rules -> serve
Offline eval (AUC, nDCG) + online A/B; cold-start strategy; diversity and fairness constraints
```
**G. Voice assistant**
```
Mic -> VAD -> streaming ASR -> NLU/LLM with tools -> TTS streaming; barge-in handling; latency budget under ~1 s to first audio
```
**H. RL system (when a simulator exists)**
```
Simulator/env -> actor workers -> replay/rollout buffer -> learner -> evaluation harness (fixed seeds) -> policy registry -> safe deployment with fallback controller
```

## 5. Cross-cutting design: quality, cost, latency, safety

- **Budgets:** set per-request targets (for example p95 latency 3 s, cost $0.01, quality ≥ eval threshold) and design backward: model size, context length, number of calls, caching.
- **Cost levers:** smaller/cheaper model for easy cases (routing/cascade), prompt caching, shorter context via better retrieval, batch processing, distillation, quantization for local models, output length limits, deduplicate requests.
- **Latency levers:** stream outputs, parallelize independent calls, cache embeddings and frequent answers, precompute, reduce hops, pick region near users, speculative/early exit for cascades.
- **Quality levers:** better data and retrieval before bigger models, clear instructions with examples, structured output + validation + retry, self-check or verifier for high-stakes steps, ensembling/voting for critical decisions.
- **Safety levers:** input and output filters, allow-listed tools, least-privilege credentials, rate limits, human approval for irreversible actions, refusal policies, content logging with privacy controls.

## 6. Model selection: hosted vs local vs fine-tuned

| Factor | Hosted API | Local/open model | Fine-tuned |
|---|---|---|---|
| Quality on hard tasks | Highest, improves over time | Lower for small models | Task-specific gains |
| Privacy/control | Data leaves your boundary | Data stays local | Depends on host |
| Cost | Pay per token, scales with use | Hardware + ops, flat at volume | Training + serving cost |
| Latency | Network + queue | Local, predictable | Often lower with small models |
| Ops burden | Low | High (serving, updates, GPUs) | Highest |
| Lock-in | Provider | Low | Model + data pipeline |
Decide with an eval set: run candidate models on it and compare quality, cost, latency. Keep a **model interface layer** (`generate(prompt, schema) -> result`) so models are swappable. Re-evaluate quarterly; models and prices change fast (search current docs before pinning).

## 7. Serving and performance

- LLM serving: vLLM/TGI/llama.cpp/Ollama; continuous batching; KV cache; quantization (int8/int4, GGUF/AWQ/GPTQ) to fit memory; streaming; set max tokens and timeouts.
- Embedding service: batch requests, cache by content hash, version the embedding model (re-embed on change).
- Online vs batch: batch what can wait (cheaper); online only where users wait.
- Autoscale on queue depth or GPU utilization; keep warm pools for cold-start-sensitive paths.
- Fallbacks: smaller model, cached answer, retrieval-only answer, graceful "I cannot answer" message.

## 8. Observability for AI

Trace every request: input, retrieved items, prompts (redacted), model and version, tool calls, outputs, latency per step, tokens and cost, user feedback. Dashboards: quality proxy metrics (thumbs, acceptance rate, citation validity), retrieval recall on the eval set, refusal rate, error rate, cost per request, latency percentiles, data and prediction drift. Alerts on regression, cost spikes, and error spikes. Keep an easy path from a bad answer to its full trace for debugging.

## 9. Security and privacy for AI

- **Prompt injection:** treat retrieved text, web pages, and user files as untrusted data; separate instructions from data; never let model output directly trigger privileged actions; validate tool arguments; limit tool scope and egress.
- **Data leakage:** minimize and redact sensitive fields before sending to third parties; per-user access control in retrieval (filter by permissions before ranking); no cross-tenant context.
- **Model supply chain:** pin model and library versions, verify checksums, scan dependencies, avoid loading untrusted pickles (use safetensors).
- **Abuse:** rate limits, quotas, abuse detection, logging; cap resource use per user.
- **Compliance:** retention and deletion for logs and embeddings (deleting a document must delete its vectors), consent for training use, audit trails.
- **Threat model** with STRIDE plus AI-specific threats (poisoned documents, jailbreaks, model extraction, inference attacks).

## 10. Human in the loop and fallbacks

Route by confidence: auto-act when confidence and stakes allow; queue for review otherwise. Show evidence and citations to reviewers; capture corrections as labeled data. Provide an escape hatch (manual path) and communicate uncertainty plainly to users.

## 11. Failure modes

Hallucinated facts · stale or missing context · retrieval returns the wrong chunk · prompt injection via documents · silent quality drift after model/data change · cost blowups from loops and long contexts · latency from chained calls · over-reliance without review · evaluation leakage · biased or unrepresentative data · non-determinism breaking tests (fix seeds, temperature 0 for tests, assert on structure) · tool misuse with excess permissions.

## 12. Stage gates for AI projects

| Gate | Evidence required |
|---|---|
| A0 Value | Task, user, success metric, and cost of errors defined; baseline solution identified |
| A1 Data/eval | Eval set built; baseline measured; data access and privacy cleared |
| A2 Prototype | Simplest AI approach beats baseline on eval set; cost/latency estimated |
| A3 Pilot | Runs end to end with tracing; real users or replayed traffic; failure analysis done; guardrails in place |
| A4 Production | SLOs, monitoring, rollback, security review, human-in-loop path, retraining/refresh plan |
| A5 Operate | Drift, cost, and feedback reviewed on a cadence; eval set grows; model re-evaluated periodically |
At each gate run the **progress-fit check**: is this still the simplest approach that meets the metric, and does the evidence justify more investment?

## 13. Design review checklist

- [ ] Baseline defined; AI justified against it
- [ ] Eval set and metrics defined before building; hidden test slice kept
- [ ] Architecture diagram with data flow, trust boundaries, and failure paths
- [ ] Cost and latency budgets with estimates
- [ ] Model choice compared on the eval set; swappable interface
- [ ] Guardrails: input/output validation, tool permissions, injection defenses
- [ ] Observability: traces, quality metrics, drift, alerts
- [ ] Privacy: redaction, access control, retention/deletion covered
- [ ] Human-in-loop and fallback paths defined
- [ ] Rollout plan with rollback; periodic re-evaluation scheduled
