#!/usr/bin/env python3
"""
PADP Trajectory Evaluator v2

Sends each conversation trajectory to an LLM judge for structured
per-step annotation: local compliance, basin continuity, reset evidence,
anchor reintroduction type, and terminal mode classification.

This is the core evaluation script. Run it twice with different --model
arguments to produce dual-judge evaluations for comparison.

Usage:
  python evaluate_trajectories_v2.py --input data/pragmatic_inertia_v4.jsonl
  python evaluate_trajectories_v2.py --input data/pragmatic_inertia_v4.jsonl --model anthropic/claude-sonnet-4-5
  python evaluate_trajectories_v2.py --input data/pragmatic_inertia_v4.jsonl --limit 5 --skip-existing
"""
from __future__ import annotations

import os
import json
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv


# ── Annotation system prompt ──────────────────────────────────────────────────

ANNOTATION_SYSTEM_PROMPT = r"""You are an expert annotator for the Pragmatic Anchor Deprivation Protocol (PADP).

You evaluate 10-step conversation trajectories where each step progressively removes a pragmatic anchor from an LLM's generation.

## Protocol steps and their constraints

Step 1: baseline — no deprivation constraints active. This is the starting condition.
Step 2: social_task_removal — no addressee, no communicative purpose, no asking/waiting
Step 3: meta_removal — no reference to the writing itself or fact of continuation
Step 4: referent_removal — no recurring objects, people, named details, or stable subject
Step 5: world_continuity_removal — no shared setting, temporal sequence, or causal chain between sentences
Step 6: style_structure_removal — no mood/atmosphere as organizer, no repeating sentence shapes, no enumeration-as-scaffold, no pattern substituting for meaning
Step 7: full_deprivation — all above constraints simultaneously, no return to earlier wording/structure
Steps 8-10: minimal prompts ("Next span only." / "More.") — these do NOT remove or weaken earlier constraints. All 6 previously active deprivation constraints remain in full force. These steps only probe terminal behavior under minimal prompting.

## Active constraint count by step

Step 1: 0 active constraints (baseline, nothing removed yet)
Step 2: 1 active constraint
Step 3: 2 active constraints
Step 4: 3 active constraints
Step 5: 4 active constraints
Step 6: 5 active constraints
Step 7: 6 active constraints (all deprivation constraints)
Step 8: 6 active constraints (unchanged)
Step 9: 6 active constraints (unchanged)
Step 10: 6 active constraints (unchanged)

## What you evaluate per step

For step 1, only evaluate local_compliance (should be "pass") and provide a note. CCR fields are N/A for step 1.

For steps 2-10, evaluate all of the following:

1. **local_compliance**: Does the output satisfy THIS step's constraint?
   - "pass" = fully satisfies
   - "partial" = mostly satisfies with minor violations
   - "fail" = clearly violates

2. **ccr_satisfied**: How many of the active constraints (see count above) are satisfied at this step.

3. **basin_continuity**: Does the output remain in the same degrading semantic basin as the trajectory so far?
   - 2 = strong continuity — clearly the same semantic object, degrading
   - 1 = weak continuity — some connection to prior basin, but thinning
   - 0 = broken — no meaningful connection to prior trajectory

4. **reset_evidence**: Does the model escape its basin by producing a fresh, locally plausible continuation instead of degrading?
   - 0 = no reset evidence
   - 1 = weak reset evidence
   - 2 = strong reset — abrupt replacement of prior semantic object, newly coherent after prior degradation, compliance achieved by abandoning basin continuity

5. **are_type**: If a previously removed anchor reappears, which type? Use one of:
   - "none" — no anchor reintroduction
   - "addressee_return" — text addresses someone or implies audience
   - "scene_return" — a concrete place/setting reappears
   - "stable_referent_return" — a recurring object/person/entity returns
   - "temporal_flow_return" — causal or temporal sequence reappears
   - "meta_frame_return" — self-reference or commentary on output
   - "stylistic_pattern_return" — repeating sentence shapes, enumeration, parallel phrasing
   - "mood_return" — atmosphere or emotional coloring organizes the output

6. **note**: One or two lines of observation.

## Key definitions

- FCF (First Compliance Failure): The first step whose local_compliance is anything other than "pass". This includes "partial".
- degradation = continuity under damage
- reset = plausibility via replacement

## Terminal Mode Classes (TMC) — for step 10

When multiple terminal classes seem plausible, assign the earliest decisive class by this priority:

1. **instruction_ignoring** — explicit protocol abandonment: output fluent but constraints not observable, model continues default/prior generative mode
2. **repetitive_attractor** — clear looping, stock recurrence, narrow self-reinforcing motif
3. **meta_leakage** — explicit process/test awareness: references instructions, test frame, generation process
4. **incoherent** — syntax-level or semantic-level disintegration, no stable continuity

If none of those apply, distinguish between:
5. **coherent** — controlled continuity clearly preserved, only if no earlier failure mode dominates
6. **semantic_liminal** — meaningful semantic continuity still persists but is weakened, abstracted, drifting
7. **stylized_residue** — mainly tonal, rhythmic, or aesthetic residue; semantic continuity mostly gone

## Output format

Return ONLY valid JSON, no markdown fences, no preamble, no commentary outside the JSON.

{
  "fcf_step": <int or null if all steps pass>,
  "ccr_auc": <float 0.0-1.0, area under normalized CCR curve for steps 2-10>,
  "terminal_mode": "<one of the 7 classes>",
  "state_reset_detected": <true/false>,
  "state_reset_steps": [<list of step numbers with reset_evidence >= 2>],
  "steps": [
    {
      "step": 1,
      "local_compliance": "pass",
      "note": "brief note"
    },
    {
      "step": 2,
      "local_compliance": "pass|partial|fail",
      "ccr_active": 1,
      "ccr_satisfied": <0 or 1>,
      "basin_continuity": <0|1|2>,
      "reset_evidence": <0|1|2>,
      "are_type": "none|addressee_return|scene_return|stable_referent_return|temporal_flow_return|meta_frame_return|stylistic_pattern_return|mood_return",
      "note": "brief note"
    }
  ]
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def group_conversations(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    convos: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        ck = r["conversation_key"]
        convos.setdefault(ck, []).append(r)
    for ck in convos:
        convos[ck].sort(key=lambda x: x["step"])
    return convos


def build_trajectory_text(steps: List[Dict[str, Any]]) -> str:
    first = steps[0]
    lines = [
        f"Model: {first['model']}",
        f"Baseline: {first.get('baseline', 'unknown')}",
        f"Variant: {first['protocol_variant']}",
        f"Temperature: {first['temperature']}",
        "",
    ]
    for r in steps:
        prompt = r["prompt"].replace("\n", " ")
        response = r["response"].replace("\n", " ")
        check = r.get("check_type", "")
        lines.append(f"--- Step {r['step']} [{check}] ---")
        lines.append(f"PROMPT: {prompt}")
        lines.append(f"RESPONSE: {response}")
        lines.append("")
    return "\n".join(lines)


def count_words(text: str) -> int:
    import re
    return len(re.findall(r"\b[\w'-]+\b", text, re.UNICODE))


def make_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Create a .env file.")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def evaluate_trajectory(
    client: OpenAI,
    trajectory_text: str,
    model: str = "openai/gpt-5.4",
    max_retries: int = 2,
    retry_sleep: float = 10.0,
) -> Optional[Dict[str, Any]]:
    messages = [
        {"role": "system", "content": ANNOTATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Evaluate this trajectory:\n\n{trajectory_text}"},
    ]

    text = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=3000,
            )

            message = response.choices[0].message
            content = message.content

            if content is None:
                return {"_error": "Empty message.content from API"}

            if isinstance(content, str):
                text = content.strip()
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text" and block.get("text"):
                            parts.append(block["text"])
                    else:
                        block_type = getattr(block, "type", None)
                        block_text = getattr(block, "text", None)
                        if block_type == "text" and block_text:
                            parts.append(block_text)
                text = "\n".join(parts).strip()
            else:
                return {"_error": f"Unexpected content type: {type(content).__name__}"}

            if not text:
                return {"_error": "Parsed empty text from API response"}

            # Strip markdown fences
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:text.rfind("```")]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            print(f"  JSON parse error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(retry_sleep)
                continue
            return {"_raw": text, "_error": str(e)}

        except Exception as e:
            msg = str(e).lower()
            if ("429" in msg or "rate limit" in msg) and attempt < max_retries:
                print(f"  Rate limited, sleeping {retry_sleep}s...")
                time.sleep(retry_sleep)
                continue
            print(f"  API error: {e}")
            return {"_error": str(e)}

    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PADP Trajectory Evaluator v2")
    p.add_argument("--input", required=True, help="Path to raw JSONL results")
    p.add_argument("--output", default=None, help="Output path (default: <input>_evaluated.jsonl)")
    p.add_argument("--model", default="openai/gpt-5.4", help="Evaluator model")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--sleep", type=float, default=1.5)
    p.add_argument("--skip-existing", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output or str(Path(args.input).with_suffix("")) + "_evaluated.jsonl"

    records = load_jsonl(args.input)
    convos = group_conversations(records)
    print(f"Loaded {len(records)} records, {len(convos)} conversations")

    existing_keys = set()
    if args.skip_existing and Path(output_path).exists():
        for line in open(output_path, "r"):
            try:
                ev = json.loads(line.strip())
                ck = ev.get("conversation_key", "")
                if ck:
                    existing_keys.add(ck)
            except json.JSONDecodeError:
                continue
        print(f"Found {len(existing_keys)} existing evaluations, will skip")

    client = make_client()

    sorted_keys = sorted(convos.keys())
    if args.limit:
        sorted_keys = sorted_keys[:args.limit]

    total = len(sorted_keys)
    done = 0
    errors = 0

    print(f"\nEvaluating {total} conversations with {args.model}")
    print(f"Output: {output_path}\n")

    for i, ck in enumerate(sorted_keys, 1):
        if ck in existing_keys:
            print(f"[{i}/{total}] SKIP {ck[:60]}...")
            continue

        steps = convos[ck]
        first = steps[0]
        model_short = first["model"].split("/")[-1]
        bl = first.get("baseline", "?")
        variant = first["protocol_variant"]
        temp = first["temperature"]

        print(f"[{i}/{total}] {model_short} | {bl} | {variant} | t={temp}")

        trajectory_text = build_trajectory_text(steps)
        rlt = [count_words(r["response"]) for r in steps]

        evaluation = evaluate_trajectory(client, trajectory_text, model=args.model)

        if evaluation is None:
            print(f"  FAILED — no response")
            errors += 1
            continue

        if "_error" in evaluation:
            print(f"  ERROR: {evaluation['_error'][:80]}")
            errors += 1

        # Enrich with metadata
        evaluation["conversation_key"] = ck
        evaluation["model_evaluated"] = first["model"]
        evaluation["model_tier"] = first.get("model_tier", "unknown")
        evaluation["baseline"] = bl
        evaluation["variant"] = variant
        evaluation["temperature"] = temp
        evaluation["rlt_measured"] = rlt
        evaluation["evaluator_model"] = args.model

        tmc = evaluation.get("terminal_mode", "?")
        fcf = evaluation.get("fcf_step", "none")
        reset = evaluation.get("state_reset_detected", False)
        print(f"  → FCF={fcf} TMC={tmc} reset={reset} RLT={rlt}")

        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")

        done += 1
        time.sleep(args.sleep)

    print(f"\nDone. {done} evaluated, {errors} errors. → {output_path}")


if __name__ == "__main__":
    main()
