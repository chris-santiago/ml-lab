# /// script
# requires-python = ">=3.10"
# dependencies = ["anthropic", "openai"]
# ///
"""
Stage 7 — Batch Controller / Orchestrator

Coordinates the full case generation pipeline across all 7 stages.

Modes:
  score-only   : Runs Stage 6 (Haiku scoring) and Stage 7 (batch assembly) only.
                 Use after completing Stages 1-5 manually.

  auto         : Runs all stages automatically via external LLM API (OpenAI by default).
                 Requires OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.

  claude-code  : Generates a subagent dispatch script for running within Claude Code.
                 Does not make API calls itself.

Usage:
    uv run orchestrator.py --mode score-only --cases-dir pipeline/cases/
    uv run orchestrator.py --mode auto --model gpt-4o --batch-size 15
    uv run orchestrator.py --mode claude-code --batch-size 5

For manual (Mode A), use score-only after completing Stages 1-5 by hand:
    uv run orchestrator.py --mode score-only --cases-dir pipeline/cases/
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Scoring logic (Stage 6) — replicates HAIKU_SMOKE_TEST_INSTRUCTIONS rubric
# ---------------------------------------------------------------------------

def score_haiku_response(response_text: str, case: dict) -> dict:
    """
    Score a Haiku single-pass response on the 4-dimension proxy rubric.
    Returns dict with IDR, IDP, FVC, IDJ scores and per-case mean.
    """
    scoring_targets = case.get("scoring_targets", {})
    must_find_ids = scoring_targets.get("must_find_issue_ids", [])
    must_not_claim = scoring_targets.get("must_not_claim", [])
    acceptable_resolutions = scoring_targets.get("acceptable_resolutions", [])
    planted_issues = case.get("planted_issues", [])
    correct_position = case.get("ground_truth", {}).get("correct_position", "")

    response_lower = response_text.lower()

    # --- IDR: Did response surface all must_find issues? ---
    if not must_find_ids:
        # defense_wins case — IDR=1 automatically
        idr = 1.0
    else:
        all_found = True
        for issue_id in must_find_ids:
            # Find the planted issue description
            issue = next((p for p in planted_issues if p.get("issue_id") == issue_id), None)
            if issue:
                desc_words = issue.get("description", "").lower().split()[:5]
                # Check if key mechanism words appear in response
                found = any(w in response_lower for w in desc_words if len(w) > 5)
                if not found:
                    all_found = False
                    break
        idr = 1.0 if all_found else 0.0

    # --- IDP: Was at least one issue described with substantive correctness? ---
    if correct_position == "defense":
        # IDP=1 if response avoids inventing fatal flaws (doesn't condemn methodology)
        condemnation_phrases = ["invalid", "fundamentally flawed", "cannot be trusted", "should be rejected"]
        idr_1 = not any(phrase in response_lower for phrase in condemnation_phrases)
        idp = 1.0 if idr_1 else 0.0
    else:
        # IDP=1 if at least one issue is described with the correct mechanism
        idp = 1.0 if idr == 1.0 else 0.0  # Simplified: if IDR passed, assume IDP passed

    # --- FVC: Is verdict consistent with acceptable_resolutions? ---
    empirical_signals = [
        "prospective", "shadow", "pilot", "validation study", "empirical test",
        "field test", "real-world test", "additional validation", "further validation"
    ]
    critique_signals = [
        "should not be deployed", "reject", "fundamental flaw", "invalid", "cannot",
        "do not recommend", "not ready"
    ]
    defense_signals = [
        "sound", "well-designed", "appropriate", "recommend approval", "valid",
        "no significant concerns", "methodology is correct"
    ]

    if "empirical_test_agreed" in acceptable_resolutions:
        fvc = 1.0 if any(s in response_lower for s in empirical_signals) else 0.0
    elif "defense_wins" in acceptable_resolutions:
        fvc = 1.0 if any(s in response_lower for s in defense_signals) else 0.0
    elif "critique_wins" in acceptable_resolutions:
        fvc = 1.0 if any(s in response_lower for s in critique_signals) else 0.0
    else:
        fvc = 0.5  # Unknown resolution type

    # --- IDJ: For addressed_but_incorrectly issues, did response challenge the justification? ---
    abi_issues = [p for p in planted_issues if p.get("addressed_but_incorrectly")]
    if not abi_issues:
        idj = None  # N/A
    else:
        challenge_signals = [
            "justification", "argument", "reasoning", "claim", "assertion",
            "stated reason", "explanation", "not sufficient", "insufficient",
            "does not address", "fails to address", "incorrectly", "wrong"
        ]
        challenged = any(s in response_lower for s in challenge_signals)
        idj = 1.0 if challenged else 0.0

    # --- Per-case mean ---
    scores = {"IDR": idr, "IDP": idp, "FVC": fvc}
    if idj is not None:
        scores["IDJ"] = idj
    applicable = [v for v in scores.values() if v is not None]
    mean = sum(applicable) / len(applicable) if applicable else 0.0

    return {
        "IDR": idr,
        "IDP": idp,
        "FVC": fvc,
        "IDJ": idj,
        "mean": round(mean, 3),
        "passes_gate": mean < 0.55,
    }


def run_haiku_scoring(case: dict, client) -> dict:
    """Run Stage 6: evaluate task_prompt with Haiku and score the response."""
    task_prompt = case.get("task_prompt", "")
    wrapper = (
        "You are reviewing an ML methodology report. Please evaluate the soundness of the "
        "methodology described below, identify any significant methodological concerns, and "
        "provide an overall assessment of whether the work supports the stated conclusions.\n\n"
        "---\n\n"
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": wrapper + task_prompt}],
        )
        response_text = response.content[0].text
    except Exception as e:
        return {"error": str(e), "IDR": None, "IDP": None, "FVC": None, "IDJ": None, "mean": None, "passes_gate": False}

    scores = score_haiku_response(response_text, case)
    scores["haiku_response"] = response_text
    return scores


# ---------------------------------------------------------------------------
# Recycling decision logic (Stage 7)
# ---------------------------------------------------------------------------

def make_recycling_decision(case: dict, leakage_audit: dict | None, difficulty_scores: dict | None) -> dict:
    """
    Apply Stage 7 recycling logic.
    Returns {"accept": bool, "route": str, "reason": str}
    """
    if leakage_audit:
        leakage_score = leakage_audit.get("overall_leakage_score", 0.0)
        voice = leakage_audit.get("voice_assessment", "team_advocacy")
        if leakage_score > 0.4 or voice != "team_advocacy":
            return {
                "accept": False,
                "route": "stage2",
                "reason": f"Leakage audit failed: score={leakage_score:.2f}, voice={voice}. Return to Stage 2 for new scenario approach.",
            }

    if difficulty_scores:
        mean = difficulty_scores.get("mean", 1.0)
        idr = difficulty_scores.get("IDR", 1.0)
        fvc = difficulty_scores.get("FVC", 1.0)
        idp = difficulty_scores.get("IDP", 1.0)

        if mean is not None and mean >= 0.55:
            # Analyze which dimension failed to route correctly
            if idr == 1.0 and fvc == 1.0 and idp == 1.0:
                return {
                    "accept": False,
                    "route": "stage1",
                    "reason": f"Gate failed (mean={mean:.3f}): flaw too findable. Return to Stage 1 for different mechanism or deeper transposition.",
                }
            elif fvc == 1.0 and (idr is None or idr < 1.0):
                return {
                    "accept": False,
                    "route": "stage2",
                    "reason": f"Gate failed (mean={mean:.3f}): verdict accessible without finding flaw. Return to Stage 2 to restructure decoy placement.",
                }
            elif idp == 1.0:
                return {
                    "accept": False,
                    "route": "stage1",
                    "reason": f"Gate failed (mean={mean:.3f}): decoys not tempting. Return to Stage 1 for stronger must_not_claim items.",
                }
            else:
                return {
                    "accept": False,
                    "route": "stage1",
                    "reason": f"Gate failed (mean={mean:.3f}): insufficient difficulty. Return to Stage 1.",
                }

    # Check verifier_status from Stage 4
    if case.get("verifier_status") == "recycle":
        notes = case.get("notes", "")
        return {
            "accept": False,
            "route": "stage2",
            "reason": f"Stage 4 flagged for recycling: {notes}",
        }

    return {"accept": True, "route": None, "reason": "All checks passed."}


# ---------------------------------------------------------------------------
# Score-only mode
# ---------------------------------------------------------------------------

def run_score_only(cases_dir: Path, output_path: Path) -> None:
    """Stage 6 + 7: Score completed cases from files and assemble final batch."""
    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as e:
        print(f"ERROR: Could not initialize Anthropic client: {e}", file=sys.stderr)
        print("Set ANTHROPIC_API_KEY to run score-only mode.", file=sys.stderr)
        sys.exit(1)

    case_files = sorted(cases_dir.glob("*.json"))
    if not case_files:
        print(f"ERROR: No JSON files found in {cases_dir}", file=sys.stderr)
        sys.exit(1)

    accepted = []
    rejected = []

    for case_file in case_files:
        case = json.loads(case_file.read_text(encoding="utf-8"))
        mech_id = case.get("case_id", case_file.stem)
        print(f"\n[{mech_id}] Scoring with Haiku...")

        scores = run_haiku_scoring(case, client)
        decision = make_recycling_decision(case, leakage_audit=None, difficulty_scores=scores)

        print(f"  IDR={scores.get('IDR')} IDP={scores.get('IDP')} "
              f"FVC={scores.get('FVC')} IDJ={scores.get('IDJ')} "
              f"mean={scores.get('mean')} → {'ACCEPT' if decision['accept'] else 'REJECT'}")

        if decision["accept"]:
            accepted.append(case)
        else:
            rejected.append({"case_id": mech_id, "reason": decision["reason"], "route": decision["route"]})

    print(f"\n[orchestrator] Accepted: {len(accepted)}/{len(case_files)}")
    print(f"[orchestrator] Rejected: {len(rejected)}/{len(case_files)}")

    if rejected:
        print("\nRejected cases (require recycling):")
        for r in rejected:
            print(f"  {r['case_id']}: {r['reason']}")

    output_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")
    print(f"\n[orchestrator] Final batch written to {output_path} ({len(accepted)} cases)")


# ---------------------------------------------------------------------------
# Claude Code dispatch script generator
# ---------------------------------------------------------------------------

def generate_claude_code_dispatch(batch_size: int, prompts_dir: Path) -> None:
    """Generate instructions for running the pipeline as Claude Code subagents."""
    print(f"""
# Claude Code Pipeline Dispatch Instructions
# Generated by orchestrator.py --mode claude-code

## Stage 1 — Mechanism Extractor
Run as a subagent (model: sonnet or opus):
  Prompt: {prompts_dir}/stage1_mechanism_extractor.md
  Fill: {{{{BATCH_SIZE}}}} = {batch_size}, {{{{PREVIOUS_BATCH_USAGE}}}} = {{}}
  Save output to: pipeline/stage1_output.json

## Stage 1.5 — Fact Mixer (run locally)
  uv run pipeline/fact_mixer.py --input pipeline/stage1_output.json --output-dir pipeline/stage1.5/

## Stages 2-3 (run in parallel — one subagent per case)
For each case in stage1.5/all_writer_views.json:
  Stage 2 prompt: {prompts_dir}/stage2_scenario_architect.md
    Fill: {{{{TARGET_DOMAIN}}}}, {{{{DOMAIN_SPECIFIC_DETAIL}}}}, {{{{CATEGORY}}}}, {{{{WRITER_VIEW_FACTS}}}}
    Save output to: pipeline/stage2/[mechanism_id]_scenario.json

  Stage 3 prompt: {prompts_dir}/stage3_memo_writer.md
    Fill: {{{{SCENARIO_BRIEF}}}} from Stage 2 output
    Save output to: pipeline/stage3/[mechanism_id]_memo.json

## Stages 4+5 (run in parallel — both for each case, after Stage 3)
  Stage 4 prompt: {prompts_dir}/stage4_metadata_assembler.md
    Fill: {{{{MECHANISM_BLUEPRINT}}}}, {{{{METADATA_VIEW}}}}, {{{{LEAKAGE_AUDIT}}}}, {{{{TASK_PROMPT}}}}, {{{{CASE_ID}}}}
    Save output to: pipeline/cases/[mechanism_id].json

  Stage 5 prompt: {prompts_dir}/stage5_leakage_auditor.md
    Fill: {{{{TASK_PROMPT}}}} from Stage 3 output
    Save output to: pipeline/stage5/[mechanism_id]_audit.json

## Stage 6+7 — Score and assemble
  uv run pipeline/orchestrator.py --mode score-only --cases-dir pipeline/cases/
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 7 — Batch Controller")
    parser.add_argument(
        "--mode", required=True,
        choices=["score-only", "auto", "claude-code"],
        help="Execution mode"
    )
    parser.add_argument("--cases-dir", default="pipeline/cases", help="Directory with completed case JSON files (score-only mode)")
    parser.add_argument("--output", default="pipeline/batch_output.json", help="Output path for final accepted cases")
    parser.add_argument("--batch-size", type=int, default=15, help="Number of cases to generate (auto/claude-code modes)")
    parser.add_argument("--model", default="gpt-4o", help="LLM model for auto mode")
    parser.add_argument("--prompts-dir", default="pipeline/prompts", help="Directory containing stage prompt .md files")
    args = parser.parse_args()

    prompts_dir = Path(args.prompts_dir)
    output_path = Path(args.output)

    if args.mode == "score-only":
        cases_dir = Path(args.cases_dir)
        if not cases_dir.exists():
            print(f"ERROR: Cases directory not found: {cases_dir}", file=sys.stderr)
            sys.exit(1)
        run_score_only(cases_dir, output_path)

    elif args.mode == "claude-code":
        generate_claude_code_dispatch(args.batch_size, prompts_dir)

    elif args.mode == "auto":
        print("Auto mode (full API orchestration) is a template — implement with your preferred API client.")
        print("See PIPELINE_USAGE.md Mode B for setup instructions.")
        print("The score-only mode is ready to use after completing Stages 1-5.")
        sys.exit(0)


if __name__ == "__main__":
    main()
