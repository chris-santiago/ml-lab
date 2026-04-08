# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
Pipeline Orchestrator — Runs all case generation stages via OpenRouter API.

Stages:
  1   Mechanism Extractor  (one LLM call per source, concurrent ≤5)
  1.5 Fact Mixer           (deterministic Python, no LLM)
  2   Scenario Architect   (per case, concurrent ≤5 across cases)
  3   Memo Writer          (per case, concurrent ≤5 across cases)
  5   Leakage Auditor      (per case, blind — runs before Stage 4)
  4   Metadata Assembler   (per case — sees audit output)
  6   Smoke Test           (per case — blind eval + separate scorer)

Usage:
    uv run pipeline/orchestrator.py \\
        --extractor-source real_paper \\
        --batch-size 15 \\
        --start-case-id 313

Models are configurable per stage via --stage1-model, --stage5-model, etc.
Code (not prompts) controls iteration. Python loop + ThreadPoolExecutor(max_workers=5).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
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
MAX_WORKERS = 5       # concurrent API calls per stage
API_TIMEOUT = 180.0   # seconds per request before raising TimeoutError

# Serializes Stage 1 recycles: fact_mixer writes to shared files so concurrent
# Stage 1 recycles must not overlap (two cases both firing difficulty_idr).
_STAGE1_RECYCLE_LOCK = threading.Lock()

# Source catalog lives alongside this script
sys.path.insert(0, str(PIPELINE_DIR))
from source_catalog import (  # noqa: E402
    select_sources,
    select_benchmark_assignments,
    CRITIQUE_SOURCES,
    DEFENSE_PATTERNS,
)

# ---------------------------------------------------------------------------
# Default model config
# ---------------------------------------------------------------------------

DEFAULT_MODELS: dict[str, str] = {
    "stage1": "openai/gpt-5.4",                      # Mechanism extractor — GPT-5.4; rich schema compliance, deep mechanism extraction
    "stage2": "qwen/qwen3-235b-a22b-2507",           # Scenario architect — Qwen3; structured output, cost-effective
    "stage3": "deepseek/deepseek-v3.2",              # Memo writer — DeepSeek; less perceptive about flaw salience → lower IDR leakage
    "stage4": "qwen/qwen3-235b-a22b-2507",           # Metadata assembler — Qwen3; structured JSON, cost-effective
    "stage5": "anthropic/claude-sonnet-4.6",         # Leakage auditor — Claude; must match debate agent family
    "smoke":  "anthropic/claude-haiku-4.5",          # Smoke test — Claude; backward compat with prior calibration runs
    "scorer": "openai/gpt-5.4-mini",                 # Binary score mapper — low-stakes JSON parsing
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
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=API_TIMEOUT)


def extract_json(text: str) -> str:
    """Strip markdown code fences from LLM response."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


def call_llm(prompt: str, model: str, client: OpenAI, dry_run: bool = False) -> str:
    """Call OpenRouter. Returns raw response text. Retries on rate-limit with backoff."""
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
    out = RUN_DIR / "stage1_blueprints.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    if config["dry_run"]:
        result = [{"mechanism_id": f"mech_{i+1:03d}", "dry_run": True} for i in range(config["batch_size"])]
        console.print(f"[Stage 1] [DRY RUN] Synthetic {config['batch_size']} blueprints")
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    if config["extractor_source"] == "benchmark":
        assignments_bm = select_benchmark_assignments(
            batch_size=config["batch_size"],
            previous_usage=config["previous_batch_usage"],
            seed=config["seed"],
        )
        template_bm = read_prompt("stage1_benchmark_extractor.md")

        console.print(
            f"[Stage 1] {len(assignments_bm)} benchmark slots → "
            f"{config['models']['stage1']} (concurrent ≤{MAX_WORKERS})"
        )
        for a in assignments_bm:
            ft_label = a["flaw_type"] or "null"
            console.print(
                f"  {a['mechanism_id']}  [{a['case_type']:12}]  {a['category']}  ({ft_label})"
            )

        def generate_benchmark(assignment: dict) -> dict:
            mechanism_id = assignment["mechanism_id"]
            prompt = fill_placeholders(template_bm, {
                "CATEGORY":             assignment["category"],
                "CASE_TYPE":            assignment["case_type"],
                "FLAW_TYPE":            assignment["flaw_type"] or "null",
                "MECHANISM_ID":         mechanism_id,
                "PREVIOUS_BATCH_USAGE": json.dumps(config["previous_batch_usage"]),
            })
            raw = call_llm_json(prompt, config["models"]["stage1"], client, dry_run=False)
            if isinstance(raw, list):
                raw = raw[0] if raw else {}
            if not isinstance(raw, dict):
                raise ValueError(
                    f"Stage 1 {mechanism_id}: expected JSON object, got {type(raw).__name__}"
                )
            raw["mechanism_id"] = mechanism_id
            raw.setdefault("pipeline_source", "benchmark")
            console.print(
                f"  [green]✓[/green] {mechanism_id} "
                f"({assignment['category']} / {assignment['flaw_type'] or 'defense_wins'})"
            )
            return raw

        bm_blueprints: list[dict | None] = [None] * len(assignments_bm)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(generate_benchmark, a): i
                for i, a in enumerate(assignments_bm)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    bm_blueprints[idx] = future.result()
                except Exception as exc:
                    mech_id = assignments_bm[idx]["mechanism_id"]
                    console.print(f"  [red]✗ {mech_id} FAILED: {exc}[/red]")
                    bm_blueprints[idx] = {
                        "mechanism_id": mech_id,
                        "pipeline_source": "benchmark",
                        "error": str(exc),
                        "status": "failed",
                    }

        result = [bp for bp in bm_blueprints if bp is not None]
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        n_ok = sum(1 for bp in result if "error" not in bp)
        console.print(f"[Stage 1] {n_ok}/{len(result)} blueprints OK → {out}")
        return result

    elif config["extractor_source"] != "real_paper":
        raise NotImplementedError(f"Unknown extractor_source: {config['extractor_source']}")

    # Select sources: code assigns which source each call uses
    assignments = select_sources(
        batch_size=config["batch_size"],
        previous_usage=config["previous_batch_usage"],
        seed=config["seed"],
    )
    template = read_prompt("stage1_mechanism_extractor.md")

    console.print(
        f"[Stage 1] {len(assignments)} sources selected → "
        f"{config['models']['stage1']} (concurrent ≤{MAX_WORKERS})"
    )
    for a in assignments:
        console.print(
            f"  {a['mechanism_id']}  [{a['case_type']:12}]  {a['source']['label']}"
        )

    def generate_one(assignment: dict) -> dict:
        mechanism_id = assignment["mechanism_id"]
        prompt = fill_placeholders(template, {
            "SOURCE_REFERENCE":    assignment["source"]["text"],
            "CASE_TYPE":           assignment["case_type"],
            "MECHANISM_ID":        mechanism_id,
            "PREVIOUS_BATCH_USAGE": json.dumps(config["previous_batch_usage"]),
        })
        raw = call_llm_json(prompt, config["models"]["stage1"], client, dry_run=False)
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        if not isinstance(raw, dict):
            raise ValueError(f"Stage 1 {mechanism_id}: expected JSON object, got {type(raw).__name__}")
        raw["mechanism_id"] = mechanism_id
        raw.setdefault("pipeline_source", config["extractor_source"])
        console.print(f"  [green]✓[/green] {mechanism_id} ({assignment['source']['label'][:50]})")
        return raw

    blueprints: list[dict | None] = [None] * len(assignments)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {executor.submit(generate_one, a): i for i, a in enumerate(assignments)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                blueprints[idx] = future.result()
            except Exception as exc:
                mech_id = assignments[idx]["mechanism_id"]
                console.print(f"  [red]✗ {mech_id} FAILED: {exc}[/red]")
                blueprints[idx] = {
                    "mechanism_id": mech_id,
                    "pipeline_source": config["extractor_source"],
                    "error": str(exc),
                    "status": "failed",
                }

    result = [bp for bp in blueprints if bp is not None]
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    n_ok = sum(1 for bp in result if "error" not in bp)
    console.print(f"[Stage 1] {n_ok}/{len(result)} blueprints OK → {out}")
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
    console.print("[Stage 1.5] Running fact_mixer.py...")
    if config["dry_run"]:
        console.print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(result.stderr, style="red")
        raise RuntimeError(f"fact_mixer.py exited {result.returncode}")
    console.print(result.stdout.rstrip())


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
        console.print(f"  S2 {mechanism_id} → {config['models']['stage2']} [dim](dry run)[/dim]")
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
    result = call_llm_json(prompt, config["models"]["stage2"], client, dry_run=False)
    out = RUN_DIR / "stage2" / f"{mechanism_id}_scenario.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_stage3(mechanism_id: str, config: dict, client: OpenAI, note: str = "") -> str:
    if config["dry_run"]:
        console.print(f"  S3 {mechanism_id} → {config['models']['stage3']} [dim](dry run)[/dim]")
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
    memo = call_llm(prompt, config["models"]["stage3"], client, dry_run=False)
    out = RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(memo, encoding="utf-8")
    return memo


def run_stage5(mechanism_id: str, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        console.print(f"  S5 {mechanism_id} → {config['models']['stage5']} [dim](dry run)[/dim]")
        return {"overall_leakage_score": 0.0, "voice_assessment": "team_advocacy", "dry_run": True}
    memo = (RUN_DIR / "stage3" / f"{mechanism_id}_memo.txt").read_text(encoding="utf-8")
    template = read_prompt("stage5_leakage_auditor.md")
    prompt = fill_placeholders(template, {"TASK_PROMPT": memo})
    result = call_llm_json(prompt, config["models"]["stage5"], client, dry_run=False)
    out = RUN_DIR / "stage5" / f"{mechanism_id}_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    leakage = result.get("overall_leakage_score", "?")
    voice = result.get("voice_assessment", "?")
    console.print(f"  S5 {mechanism_id} leakage={leakage} voice={voice}")
    return result


def run_stage4(mechanism_id: str, case_id: str, config: dict, client: OpenAI) -> dict:
    if config["dry_run"]:
        console.print(f"  S4 {mechanism_id} → {config['models']['stage4']} [dim](dry run)[/dim]")
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
        console.print(f"  S6 {mechanism_id} → {config['models']['smoke']} / {config['models']['scorer']} [dim](dry run)[/dim]")
        return {"mechanism_id": mechanism_id, "proxy_mean": 0.0, "gate_pass": True, "dry_run": True}
    task_prompt = case.get("task_prompt", "")
    scoring_targets = case.get("scoring_targets", {})
    planted_issues = case.get("planted_issues", [])
    must_find_ids = scoring_targets.get("must_find_issue_ids", [])
    acceptable = scoring_targets.get("acceptable_resolutions", [])

    # Call 1: blind evaluation (no answer key)
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

    console.print(f"  S6 {mechanism_id} → scorer")
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

    gate_color = "green" if result["gate_pass"] else "red"
    status = "PASS" if result["gate_pass"] else "FAIL"
    console.print(f"  S6 {mechanism_id} proxy={proxy_mean:.3f} IDR={idr} IDP={idp} FVC={fvc} IDJ={idj} [{gate_color}]{status}[/{gate_color}]")
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
      smoke IDR=1.0  → Stage 1 (mechanism itself is too recognizable; new domain transposition)
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
                "stage1",
                "difficulty_idr",
                f"Smoke test IDR=1.0 (proxy_mean={smoke.get('proxy_mean', '?')}): all must-find issues "
                "identified in a single pass. The abstract mechanism is too recognizable through general "
                "ML pattern-matching. Re-generate with a completely different target domain — the flaw "
                "should only be detectable by someone with domain-specific expertise (regulatory standard, "
                "field-specific measurement convention, or operational constraint), not general ML knowledge.",
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
# Stage 1 single-mechanism recycle
# ---------------------------------------------------------------------------

def run_stage1_recycle(
    mechanism_id: str,
    config: dict,
    client: OpenAI,
    note: str = "",
) -> None:
    """
    Re-generate the Stage 1 blueprint for one mechanism, then re-run fact_mixer.

    Serialized via _STAGE1_RECYCLE_LOCK: fact_mixer writes to shared stage1.5 files
    so concurrent Stage 1 recycles (two cases both firing difficulty_idr) must not overlap.

    Used when IDR=1.0 persists — the abstract mechanism is too recognizable, not just
    the scenario framing. Picks the same source, forces a completely different domain.
    """
    with _STAGE1_RECYCLE_LOCK:
        blueprints_path = RUN_DIR / "stage1_blueprints.json"
        blueprints: list[dict] = json.loads(blueprints_path.read_text(encoding="utf-8"))

        current = next((bp for bp in blueprints if bp.get("mechanism_id") == mechanism_id), None)
        if current is None:
            raise RuntimeError(f"run_stage1_recycle: {mechanism_id} not found in stage1_blueprints.json")

        # Look up original source from catalog
        source_ref = current.get("source_reference", "")
        all_sources = CRITIQUE_SOURCES + DEFENSE_PATTERNS
        source_entry = next((s for s in all_sources if s["label"] == source_ref), None)

        if source_entry is None:
            raise RuntimeError(
                f"run_stage1_recycle: cannot find source '{source_ref}' in catalog — "
                "cannot re-run Stage 1 without the source text"
            )

        console.print(f"  S1↻ {mechanism_id} → {config['models']['stage1']} (Stage 1 recycle)")

        operator_note = (
            f"RECYCLE (IDR=1.0 after prior attempt): {note}\n\n"
            "The previous domain transposition was too shallow — the mechanism remained "
            "identifiable through general ML pattern-matching alone. Choose a completely "
            "different target domain. The flaw must require domain-specific expertise to "
            "detect, not general ML knowledge. Vocabulary, regulatory context, and "
            "operational stakes must all be domain-specific enough to prevent pattern-matching."
        )

        template = read_prompt("stage1_mechanism_extractor.md")
        prompt = fill_placeholders(template, {
            "SOURCE_REFERENCE":     source_entry["text"] + f"\n\n**Operator note:** {operator_note}",
            "CASE_TYPE":            current.get("case_type", "critique"),
            "MECHANISM_ID":         mechanism_id,
            "PREVIOUS_BATCH_USAGE": json.dumps(config["previous_batch_usage"]),
        })

        raw = call_llm_json(prompt, config["models"]["stage1"], client, dry_run=config.get("dry_run", False))
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        raw["mechanism_id"] = mechanism_id
        raw.setdefault("pipeline_source", config["extractor_source"])

        # Update stage1_blueprints.json in-place
        for i, bp in enumerate(blueprints):
            if bp.get("mechanism_id") == mechanism_id:
                blueprints[i] = raw
                break
        blueprints_path.write_text(json.dumps(blueprints, indent=2), encoding="utf-8")

        console.print(f"  S1↻ {mechanism_id} blueprint updated → re-running fact_mixer")
        run_fact_mixer(config)


# ---------------------------------------------------------------------------
# Full per-case pipeline
# ---------------------------------------------------------------------------

def run_case(
    mechanism_id: str,
    case_id: str,
    config: dict,
    client: OpenAI,
    *,
    progress: Progress | None = None,
    case_task: TaskID | None = None,
    stages_per_case: int = 6,
) -> dict | None:
    """Run Stages 2→3→5→4→[6] for one case, with auto-recycling."""
    max_recycles = config["max_recycles"]
    note_s1 = ""
    note_s2 = ""
    note_s3 = ""
    next_recycle_stage = "stage2"  # default; updated after each attempt

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

            if next_recycle_stage == "stage1":
                run_stage1_recycle(mechanism_id, config, client, note=note_s1)
                note_s2 = ""  # fresh blueprint — clear any prior stage2 note

        try:
            _step("S2 scenario architect")
            run_stage2(mechanism_id, config, client, note=note_s2)
            _advance()

            _step("S3 memo writer")
            run_stage3(mechanism_id, config, client, note=note_s3)
            _advance()

            _step("S5 leakage audit")
            audit = run_stage5(mechanism_id, config, client)
            _advance()

            _step("S4 metadata assembly")
            case = run_stage4(mechanism_id, case_id, config, client)
            _advance()

            smoke = None
            if not config["no_smoke"]:
                _step("S6 smoke eval")
                smoke = run_smoke_test(mechanism_id, case, config, client)
                _advance()
                _advance()  # smoke counts as 2 steps (eval + scorer call inside)

            stage, reason, note = recycle_action(audit, smoke)

            if stage is None:
                console.print(f"  [green]✓ {mechanism_id} ACCEPTED[/green] (attempt {attempt})")
                return case

            if attempt >= max_recycles:
                console.print(f"  [red]✗ {mechanism_id} EXHAUSTED[/red] ({max_recycles} recycles, reason: {reason})")
                case["verifier_status"] = "exhausted"
                case["recycle_failure_reason"] = reason
                (RUN_DIR / "cases" / f"{mechanism_id}.json").write_text(
                    json.dumps(case, indent=2), encoding="utf-8"
                )
                return case

            console.print(f"  [yellow]→ {mechanism_id} recycle → {stage}[/yellow] ({reason})")
            _archive(mechanism_id, attempt)

            next_recycle_stage = stage
            if stage == "stage1":
                note_s1 = note
                note_s2 = ""
                note_s3 = ""
            elif stage == "stage3":
                note_s3 = note
            else:
                note_s2 = note
                note_s3 = ""

        except Exception as exc:
            console.print(f"  [red]ERROR {mechanism_id}: {exc}[/red]")
            if attempt >= max_recycles:
                return None

    return None


# ---------------------------------------------------------------------------
# Batch assembly
# ---------------------------------------------------------------------------

def assemble_batch(config: dict) -> None:
    start = config["start_case_id"]
    end = start + config["batch_size"] - 1
    out_name = f"cases_{start}-{end}.json"
    if config["dry_run"]:
        console.print(f"\n[dim][DRY RUN] Would assemble {out_name} from pipeline/run/cases/[/dim]")
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

    out_path = PIPELINE_DIR.parent / out_name
    out_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")

    total = len(accepted) + len(recycled) + len(exhausted)
    console.rule(f"[bold]Cases {start}–{end} Summary[/bold]")
    console.print(f"  Total processed : {total}")
    console.print(f"  [green]Accepted        : {len(accepted)}[/green]")
    if recycled:
        console.print(f"  [yellow]Recycle-flagged : {len(recycled)}[/yellow]")
    if exhausted:
        console.print(f"  [red]Exhausted       : {len(exhausted)}[/red]")
    console.print(f"  Output          : {out_path}")

    if exhausted:
        console.print("\n  Exhausted cases:")
        for c in exhausted:
            console.print(f"    [red]{c.get('case_id', '?')}[/red] — {c.get('recycle_failure_reason', 'unknown')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline Orchestrator — all stages via OpenRouter")
    p.add_argument("--extractor-source", required=True, choices=["real_paper", "benchmark"],
                   help="Which Stage 1 extractor to use")
    p.add_argument("--batch-size", type=int, required=True,
                   help="Number of cases to generate")
    p.add_argument("--start-case-id", type=int, required=True,
                   help="First eval_scenario_NNN number (e.g. 310 for batch following 301-309). Output file is named cases_NNN-MMM.json.")
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

    console.rule("[bold]Pipeline Orchestrator[/bold]")
    start = config["start_case_id"]
    end = start + config["batch_size"] - 1
    console.print(f"  Extractor : {config['extractor_source']}")
    console.print(f"  Cases     : {config['batch_size']} cases, IDs {start}–{end}  →  cases_{start}-{end}.json")
    console.print(f"  Recycles  : max {config['max_recycles']} per case")
    console.print(f"  Smoke test: {'[dim]OFF (--no-smoke)[/dim]' if config['no_smoke'] else '[green]ON[/green]'}")
    console.print("  Models:")
    for stage, model in config["models"].items():
        console.print(f"    [dim]{stage:8}[/dim]: {model}")
    console.print()

    client = get_client()

    # Stage 1 — runs outside progress context (batch-level, one call)
    stage1_out = RUN_DIR / "stage1_blueprints.json"
    if config["resume"] and stage1_out.exists():
        console.print("[Stage 1] Resuming — loading existing blueprints")
        blueprints: list[dict] = json.loads(stage1_out.read_text(encoding="utf-8"))
    else:
        console.print(f"[Stage 1] {config['models']['stage1']}")
        blueprints = run_stage1(config, client)

    # Stage 1.5
    run_fact_mixer(config)

    # Per-case stages — concurrent across cases, sequential within each case
    stages_per_case = 4 + (2 if not config["no_smoke"] else 0)

    # Pre-filter: resolve resume before entering Progress context
    cases_to_run: list[tuple[str, str]] = []
    for i, blueprint in enumerate(blueprints):
        if blueprint.get("status") == "failed":
            console.print(f"  [dim]Skipping {blueprint.get('mechanism_id')} — Stage 1 failed[/dim]")
            continue
        mechanism_id = blueprint.get("mechanism_id", f"mech_{i+1:03d}")
        case_id = f"eval_scenario_{config['start_case_id'] + i}"
        case_out = RUN_DIR / "cases" / f"{mechanism_id}.json"
        if config["resume"] and case_out.exists():
            existing = json.loads(case_out.read_text(encoding="utf-8"))
            if existing.get("verifier_status") == "pending":
                console.print(f"  [dim]{mechanism_id} → already accepted, skipping[/dim]")
                continue
        cases_to_run.append((mechanism_id, case_id))

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
            f"[bold]Cases {start}–{end}[/bold]",
            total=len(blueprints),
        )
        # Advance past skipped (resumed) cases
        skipped = len(blueprints) - len(cases_to_run)
        for _ in range(skipped):
            progress.advance(batch_task)

        def process_case(args: tuple[str, str]) -> None:
            mechanism_id, case_id = args
            case_task = progress.add_task(
                f"[cyan]{mechanism_id}[/cyan]",
                total=stages_per_case,
            )
            try:
                run_case(
                    mechanism_id, case_id, config, client,
                    progress=progress,
                    case_task=case_task,
                    stages_per_case=stages_per_case,
                )
            except Exception as exc:
                console.print(f"  [red]FATAL {mechanism_id}: {exc}[/red]")
            finally:
                progress.update(case_task, visible=False)
                progress.advance(batch_task)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(process_case, cases_to_run))

    # Assemble
    assemble_batch(config)


if __name__ == "__main__":
    main()
