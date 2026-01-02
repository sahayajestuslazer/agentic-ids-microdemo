# agentic-ids-microdemo

An offline anomaly and intrusion detection micro-demo using synthetic NetFlow-style
logs. This project compares classical anomaly detection techniques with an
LLM-assisted agent that produces explainable decisions under policy-gated execution.

The demo is designed to showcase **agentic AI workflows**, **explainability**,
and **governance controls** in a safe, reproducible setting.

---

## What This Demonstrates

This project showcases skills relevant to security engineering, machine learning,
and applied AI:

- Designing **agentic workflows** around an LLM
- Combining **classical ML baselines** with modern LLM reasoning
- Implementing **retrieval-augmented prompting (RAG)** using TF-IDF
- Enforcing **policy gates** and **audit logging** for agent actions
- Evaluating models using operationally meaningful metrics
- Building **safe, offline security simulations**

No live networks, exploits, or external systems are involved.

---

## Overview

The demo simulates an intrusion detection system using **synthetic NetFlow-like
windowed logs**. Each window summarizes traffic behavior using features such as:

- Bytes per second
- Packets per second
- SYN packet rate
- Failed connection rate

Each window is labeled as **normal** or **anomalous**.

Two approaches are evaluated:

### 1. Baseline Detectors
- Z-score anomaly detection
- Isolation Forest (optional)

### 2. Agentic IDS
- Local LLM (Mistral via Ollama)
- Retrieval-augmented reasoning using a small playbook
- Structured outputs (label + rationale)
- Policy-gated execution with full audit logs

---

## Repository Structure

agentic-ids-microdemo/
├─ data/
│  └─ rag_corpus.txt        # Small playbook used for retrieval (RAG)
├─ baseline.py              # Z-score and Isolation Forest baselines
├─ agents.py                # LLM-based IDS agent
├─ retriever.py             # TF-IDF retrieval for RAG
├─ metrics.py               # AUROC, F1, explanation usefulness
├─ governance.py            # Policy gate and audit logging
├─ generate_netflow.py      # Synthetic NetFlow-like data generator
├─ run_ids.py               # Main experiment runner
├─ requirements.txt
└─ README.md

Generated outputs such as result CSVs and audit logs are excluded from version
control and can be regenerated locally.

---

## Installation

Create a Python environment and install dependencies:

pip install -r requirements.txt

### Optional: Enable the LLM agent

To run the agentic IDS, install and run Ollama locally:

ollama pull mistral
ollama run mistral

If the LLM is unavailable, the demo supports baseline-only execution.

---

## Running the Demo

### 1. Generate synthetic NetFlow-like data

python generate_netflow.py

### 2. Run baseline anomaly detection

python run_ids.py --no-llm

### 3. Run LLM-assisted agentic IDS

python run_ids.py

### Optional flags

--iforest        Enable Isolation Forest baseline
--thresh 3.0     Set z-score threshold
--contam 0.12    Set Isolation Forest contamination rate

---

## Metrics and Outputs

The demo reports:

- **AUROC** — anomaly separation quality
- **F1 score** — balance of precision and recall
- **Explanation usefulness** (agent only):
  - Consistency: rationale aligns with observed anomaly
  - Specificity: rationale references concrete traffic features

Results are saved to a CSV file and accompanied by an append-only audit log.

---

## Governance and Safety

This project emphasizes **safe agent design**:

- The agent performs **analysis only**
- No real actions are executed
- A policy gate restricts allowed operations
- All agent activity is logged for observability

This models how agentic AI systems can be safely constrained in security workflows.

---

## Notes for Employers

This repository demonstrates:

- Practical integration of LLMs into analytical pipelines
- Thoughtful use of classical ML alongside modern AI
- Emphasis on explainability and auditability
- Clean, modular Python design
- Awareness of security and safety considerations

The focus is on **engineering patterns**, not on exploiting real systems.

---

## License

MIT License.
