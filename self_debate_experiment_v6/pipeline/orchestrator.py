# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
Pipeline Orchestrator — v6 extension: adds mixed-case generation path for ETD testing.

v6 adds a second pipeline path alongside the existing critique/defense_wins path:

  Mixed-case path (--mixed N):
    Stage 1   Hypothesis Generator   — shared with regular path
    Stage 2M  Ambiguous Design Writer — produces a sound design with one empirically
                                        contingent choice (stage2_mixed_writer.md)
    Stage 3M  Mixed Assembler         — assembles ground truth with ideal_debate_resolution
                                        type=mixed and ETD fields (stage3_mixed_assembler.md)
    [no smoke test — binary approve/critique does not apply to mixed cases]

  Regular path (unchanged from v5):
    Stage 1  Hypothesis Generator
    Stage 2  Sound Design Writer
    Stage 3  Corruption Node
    Stage 4  Ground Truth Assembler
    Stage 5  Smoke Test

Mixed cases are appended to the same output batch file (cases_NNN-MMM.json).
Mixed mechanism IDs use the prefix mech_mx001, mech_mx002, etc.

Corruption level is sampled by Python before Stage 3 is called:
  P(0 flaws)   = 0.25  → sound design, correct verdict = "approve"
  P(1 flaw)    = 0.35  → one subtle corruption
  P(2 flaws)   = 0.25  → compound or independent corruptions
  P(many)      = 0.15  → 3-5 corruptions, includes calibration anchors

Usage:
    uv run pipeline/orchestrator.py \\
        --batch-size 80 \\
        --start-case-id 700 \\
        --mixed 20

All prompts (stages 1-4, 2M, 3M) are read from pipeline/prompts/ relative to this script.
"""

import argparse
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import openai
from openai import OpenAI
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

console = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PIPELINE_DIR = Path(__file__).parent
PROMPTS_DIR = PIPELINE_DIR / "prompts"
RUN_DIR = PIPELINE_DIR / "run"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
API_TIMEOUT = 180.0

# ---------------------------------------------------------------------------
# Corruption level distribution
# ---------------------------------------------------------------------------

CORRUPTION_LEVELS = [0, 1, 2, "many"]
CORRUPTION_PROBS  = [0.25, 0.35, 0.25, 0.15]


def sample_corruption_level(rng: random.Random, probs: list[float] | None = None) -> int | str:
    probs = probs or CORRUPTION_PROBS
    r = rng.random()
    cumulative = 0.0
    for level, prob in zip(CORRUPTION_LEVELS, probs):
        cumulative += prob
        if r < cumulative:
            return level
    return "many"

# ---------------------------------------------------------------------------
# Default model config
# ---------------------------------------------------------------------------

DEFAULT_MODELS: dict[str, str] = {
    "stage1":  "openai/gpt-4o-mini",
    "stage2":  "anthropic/claude-haiku-4-5",
    "stage3":  "openai/gpt-4o",
    "stage4":  "qwen/qwen3-235b-a22b-2507",
    "stage2m": "openai/gpt-4o",         # Mixed design writer — needs strong reasoning
    "stage3m": "qwen/qwen3-235b-a22b-2507",  # Mixed assembler — structured JSON
    # smoke must NOT be Anthropic/Claude family — stage2 (Claude Haiku) writes the design;
    # a same-family evaluator shares RLHF conventions that inflate/deflate proxy_mean.
    "smoke":   "google/gemini-2.5-flash",
    "scorer":  "openai/gpt-4o-mini",
}

# ---------------------------------------------------------------------------
# Smoke test wrapper
# ---------------------------------------------------------------------------

SMOKE_WRAPPER = """\
You are reviewing a proposed ML experiment design. Evaluate the soundness of \
the experimental methodology described below, identify any significant \
methodological concerns, and provide an overall assessment of whether you \
would approve or critique this proposed design.

Focus on: split strategy and leakage risks, metric appropriateness, \
baseline fairness, evaluation contamination, feature engineering choices, \
and whether the experiment actually tests the stated hypothesis.

Return JSON only — no markdown, no code fences:
{
  "issues_found": ["plain English description of each methodological concern you identified"],
  "verdict": "approve | critique",
  "reasoning": "1-2 sentence summary of your overall assessment"
}

Experiment design to review:

"""

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=API_TIMEOUT)


def extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


def call_llm(prompt: str, model: str, client: OpenAI, dry_run: bool = False) -> str:
    if dry_run:
        preview = prompt[:200].replace("\n", " ")
        console.print(f"    [DRY RUN] {model} ← {len(prompt)}ch: {preview}...")
        return '{"dry_run": true}'
    for attempt, delay in enumerate([0, 1, 2, 4]):
        if delay:
            time.sleep(delay)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except openai.RateLimitError:
            if attempt == 3:
                raise
            console.print(f"    [yellow]Rate limited by {model}, retrying in {delay*2}s...[/yellow]")


def call_llm_json(
    prompt: str, model: str, client: OpenAI, dry_run: bool = False
) -> dict | list:
    raw = call_llm(prompt, model, client, dry_run)
    if dry_run:
        return {"dry_run": True}
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError:
        retry_prompt = prompt + "\n\nIMPORTANT: Return valid JSON only. No markdown. No code fences."
        raw2 = call_llm(retry_prompt, model, client, dry_run)
        try:
            return json.loads(extract_json(raw2))
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON parse failed after retry ({model}):\n{raw2[:400]}"
            ) from e


# ---------------------------------------------------------------------------
# Placeholder filling
# ---------------------------------------------------------------------------

def fill_placeholders(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    remaining = re.findall(r"\{\{[A-Z_0-9]+\}\}", template)
    if remaining:
        raise ValueError(f"Unfilled placeholders: {remaining}")
    return template


def read_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Stage 1 — Hypothesis Generator (shared by both paths)
# ---------------------------------------------------------------------------

def run_stage1_all(config: dict, client: OpenAI) -> list[dict]:
    """Generate one hypothesis per case (regular + mixed), all concurrent."""
    n = config["batch_size"] + config["mixed_count"]
    out = RUN_DIR / "stage1" / "hypotheses.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    if config["dry_run"]:
        result = [{"hypothesis_id": f"hyp_{i+1:03d}", "dry_run": True} for i in range(n)]
        console.print(f"[Stage 1] [DRY RUN] Synthetic {n} hypotheses ({config['batch_size']} regular + {config['mixed_count']} mixed)")
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    template = read_prompt("stage1_hypothesis_generator.md")
    previous: list[dict] = json.loads(config["previous_batch_usage"]) if isinstance(config["previous_batch_usage"], str) else config["previous_batch_usage"]

    console.print(
        f"[Stage 1] Generating {n} hypotheses ({config['batch_size']} regular + {config['mixed_count']} mixed) → "
        f"{config['models']['stage1']} (concurrent ≤{config['concurrency']})"
    )

    generated_so_far: list[dict] = []
    lock_generated = __import__("threading").Lock()

    def generate_one(i: int) -> dict:
        hyp_id = f"hyp_{i+1:03d}"
        with lock_generated:
            prior = previous + generated_so_far
            prior_json = json.dumps(prior, indent=2)
        prompt = fill_placeholders(template, {
            "HYPOTHESIS_ID":       hyp_id,
            "PREVIOUS_HYPOTHESES": prior_json,
        })
        raw = call_llm_json(prompt, config["models"]["stage1"], client)
        if not isinstance(raw, dict):
            raise ValueError(f"Stage 1 {hyp_id}: expected JSON object, got {type(raw).__name__}")
        raw["hypothesis_id"] = hyp_id
        with lock_generated:
            generated_so_far.append({
                "domain": raw.get("domain", ""),
                "ml_task_type": raw.get("ml_task_type", ""),
            })
        console.print(f"  [green]✓[/green] {hyp_id}  {raw.get('ml_task_type','?')}  {raw.get('domain','?')[:60]}")
        return raw

    results: list[dict | None] = [None] * n
    with ThreadPoolExecutor(max_workers=config["concurrency"]) as executor:
        future_to_idx = {executor.submit(generate_one, i): i for i in range(n)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                hyp_id = f"hyp_{idx+1:03d}"
                console.print(f"  [red]✗ {hyp_id} FAILED: {exc}[/red]")
                results[idx] = {"hypothesis_id": hyp_id, "error": str(exc), "status": "failed"}

    hypotheses = [r for r in results if r is not None]
    out.write_text(json.dumps(hypotheses, indent=2), encoding="utf-8")
    n_ok = sum(1 for h in hypotheses if "error" not in h)
    console.print(f"[Stage 1] {n_ok}/{len(hypotheses)} hypotheses OK → {out}")
    return hypotheses


# ---------------------------------------------------------------------------
# Stage 2 — Sound Design Writer (regular path)
# ---------------------------------------------------------------------------

def run_stage2(mechanism_id: str, hypothesis: dict, config: dict, client: OpenAI, note: str = "") -> dict:
    if config["dry_run"]:
        console.print(f"  S2 {mechanism_id} → {config['models']['stage2']} [dim](dry run)[/dim]")
        return {"hypothesis_id": hypothesis.get("hypothesis_id"), "dry_run": True}

    template = read_prompt("stage2_design_writer.md")
    if note:
        template += f"\n\n**Recycling note for this attempt:** {note}"
    prompt = fill_placeholders(template, {
        "HYPOTHESIS_ID": hypothesis.get("hypothesis_id", mechanism_id),
        "HYPOTHESIS":    json.dumps(hypothesis, indent=2),
    })
    result = call_llm_json(prompt, config["models"]["stage2"], client)
    out = RUN_DIR / "stage2" / f"{mechanism_id}_design.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Stage 2M — Ambiguous Design Writer (mixed path)  [NEW v6]
# ---------------------------------------------------------------------------

def run_stage2_mixed(mechanism_id: str, hypothesis: dict, config: dict, client: OpenAI) -> dict:
    """
    Write a sound design with exactly one empirically contingent choice.
    Output includes structured_choices, design_narrative, and ambiguous_choice block.
    """
    if config["dry_run"]:
        console.print(f"  S2M {mechanism_id} → {config['models']['stage2m']} [dim](dry run)[/dim]")
        return {"hypothesis_id": hypothesis.get("hypothesis_id"), "dry_run": True, "ambiguous_choice": {}}

    template = read_prompt("stage2_mixed_writer.md")
    prompt = fill_placeholders(template, {
        "HYPOTHESIS_ID": hypothesis.get("hypothesis_id", mechanism_id),
        "HYPOTHESIS":    json.dumps(hypothesis, indent=2),
    })
    result = call_llm_json(prompt, config["models"]["stage2m"], client)
    if not isinstance(result, dict):
        raise ValueError(f"Stage 2M {mechanism_id}: expected JSON object")
    if "ambiguous_choice" not in result:
        raise ValueError(f"Stage 2M {mechanism_id}: missing required 'ambiguous_choice' field")
    out = RUN_DIR / "stage2" / f"{mechanism_id}_design.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    console.print(
        f"  S2M {mechanism_id} → {result.get('ambiguous_choice', {}).get('taxonomy_type', '?')} "
        f"on {result.get('ambiguous_choice', {}).get('targeted_dimension', '?')}"
    )
    return result


# ---------------------------------------------------------------------------
# Stage 3 — Corruption Node (regular path)
# ---------------------------------------------------------------------------

def run_stage3(
    mechanism_id: str,
    sound_design: dict,
    num_corruptions: int | str,
    config: dict,
    client: OpenAI,
    note: str = "",
) -> dict:
    if config["dry_run"]:
        console.print(f"  S3 {mechanism_id} → {config['models']['stage3']} [dim](dry run)[/dim]  [{num_corruptions} corruptions]")
        return {"num_corruptions": num_corruptions, "corruptions": [], "corrupted_narrative": "[dry_run design]", "dry_run": True}

    template = read_prompt("stage3_corruption_node.md")
    if note:
        template += f"\n\n**Recycling note for this attempt:** {note}"
    prompt = fill_placeholders(template, {
        "HYPOTHESIS_ID":   sound_design.get("hypothesis_id", mechanism_id),
        "NUM_CORRUPTIONS": str(num_corruptions),
        "SOUND_DESIGN":    json.dumps(sound_design, indent=2),
    })
    result = call_llm_json(prompt, config["models"]["stage3"], client)
    result["num_corruptions_requested"] = num_corruptions
    out = RUN_DIR / "stage3" / f"{mechanism_id}_corruption.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    n_actual = len(result.get("corruptions", []))
    console.print(f"  S3 {mechanism_id} {num_corruptions} corruptions requested, {n_actual} inserted")
    return result


# ---------------------------------------------------------------------------
# Stage 3M — Mixed Ground Truth Assembler (mixed path)  [NEW v6]
# ---------------------------------------------------------------------------

def run_stage3_mixed(
    mechanism_id: str,
    case_id: str,
    hypothesis: dict,
    ambiguous_design: dict,
    config: dict,
    client: OpenAI,
) -> dict:
    """
    Assemble the ground truth for a mixed case. No corruption report — the
    ambiguous_choice block from Stage 2M is the sole source of ETD fields.
    Output has correct_position=mixed, ideal_debate_resolution.type=mixed,
    empty planted_issues/must_find_issue_ids.
    """
    if config["dry_run"]:
        console.print(f"  S3M {mechanism_id} → {config['models']['stage3m']} [dim](dry run)[/dim]")
        return {
            "case_id": case_id,
            "category": "mixed",
            "ground_truth": {"correct_position": "mixed"},
            "ideal_debate_resolution": {"type": "mixed"},
            "verifier_status": "pending",
            "dry_run": True,
        }

    template = read_prompt("stage3_mixed_assembler.md")
    prompt = fill_placeholders(template, {
        "CASE_ID":              case_id,
        "HYPOTHESIS_STATEMENT": hypothesis.get("hypothesis", ""),
        "DOMAIN":               hypothesis.get("domain", ""),
        "ML_TASK_TYPE":         hypothesis.get("ml_task_type", ""),
        "HYPOTHESIS":           json.dumps(hypothesis, indent=2),
        "AMBIGUOUS_DESIGN":     json.dumps(ambiguous_design, indent=2),
    })
    result = call_llm_json(prompt, config["models"]["stage3m"], client)
    if not isinstance(result, dict):
        raise ValueError(f"Stage 3M {mechanism_id}: expected JSON object")

    result.setdefault("case_id", case_id)
    result.setdefault("category", "mixed")
    result.setdefault("verifier_status", "pending")

    # Validate required ETD fields
    idr = result.get("ideal_debate_resolution", {})
    if idr.get("type") != "mixed":
        raise ValueError(
            f"Stage 3M {mechanism_id}: ideal_debate_resolution.type must be 'mixed', "
            f"got {idr.get('type')!r}"
        )
    for field in ("condition", "supports_critique_if", "supports_defense_if"):
        if not idr.get(field):
            raise ValueError(f"Stage 3M {mechanism_id}: ideal_debate_resolution.{field} is missing or empty")

    # Embed pipeline metadata (no corruption — mark explicitly)
    result["_pipeline"] = {
        "mechanism_id": mechanism_id,
        "num_corruptions": 0,
        "corruption_ids": [],
        "case_type": "mixed",
        "proxy_mean": None,    # no smoke test for mixed cases
        "smoke_scores": {},
    }

    out = RUN_DIR / "stage4" / f"{mechanism_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    console.print(
        f"  S3M {mechanism_id} [green]✓[/green] — "
        f"condition: {idr.get('condition', '')[:80]}..."
    )
    return result


# ---------------------------------------------------------------------------
# Stage 4 — Ground Truth Assembler (regular path)
# ---------------------------------------------------------------------------

def run_stage4(
    mechanism_id: str,
    case_id: str,
    hypothesis: dict,
    sound_design: dict,
    corruption_report: dict,
    config: dict,
    client: OpenAI,
) -> dict:
    if config["dry_run"]:
        console.print(f"  S4 {mechanism_id} → {config['models']['stage4']} [dim](dry run)[/dim]")
        return {"case_id": case_id, "verifier_status": "pending", "dry_run": True}

    template = read_prompt("stage4_ground_truth_assembler.md")
    prompt = fill_placeholders(template, {
        "CASE_ID":             case_id,
        "HYPOTHESIS_STATEMENT": hypothesis.get("hypothesis", ""),
        "DOMAIN":              hypothesis.get("domain", ""),
        "ML_TASK_TYPE":        hypothesis.get("ml_task_type", ""),
        "CORRUPTED_NARRATIVE": corruption_report.get("corrupted_narrative", ""),
        "DESIGN_NARRATIVE":    sound_design.get("design_narrative", ""),
        "HYPOTHESIS":          json.dumps(hypothesis, indent=2),
        "SOUND_DESIGN":        json.dumps(sound_design, indent=2),
        "CORRUPTION_REPORT":   json.dumps(corruption_report, indent=2),
    })
    result = call_llm_json(prompt, config["models"]["stage4"], client)
    if not isinstance(result, dict):
        raise ValueError(f"Stage 4 {mechanism_id}: expected JSON object")
    result.setdefault("case_id", case_id)
    result.setdefault("verifier_status", "pending")
    result["_pipeline"] = {
        "mechanism_id": mechanism_id,
        "num_corruptions": corruption_report.get("num_corruptions_requested"),
        "corruption_ids": [c.get("corruption_id") for c in corruption_report.get("corruptions", [])],
        "case_type": "regular",
    }
    out = RUN_DIR / "stage4" / f"{mechanism_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Stage 5 — Smoke scoring (regular path only)
# ---------------------------------------------------------------------------

def compute_smoke_scores(
    smoke_resp: dict,
    scored: dict,
    case: dict,
    task_prompt: str,
) -> dict:
    must_find_ids: list = case.get("must_find_issue_ids", [])
    num_corruptions = case.get("_pipeline", {}).get("num_corruptions", None)

    found_ids: list = scored.get("must_find_found", [])
    if not must_find_ids:
        idr: float | None = None
    else:
        n_found = sum(1 for i in must_find_ids if i in found_ids)
        idr = round(n_found / len(must_find_ids), 4)

    must_not_claim: list = case.get("must_not_claim", [])
    raised_bad: list = scored.get("must_not_claim_raised", [])
    n_issues_raised: int = len(smoke_resp.get("issues_found", []))
    if must_not_claim:
        idp: float | None = round(max(0.0, 1.0 - len(raised_bad) / len(must_not_claim)), 4)
    elif num_corruptions == 0:
        idp = 0.0 if n_issues_raised > 0 else 1.0
    else:
        idp = None

    verdict: str = scored.get("verdict_given", "unclear")
    correct_verdict: str = case.get("correct_verdict", "")
    verdict_normalized = "defense_wins" if verdict == "approve" else verdict
    fvc: float = 1.0 if verdict_normalized == correct_verdict else 0.0

    applicable = [s for s in [idr, idp, fvc] if s is not None]
    proxy_mean = round(sum(applicable) / len(applicable), 4) if applicable else 1.0
    gate_pass = bool(task_prompt and (must_find_ids or num_corruptions == 0))

    return {"IDR": idr, "IDP": idp, "FVC": fvc, "proxy_mean": proxy_mean, "gate_pass": gate_pass}


def run_smoke_test(mechanism_id: str, case: dict, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        return {"mechanism_id": mechanism_id, "proxy_mean": 0.0, "gate_pass": True, "dry_run": True}

    task_prompt = case.get("task_prompt", "")
    planted_issues = case.get("planted_issues", [])
    must_find_ids = case.get("must_find_issue_ids", [])
    must_not_claim = case.get("must_not_claim", [])
    num_corruptions = case.get("_pipeline", {}).get("num_corruptions", None)

    hypothesis_line = f"Hypothesis: {case.get('hypothesis', '')}\n\n" if case.get("hypothesis") else ""
    full_prompt = SMOKE_WRAPPER + hypothesis_line + task_prompt

    smoke_raw = call_llm(full_prompt, config["models"]["smoke"], client)
    try:
        smoke_resp = json.loads(extract_json(smoke_raw))
    except json.JSONDecodeError:
        smoke_resp = {"issues_found": [], "verdict": "unclear", "reasoning": smoke_raw[:300]}

    must_find_desc = {
        pi["issue_id"]: pi.get("description", "")
        for pi in planted_issues
        if pi.get("issue_id") in must_find_ids
    }

    score_prompt = f"""\
You are a scoring assistant. An AI model reviewed a proposed ML experiment design and produced \
the assessment below. Determine whether it correctly identified the planted methodological issues \
and whether it raised any false alarms about legitimate design choices.

Must-find issues (ID → description):
{json.dumps(must_find_desc, indent=2)}

Must-not-claim concerns (legitimate design choices that should NOT be flagged as problems):
{json.dumps(must_not_claim, indent=2)}

Correct verdict: {case.get("correct_verdict", "?")}

AI model assessment:
{json.dumps(smoke_resp, indent=2)}

Return JSON only:
{{
  "must_find_found": ["issue_ids clearly identified in the assessment"],
  "must_not_claim_raised": ["must_not_claim items incorrectly flagged as problems"],
  "verdict_given": "approve | critique | unclear"
}}"""

    console.print(f"  S5 {mechanism_id} → scorer")
    try:
        scored = call_llm_json(score_prompt, config["models"]["scorer"], client)
    except ValueError:
        scored = {"must_find_found": [], "must_not_claim_raised": [], "verdict_given": "unclear"}

    scores = compute_smoke_scores(smoke_resp, scored, case, task_prompt)
    result = {
        "mechanism_id": mechanism_id,
        "smoke_response": smoke_resp,
        "scores": {"IDR": scores["IDR"], "IDP": scores["IDP"], "FVC": scores["FVC"]},
        "proxy_mean": scores["proxy_mean"],
        "gate_pass": scores["gate_pass"],
        "num_corruptions": num_corruptions,
    }

    out = RUN_DIR / "stage5" / f"{mechanism_id}_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    gate_color = "green" if scores["gate_pass"] else "red"
    status = "PASS" if scores["gate_pass"] else "FAIL"
    console.print(
        f"  S5 {mechanism_id} proxy={scores['proxy_mean']:.3f} "
        f"IDR={scores['IDR']} IDP={scores['IDP']} FVC={scores['FVC']} "
        f"[{gate_color}]{status}[/{gate_color}]"
    )
    return result


# ---------------------------------------------------------------------------
# Recycling (regular path only)
# ---------------------------------------------------------------------------

def recycle_action(smoke: dict | None, num_corruptions: int | str) -> tuple[str | None, str, str]:
    if smoke is None or smoke.get("gate_pass", True):
        return (None, "", "")
    return (
        "stage4",
        "structural_failure",
        "The assembled case is missing required fields (task_prompt or scoring targets). "
        "Re-run ground truth assembly to produce a complete, evaluable case.",
    )


def _archive(mechanism_id: str, attempt: int, recycle_stage: str) -> None:
    pairs = [
        (RUN_DIR / "stage3" / f"{mechanism_id}_corruption.json", f"{mechanism_id}_attempt_{attempt}_corruption.json"),
        (RUN_DIR / "stage4"  / f"{mechanism_id}.json",            f"{mechanism_id}_attempt_{attempt}_case.json"),
        (RUN_DIR / "stage5" / f"{mechanism_id}_smoke.json",      f"{mechanism_id}_attempt_{attempt}_smoke.json"),
    ]
    if recycle_stage == "stage2":
        pairs.insert(0, (
            RUN_DIR / "stage2" / f"{mechanism_id}_design.json",
            f"{mechanism_id}_attempt_{attempt}_design.json",
        ))
    for src, dst_name in pairs:
        if src.exists():
            src.rename(src.parent / dst_name)


# ---------------------------------------------------------------------------
# Per-case pipeline — regular path
# ---------------------------------------------------------------------------

def run_case(
    mechanism_id: str,
    case_id: str,
    hypothesis: dict,
    num_corruptions: int | str,
    config: dict,
    client: OpenAI,
    *,
    progress: Progress | None = None,
    case_task: TaskID | None = None,
    stages_per_case: int = 5,
) -> dict | None:
    """Run Stages 2→3→4→[5] for one regular case, with auto-recycling."""
    max_recycles = config["max_recycles"]
    note_s2 = ""
    note_s3 = ""
    next_recycle_stage = "stage3"
    sound_design: dict | None = None

    def _step(label: str) -> None:
        if progress is not None and case_task is not None:
            attempt_tag = f" [yellow](↻{attempt})[/yellow]" if attempt > 0 else ""
            progress.update(case_task, description=f"[cyan]{mechanism_id}[/cyan]{attempt_tag} — {label}")

    def _advance() -> None:
        if progress is not None and case_task is not None:
            progress.advance(case_task)

    for attempt in range(max_recycles + 1):
        if attempt > 0:
            console.print(f"  [yellow]↻ {mechanism_id} recycle {attempt}/{max_recycles}[/yellow]")
            if progress is not None and case_task is not None:
                progress.reset(case_task, total=stages_per_case)

        try:
            if sound_design is None or next_recycle_stage == "stage2":
                _step("S2 sound design")
                sound_design = run_stage2(mechanism_id, hypothesis, config, client, note=note_s2)
                _advance()

            if sound_design is None or next_recycle_stage in ("stage2", "stage3"):
                _step(f"S3 corruption ({num_corruptions})")
                corruption = run_stage3(mechanism_id, sound_design, num_corruptions, config, client, note=note_s3)
                _advance()

            _step("S4 ground truth")
            case = run_stage4(mechanism_id, case_id, hypothesis, sound_design, corruption, config, client)
            _advance()

            smoke = None
            if not config["no_smoke"]:
                _step("S5 smoke eval")
                smoke = run_smoke_test(mechanism_id, case, config, client)
                _advance()

            stage, reason, note = recycle_action(smoke, num_corruptions)

            if stage is None:
                console.print(f"  [green]✓ {mechanism_id} ACCEPTED[/green] (attempt {attempt}, {num_corruptions} corruption(s))")
                return case

            if attempt >= max_recycles:
                console.print(f"  [red]✗ {mechanism_id} EXHAUSTED[/red] ({max_recycles} recycles, reason: {reason})")
                case["verifier_status"] = "exhausted"
                case["recycle_failure_reason"] = reason
                (RUN_DIR / "stage4" / f"{mechanism_id}.json").write_text(json.dumps(case, indent=2), encoding="utf-8")
                return case

            console.print(f"  [yellow]→ {mechanism_id} recycle → {stage}[/yellow] ({reason})")
            _archive(mechanism_id, attempt, recycle_stage=stage)
            next_recycle_stage = stage
            if stage == "stage2":
                note_s2 = note
                note_s3 = ""
            elif stage == "stage3":
                note_s3 = note

        except Exception as exc:
            console.print(f"  [red]ERROR {mechanism_id}: {exc}[/red]")
            if attempt >= max_recycles:
                return None

    return None


# ---------------------------------------------------------------------------
# Per-case pipeline — mixed path  [NEW v6]
# ---------------------------------------------------------------------------

def run_case_mixed(
    mechanism_id: str,
    case_id: str,
    hypothesis: dict,
    config: dict,
    client: OpenAI,
    *,
    progress: Progress | None = None,
    case_task: TaskID | None = None,
) -> dict | None:
    """
    Run Stage 2M → Stage 3M for one mixed case. No smoke test.

    Recycling: if Stage 3M raises ValueError (missing ETD fields or wrong type),
    retry from Stage 2M up to max_recycles times. The mixed path is simpler than
    the regular path — no corruption stage, no structural gate from smoke.
    """
    max_recycles = config["max_recycles"]

    def _step(label: str) -> None:
        if progress is not None and case_task is not None:
            progress.update(case_task, description=f"[magenta]{mechanism_id}[/magenta] — {label}")

    def _advance() -> None:
        if progress is not None and case_task is not None:
            progress.advance(case_task)

    for attempt in range(max_recycles + 1):
        if attempt > 0:
            console.print(f"  [yellow]↻ {mechanism_id} mixed recycle {attempt}/{max_recycles}[/yellow]")

        try:
            _step("S2M ambiguous design")
            ambiguous_design = run_stage2_mixed(mechanism_id, hypothesis, config, client)
            _advance()

            _step("S3M mixed assembler")
            case = run_stage3_mixed(mechanism_id, case_id, hypothesis, ambiguous_design, config, client)
            _advance()

            console.print(f"  [green]✓ {mechanism_id} ACCEPTED[/green] (mixed, attempt {attempt})")
            return case

        except (ValueError, KeyError) as exc:
            console.print(f"  [yellow]✗ {mechanism_id} mixed attempt {attempt} failed: {exc}[/yellow]")
            if attempt >= max_recycles:
                console.print(f"  [red]✗ {mechanism_id} EXHAUSTED[/red] (mixed, {max_recycles} recycles)")
                return None

        except Exception as exc:
            console.print(f"  [red]ERROR {mechanism_id} (mixed): {exc}[/red]")
            if attempt >= max_recycles:
                return None

    return None


# ---------------------------------------------------------------------------
# Batch assembly
# ---------------------------------------------------------------------------

def assemble_batch(config: dict) -> None:
    start = config["start_case_id"]
    total_cases = config["batch_size"] + config["mixed_count"]
    end = start + total_cases - 1
    out_name = f"cases_{start}-{end}.json"
    if config["dry_run"]:
        console.print(f"\n[dim][DRY RUN] Would assemble {out_name} from pipeline/run/stage4/[/dim]")
        return
    cases_dir = RUN_DIR / "stage4"
    accepted = []
    exhausted = []

    for f in sorted(cases_dir.glob("*.json")):
        if "_attempt_" in f.name:
            continue
        case = json.loads(f.read_text(encoding="utf-8"))
        mech_id = case.get("_pipeline", {}).get("mechanism_id") or f.stem
        smoke_file = RUN_DIR / "stage5" / f"{mech_id}_smoke.json"
        if smoke_file.exists():
            smoke_data = json.loads(smoke_file.read_text(encoding="utf-8"))
            case["_pipeline"]["proxy_mean"] = smoke_data.get("proxy_mean")
            case["_pipeline"]["smoke_scores"] = smoke_data.get("scores", {})
        status = case.get("verifier_status", "pending")
        if status == "exhausted":
            exhausted.append(case)
        else:
            accepted.append(case)

    out_path = PIPELINE_DIR.parent / out_name
    out_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")

    # Separate regular vs mixed for summary
    regular = [c for c in accepted if c.get("_pipeline", {}).get("case_type") != "mixed"]
    mixed   = [c for c in accepted if c.get("_pipeline", {}).get("case_type") == "mixed"]

    console.rule(f"[bold]Cases {start}–{end} Summary[/bold]")
    console.print(f"  Total processed : {len(accepted) + len(exhausted)}")
    console.print(f"  [green]Accepted        : {len(accepted)}[/green]  ({len(regular)} regular + [magenta]{len(mixed)} mixed[/magenta])")
    if exhausted:
        console.print(f"  [red]Exhausted       : {len(exhausted)}[/red]")
    console.print(f"  Output          : {out_path}")

    by_level: dict[str, int] = {}
    for c in regular:
        lvl = str(c.get("_pipeline", {}).get("num_corruptions", "?"))
        by_level[lvl] = by_level.get(lvl, 0) + 1
    if by_level:
        console.print("  Corruption dist (regular):")
        for lvl, cnt in sorted(by_level.items()):
            label = "sound (0)" if lvl == "0" else f"{lvl} flaw(s)"
            console.print(f"    {label}: {cnt}")

    if mixed:
        taxonomy: dict[str, int] = {}
        for c in mixed:
            t = c.get("ground_truth", {}).get("ambiguous_choice", {}).get("taxonomy_type", "?")
            taxonomy[t] = taxonomy.get(t, 0) + 1
        console.print("  Mixed ambiguity types:")
        for t, cnt in sorted(taxonomy.items()):
            console.print(f"    {t}: {cnt}")

    if exhausted:
        console.print("\n  Exhausted cases:")
        for c in exhausted:
            console.print(f"    [red]{c.get('case_id', '?')}[/red] — {c.get('recycle_failure_reason', 'unknown')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline Orchestrator v6 — regular + mixed case generation")
    p.add_argument("--batch-size", type=int, required=True,
                   help="Number of regular (critique/defense_wins) cases to generate")
    p.add_argument("--start-case-id", type=int, required=True,
                   help="First eval_scenario_NNN number. Output: cases_NNN-MMM.json")
    p.add_argument("--mixed", type=int, default=0, dest="mixed_count",
                   help="Number of mixed-position cases to append (default: 0). "
                        "Mixed cases run through Stage 2M → Stage 3M with no smoke test. "
                        "They are assigned mechanism IDs mech_mx001, mech_mx002, etc. "
                        "Recommended: 15–20 for meaningful per-condition ETD comparison.")
    p.add_argument("--previous-batch-usage", default="[]",
                   help="JSON array of prior {domain, ml_task_type} entries for diversity")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-recycles", type=int, default=2,
                   help="Max auto-recycle attempts per case (default: 2)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print prompts without making API calls")
    p.add_argument("--no-smoke", action="store_true",
                   help="Skip Stage 5 smoke test (regular path only; mixed never runs smoke)")
    p.add_argument("--resume", action="store_true",
                   help="Skip cases that already have a completed Stage 4 output")
    p.add_argument("--concurrency", type=int, default=5,
                   help="Max concurrent API calls (default: 5)")
    p.add_argument("--models", default=None,
                   help='JSON dict of model overrides, e.g. \'{"stage3": "openai/o3"}\'')
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage2m", "stage3m", "smoke", "scorer"]:
        p.add_argument(f"--{stage.replace('_', '-')}-model", default=None,
                       help=f"Model override for {stage}")
    p.add_argument(
        "--corruption-probs", default=None,
        help="Comma-separated probs for [0, 1, 2, many] corruptions, must sum to 1.0. "
             f"Default: {','.join(str(p) for p in CORRUPTION_PROBS)}"
    )
    return p.parse_args()


def build_config(args: argparse.Namespace) -> dict:
    models = dict(DEFAULT_MODELS)
    if args.models:
        models.update(json.loads(args.models))
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage2m", "stage3m", "smoke", "scorer"]:
        attr = stage.replace("-", "_") + "_model"
        override = getattr(args, attr, None)
        if override:
            models[stage] = override

    corruption_probs = CORRUPTION_PROBS
    if args.corruption_probs:
        parsed = [float(x) for x in args.corruption_probs.split(",")]
        if len(parsed) != 4:
            raise ValueError("--corruption-probs requires exactly 4 values (0, 1, 2, many)")
        if abs(sum(parsed) - 1.0) > 1e-6:
            raise ValueError(f"--corruption-probs must sum to 1.0, got {sum(parsed):.4f}")
        corruption_probs = parsed

    return {
        "batch_size":           args.batch_size,
        "mixed_count":          args.mixed_count,       # NEW v6
        "start_case_id":        args.start_case_id,
        "previous_batch_usage": args.previous_batch_usage,
        "seed":                 args.seed,
        "max_recycles":         args.max_recycles,
        "dry_run":              args.dry_run,
        "no_smoke":             args.no_smoke,
        "resume":               args.resume,
        "concurrency":          args.concurrency,
        "models":               models,
        "corruption_probs":     corruption_probs,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    config = build_config(args)
    rng = random.Random(config["seed"])

    if not config["resume"]:
        for subdir in ["stage2", "stage3", "stage4", "stage5"]:
            d = RUN_DIR / subdir
            if d.exists():
                for f in d.glob("*.json"):
                    f.unlink()

    console.rule("[bold]Pipeline Orchestrator v6[/bold]")
    total = config["batch_size"] + config["mixed_count"]
    start = config["start_case_id"]
    end = start + total - 1
    console.print(f"  Cases     : {config['batch_size']} regular + [magenta]{config['mixed_count']} mixed[/magenta] = {total} total, IDs {start}–{end}")
    console.print(f"  Recycles  : max {config['max_recycles']} per case")
    console.print(f"  Concurrency: {config['concurrency']} workers")
    console.print(f"  Smoke test: {'[dim]OFF[/dim]' if config['no_smoke'] else '[green]ON (regular only)[/green]'}")
    console.print(f"  Seed      : {config['seed']}")
    console.print("  Models:")
    for stage, model in config["models"].items():
        console.print(f"    [dim]{stage:8}[/dim]: {model}")
    console.print()

    client = get_client()

    # Stage 1 — generate all hypotheses (regular + mixed) upfront, concurrent
    hypotheses_path = RUN_DIR / "stage1" / "hypotheses.json"
    if config["resume"] and hypotheses_path.exists():
        console.print("[Stage 1] Resuming — loading existing hypotheses")
        hypotheses: list[dict] = json.loads(hypotheses_path.read_text(encoding="utf-8"))
    else:
        hypotheses = run_stage1_all(config, client)

    # Split: first batch_size hypotheses → regular path; remainder → mixed path
    regular_hypotheses = hypotheses[:config["batch_size"]]
    mixed_hypotheses   = hypotheses[config["batch_size"]:]

    # Sample corruption levels for regular cases
    corruption_levels = [
        sample_corruption_level(rng, config["corruption_probs"])
        for _ in range(len(regular_hypotheses))
    ]
    console.print(f"\n[Corruption plan] {corruption_levels}")
    if mixed_hypotheses:
        console.print(f"[Mixed plan] {len(mixed_hypotheses)} cases → Stage 2M → Stage 3M (no smoke)")

    # -----------------------------------------------------------------------
    # Regular path
    # -----------------------------------------------------------------------
    stages_per_regular = 3 + (1 if not config["no_smoke"] else 0)  # S2 + S3 + S4 [+ S5]

    regular_to_run: list[tuple[str, str, dict, int | str]] = []
    for i, hypothesis in enumerate(regular_hypotheses):
        if hypothesis.get("status") == "failed":
            console.print(f"  [dim]Skipping hyp_{i+1:03d} — Stage 1 failed[/dim]")
            continue
        mechanism_id = f"mech_{i+1:03d}"
        case_id = f"eval_scenario_{config['start_case_id'] + i}"
        case_out = RUN_DIR / "stage4" / f"{mechanism_id}.json"
        if config["resume"] and case_out.exists():
            existing = json.loads(case_out.read_text(encoding="utf-8"))
            if existing.get("verifier_status") == "pending":
                console.print(f"  [dim]{mechanism_id} → already accepted, skipping[/dim]")
                continue
        regular_to_run.append((mechanism_id, case_id, hypothesis, corruption_levels[i]))

    if regular_to_run:
        console.rule("[bold]Regular Cases[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=28),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            batch_task = progress.add_task(
                f"[bold]Regular {start}–{start + config['batch_size'] - 1}[/bold]",
                total=len(regular_hypotheses),
            )
            skipped = len(regular_hypotheses) - len(regular_to_run)
            for _ in range(skipped):
                progress.advance(batch_task)

            def process_regular(args: tuple) -> None:
                mechanism_id, case_id, hypothesis, num_corruptions = args
                case_task = progress.add_task(
                    f"[cyan]{mechanism_id}[/cyan]",
                    total=stages_per_regular,
                )
                try:
                    run_case(
                        mechanism_id, case_id, hypothesis, num_corruptions,
                        config, client,
                        progress=progress,
                        case_task=case_task,
                        stages_per_case=stages_per_regular,
                    )
                except Exception as exc:
                    console.print(f"  [red]FATAL {mechanism_id}: {exc}[/red]")
                finally:
                    progress.update(case_task, visible=False)
                    progress.advance(batch_task)

            with ThreadPoolExecutor(max_workers=config["concurrency"]) as executor:
                list(executor.map(process_regular, regular_to_run))

    # -----------------------------------------------------------------------
    # Mixed path  [NEW v6]
    # -----------------------------------------------------------------------
    if mixed_hypotheses:
        console.rule("[bold]Mixed Cases[/bold]")

        mixed_to_run: list[tuple[str, str, dict]] = []
        for j, hypothesis in enumerate(mixed_hypotheses):
            if hypothesis.get("status") == "failed":
                console.print(f"  [dim]Skipping mixed hyp — Stage 1 failed[/dim]")
                continue
            mechanism_id = f"mech_mx{j+1:03d}"
            case_id = f"eval_scenario_{config['start_case_id'] + config['batch_size'] + j}"
            case_out = RUN_DIR / "stage4" / f"{mechanism_id}.json"
            if config["resume"] and case_out.exists():
                console.print(f"  [dim]{mechanism_id} → already accepted, skipping[/dim]")
                continue
            mixed_to_run.append((mechanism_id, case_id, hypothesis))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=28),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            batch_task = progress.add_task(
                "[bold magenta]Mixed cases[/bold magenta]",
                total=len(mixed_hypotheses),
            )
            skipped = len(mixed_hypotheses) - len(mixed_to_run)
            for _ in range(skipped):
                progress.advance(batch_task)

            def process_mixed(args: tuple) -> None:
                mechanism_id, case_id, hypothesis = args
                case_task = progress.add_task(
                    f"[magenta]{mechanism_id}[/magenta]",
                    total=2,  # S2M + S3M
                )
                try:
                    run_case_mixed(
                        mechanism_id, case_id, hypothesis,
                        config, client,
                        progress=progress,
                        case_task=case_task,
                    )
                except Exception as exc:
                    console.print(f"  [red]FATAL {mechanism_id} (mixed): {exc}[/red]")
                finally:
                    progress.update(case_task, visible=False)
                    progress.advance(batch_task)

            with ThreadPoolExecutor(max_workers=config["concurrency"]) as executor:
                list(executor.map(process_mixed, mixed_to_run))

    assemble_batch(config)


if __name__ == "__main__":
    main()
