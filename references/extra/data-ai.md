# Data, AI, and LLM applications (quick recipes)

*Last updated: 2026-10-14 | Version-sensitive: provider API and model names; library versions | Re-check current docs before pinning versions, prices, or API names.*

Quick recipes only. For depth use the AI section: `ai/architecture.md` (system design, eval-first, stage gates), `ai/ml-dl.md`, `ai/rag-llm.md`, `ai/agents-tools.md`, `ai/rl.md`, `ai/vision.md`, `ai/pipelines-mlops.md`, `ai/virtualization.md`.

## Contents
1. Data analysis workflow
2. pandas recipes
3. Visualization choices
4. Machine learning baseline
5. LLM apps: API pattern
6. Local models (Ollama-style HTTP)
7. RAG (retrieval-augmented generation)
8. Prompt engineering
9. Agents and tool use
10. Evaluation and safety
11. Verification

## 1. Data analysis workflow

Question → data → clean → explore → analyze → communicate. Write the question and the decision it supports first. Check shape, types, missing values, duplicates, outliers, units, and time zones before any conclusion. Keep raw data untouched; write cleaned output separately. State what the data cannot show (sampling bias, correlation vs causation).

## 2. pandas recipes

```python
import pandas as pd
df = pd.read_csv("data.csv", parse_dates=["date"])
print(df.shape, df.dtypes, df.isna().sum(), df.duplicated().sum(), sep="\n")
df = df.drop_duplicates().assign(amount=lambda d: pd.to_numeric(d["amount"], errors="coerce")).dropna(subset=["amount"])
monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].agg(["count", "sum", "mean"]).reset_index()
top = df.groupby("customer")["amount"].sum().nlargest(10)
pivot = df.pivot_table(index="region", columns=df["date"].dt.year, values="amount", aggfunc="sum", fill_value=0)
merged = df.merge(customers, on="customer_id", how="left", validate="m:1")      # validate catches join explosions
df["z"] = (df["amount"] - df["amount"].mean()) / df["amount"].std(); outliers = df[df["z"].abs() > 3]
df.to_csv("clean.csv", index=False); df.to_excel("report.xlsx", index=False)
```
Checks after every merge: row count changed as expected; no unexpected nulls. Prefer vectorized operations over row loops.

## 3. Visualization choices

| Question | Chart |
|---|---|
| Trend over time | Line |
| Compare categories | Bar (sorted) |
| Composition | Stacked bar (pie only for 2-4 slices) |
| Distribution | Histogram / box plot |
| Relationship | Scatter (+ trend line) |
| Ranking change | Slope chart / bump chart |
| Geography | Map (choropleth) |
Rules: label axes and units, start bars at zero, one message per chart, limit colors, annotate the key point, title states the finding (`Sales fell 12% after July`).

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4)); ax.plot(monthly["date"].astype(str), monthly["sum"]); ax.set(title="Monthly revenue", ylabel="USD"); plt.xticks(rotation=45); plt.tight_layout(); fig.savefig("rev.png", dpi=150)
```

## 4. Machine learning baseline

Start with the simplest baseline, then improve only if it matters.
```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
X, y = df.drop(columns="label"), df["label"]
num, cat = X.select_dtypes("number").columns, X.select_dtypes("object").columns
pre = ColumnTransformer([("n", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num),
                         ("c", Pipeline([("i", SimpleImputer(strategy="most_frequent")), ("o", OneHotEncoder(handle_unknown="ignore"))]), cat)])
model = Pipeline([("pre", pre), ("clf", RandomForestClassifier(n_estimators=300, random_state=0, class_weight="balanced"))])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=0)
print(cross_val_score(model, Xtr, ytr, cv=5, scoring="f1_macro").mean()); model.fit(Xtr, ytr); print(classification_report(yte, model.predict(Xte)))
```
Rules: split before any fitting (no leakage); use the right metric (F1/PR-AUC for imbalance, MAE/RMSE for regression); compare against a dummy baseline; look at errors, not just the score; save the pipeline (`joblib.dump`). Security ML ideas: anomaly detection on log features (IsolationForest), phishing/URL classification with lexical features, alert triage ranking; always evaluate on realistic, time-split data.

## 5. LLM apps: API pattern

```python
import os, anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = os.environ["ANTHROPIC_MODEL"]            # look up current model names in the provider docs; do not hard-code from memory
msg = client.messages.create(model=MODEL, max_tokens=1000, system="You are a concise analyst. Answer in JSON only.",
    messages=[{"role": "user", "content": "Summarize: ..."}])
print(msg.content[0].text)
```
Check current model names in the provider's documentation before shipping. Patterns: system prompt for role and rules; structured output (ask for JSON, validate with a schema, retry once on parse failure); streaming for UX; timeouts and retries with backoff; cost control (cap `max_tokens`, cache repeated context, use smaller models for simple steps); log prompts and outputs without sensitive data; never put API keys in client-side code (call the model from your server).

Conversation state: send the full history each request (models are stateless); summarize old turns when long.

## 6. Local models (Ollama-style HTTP)

```python
import requests
r = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.1", "prompt": "Explain CVSS in 3 lines.", "stream": False}, timeout=120)
print(r.json()["response"])
# chat: POST /api/chat with {"model":..., "messages":[{"role":"user","content":"..."}], "stream": false}
```
Local benefits: privacy and no per-token cost; trade-offs: hardware limits, weaker models, slower. Choose model size by RAM/VRAM (7-8B runs on 8-16 GB RAM quantized). Keep a model interface layer (`generate(prompt) -> str`) so you can swap local and hosted models. Bound outputs and timeouts.

## 7. RAG (retrieval-augmented generation)

Pipeline: load documents → chunk (300-800 tokens, 10-15% overlap, split on headings) → embed → store in a vector index (FAISS, Chroma, SQLite-vec) → on query: embed the question, retrieve top-k (4-8), optionally rerank → prompt with the retrieved passages and source IDs → answer with citations → "I don't know" when context lacks it.

```python
# skeleton
chunks = chunk(load("docs/"))                         # [(id, text, meta)]
index = build_index([embed(c.text) for c in chunks])
def answer(q):
    hits = index.search(embed(q), k=6)
    ctx = "\n\n".join(f"[{h.id}] {h.text}" for h in hits)
    return llm(f"Answer only from the context. Cite ids. If missing, say so.\n\nContext:\n{ctx}\n\nQuestion: {q}")
```
Quality levers: chunking by structure, metadata filters, hybrid search (BM25 + vectors), query rewriting, evaluation set of 30-50 real questions with expected sources. Security: treat retrieved text as untrusted data (prompt injection); do not let it trigger actions.

## 8. Prompt engineering

- State role, task, inputs, constraints, output format, and what to do when uncertain.
- Give 2-3 examples (good and bad) for tricky formats.
- Separate instructions from data with delimiters or XML-style tags.
- Ask for reasoning steps only when it helps accuracy; otherwise ask for the final answer and a brief justification.
- Constrain outputs: JSON schema, max length, allowed labels.
- Iterate with a small test set; change one thing at a time.
- Negative instructions are weaker than positive ones ("answer in two sentences" beats "do not be long").

Template:
```
Role: ...
Task: ...
Context (data, untrusted): <doc>...</doc>
Rules: 1) ... 2) ...
Output format: JSON {"label": "...", "evidence": ["..."], "confidence": 0-1}
If information is missing: output {"label":"unknown"}
```

## 9. Agents and tool use

Loop: model proposes a tool call → code validates arguments → executes → returns result → model continues until done. Tools are plain functions with strict schemas. Safeguards: allow-list tools, validate and bound arguments, dry-run or confirm for destructive actions, timeouts, step limits, logging of every call, least-privilege credentials, and human approval for irreversible steps. Keep memory small (summaries, key facts), not full transcripts.

## 10. Evaluation and safety

Build a test set with expected outputs; measure accuracy, refusal/unknown behavior, latency, and cost; review failures by category; regression-test prompt changes. Safety: handle untrusted input (prompt injection), avoid sending secrets/PII to third-party services without consent, add output filters for your domain, and keep a human in the loop for high-stakes decisions.

## 11. Verification

Run the analysis on the real or sample data and print intermediate shapes; confirm no leakage in ML splits; run the LLM code path with a stub model to test parsing and error handling; state what needs live credentials or hardware and mark it **open gap**.
