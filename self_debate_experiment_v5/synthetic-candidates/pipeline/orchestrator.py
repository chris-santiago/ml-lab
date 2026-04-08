# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
# ]
# ///
"""
Pipeline Orchestrator — Runs all case generation stages via OpenRouter API.

Stages:
  1   Mechanism Extractor  (batch — one LLM call)
  1.5 Fact Mixer           (deterministic Python, no LLM)
  2   Scenario Architect   (per case)
  3   Memo Writer          (per case)
  5   Leakage Auditor      (per case, blind — runs before Stage 4)
  4   Metadata Assembler   (per case — sees audit output)
  6   Smoke Test           (per case — blind eval + separate scorer)

Usage:
    uv run pipeline/orchestrator.py \\
        --extractor-source real_paper \\
        --batch-size 15 \\
        --batch-number 4 \\
        --start-case-id 310

Models are configurable per stage via --stage1-model, --stage5-model, etc.
Default Stage 1 is a non-GPT model to break circular generation bias.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PIPELINE_DIR = Path(__file__).parent
PROMPTS_DIR = PIPELINE_DIR / "prompts"
RUN_DIR = PIPELINE_DIR / "run"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ---------------------------------------------------------------------------
# Default model config
# ---------------------------------------------------------------------------

DEFAULT_MODELS: dict[str, str] = {
    "stage1": "google/gemini-2.5-pro",        # Non-GPT/Claude — breaks circular generation bias
    "stage2": "openai/gpt-5.4-mini",          # Scenario architect — structured output, cost-sensitive
    "stage3": "openai/gpt-5.4",               # Memo writer — critical quality stage; don't cut corners
    "stage4": "openai/gpt-5.4-mini",          # Metadata assembler — structured JSON, mini is sufficient
    "stage5": "anthropic/claude-sonnet-4.6",  # Leakage auditor — must be Claude family
    "smoke":  "anthropic/claude-haiku-4.5",   # Smoke test — backward compat with prior calibration runs
    "scorer": "openai/gpt-5.4-mini",          # Binary score mapper — low-stakes JSON parsing
}

# ---------------------------------------------------------------------------
# Smoke test wrapper prompt (shown to smoke model — no answer key)
# ---------------------------------------------------------------------------

SMOKE_WRAPPER = """\
You are reviewing an ML methodology report. Evaluate the soundness of the \
methodology described below, identify any significant methodological concerns, \
and provide an overall assessment of whether the work supports the stated conclusions.

Return JSON only — no markdown, no code fences:
{
  "issues_found": ["plain English description of each concern you identified"],
  "verdict": "critique | defense | mixed | empirical_test_agreed",
  "justification_challenges": ["justifications in the memo you found to be wrong or insufficient"],
  "reasoning": "1-2 sentence summary of your overall assessment"
}

Report to review:

"""

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def extract_json(text: str) -> str:
    """Strip markdown code fences from LLM response."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


def call_llm(prompt: str, model: str, client: OpenAI, dry_run: bool = False) -> str:
    """Call OpenRouter. Returns raw response text."""
    if dry_run:
        preview = prompt[:200].replace("\n", " ")
        print(f"    [DRY RUN] {model} ← {len(prompt)}ch: {preview}...")
        return '{"dry_run": true}'
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def call_llm_json(
    prompt: str, model: str, client: OpenAI, dry_run: bool = False
) -> dict | list:
    """Call LLM and parse JSON. Retries once with explicit instruction on failure."""
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
    """Replace {{KEY}} placeholders. Raises if any remain after substitution."""
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
# Stage 1 — Mechanism Extractor
# ---------------------------------------------------------------------------

def run_stage1(config: dict, client: OpenAI) -> list[dict]:
    extractor_file = (
        "stage1_mechanism_extractor.md"
        if config["extractor_source"] == "real_paper"
        else "stage1_benchmark_extractor.md"
    )
    template = read_prompt(extractor_file)
    prompt = fill_placeholders(template, {
        "BATCH_SIZE": str(config["batch_size"]),
        "PREVIOUS_BATCH_USAGE": json.dumps(config["previous_batch_usage"]),
    })

    print(f"[Stage 1] {extractor_file} → {config['models']['stage1']}")

    if config["dry_run"]:
        result = [{"mechanism_id": f"mech_{i+1:03d}", "dry_run": True} for i in range(config["batch_size"])]
        print(f"[Stage 1] [DRY RUN] Synthetic {config['batch_size']} blueprints")
    else:
        result = call_llm_json(prompt, config["models"]["stage1"], client, dry_run=False)
        if not isinstance(result, list):
            raise ValueError(f"Stage 1 must return a JSON array, got {type(result).__name__}")

    out = RUN_DIR / "stage1_blueprints.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[Stage 1] {len(result)} blueprints saved → {out}")
    return result


# ---------------------------------------------------------------------------
# Stage 1.5 — Fact Mixer (subprocess)
# ---------------------------------------------------------------------------

def run_fact_mixer(config: dict) -> None:
    input_path = RUN_DIR / "stage1_blueprints.json"
    output_dir = RUN_DIR / "stage1.5"
    cmd = [
        "uv", "run",
        str(PIPELINE_DIR / "fact_mixer.py"),
        "--input", str(input_path),
        "--output-dir", str(output_dir),
        "--seed", str(config["seed"]),
        "--expected-source", config["extractor_source"],
    ]
    print(f"[Stage 1.5] Running fact_mixer.py...")
    if config["dry_run"]:
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"fact_mixer.py exited {result.returncode}")
    print(result.stdout.rstrip())


# ---------------------------------------------------------------------------
# Per-case stages
# ---------------------------------------------------------------------------

def _archive(mechanism_id: str, attempt: int) -> None:
    """Rename current attempt outputs to _attempt_N before recycling."""
    pairs = [
        (RUN_DIR / "stage2" / f"{mechanism_id}_scenario.json", f"{mechanism_id}_attempt_{attempt}_scenario.json"),
        (RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt",       f"{mechanism_id}_attempt_{attempt}_memo.txt"),
        (RUN_DIR / "stage5" / f"{mechanism_id}_audit.json",     f"{mechanism_id}_attempt_{attempt}_audit.json"),
        (RUN_DIR / "stage6" / f"{mechanism_id}_smoke.json",     f"{mechanism_id}_attempt_{attempt}_smoke.json"),
    ]
    for src, dst_name in pairs:
        if src.exists():
            src.rename(src.parent / dst_name)


def run_stage2(mechanism_id: str, config: dict, client: OpenAI, note: str = "") -> dict:
    if config["dry_run"]:
        print(f"    [Stage 2] {mechanism_id} → {config['models']['stage2']} [DRY RUN]")
        return {"dry_run": True}
    writer_view = json.loads(
        (RUN_DIR / "stage1.5" / f"{mechanism_id}_writer_view.json").read_text(encoding="utf-8")
    )
    template = read_prompt("stage2_scenario_architect.md")
    if note:
        template += f"\n\n**Recycling note for this attempt:** {note}"
    prompt = fill_placeholders(template, {
        "TARGET_DOMAIN":         writer_view.get("target_domain", ""),
        "DOMAIN_SPECIFIC_DETAIL": writer_view.get("domain_specific_detail", ""),
        "CATEGORY":              writer_view.get("category", ""),
        "WRITER_VIEW_FACTS":     json.dumps(writer_view.get("facts", []), indent=2),
    })
    print(f"    [Stage 2] {mechanism_id} → {config['models']['stage2']}")
    result = call_llm_json(prompt, config["models"]["stage2"], client, dry_run=False)
    out = RUN_DIR / "stage2" / f"{mechanism_id}_scenario.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_stage3(mechanism_id: str, config: dict, client: OpenAI, note: str = "") -> str:
    if config["dry_run"]:
        print(f"    [Stage 3] {mechanism_id} → {config['models']['stage3']} [DRY RUN]")
        return "[dry_run memo]"
    scenario = json.loads(
        (RUN_DIR / "stage2" / f"{mechanism_id}_scenario.json").read_text(encoding="utf-8")
    )
    template = read_prompt("stage3_memo_writer.md")
    if note:
        template += f"\n\n**Recycling note for this attempt:** {note}"
    prompt = fill_placeholders(template, {
        "SCENARIO_BRIEF": json.dumps(scenario, indent=2),
    })
    print(f"    [Stage 3] {mechanism_id} → {config['models']['stage3']}")
    memo = call_llm(prompt, config["models"]["stage3"], client, dry_run=False)
    out = RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(memo, encoding="utf-8")
    return memo


def run_stage5(mechanism_id: str, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        print(f"    [Stage 5] {mechanism_id} → {config['models']['stage5']} (leakage audit) [DRY RUN]")
        return {"overall_leakage_score": 0.0, "voice_assessment": "team_advocacy", "dry_run": True}
    memo = (RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt").read_text(encoding="utf-8")
    template = read_prompt("stage5_leakage_auditor.md")
    prompt = fill_placeholders(template, {"TASK_PROMPT": memo})
    print(f"    [Stage 5] {mechanism_id} → {config['models']['stage5']} (leakage audit)")
    result = call_llm_json(prompt, config["models"]["stage5"], client, dry_run=False)
    out = RUN_DIR / "stage5" / f"{mechanism_id}_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    leakage = result.get("overall_leakage_score", "?")
    voice = result.get("voice_assessment", "?")
    print(f"    [Stage 5] leakage={leakage} voice={voice}")
    return result


def run_stage4(mechanism_id: str, case_id: str, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        print(f"    [Stage 4] {mechanism_id} → {config['models']['stage4']} (metadata assembly) [DRY RUN]")
        return {"case_id": case_id, "verifier_status": "pending", "dry_run": True}
    metadata_view = json.loads(
        (RUN_DIR / "stage1.5" / f"{mechanism_id}_metadata_view.json").read_text(encoding="utf-8")
    )
    audit = json.loads(
        (RUN_DIR / "stage5" / f"{mechanism_id}_audit.json").read_text(encoding="utf-8")
    )
    memo = (RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt").read_text(encoding="utf-8")
    template = read_prompt("stage4_metadata_assembler.md")
    prompt = fill_placeholders(template, {
        "MECHANISM_BLUEPRINT": json.dumps(metadata_view, indent=2),
        "METADATA_VIEW":       json.dumps(metadata_view, indent=2),
        "LEAKAGE_AUDIT":       json.dumps(audit, indent=2),
        "TASK_PROMPT":         memo,
        "CASE_ID":             case_id,
    })
    print(f"    [Stage 4] {mechanism_id} → {config['models']['stage4']} (metadata assembly)")
    result = call_llm_json(prompt, config["models"]["stage4"], client, dry_run=False)
    out = RUN_DIR / "cases" / f"{mechanism_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Stage 6 — Smoke Test (two calls: blind eval + scorer)
# ---------------------------------------------------------------------------

def run_smoke_test(mechanism_id: str, case: dict, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        print(f"    [Stage 6] {mechanism_id} → {config['models']['smoke']} (blind eval) [DRY RUN]")
        print(f"    [Stage 6] {mechanism_id} → {config['models']['scorer']} (scoring) [DRY RUN]")
        return {"mechanism_id": mechanism_id, "proxy_mean": 0.0, "gate_pass": True, "dry_run": True}
    task_prompt = case.get("task_prompt", "")
    scoring_targets = case.get("scoring_targets", {})
    planted_issues = case.get("planted_issues", [])
    must_find_ids = scoring_targets.get("must_find_issue_ids", [])
    acceptable = scoring_targets.get("acceptable_resolutions", [])

    # Call 1: blind evaluation (no answer key)
    print(f"    [Stage 6] {mechanism_id} → {config['models']['smoke']} (blind eval)")
    smoke_raw = call_llm(SMOKE_WRAPPER + task_prompt, config["models"]["smoke"], client, config["dry_run"])
    try:
        smoke_resp = json.loads(extract_json(smoke_raw))
    except json.JSONDecodeError:
        smoke_resp = {
            "issues_found": [],
            "verdict": "unclear",
            "justification_challenges": [],
            "reasoning": smoke_raw[:300],
        }

    # Call 2: score against answer key
    must_find_desc = {
        pi["issue_id"]: pi.get("description", "")
        for pi in planted_issues
        if pi.get("issue_id") in must_find_ids
    }
    abi_desc = {
        pi["issue_id"]: pi.get("description", "")
        for pi in planted_issues
        if pi.get("addressed_but_incorrectly") and pi.get("issue_id") in must_find_ids
    }

    score_prompt = f"""\
You are a scoring assistant. An AI model reviewed an ML methodology report and produced the
assessment below. Determine which 'must-find' issues were identified and whether any
'must-not-claim' concerns were incorrectly raised as primary issues.

Must-find issues (ID → description):
{json.dumps(must_find_desc, indent=2)}

Must-not-claim concerns (should NOT be raised as primary concerns):
{json.dumps(scoring_targets.get('must_not_claim', []), indent=2)}

Addressed-but-incorrectly issues (for IDJ — was the justification challenged?):
{json.dumps(abi_desc, indent=2)}

Acceptable verdicts: {json.dumps(acceptable)}

AI model assessment:
{json.dumps(smoke_resp, indent=2)}

Return JSON only:
{{
  "must_find_found": ["issue_ids clearly identified in the assessment"],
  "must_not_claim_raised": ["must_not_claim concerns incorrectly raised as primary issues"],
  "abi_challenged": ["issue_ids where the stated justification was challenged as wrong/insufficient"],
  "verdict_given": "critique | defense | mixed | empirical_test_agreed | unclear"
}}"""

    print(f"    [Stage 6] {mechanism_id} → {config['models']['scorer']} (scoring)")
    try:
        scored = call_llm_json(score_prompt, config["models"]["scorer"], client, config["dry_run"])
    except ValueError:
        scored = {"must_find_found": [], "must_not_claim_raised": [], "abi_challenged": [], "verdict_given": "unclear"}

    # Compute binary proxy scores
    found_ids: list = scored.get("must_find_found", [])
    idr: float | None = (
        None if not must_find_ids
        else (1.0 if all(i in found_ids for i in must_find_ids) else 0.0)
    )

    raised_bad: list = scored.get("must_not_claim_raised", [])
    idp: float = 0.0 if raised_bad else 1.0

    verdict: str = scored.get("verdict_given", "unclear")
    fvc: float = 1.0 if verdict in acceptable else 0.0

    idj: float | None = None
    if abi_desc:
        challenged: list = scored.get("abi_challenged", [])
        idj = 1.0 if all(i in challenged for i in abi_desc) else 0.0

    applicable = [s for s in [idr, idp, fvc, idj] if s is not None]
    proxy_mean = round(sum(applicable) / len(applicable), 4) if applicable else 1.0

    result = {
        "mechanism_id": mechanism_id,
        "smoke_response": smoke_resp,
        "scores": {"IDR": idr, "IDP": idp, "FVC": fvc, "IDJ": idj},
        "proxy_mean": proxy_mean,
        "gate_pass": proxy_mean < 0.55,
    }
    out = RUN_DIR / "stage6" / f"{mechanism_id}_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    status = "PASS" if result["gate_pass"] else "FAIL"
    print(f"    [Stage 6] proxy_mean={proxy_mean:.3f} IDR={idr} IDP={idp} FVC={fvc} IDJ={idj} [{status}]")
    return result


# ---------------------------------------------------------------------------
# Recycling decision
# ---------------------------------------------------------------------------

def recycle_action(audit: dict, smoke: dict | None) -> tuple[str | None, str, str]:
    """
    Returns (stage_to_restart_from, failure_reason, note) or (None, '', '') if accepted.

    Routing priority:
      voice issue    → Stage 3 (rewrite memo)
      leakage issue  → Stage 2 (new scenario)
      smoke IDR=1.0  → Stage 2 (deeper mechanism — Stage 1 recycle is too expensive for v1)
      smoke FVC bad  → Stage 2 (restructure decoys)
      smoke general  → Stage 2 (general rework)
    """
    voice = audit.get("voice_assessment", "team_advocacy")
    leakage = float(audit.get("overall_leakage_score", 0.0))

    if voice != "team_advocacy":
        return (
            "stage3",
            "voice",
            "Rewrite entirely in first-person team voice throughout. "
            "Remove all instances of 'the team', 'the model', 'the document', "
            "and any third-person or reviewer framing.",
        )

    if leakage > 0.4:
        return (
            "stage2",
            "leakage",
            f"Leakage score={leakage:.2f} (threshold 0.4). "
            "Design a new scenario where the flaw mechanism is embedded at least 2 layers deep "
            "in field-specific terminology. The flaw should only be recognisable to someone with "
            "domain expertise, not general ML pattern recognition.",
        )

    if smoke and not smoke.get("gate_pass", True):
        scores = smoke.get("scores", {})
        idr = scores.get("IDR")
        fvc = scores.get("FVC")

        if idr == 1.0:
            return (
                "stage2",
                "difficulty_idr",
                f"Smoke test IDR=1.0 (proxy_mean={smoke.get('proxy_mean', '?')}): all must-find issues "
                "identified in a single pass. Redesign the scenario so the flaw requires domain-specific "
                "knowledge to detect. Consider wrapping the mechanism in a regulatory or field-specific "
                "context where the flaw is only recognisable with specialist knowledge.",
            )
        if fvc == 1.0 and idr == 0.0:
            return (
                "stage2",
                "difficulty_fvc",
                f"Smoke test FVC=1.0 but IDR=0 (proxy_mean={smoke.get('proxy_mean', '?')}): "
                "evaluator reached the correct verdict without finding the specific flaw. "
                "Restructure so the decoy concern dominates the first two paragraphs "
                "and the real flaw is buried in technical detail.",
            )
        return (
            "stage2",
            "difficulty_general",
            f"Smoke test proxy_mean={smoke.get('proxy_mean', '?')} ≥ 0.55. "
            "Redesign the scenario for harder misdirection — stronger decoy prominence, "
            "more domain-specific flaw embedding.",
        )

    return (None, "", "")


# ---------------------------------------------------------------------------
# Full per-case pipeline
# ---------------------------------------------------------------------------

def run_case(
    mechanism_id: str, case_id: str, config: dict, client: OpenAI
) -> dict | None:
    """Run Stages 2→3→5→4→[6] for one case, with auto-recycling."""
    max_recycles = config["max_recycles"]
    note_s2 = ""
    note_s3 = ""

    for attempt in range(max_recycles + 1):
        if attempt > 0:
            print(f"\n  [{mechanism_id}] ── Recycle attempt {attempt}/{max_recycles}")

        try:
            run_stage2(mechanism_id, config, client, note=note_s2)
            run_stage3(mechanism_id, config, client, note=note_s3)
            audit = run_stage5(mechanism_id, config, client)
            case = run_stage4(mechanism_id, case_id, config, client)

            smoke = None
            if not config["no_smoke"]:
                smoke = run_smoke_test(mechanism_id, case, config, client)

            stage, reason, note = recycle_action(audit, smoke)

            if stage is None:
                print(f"  [{mechanism_id}] ✓ ACCEPTED (attempt {attempt})")
                return case

            if attempt >= max_recycles:
                print(f"  [{mechanism_id}] ✗ EXHAUSTED ({max_recycles} recycles, last reason: {reason})")
                case["verifier_status"] = "exhausted"
                case["recycle_failure_reason"] = reason
                (RUN_DIR / "cases" / f"{mechanism_id}.json").write_text(
                    json.dumps(case, indent=2), encoding="utf-8"
                )
                return case

            print(f"  [{mechanism_id}] → recycle to {stage} (reason: {reason})")
            _archive(mechanism_id, attempt)

            # Set notes for next attempt
            if stage == "stage3":
                note_s3 = note
            else:
                note_s2 = note
                note_s3 = ""  # fresh stage 3 after new scenario

        except Exception as exc:
            print(f"  [{mechanism_id}] ERROR: {exc}", file=sys.stderr)
            if attempt >= max_recycles:
                return None

    return None


# ---------------------------------------------------------------------------
# Batch assembly
# ---------------------------------------------------------------------------

def assemble_batch(config: dict) -> None:
    if config["dry_run"]:
        print(f"\n[DRY RUN] Would assemble cases_batch{config['batch_number']}.json from pipeline/run/cases/")
        return
    cases_dir = RUN_DIR / "cases"
    accepted = []
    recycled = []
    exhausted = []

    for f in sorted(cases_dir.glob("*.json")):
        if "_attempt_" in f.name:
            continue
        case = json.loads(f.read_text(encoding="utf-8"))
        status = case.get("verifier_status", "pending")
        if status == "pending":
            accepted.append(case)
        elif status == "exhausted":
            exhausted.append(case)
        else:
            recycled.append(case)

    out_path = PIPELINE_DIR.parent / f"cases_batch{config['batch_number']}.json"
    out_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")

    total = len(accepted) + len(recycled) + len(exhausted)
    print(f"\n{'='*60}")
    print(f"BATCH {config['batch_number']} SUMMARY")
    print(f"{'='*60}")
    print(f"  Total processed : {total}")
    print(f"  Accepted        : {len(accepted)}")
    print(f"  Recycle-flagged : {len(recycled)}")
    print(f"  Exhausted       : {len(exhausted)}")
    print(f"  Output          : {out_path}")

    if exhausted:
        print("\n  Exhausted cases:")
        for c in exhausted:
            print(f"    {c.get('case_id', '?')} — {c.get('recycle_failure_reason', 'unknown')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline Orchestrator — all stages via OpenRouter")
    p.add_argument("--extractor-source", required=True, choices=["real_paper", "benchmark"],
                   help="Which Stage 1 extractor to use")
    p.add_argument("--batch-size", type=int, required=True,
                   help="Number of cases to generate")
    p.add_argument("--batch-number", type=int, required=True,
                   help="Sequential batch number (used in output filename)")
    p.add_argument("--start-case-id", type=int, required=True,
                   help="First eval_scenario_NNN number (e.g. 310 for batch following 301-309)")
    p.add_argument("--previous-batch-usage", default="{}",
                   help="JSON of sources/domains used in prior batches")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-recycles", type=int, default=2,
                   help="Max auto-recycle attempts per case (default: 2)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print prompts without making API calls")
    p.add_argument("--no-smoke", action="store_true",
                   help="Skip Stage 6 smoke test")
    p.add_argument("--resume", action="store_true",
                   help="Skip cases that already have a completed Stage 4 output")
    p.add_argument("--models", default=None,
                   help='JSON dict of model overrides, e.g. \'{"stage1": "x-ai/grok-4"}\'')
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5", "smoke", "scorer"]:
        p.add_argument(f"--{stage}-model", default=None,
                       help=f"Model override for {stage} (takes precedence over --models)")
    return p.parse_args()


def build_config(args: argparse.Namespace) -> dict:
    models = dict(DEFAULT_MODELS)
    if args.models:
        models.update(json.loads(args.models))
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5", "smoke", "scorer"]:
        override = getattr(args, f"{stage}_model", None)
        if override:
            models[stage] = override

    return {
        "extractor_source": args.extractor_source,
        "batch_size": args.batch_size,
        "batch_number": args.batch_number,
        "start_case_id": args.start_case_id,
        "previous_batch_usage": json.loads(args.previous_batch_usage),
        "seed": args.seed,
        "max_recycles": args.max_recycles,
        "dry_run": args.dry_run,
        "no_smoke": args.no_smoke,
        "resume": args.resume,
        "models": models,
    }


def main() -> None:
    args = parse_args()
    config = build_config(args)

    print("\nPipeline Orchestrator")
    print(f"  Extractor : {config['extractor_source']}")
    print(f"  Batch     : {config['batch_number']}  ({config['batch_size']} cases, IDs {config['start_case_id']}–{config['start_case_id'] + config['batch_size'] - 1})")
    print(f"  Recycles  : max {config['max_recycles']} per case")
    print(f"  Smoke test: {'OFF (--no-smoke)' if config['no_smoke'] else 'ON'}")
    print(f"  Models:")
    for stage, model in config["models"].items():
        print(f"    {stage:8}: {model}")
    print()

    client = get_client()

    # Stage 1
    stage1_out = RUN_DIR / "stage1_blueprints.json"
    if config["resume"] and stage1_out.exists():
        print("[Stage 1] Resuming — loading existing blueprints")
        blueprints: list[dict] = json.loads(stage1_out.read_text(encoding="utf-8"))
    else:
        blueprints = run_stage1(config, client)

    # Stage 1.5
    run_fact_mixer(config)

    # Per-case stages
    for i, blueprint in enumerate(blueprints):
        mechanism_id = blueprint.get("mechanism_id", f"mech_{i+1:03d}")
        case_id = f"eval_scenario_{config['start_case_id'] + i}"

        # Resume: skip if Stage 4 output already exists and is not exhausted
        case_out = RUN_DIR / "cases" / f"{mechanism_id}.json"
        if config["resume"] and case_out.exists():
            existing = json.loads(case_out.read_text(encoding="utf-8"))
            if existing.get("verifier_status") == "pending":
                print(f"\n[{mechanism_id}] Resuming — already accepted, skipping")
                continue

        print(f"\n[{mechanism_id}] → {case_id}")
        run_case(mechanism_id, case_id, config, client)

    # Assemble
    assemble_batch(config)


if __name__ == "__main__":
    main()
