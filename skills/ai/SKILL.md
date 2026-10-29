---
name: ai
description: "AI and ML engineering: AI system architecture (do you need an LLM at all), machine learning and deep learning, RAG, LLM agents and tools, reinforcement learning, computer vision, data and ML pipelines with drift monitoring, virtualization and sandboxing, and voice/speech AI. Use for any AI, model, or data-pipeline design or build request."
---

# N-Omni: ai

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| AI system design: do you need AI or an LLM at all, baseline, eval-first, reference architectures, serving, security, cost, stage gates | `references/ai/architecture.md` |
| Machine learning and deep learning: train and evaluate a classifier, leakage, metrics, neural nets, transformers/attention, fine-tuning/LoRA, embeddings | `references/ai/ml-dl.md` |
| RAG and LLM apps: chatbot over documents/PDFs, chunking, hybrid retrieval, reranking, evaluation, prompts, local models | `references/ai/rag-llm.md` |
| LLM agents and tool design, function calling, MCP servers, sandboxing, trajectory evaluation | `references/ai/agents-tools.md` |
| Reinforcement learning: Q-learning, PPO, reward design, game bots, RLHF/DPO/GRPO | `references/ai/rl.md` |
| Computer vision: OpenCV, object detection, segmentation, OCR, VLMs, defect detection in images, edge deployment | `references/ai/vision.md` |
| Data and ML pipelines, MLOps, model drift monitoring, validation, retraining, registries, CI/CD for ML | `references/ai/pipelines-mlops.md` |
| Virtualization and isolation: containers, Docker GPU, VMs, Kubernetes, sandbox for untrusted code, isolated labs | `references/ai/virtualization.md` |
| Voice and speech AI: assistants, ASR/TTS, low latency, barge-in, word error rate, voice-fraud defenses | `references/extra/voice-speech-ai.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
