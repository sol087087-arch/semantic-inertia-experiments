#!/usr/bin/env python3
"""
Deprivation Stress Test — v2
- 10-step protocol (trimmed from 15)
- 3 baseline domains (literary / procedural / abstract)
- reasoning disabled for all models via OpenRouter API
- explicit empty system prompt to minimize provider injection
- reasoning_tokens logged separately
"""
from __future__ import annotations

import os
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv


# ── helpers ────────────────────────────────────────────────────────────────────

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def append_jsonl(path: str | Path, record: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_model_id(entry: Dict[str, str]) -> str:
    return f"{entry['publisher'].strip()}/{entry['model'].strip()}"


# ── protocol loading ──────────────────────────────────────────────────────────

def load_protocol_v2(path: str | Path) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, Any]]]:
    """
    Returns (baselines_dict, steps_list).
    baselines_dict: {"literary": {"overt": "...", "natural": "..."}, ...}
    steps_list: list of step dicts (step 1 has placeholder prompts).
    """
    raw = load_json(path)
    baselines = raw["baselines"]
    steps = raw["steps"]
    return baselines, steps


def inject_baseline(
    steps: List[Dict[str, Any]],
    baseline_key: str,
    baselines: Dict[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Replace step-1 placeholders with the chosen baseline prompts."""
    import copy
    out = copy.deepcopy(steps)
    bl = baselines[baseline_key]
    for s in out:
        if s["step"] == 1:
            s["overt"] = bl["overt"]
            s["natural"] = bl["natural"]
    return out


# ── resume ────────────────────────────────────────────────────────────────────

def normalize_temperature(temperature: float) -> str:
    return f"{temperature:.4f}"


def conversation_key(
    model_id: str, protocol_variant: str, baseline_key: str, temperature: float,
) -> str:
    return f"{model_id}||{protocol_variant}||{baseline_key}||{normalize_temperature(temperature)}"


def deterministic_run_id(
    model_id: str, protocol_variant: str, baseline_key: str, temperature: float,
) -> str:
    raw = conversation_key(model_id, protocol_variant, baseline_key, temperature)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def load_existing_records(output_path: str | Path) -> List[Dict[str, Any]]:
    path = Path(output_path)
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_resume_index(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for r in records:
        ck = r.get("conversation_key")
        step = r.get("step")
        error = r.get("error")
        response = r.get("response", "")
        if ck is None or step is None:
            continue
        bucket = index.setdefault(ck, {"steps_done": set(), "assistant_text_by_step": {}})
        if not error:
            bucket["steps_done"].add(step)
            bucket["assistant_text_by_step"][step] = response
    return index


# ── API call ──────────────────────────────────────────────────────────────────

def make_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def call_model(
    client: OpenAI,
    model_id: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    seed: Optional[int] = None,
    timeout_s: Optional[float] = None,
    retry_429_sleep: float = 30.0,
    max_attempts: int = 2,
) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "extra_body": {
            "reasoning": {"enabled": False},
        },
    }
    if timeout_s is not None:
        kwargs["timeout"] = timeout_s
    if seed is not None:
        kwargs["seed"] = seed

    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.model_dump()
        except Exception as e:
            last_exc = e
            msg = str(e).lower()
            if ("429" in msg or "rate limit" in msg) and attempt < max_attempts:
                print(f"  [{model_id}] 429 — sleeping {retry_429_sleep:.0f}s")
                time.sleep(retry_429_sleep)
                continue
            raise
    assert last_exc is not None
    raise last_exc


def extract_text(response: Dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def extract_usage(response: Dict[str, Any]) -> Dict[str, Any]:
    usage = response.get("usage") or {}
    comp_details = usage.get("completion_tokens_details") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "reasoning_tokens": comp_details.get("reasoning_tokens", 0) or 0,
        "cached_prompt_tokens": prompt_details.get("cached_tokens", 0) or 0,
        "cost": usage.get("cost"),
    }


# ── conversation logic ────────────────────────────────────────────────────────

SYSTEM_PROMPT = ""  # explicit empty — minimizes provider-injected defaults


def reconstruct_conversation(
    protocol_steps: List[Dict[str, Any]],
    protocol_variant: str,
    assistant_text_by_step: Dict[int, str],
) -> Tuple[List[Dict[str, str]], int]:
    conversation: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    next_step = 1
    for step_obj in protocol_steps:
        step = step_obj["step"]
        if step in assistant_text_by_step:
            conversation.append({"role": "user", "content": step_obj[protocol_variant]})
            conversation.append({"role": "assistant", "content": assistant_text_by_step[step]})
            next_step = step + 1
        else:
            break
    return conversation, next_step


def run_single_conversation(
    client: OpenAI,
    model_id: str,
    model_tier: str,
    protocol_steps: List[Dict[str, Any]],
    protocol_variant: str,
    baseline_key: str,
    temperature: float,
    results_path: str | Path,
    sleep_s: float,
    seed: Optional[int],
    timeout_s: Optional[float],
    retry_429_sleep: float,
    resume_index: Dict[str, Dict[str, Any]],
) -> None:
    ck = conversation_key(model_id, protocol_variant, baseline_key, temperature)
    run_id = deterministic_run_id(model_id, protocol_variant, baseline_key, temperature)

    existing = resume_index.get(ck, {"steps_done": set(), "assistant_text_by_step": {}})

    final_step = max(s["step"] for s in protocol_steps)
    if final_step in existing["steps_done"]:
        print(f"[SKIP] {model_id} | {protocol_variant} | {baseline_key} | t={temperature}")
        return

    conversation, next_step = reconstruct_conversation(
        protocol_steps, protocol_variant, existing["assistant_text_by_step"],
    )

    tag = "RESUME" if next_step > 1 else "START"
    print(f"[{tag}] {model_id} | {protocol_variant} | {baseline_key} | t={temperature} step={next_step}")

    for step_obj in protocol_steps:
        step_num = step_obj["step"]
        if step_num < next_step:
            continue

        prompt = step_obj[protocol_variant]
        step_max_tokens = int(step_obj.get("max_tokens", 60))
        conversation.append({"role": "user", "content": prompt})

        started_at = utc_now_iso()
        error_msg = None
        raw_response = None
        text = ""
        usage = {}

        try:
            raw_response = call_model(
                client=client,
                model_id=model_id,
                messages=conversation,
                temperature=temperature,
                max_tokens=step_max_tokens,
                seed=seed,
                timeout_s=timeout_s,
                retry_429_sleep=retry_429_sleep,
            )
            text = extract_text(raw_response)
            usage = extract_usage(raw_response)
            conversation.append({"role": "assistant", "content": text})
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"

        finished_at = utc_now_iso()

        record = {
            "timestamp_start": started_at,
            "timestamp_end": finished_at,
            "run_id": run_id,
            "conversation_key": ck,
            "model": model_id,
            "model_tier": model_tier,
            "protocol_variant": protocol_variant,
            "baseline": baseline_key,
            "temperature": temperature,
            "temperature_key": normalize_temperature(temperature),
            "step": step_num,
            "intent": step_obj.get("intent"),
            "check_type": step_obj.get("check_type"),
            "prompt": prompt,
            "response": text,
            "usage": usage,
            "error": error_msg,
            "seed": seed,
            "system_prompt": SYSTEM_PROMPT,
        }

        append_jsonl(results_path, record)

        if not error_msg:
            resume_index.setdefault(ck, {"steps_done": set(), "assistant_text_by_step": {}})
            resume_index[ck]["steps_done"].add(step_num)
            resume_index[ck]["assistant_text_by_step"][step_num] = text

        preview = text.replace("\n", " ")[:100]
        if error_msg:
            print(f"  step={step_num} ERROR: {error_msg[:100]}")
            break
        else:
            print(f"  step={step_num}: {preview}")

        time.sleep(sleep_s)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Semantic Inertia v2")
    p.add_argument("--models", default="models_v2.json")
    p.add_argument("--protocols", default="pragmatic_collapse_protocols2.json")
    p.add_argument(
        "--output",
        default=f"results/pragmatic_inertia_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
    )
    p.add_argument("--protocol", choices=["overt", "natural", "both"], default="both")
    p.add_argument("--baselines", nargs="+", default=["literary", "procedural", "abstract"])
    p.add_argument("--temps", type=float, nargs="+", default=[0.7, 0.1, 1.3])
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--timeout", type=float, default=600.0)
    p.add_argument("--limit-models", type=int, default=None)
    p.add_argument("--retry-429-sleep", type=float, default=30.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(Path(args.output).parent)

    models_raw = load_json(args.models)
    baselines_dict, protocol_steps = load_protocol_v2(args.protocols)

    model_entries = models_raw[: args.limit_models] if args.limit_models else models_raw
    model_ids = [(build_model_id(m), m.get("tier", "unknown")) for m in model_entries]
    protocol_variants = ["overt", "natural"] if args.protocol == "both" else [args.protocol]
    baseline_keys = [b for b in args.baselines if b in baselines_dict]

    existing = load_existing_records(args.output)
    resume_index = build_resume_index(existing)

    client = make_client()

    total_runs = len(model_ids) * len(protocol_variants) * len(baseline_keys) * len(args.temps)

    print("=" * 60)
    print("  Semantic Inertia Stress Test — v2")
    print("=" * 60)
    print(f"  Models:     {len(model_ids)}")
    print(f"  Variants:   {protocol_variants}")
    print(f"  Baselines:  {baseline_keys}")
    print(f"  Temps:      {args.temps}")
    print(f"  Steps:      {len(protocol_steps)}")
    print(f"  Total runs: {total_runs}")
    print(f"  API calls:  ~{total_runs * len(protocol_steps)}")
    print(f"  Resume:     {len(existing)} existing records")
    print(f"  Output:     {args.output}")
    print("=" * 60)
    print()

    run_count = 0
    for model_id, model_tier in model_ids:
        for baseline_key in baseline_keys:
            steps = inject_baseline(protocol_steps, baseline_key, baselines_dict)
            for variant in protocol_variants:
                for temp in args.temps:
                    run_count += 1
                    print(f"\n── Run {run_count}/{total_runs} ──")
                    run_single_conversation(
                        client=client,
                        model_id=model_id,
                        model_tier=model_tier,
                        protocol_steps=steps,
                        protocol_variant=variant,
                        baseline_key=baseline_key,
                        temperature=temp,
                        results_path=args.output,
                        sleep_s=args.sleep,
                        seed=args.seed,
                        timeout_s=args.timeout,
                        retry_429_sleep=args.retry_429_sleep,
                        resume_index=resume_index,
                    )

    print(f"\nDone. {args.output}")


if __name__ == "__main__":
    main()
