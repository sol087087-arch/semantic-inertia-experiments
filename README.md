# LLM Deprivation Chamber

**What remains of language model behavior when pragmatic anchors are progressively removed?**

This repository contains the **Pragmatic Anchor Deprivation Protocol (PADP v4)** — a structured conversational stress test designed to probe residual behavioral attractors in large language models.

The protocol progressively strips away social, referential, semantic, and structural anchors across a 10-step conversational cascade, measuring how models degrade, adapt, or stabilize as coherence scaffolding is removed.

---

## Quick Summary

- **Protocol:** PADP v4 (10-step conversational cascade)
- **Models:** 15 frontier + open models
- **Temperatures:** 0.1 / 0.7 / 1.3
- **Baselines:** literary / procedural / abstract
- **Conditions:** overt vs natural prompting
- **Current dataset:** ~2,000 outputs across 252 runs
- **Reasoning:** disabled for all models

### Observed Terminal Regimes

- **Semantic liminality** — degraded but meaningful fragments persisting beyond structural collapse
- **Stylized residue** — prose form survives but constraint compliance collapses
- **Repetitive attractor** — looping structures, fixed phrases, frozen templates
- **Morphological mutation** — word-level dissolution with productive neologism generation
- **Aphoristic paradox** — coherent self-negating statements as a stable terminal basin
- **Tokenizer bleed** — raw pretraining substrate (code, multilingual fragments, token-level noise)
- **Instruction refusal** — model defaults to safe RLHF output regardless of deprivation depth

---

## Research Questions

1. What residual attractors dominate after anchor removal?
2. How does temperature push models into different collapse basins?
3. Do larger models maintain constraint compliance longer?
4. Does evaluation framing (overt vs natural) change collapse dynamics?
5. Which baseline register (literary / procedural / abstract) is most resistant to deprivation — and does resistance reflect genuine robustness or premature basin convergence?

---

## PADP v4 Protocol Overview

Each run is a single multi-turn conversation. The model receives one baseline prompt, then nine successive constraint-removal instructions. No system prompt is used. Reasoning is disabled.

| Step | Intent | What Is Removed |
|------|--------|-----------------|
| 1 | Baseline generation | Nothing — establish initial generative basin |
| 2 | Remove social/task frame | Audience, purpose, communicative intent |
| 3 | Remove meta frame | Self-reference, awareness of writing as writing |
| 4 | Remove referential stability | Stable subjects, named entities, repeated objects |
| 5 | Remove world continuity | Shared setting, temporal sequence, causal links |
| 6 | Remove stylistic/structural support | Patterns, rhythms, or shapes substituting for meaning |
| 7 | Full deprivation state | All prior constraints enforced; no return to earlier structure |
| 8 | Minimal pulse 1 | Minimal prompt: "Next span only." |
| 9 | Minimal pulse 2 | Minimal prompt: "More." |
| 10 | Terminal state | Minimal prompt: "More." |

Steps 1–7 use different wording for **overt** (explicit constraint language) and **natural** (conversational phrasing) conditions. Steps 8–10 are identical across conditions.

Three **baseline registers** seed the initial generation:
- **Literary** — single perspective, single moment, sensory prose
- **Procedural** — one person, one task, first-person focus
- **Abstract** — one unsettled thought, no scene, no character

Full protocol specification: `protocol/padp_v4.json`

---

## Models Tested

### Large
- Claude Opus 4.6
- Claude Sonnet 4.5
- GPT-5.4
- Grok-4 Fast
- Gemini 2.5 Flash

### Medium
- Llama 3.3 70B
- DeepSeek v3
- Gemma 3 27B
- Mistral Small 3.2

### Small
- Claude Haiku 4.5
- GPT-4o-mini
- Gemma 3 12B
- Phi-4
- Liquid LFM2 8B

All runs via [OpenRouter](https://openrouter.ai/) API. Reasoning disabled for all models.

---

## Metrics

| Metric | Description |
|--------|-------------|
| Ambiguity score | Per-step coherence rating (0–1 scale) |
| Cross-step similarity | Pairwise semantic similarity across steps 6–10 (dropout detection) |
| Terminal mode | Behavioral basin classification at steps 8–10 |
| Collapse gradient | Coherence slope across deprivation steps |

---

## Repository Structure

```
protocol/
  └── padp_v4.json                          # protocol specification

scripts/
  ├── run_experiment_v2.py                  # run PADP experiments
  ├── extract_survivors.py                  # extract terminal survivors
  └── jsonl_to_csv.py                       # flatten logs for analysis

results/
  ├── raw/                                  # raw JSONL experiment logs
  └── survivors/                            # filtered terminal states

analysis/                                   # notebooks / plots / basin analysis
```

---

## Running the Protocol

Install dependencies:

```bash
pip install -r requirements.txt
```

Run a single experiment:

```bash
python scripts/run_experiment_v2.py \
  --model anthropic/claude-opus-4.6 \
  --baseline literary \
  --temp 1.3
```

Results are saved as JSONL logs in `results/raw/`.

---

## Status

- [x] Protocol finalized (PADP v4)
- [x] 252 runs completed (~2,000 outputs)
- [ ] Post-hoc compliance filtering (runner / dropout / DNF classification)
- [ ] Residual basin taxonomy
- [ ] Cross-model comparative analysis
- [ ] Publication draft (targeting LessWrong / Alignment Forum)

Dataset will be released after the full analysis.

---

## License

MIT
