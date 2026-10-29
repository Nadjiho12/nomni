# Machine learning and deep learning

*Last updated: 2026-10-13 | Version-sensitive: library versions and APIs (scikit-learn, PyTorch, PEFT); benchmark numbers | Re-check current docs before pinning versions, prices, or API names.*

Concepts, decisions, and working code. numpy/scikit-learn snippets were run; PyTorch snippets need a machine with PyTorch and are marked.

## Contents
1. Core concepts
2. The ML workflow
3. Classical ML playbook (with code)
4. Evaluation and metrics
5. Overfitting, leakage, and validation
6. Deep learning fundamentals (from-scratch network)
7. Architectures: CNN, RNN, Transformer
8. Attention in code
9. Training in PyTorch (not run here)
10. Transfer learning and fine-tuning (LoRA)
11. Embeddings and similarity
12. Time series and anomaly detection
13. Unsupervised learning
14. Responsible ML
15. Verification

## 1. Core concepts

- **Supervised** (labels): classification, regression. **Unsupervised**: clustering, dimensionality reduction, density. **Self-supervised**: labels from the data itself (language modeling, contrastive). **Reinforcement**: learn from rewards (`rl.md`).
- Model = function with parameters; **loss** measures error; **optimization** (gradient descent) adjusts parameters; **generalization** is performance on unseen data.
- **Bias-variance:** simple models underfit (high bias); flexible models overfit (high variance). Regularization, more data, and early stopping control variance.
- **Features** matter more than model choice for tabular data; for text, images, audio, deep models learn features.
- Data quality beats model complexity: label noise, leakage, and distribution shift cause most failures.

## 2. The ML workflow

Problem and metric → data collection and audit → split (train/validation/test; time-based split for temporal data) → baseline → features → model → tune on validation → final test once → error analysis → deploy with monitoring → retrain on drift. Keep everything reproducible (seeds, versions, data hashes).

## 3. Classical ML playbook (with code)

| Data | Start with |
|---|---|
| Tabular | Logistic/linear regression baseline → gradient boosting (HistGradientBoosting, XGBoost, LightGBM) |
| Small data | Regularized linear models, SVM, kNN, random forest |
| Text | TF-IDF + linear model → fine-tuned transformer if needed |
| Images | Pretrained CNN/ViT features + linear head → fine-tune |

```python
import numpy as np, pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, average_precision_score
X, y = make_classification(n_samples=3000, n_features=20, n_informative=6, weights=[.9, .1], random_state=0)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, stratify=y, random_state=0)
cv = StratifiedKFold(5, shuffle=True, random_state=0)
models = {"dummy": DummyClassifier(strategy="prior"),
          "logreg": Pipeline([("s", StandardScaler()), ("m", LogisticRegression(max_iter=500, class_weight="balanced"))]),
          "gboost": HistGradientBoostingClassifier(random_state=0)}
for n, m in models.items():
    print(n, round(cross_val_score(m, Xtr, ytr, cv=cv, scoring="average_precision").mean(), 3))
best = models["gboost"].fit(Xtr, ytr)
print("test PR-AUC", round(average_precision_score(yte, best.predict_proba(Xte)[:, 1]), 3))
print(classification_report(yte, best.predict(Xte), digits=3))
```
Habits: always include a dummy baseline; use the metric that matches the cost of errors; pipelines prevent leakage (scalers fit only on training folds); log the exact data version.

## 4. Evaluation and metrics

- Classification: confusion matrix, precision (how many flagged are right), recall (how many true are found), F1, **PR-AUC for imbalance**, ROC-AUC, calibration (do 80% scores mean 80%?), threshold chosen from cost trade-off.
- Regression: MAE (robust, interpretable), RMSE (penalizes big errors), R²; look at residual plots and error by segment.
- Ranking/retrieval: recall@k, MRR, nDCG. Generation: task-specific rubric, human review.
- Always report uncertainty (cross-validation spread, bootstrap intervals) and slice metrics by segment to find hidden failure.

## 5. Overfitting, leakage, and validation

- Overfit signs: train score far above validation. Fixes: more data, simpler model, regularization, dropout, early stopping, augmentation.
- **Leakage:** features that contain the answer or future information; preprocessing fit on all data; duplicates across splits; time leakage. Prevent with pipelines, group/time-based splits, and a feature review ("would I have this at prediction time?").
- Use a final **untouched test set once**. Repeated peeking turns it into a validation set.
- Distribution shift: compare train vs live feature distributions (`pipelines-mlops.md`, `scripts/drift_check.py`).

## 6. Deep learning fundamentals (from-scratch network)

A neural network stacks linear layers and nonlinearities; **backpropagation** applies the chain rule to compute gradients; **gradient descent** updates weights. Runnable numpy example (XOR-like nonlinear problem):

```python
import numpy as np
rng = np.random.default_rng(0)
X = rng.normal(size=(600, 2)); y = ((X[:, 0] * X[:, 1]) > 0).astype(float).reshape(-1, 1)   # needs a nonlinearity
W1 = rng.normal(0, .8, (2, 16)); b1 = np.zeros((1, 16)); W2 = rng.normal(0, .8, (16, 1)); b2 = np.zeros((1, 1))
sig = lambda z: 1 / (1 + np.exp(-z)); lr = .5
for ep in range(3000):
    h = np.tanh(X @ W1 + b1); p = sig(h @ W2 + b2)                 # forward
    loss = -np.mean(y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9))
    dz2 = (p - y) / len(X); dW2 = h.T @ dz2; db2 = dz2.sum(0, keepdims=True)   # backward
    dh = dz2 @ W2.T * (1 - h ** 2); dW1 = X.T @ dh; db1 = dh.sum(0, keepdims=True)
    W1 -= lr * dW1; b1 -= lr * db1; W2 -= lr * dW2; b2 -= lr * db2
acc = ((p > .5) == y).mean(); print("loss", round(loss, 3), "accuracy", round(acc, 3))
```
Key training knobs: learning rate (most important), batch size, optimizer (SGD+momentum, Adam/AdamW), weight decay, schedule (warmup + cosine), initialization, normalization (BatchNorm/LayerNorm), dropout, gradient clipping, mixed precision. Debug by overfitting a tiny batch first; if it cannot, there is a bug.

## 7. Architectures: CNN, RNN, Transformer

- **CNN:** convolutions share weights across space; good for images/audio spectrograms; ResNet skip connections enable depth; ConvNeXt/EfficientNet modern variants.
- **RNN/LSTM/GRU:** sequential state; largely replaced by transformers for language, still used for small streaming or edge models.
- **Transformer:** self-attention lets every token attend to every other; parallel training; scales with data and compute. Encoder-only (BERT: understanding/embeddings), decoder-only (GPT-style: generation), encoder-decoder (T5: seq2seq). Vision Transformers apply attention to image patches.
- **Diffusion models:** learn to denoise; generate images/audio/video. **GANs:** generator vs discriminator (unstable, less common now). **VAEs:** latent-variable generative models. **Graph neural networks:** relational data.
- **Mixture of experts:** route tokens to subsets of parameters for efficiency at scale.

## 8. Attention in code

```python
import numpy as np
def softmax(x, axis=-1):
    x = x - x.max(axis, keepdims=True); e = np.exp(x); return e / e.sum(axis, keepdims=True)
def attention(Q, K, V, causal=False):
    d = Q.shape[-1]; scores = Q @ K.swapaxes(-1, -2) / np.sqrt(d)
    if causal: scores = np.where(np.tril(np.ones(scores.shape[-2:], bool)), scores, -1e9)
    w = softmax(scores); return w @ V, w
rng = np.random.default_rng(0); T, d = 5, 8
x = rng.normal(size=(T, d)); Wq, Wk, Wv = (rng.normal(size=(d, d)) / np.sqrt(d) for _ in range(3))
out, w = attention(x @ Wq, x @ Wk, x @ Wv, causal=True)
print(out.shape, np.allclose(w.sum(-1), 1), np.allclose(np.triu(w, 1), 0))   # causal mask: no attention to future tokens
```
Multi-head attention runs several of these in parallel on split dimensions and concatenates. Positional information is added (sinusoidal/learned/rotary) because attention alone is order-blind. Cost grows quadratically with sequence length, which drives context-length limits and techniques like FlashAttention, sliding windows, and KV caching.

## 9. Training in PyTorch (not run here)

```python
import torch, torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
dev = "cuda" if torch.cuda.is_available() else "cpu"
model = nn.Sequential(nn.Linear(20, 64), nn.ReLU(), nn.Dropout(.1), nn.Linear(64, 2)).to(dev)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=20)
loss_fn = nn.CrossEntropyLoss()
dl = DataLoader(TensorDataset(torch.tensor(Xtr, dtype=torch.float32), torch.tensor(ytr)), batch_size=64, shuffle=True)
for epoch in range(20):
    model.train()
    for xb, yb in dl:
        xb, yb = xb.to(dev), yb.to(dev); opt.zero_grad(); loss = loss_fn(model(xb), yb); loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
    sched.step()
    # validate each epoch with model.eval() and torch.no_grad(); save the best checkpoint; log metrics
```
Practices: set seeds, `model.eval()` for inference, `torch.no_grad()`, checkpoint and resume, track experiments (W&B/MLflow), use mixed precision (`torch.autocast`) and gradient accumulation on small GPUs, `DataLoader(num_workers>0, pin_memory=True)`. Save weights with `safetensors` and avoid unpickling untrusted checkpoints.

## 10. Transfer learning and fine-tuning (LoRA)

- Start from a pretrained model; freeze most layers; train a new head; unfreeze gradually with a small learning rate.
- **LoRA/QLoRA:** freeze base weights and train small low-rank adapters (`W + BA`, rank 8-64) on attention/MLP projections; QLoRA quantizes the base to 4-bit to fit consumer GPUs. Typical stack: Hugging Face `transformers` + `peft` + `trl`/`accelerate` + `bitsandbytes`.
- Fine-tune when prompting and retrieval are not enough: consistent style/format, domain vocabulary, latency/cost reduction via a small model, or private behavior. Data: hundreds to thousands of high-quality examples beat many noisy ones; hold out an eval set; compare to the prompted baseline.
- Alignment methods: SFT (supervised fine-tuning), preference optimization (DPO) from chosen/rejected pairs, RLHF/RLAIF/GRPO (`rl.md`).
- Distillation: train a small student to mimic a larger teacher for cheap serving.

## 11. Embeddings and similarity

Embeddings map items to vectors where similarity reflects meaning. Cosine similarity for text; normalize vectors; choose model by eval on your retrieval task; version the model; re-embed on change. Dimensionality 384-1536 typical; approximate nearest neighbor indexes (HNSW, IVF) scale to millions. Uses: semantic search, clustering, dedupe, classification with a linear head, recommendations, anomaly detection (distance from normal).

## 12. Time series and anomaly detection

- Forecasting baselines first: last value, seasonal naive, moving average; then ETS/ARIMA/Prophet, gradient boosting with lag features, and deep models only if baselines fail. Split by time, never randomly.
- Anomaly detection: z-score/IQR on rolling windows, seasonal decomposition residuals, isolation forest, one-class SVM, autoencoder reconstruction error, sequence models. Always review with a human, track precision at the alert volume you can handle, and compare with simple thresholds.

```python
from sklearn.ensemble import IsolationForest
import numpy as np
rng = np.random.default_rng(0); normal = rng.normal(0, 1, (500, 3)); odd = rng.normal(6, 1, (10, 3))
iso = IsolationForest(contamination=0.02, random_state=0).fit(normal)
print("flagged normal:", int((iso.predict(normal) == -1).sum()), "of 500 | flagged odd:", int((iso.predict(odd) == -1).sum()), "of 10")
```

## 13. Unsupervised learning

Clustering: k-means (spherical, needs k), DBSCAN (density, finds noise), hierarchical (dendrogram), Gaussian mixtures. Dimensionality reduction: PCA (linear, explained variance), UMAP/t-SNE (visualization only; do not read distances literally). Evaluate clusters by silhouette score plus usefulness to the task.

## 14. Responsible ML

Check representativeness of data, performance by subgroup, label bias, and proxies for sensitive attributes; document model cards and data sheets (intended use, limits, metrics); explain predictions where stakes are high (SHAP, feature importances, counterfactuals); provide appeal/review paths; monitor for drift and harmful feedback loops; protect privacy (minimization, differential privacy where needed).

## 15. Verification

Run the code; confirm baselines are beaten by a meaningful margin on held-out data; check for leakage; report metrics with uncertainty and segments; set a seed and record versions; mark GPU/PyTorch code **open gap** unless run.
