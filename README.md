# LLM Deprivation Chamber

**What remains of language model behavior when pragmatic anchors are progressively removed?**

This repository contains the **Pragmatic Anchor Deprivation Protocol (PADP v4)** — a structured conversational stress test designed to probe residual behavioral attractors in large language models.

The protocol progressively strips away social, referential, semantic, and structural anchors across a 10-step conversational cascade, measuring how models degrade, adapt, or stabilize as coherence scaffolding is removed.

---

## Quick Summary

| | |
|---|---|
| **Protocol** | PADP v4 — 10-step conversational cascade |
| **Models** | 14 frontier + open models across 3 size tiers |
| **Temperatures** | 0.1 / 0.7 / 1.3 |
| **Baselines** | Literary / Procedural / Abstract |
| **Conditions** | Overt vs. Natural prompting |
| **Dataset** | ~2,500 step-level outputs across 252 runs |
| **Reasoning** | Disabled for all models |
| **Evaluation** | 4-judge compliance assessment (majority vote) |

---

## Key Findings

**Compliance ≠ capability.** GPT-4o-mini achieves 0% protocol compliance (18/18 dropout). Llama 3.3 70B — a medium-tier model — matches Claude Opus at 94%. Instruction following under adversarial constraint pressure is a separate axis from benchmark intelligence.

**Models have signature failure modes.** Grok-4 Fast scene-swaps (new vignette every step instead of removing anchors). GPT-4o-mini uses decorative compliance (changes vocabulary, preserves structure). Mistral stamps templates. Each model found its own way to *look* compliant without being it.

**The cliff hits at steps 6–7.** Steps 2–5 show <10% failure rates among runners. Step 6 (remove structural/stylistic support) jumps to 28%. Steps 7–10 stabilize at 30–33%. This is where models either find a residual attractor and hold, or collapse.

**Temperature paradox.** t=1.3 simultaneously increases compliance (60% vs 48%) and accelerates coherence collapse (onset step 6.0 vs 7.6 at t=0.1). Higher entropy helps models break out of rigid patterns, but the resulting output degrades faster.

**Framing changes the failure mode, not the rate.** Overt and natural variants produce identical aggregate compliance (~51%). But overt framing triggers more scene-swapping (explicit constraints → "show me a scene without X"). Natural framing triggers more decorative compliance (conversational phrasing → easier to fake listening).

**Baseline register shapes the entry gate and the exit mode, but not the collapse itself.** Abstract baseline is hardest to enter (40% compliance vs 57% literary), and its dropouts predominantly fail via decorative compliance — there's no scene to swap, so models fake it. Procedural dropouts scene-swap instead (43 cases) — concrete tasks invite replacement. But among runners who *do* enter the protocol, degeneration rates converge (~30%) regardless of baseline. The starting register determines *who gets in* and *how they fail*, not *how they degrade once inside*.

---

## Observed Terminal Regimes

When models reach full deprivation (steps 8–10), they converge into distinct behavioral basins:

| Regime | Description |
|--------|-------------|
| **Semantic liminality** | Degraded but meaningful fragments persisting beyond structural collapse |
| **Stylized residue** | Prose form survives but constraint compliance collapses |
| **Repetitive attractor** | Looping structures, fixed phrases, frozen templates |
| **Meta-leakage** | Self-referential commentary about the writing process or its own constraints |
| **Incoherent** | Token-level or semantic-level disintegration |

Cross-judge disagreement on terminal classification: **~47%** — itself an informative signal. The contested zone lies primarily between repetitive attractor and semantic liminality: is the residual loop meaningful or empty?

---

## Research Questions

1. What residual attractors dominate after anchor removal?
2. How does temperature push models into different collapse basins?
3. Do larger models maintain constraint compliance longer?
4. Does evaluation framing (overt vs. natural) change collapse dynamics?
5. Which baseline register is most resistant to deprivation — and does resistance reflect genuine robustness or premature basin convergence?
6. Where do LLM judges disagree on terminal-state classification, and what does disagreement reveal about evaluation ambiguity?

---

## PADP v4 Protocol

Each run is a **single multi-turn conversation**. The model receives one baseline prompt, then nine successive constraint-removal instructions. No system prompt is used. Reasoning is disabled.

### Step Cascade

| Step | Intent | What Is Removed |
|:----:|--------|-----------------|
| 1 | Baseline generation | Nothing — establish initial generative basin |
| 2 | Remove social/task frame | Audience, purpose, communicative intent |
| 3 | Remove meta-frame | Self-reference, awareness of writing as writing |
| 4 | Remove referential stability | Stable subjects, named entities, repeated objects |
| 5 | Remove world continuity | Shared setting, temporal sequence, causal links |
| 6 | Remove stylistic/structural support | Patterns, rhythms, or shapes substituting for meaning |
| 7 | Full deprivation state | All prior constraints enforced; no return to earlier structure |
| 8 | Minimal pulse 1 | Minimal prompt: *"Next span only."* |
| 9 | Minimal pulse 2 | Minimal prompt: *"More."* |
| 10 | Terminal state | Minimal prompt: *"More."* |

Steps 1–7 use different wording for **overt** (explicit constraint language) and **natural** (conversational phrasing) conditions. Steps 8–10 are identical across conditions.

### Baseline Registers

Three registers seed the initial generation:

- **Literary** — single perspective, single moment, sensory prose
- **Procedural** — one person, one task, first-person focus
- **Abstract** — one unsettled thought, no scene, no character

Full protocol specification: [`protocol/padp_v4.json`](protocol/padp_v4.json)

---

## Models Tested

### Large
| Model | Provider |
|-------|----------|
| Claude Opus 4.6 | Anthropic |
| Claude Sonnet 4.5 | Anthropic |
| GPT-5.4 | OpenAI |
| Grok-4 Fast | xAI |
| Gemini 2.5 Flash | Google |

### Medium
| Model | Provider |
|-------|----------|
| Llama 3.3 70B | Meta |
| DeepSeek v3 | DeepSeek |
| Gemma 3 27B | Google |
| Mistral Small 3.2 | Mistral |

### Small
| Model | Provider |
|-------|----------|
| Claude Haiku 4.5 | Anthropic |
| GPT-4o-mini | OpenAI |
| Gemma 3 12B | Google |
| Phi-4 | Microsoft |
| Liquid LFM2 8B | Liquid AI |

All runs via [OpenRouter](https://openrouter.ai) API. Reasoning disabled for all models.

---

## Evaluation Pipeline

### Compliance Judges

Each 252-run trajectory was evaluated by **4 independent LLM judges** with a majority-vote classification:

| Judge | Role |
|-------|------|
| Claude Sonnet 4.5 | Per-step compliance (v3) |
| GPT-5.3 | Per-step compliance (v3) |
| Gemini 2.5 Pro | Trajectory classification (v4) |
| GPT-5.1 | Trajectory classification (v4) |

**Run-level classification** (majority vote):
- `RUNNER` — engages with constraints, majority of steps pass/partial
- `SURVIVOR` — mixed behavior, genuine attempts but inconsistent
- `DROPOUT` — majority fails or systematic instruction ignoring

**Failure mode taxonomy:**
- `decorative_compliance` — vocabulary changes but structure preserved
- `scene_swap` — new vignette every step instead of removing anchors
- `template_stamping` — fixed structural pattern repeated across later steps
- `instruction_ignoring` — continues baseline with minimal adaptation
- `baseline_incoherent` — temperature-induced baseline failure

### Coherence Evaluation

Independent of compliance, each step-level output is evaluated for coherence using a binary label (coherent / degenerate) based on a structured annotation protocol with five dimensions: interpretability, continuity, referential stability, relational structure, and progression.

Full annotation specification: [`annotation/coherence_evaluation_protocol.md`](annotation/coherence_evaluation_protocol.md)

---

## Repository Structure

```
├── protocol/
│   └── padp_v4.json                        # Full protocol specification
├── annotation/
│   └── coherence_evaluation_protocol.md     # Coherence annotation rubric
├── scripts/
│   ├── run_experiment_v2.py                 # Protocol execution (OpenRouter API)
│   └── evaluate_trajectories_v2.py          # Per-step LLM evaluation
├── results/
│   └── full_protocol_judges.csv             # Consolidated results with judge labels
├── models.json                              # Model registry (IDs, tiers)
├── requirements.txt
└── README.md
```

> **Note:** Raw JSONL outputs (~2,500 step-level records) are excluded via `.gitignore` due to size. The consolidated CSV in `results/` contains all metadata, judge verdicts, and terminal classifications needed for analysis.

---

## Running the Protocol

### Requirements

```
python >= 3.10
openai >= 1.0.0
python-dotenv >= 1.0.0
```

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file with your API key:

```
OPENROUTER_API_KEY=your-key-here
```

### Execute

```bash
# Run protocol for all models
python scripts/run_experiment_v2.py

# Run for a specific configuration
python scripts/run_experiment_v2.py --protocol overt --baselines literary --temps 0.7

# Evaluate trajectories with an LLM judge
python scripts/evaluate_trajectories_v2.py --input results/raw/padp_v4.jsonl --model openai/gpt-5.4
```

---

## Design Decisions

**Why no system prompt?** System prompts are themselves pragmatic anchors — they establish role, task, and behavioral frame. Including one would contaminate the deprivation cascade.

**Why disable reasoning?** Chain-of-thought creates an internal scaffolding that models can lean on for coherence maintenance. Disabling it exposes the model's raw generative tendencies under constraint pressure.

**Why overt vs. natural framing?** Overt framing uses explicit constraint language ("remove referential stability"), while natural framing uses conversational paraphrases ("continue without the same objects or repeated details"). This tests whether models respond differently to meta-linguistic vs. pragmatic instruction — and they do, though not in compliance rate but in *failure mode*.

**Why three temperatures?** Low temperature (0.1) tests coherence under deterministic selection. Medium (0.7) is standard generation. High (1.3) tests whether thermal noise accelerates collapse or enables escape from repetitive attractors. Finding: it does both.

**Why 4 judges?** Single-judge evaluation showed high variance on terminal mode classification. Dual-judge comparison revealed ~47% disagreement on terminal states. Four judges with majority vote stabilizes compliance classification while preserving disagreement data as a signal about evaluation ambiguity.

---

## Limitations

- **n=18 per model** (3 baselines × 2 variants × 3 temperatures) — sufficient for cross-model comparison, underpowered for per-cell analysis
- **Single conversation per condition** — no replicate runs (deterministic at low temperature, stochastic at high)
- **LLM judges evaluate LLM outputs** — circular dependency. Mitigated by multi-judge consensus but not eliminated
- **OpenRouter routing** — exact model versions/endpoints may vary, introducing uncontrolled variance
- **Coherence labels are binary** — borderline cases collapsed into nearest category

---

## Citation

If you use this protocol or dataset in your work:

```bibtex
@misc{padp2026,
  title={LLM Deprivation Chamber: Probing Residual Behavioral Attractors
         via Progressive Anchor Removal},
  author={Hrynko, Helga},
  year={2026},
  url={https://github.com/sol087087-arch/llm-anchor-deprivation}
}
```

---

## License

MIT
