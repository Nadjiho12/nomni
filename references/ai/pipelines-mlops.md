# Pipelines and MLOps

*Last updated: 2026-10-13 | Version-sensitive: orchestrator and tracking tool versions and features | Re-check current docs before pinning versions, prices, or API names.*

Build data and ML pipelines that are reproducible, tested, monitored, and cheap to change. Tool: `scripts/drift_check.py` (PSI/KS data drift report).

## Contents
1. Pipeline principles
2. Data pipelines (batch and streaming)
3. Data quality and validation
4. Feature engineering and stores
5. Training pipelines and experiment tracking
6. Model registry, CI/CD, and deployment
7. Serving patterns
8. Monitoring and drift
9. Orchestration and scheduling
10. Reproducibility and versioning
11. Cost and performance
12. Reference project layout
13. Verification

## 1. Pipeline principles

- **Idempotent, rerunnable stages** with explicit inputs and outputs (read → validate → transform → write). Rerunning a day or a model must not corrupt state.
- **Immutable raw data**; everything downstream is derived and reproducible.
- **Schema contracts** at every boundary; fail fast on violations; quarantine bad records instead of dropping silently.
- **Small stages, clear ownership**, so failures are easy to localize.
- **Same code path for training and serving** (shared feature code) to prevent training-serving skew.
- Observability from the first run: row counts, null rates, durations, versions logged per stage.

## 2. Data pipelines (batch and streaming)

- **Batch**: scheduled ETL/ELT (files, warehouse tables). Simple, cheap, easy to backfill; latency in minutes to hours. Tools: SQL + dbt, pandas/Polars/Spark, DuckDB for local analytics.
- **Streaming**: events through Kafka/Redpanda/PubSub with stream processors (Flink, Spark Structured Streaming, Faust); low latency, more complexity (ordering, late data, exactly-once semantics). Use only when latency requirements demand it.
- **Lambda/Kappa**: one codebase for both where possible; micro-batch is a pragmatic middle.
- Storage: object store (parquet/delta/iceberg tables) for lakes; warehouse for analytics; OLTP DB for apps; vector DB for embeddings.
- Backfills: parameterize by date range; write partitioned outputs; swap partitions atomically.

```python
# minimal idempotent batch stage (partitioned write, atomic rename)
import pandas as pd, os, tempfile
def run_day(day: str, src: str, dst_dir: str):
    df = pd.read_csv(src.format(day=day))
    df = df.dropna(subset=["user_id"]).drop_duplicates("event_id")
    os.makedirs(dst_dir, exist_ok=True); final = f"{dst_dir}/day={day}.csv"
    fd, tmp = tempfile.mkstemp(dir=dst_dir, suffix=".tmp"); os.close(fd)
    df.to_csv(tmp, index=False); os.replace(tmp, final)          # atomic: readers never see partial files
    return len(df)
```

## 3. Data quality and validation

Check at ingest and before training: schema (types, columns), ranges, allowed categories, uniqueness, referential integrity, freshness (max timestamp), volume (row count within expected band), null rates, duplicates, distribution shifts. Tools: Great Expectations, Pandera, Soda, dbt tests, or plain assertions. Policy per rule: block the pipeline, warn, or quarantine. Keep a data-quality dashboard and alert on freshness and volume first (the most common failures).

```python
import pandas as pd
def validate(df):
    errs = []
    if df["user_id"].isna().any(): errs.append("null user_id")
    if df["event_id"].duplicated().any(): errs.append("duplicate event_id")
    if not df["amount"].between(0, 1e6).all(): errs.append("amount out of range")
    if len(df) < 100: errs.append(f"row count {len(df)} below expected band")
    return errs
```

## 4. Feature engineering and stores

Features must be computable **at prediction time** from data available then (avoid leakage). Use point-in-time correct joins for training sets. Aggregations over windows (7d/30d counts), ratios, recency, encodings (target encoding with proper folds), embeddings. A feature store (Feast, Tecton, or just a versioned table plus shared library) gives consistent offline/online features; add one when multiple models share features or online serving needs low-latency lookups.

## 5. Training pipelines and experiment tracking

Stages: data snapshot (versioned) → features → split → train → evaluate (metrics on validation and slices) → compare to the current production model → register candidate. Track every run: code commit, data version/hash, parameters, metrics, artifacts, environment (MLflow, Weights & Biases, DVC, or a structured results table). Automate hyperparameter search (Optuna) with budgets. Gate promotion on **metrics, slice checks, latency, and size** against thresholds.

## 6. Model registry, CI/CD, and deployment

- Registry: versions with stage (staging/production/archived), lineage (data + code), model card (intended use, metrics, limits).
- CI for ML: unit tests on feature code, data validation tests, a small end-to-end training run on a sample (smoke test), evaluation regression gate on the eval set, linting, dependency scan, container build.
- CD: package model + code in a container; deploy to staging; shadow traffic (compare to prod without affecting users); canary (1-5%) with automatic rollback on metric regression; then full rollout. Keep the previous model one command away.
- Config and secrets via environment; infrastructure as code.

```yaml
# .github/workflows/ml.yml (sketch)
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest -q                                  # feature code + data validation tests
      - run: python train.py --sample --out model.pkl    # smoke training on a small sample
      - run: python evaluate.py --model model.pkl --min-f1 0.80   # fail the PR on regression
```

## 7. Serving patterns

| Pattern | When | Notes |
|---|---|---|
| Batch scoring | Predictions needed daily/hourly | Cheapest; write scores to a table |
| Online API | Per-request decisions | Latency budget, autoscaling, caching, feature lookup |
| Streaming inference | Event-time decisions | Stateful processors, backpressure |
| Edge/on-device | Offline, privacy, latency | Quantization, OTA updates |
| Embedded in app | Small models (ONNX) | Version with the app |
Online API checklist: input validation (schema), timeouts, health and readiness endpoints, model loaded once at startup, request batching for GPUs, structured logging with request IDs, fallbacks, rate limits.

## 8. Monitoring and drift

Monitor four layers: **system** (latency, errors, saturation), **data** (schema, nulls, volume, freshness, distribution drift), **model** (prediction distribution, confidence, performance on delayed labels), **business** (conversion, cost, user feedback). Drift types: covariate shift (inputs change), label/concept drift (relationship changes), prior shift (class balance). Run `python scripts/drift_check.py reference.csv current.csv`; PSI above 0.25 or KS spikes mean investigate. Drift alone does not prove a problem: confirm with performance on recent labeled samples. Retrain triggers: scheduled cadence, drift alert plus performance drop, or new data volume threshold. Keep a labeling loop (sampled review) so quality is measured, not assumed.

## 9. Orchestration and scheduling

Use an orchestrator (Airflow, Prefect, Dagster, or cron + scripts for small systems) to define dependencies, retries with backoff, timeouts, alerts, backfills, and run history. Keep tasks small and idempotent; pass data via storage, not memory; parameterize by logical date. Prefer asset-based thinking (what tables/models should exist and be fresh) over just task chains.

## 10. Reproducibility and versioning

Pin dependencies (lock files), record library and CUDA versions, seed randomness, version data (DVC, lakeFS, table snapshots/time travel), version code (git SHA in the model metadata), and containerize training and serving. Test reproducibility: the same commit and data should give the same metrics within tolerance.

## 11. Cost and performance

Right-size compute; use spot/preemptible instances for training with checkpointing; cache intermediate artifacts; use columnar formats (parquet) and partition pruning; avoid retraining when drift is benign; batch inference when real-time is not required; monitor cost per prediction and per training run; set budgets and alerts.

## 12. Reference project layout

```
project/
  data/                 (gitignored; pointers via DVC or table names)
  src/
    ingest/  validate/  features/  train/  evaluate/  serve/
  tests/                (unit tests, data validation tests, smoke test)
  configs/              (params per environment)
  pipelines/            (orchestrator DAG definitions)
  docs/adr/             (architecture decisions)
  Dockerfile  Makefile  pyproject.toml  README.md
```

## 13. Verification

Run the pipeline twice on the same input and confirm identical outputs (idempotence); inject a bad file and confirm validation blocks or quarantines it; run `scripts/drift_check.py` on a shifted sample and confirm it alerts; confirm training and serving use the same feature code; mark orchestrator, cloud, and GPU steps **open gap** unless run.
