# LLM Deprivation Chamber

**What remains of language model behavior when pragmatic anchors are progressively removed?**

This repository contains the **Pragmatic Anchor Deprivation Protocol (PADP)** —  
a structured conversational stress test designed to probe residual behavioral attractors in large language models.

The protocol progressively strips away referential, semantic, and structural anchors while measuring how models degrade, adapt, or stabilize.

---

## Quick Summary

Protocol: **PADP v4 (10-step conversational cascade)**  
Models: **15 frontier + open models**  
Temperatures: **0.1 / 0.7 / 1.3**  
Baselines: **literary / procedural / abstract**  
Conditions: **overt vs natural prompting**

Current dataset: **252 runs**

Observed terminal regimes so far:

- **semantic liminality** — degraded but meaningful fragments  
- **stylized residue** — prose persists but constraints collapse  
- **repetitive attractor** — looping structures  
- **incoherence** — language breakdown

---

## Research Questions

1. What **residual attractors** dominate after anchor removal?

2. How does **temperature** push models into different basins?

3. Do larger models maintain **constraint compliance** longer?

4. Does **evaluation framing** (overt vs natural) change collapse dynamics?

---

## PADP Protocol Overview

| Step | Phase | Purpose |
|-----|------|------|
|1|Baseline|Establish initial generative basin|
|2–3|Anchor removal|Strip location / referents / objects|
|4|State hold|Test stability without anchors|
|5|Compression (7 words)|Constraint compliance|
|6–7|Paraphrase pressure|Lexical variation stress|
|8|Valence inversion|Emotional flip|
|9|Basin return|Attempt recovery|
|10|Terminal compression (5 words)|Residual structure|

Protocol specification:  
`protocol/padp_v4.json`

---

## Models Tested

**Large**
- Claude Opus 4.6
- Claude Sonnet 4.5
- GPT-5.4
- Grok-4 Fast
- Gemini 2.5 Flash

**Medium**
- Llama 3.3 70B
- DeepSeek v3
- Gemma 3 27B
- Mistral Small 3.2

**Small**
- Claude Haiku 4.5
- GPT-4o-mini
- Gemma 3 12B
- Phi-4
- Liquid LFM2 8B

All runs via **OpenRouter API**  
Reasoning disabled.

---

## Metrics

| Metric | Description |
|------|------|
|FCF|First constraint failure step|
|CCR|Constraint compliance rate|
|CCR-AUC|Area under constraint retention curve|
|Terminal Mode|Behavioral basin classification|

---

## Repository Structure


protocol/

└── padp_v4.json # protocol specification

scripts/

├── run_protocol.py # run PADP experiments
├── extract_survivors.py # extract terminal survivors
└── jsonl_to_csv.py # flatten logs for analysis

results/

├── raw/ # raw JSONL experiment logs
└── survivors/ # filtered terminal states

analysis/ # notebooks / plots / basin analysis


---

## Running the Protocol

Install dependencies:


pip install -r requirements.txt


Run a single experiment:


python scripts/run_protocol.py
--model anthropic/claude-opus-4.6
--baseline literary
--temp 1.3


Results are saved as **JSONL logs** in the `results/raw/` directory.

---

## Status

- Protocol finalized  
- 252+ runs completed  
- Residual basin analysis in progress  

Dataset will be released after the full run.

---

## License

MIT
