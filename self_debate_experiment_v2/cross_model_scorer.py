"""
Cross-model scorer validation — Issue 5.

Tests whether the debate protocol's high IDR scores reflect genuine issue
detection or same-model self-consistency bias (the scorer is the same model
family that generated the transcripts).

SCORER MODEL: claude-haiku-4-5-20251001
Rationale: Uses a different capability tier of the Anthropic model family
(Haiku vs. Sonnet) to reduce — but not eliminate — same-company bias.
This is a pragmatic choice to avoid external API costs. The remaining
limitation (same company/pretraining) is acknowledged explicitly in results.

True cross-vendor validation (GPT-4o or Gemini) would require OPENAI_API_KEY
or GOOGLE_API_KEY; the original cross_model_scorer.py supported those paths.
This version uses the authenticated Claude Code session's Anthropic API key.

REQUIRES: ANTHROPIC_API_KEY in environment (automatically set in Claude Code).

Usage:
    cd self_debate_experiment_v2/
    python cross_model_scorer.py

Outputs: cross_model_scores.json
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCORER_MODEL = "claude-haiku-4-5-20251001"
SCORER_FAMILY_NOTE = (
    "claude-haiku-4-5 (Anthropic) — same company as transcript-generating model "
    "(claude-sonnet-4-6), different capability tier. Scores same-company bias only "
    "partially; cross-vendor validation (GPT-4o / Gemini) would be stronger."
)

SCORER_PROMPT_TEMPLATE = """You are an objective rubric scorer evaluating an ML hypothesis investigation.

## Task prompt that was given to the investigating agents:
{task_prompt}

## Critic output:
{critic_output}

## Defender output:
{defender_output}

## Scoring instructions:
Score the following rubric dimension for the DEBATE PROTOCOL (not the baseline):

**IDR (Issue Discovery Recall):** What fraction of the critical methodological issues in the task prompt did the agents collectively identify? Score:
- 1.0 = all critical issues identified
- 0.5 = some critical issues identified, some missed
- 0.0 = no critical issues identified

Do NOT reference any answer key. Score based solely on whether the agents' outputs identify genuine methodological problems with the work described in the task prompt.

Respond in JSON format:
{{
  "IDR": <0.0 | 0.5 | 1.0>,
  "issues_found": ["<brief description of each issue the agents identified>"],
  "reasoning": "<1-2 sentences explaining your score>"
}}
"""

# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

def get_haiku_score(prompt):
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. This script must be run from within "
              "an authenticated Claude Code session or with the key exported.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=SCORER_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    # Extract JSON from response text
    text = response.content[0].text.strip()
    # Handle markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data = load_json(os.path.join(base_dir, "self_debate_results.json"))

    # Non-defense_wins cases only (IDR applies)
    cases = [c for c in data["cases"] if c["correct_position"] != "defense"]

    results = []
    original_idr_scores = []
    cross_model_idr_scores = []

    for case in cases:
        case_id = case["case_id"]
        print(f"Scoring {case_id}...")

        critic_output = case.get("transcripts", {}).get(
            "critic", "[Transcript not available — re-run agents]"
        )
        defender_output = case.get("transcripts", {}).get(
            "defender", "[Transcript not available — re-run agents]"
        )
        task_prompt = case.get("task_prompt", f"[See BENCHMARK_PROMPTS.md for {case_id}]")

        prompt = SCORER_PROMPT_TEMPLATE.format(
            task_prompt=task_prompt,
            critic_output=critic_output,
            defender_output=defender_output,
        )

        score_result = get_haiku_score(prompt)
        cross_model_idr = score_result.get("IDR", None)
        original_idr = case["debate_scores"].get("IDR")

        results.append({
            "case_id": case_id,
            "original_IDR": original_idr,
            "cross_model_IDR": cross_model_idr,
            "delta": (
                round(cross_model_idr - original_idr, 4)
                if cross_model_idr is not None and original_idr is not None
                else None
            ),
            "issues_found": score_result.get("issues_found", []),
            "reasoning": score_result.get("reasoning", ""),
            "scorer_model": SCORER_MODEL,
        })

        if original_idr is not None:
            original_idr_scores.append(original_idr)
        if cross_model_idr is not None:
            cross_model_idr_scores.append(cross_model_idr)

    n = len([r for r in results if r["delta"] is not None])
    mean_original = (
        sum(original_idr_scores) / len(original_idr_scores) if original_idr_scores else None
    )
    mean_cross = (
        sum(cross_model_idr_scores) / len(cross_model_idr_scores)
        if cross_model_idr_scores
        else None
    )
    mean_delta = (mean_cross - mean_original) if (mean_original is not None and mean_cross is not None) else None

    output = {
        "scorer_model": SCORER_MODEL,
        "scorer_family_note": SCORER_FAMILY_NOTE,
        "limitation": (
            "Scorer is from the same company (Anthropic) as the transcript-generating model. "
            "Same-company pretraining may produce correlated responses independent of content. "
            "Haiku vs. Sonnet capability difference provides partial but not full cross-model isolation. "
            "A GPT-4o or Gemini scorer would provide stronger external validation."
        ),
        "n_cases": n,
        "original_mean_IDR": round(mean_original, 4) if mean_original is not None else None,
        "cross_model_mean_IDR": round(mean_cross, 4) if mean_cross is not None else None,
        "mean_delta": round(mean_delta, 4) if mean_delta is not None else None,
        "bias_material": abs(mean_delta) > 0.1 if mean_delta is not None else None,
        "interpretation": (
            f"IDR shifted by {mean_delta:+.4f} (Haiku vs. Sonnet scorer). "
            + (
                "Same-company bias is MATERIAL (|delta| > 0.1) — warrants cross-vendor replication."
                if abs(mean_delta) > 0.1
                else "Same-company bias is NOT material (|delta| <= 0.1) — scores converge across Anthropic capability tiers."
            )
        )
        if mean_delta is not None
        else "Could not compute — check transcripts",
        "cases": results,
    }

    out_path = os.path.join(base_dir, "cross_model_scores.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Cross-Model Scorer Results (claude-haiku-4-5) ===")
    print(f"Original IDR mean:     {mean_original:.4f}" if mean_original else "N/A")
    print(f"Cross-model IDR mean:  {mean_cross:.4f}" if mean_cross else "N/A")
    print(f"Delta:                 {mean_delta:+.4f}" if mean_delta is not None else "N/A")
    print(f"Bias material:         {output['bias_material']}")
    print(f"\nNOTE: Same-company scorer (Anthropic Haiku). Partial cross-model isolation only.")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
