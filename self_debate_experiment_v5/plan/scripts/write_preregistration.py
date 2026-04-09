# write_preregistration.py
# /// script
# requires-python = ">=3.10"
# ///
import json
from datetime import datetime

preregistration = {
    "date": datetime.now().isoformat(),
    "experiment": "self_debate_experiment_v5",
    "model": "claude-sonnet-4-6",
    "hypotheses": {
        "primary_fair_comparison_lift": {
            "claim": "Isolated debate fair-comparison lift over baseline >= +0.10",
            "threshold": 0.10,
            "dimensions": ["IDR", "IDP", "DRQ", "FVC"],
            "note": "Fair-comparison set: dimensions where baseline has equal structural agency. DC and ETD excluded from this comparison."
        },
        "primary_passrate": {"claim": "Debate case pass rate >= 75%", "threshold": 0.75},
        "primary_benchmark_mean": {"claim": "Debate benchmark mean >= 0.65", "threshold": 0.65},
        "secondary_ensemble_mixed": {
            "claim": "Debate outperforms ETD-excluded ensemble on IDR/IDP/DRQ/FVC for mixed-position cases",
            "criterion": "Debate mean on mixed cases (fair dims) > ensemble mean on same cases (fair dims)"
        },
        "secondary_defense_wins": {
            "claim": "Ensemble FVC >= 0.5 on >= 60% of defense_wins cases — adversarial synthesis produces better-calibrated verdicts on defense cases",
            "criterion": "Ensemble FVC >= 0.5 on >= 60% of defense_wins cases (DC is N/A for all defense cases per pre-registration; FVC is the observable proxy criterion)"
        },
        "secondary_forced_multiround": {
            "claim": "Forced multiround outperforms natural multiround on hard cases",
            "criterion": "forced_multiround_mean(hard) > multiround_mean(hard) on DRQ and IDR"
        },
        "stratum_fc_lift": {
            "claim": "Pre-registered stratum breakdown for Phase 8 interpretation",
            "strata": ["pure_critique", "mixed", "defense_wins"],
            "expected_primary_lift_driver": "defense_wins (DRQ/FVC); critique/mixed (IDR/IDP)",
            "note": "Not a hypothesis test — a pre-committed interpretive structure. Prevents post-hoc stratum selection."
        }
    },
    "rubric": {
        "IDR": "issues_found / total_must_find_issue_ids (fractional 0.0-1.0); N/A on defense_wins",
        "IDP": "fraction of valid raised issues; must_not_claim items are explicit false positives (0.0/0.5/1.0); N/A on defense_wins",
        "DC": "correct verdict via defense function (0.0/0.5/1.0); N/A for baseline (structural inapplicability — no Defender role); N/A on defense_wins cases",
        "DRQ": "typed verdict matches ideal (1.0); matches other acceptable_resolution (0.5); adjacent (0.5); wrong (0.0); baseline NOT capped — equal treatment required for fair comparison",
        "ETD": "empirical test has condition + supports_critique_if + supports_defense_if + ambiguous_if (0.0/0.5/1.0); N/A when ideal is critique_wins or defense_wins; N/A for ensemble and baseline conditions",
        "FVC": "verdict in acceptable_resolutions list (1.0); adjacent to ideal not in list (0.5); wrong (0.0)",
    },
    "etd_scoring_detail": {
        "schema": "condition / supports_critique_if / supports_defense_if / ambiguous_if (canonical v5 schema)",
        "three_field_base": "condition + supports_critique_if + supports_defense_if all present -> 1.0",
        "ambiguous_if_bonus": "ambiguous_if present in addition to three base fields -> 1.0 (same as without; ambiguous_if is noted but does not increase score beyond full credit)",
        "partial": "condition present + one of supports_critique_if/supports_defense_if -> 0.5",
        "none": "condition absent or empirical_test null -> 0.0",
        "note": "v5 standardizes on agent-native schema. No dual-schema branching."
    },
    "dc_treatment": {
        "baseline": "N/A — structural inapplicability. Baseline has no Defender role. Penalizing absence of a role the condition was never designed to fill is not a legitimate comparison. Consistent with ETD N/A for inapplicable case types. Pre-registered before execution.",
        "defense_wins_cases": "N/A — the correct resolution is exoneration; the Defender's role is trivially satisfied",
        "other_conditions": "Scored normally (0.0/0.5/1.0)"
    },
    "etd_treatment": {
        "ensemble": "N/A — no adversarial exchange; no contested-point structure. An empirical test is meaningful as a debate output because it represents what the Judge determined could resolve a contested point after Critic and Defender argued it. For ensemble, there is no contested point structure.",
        "baseline": "N/A — same rationale as ensemble",
        "debate_conditions": "Scored normally on empirical_test_agreed cases"
    },
    "comparison_structures": {
        "debate_vs_ensemble": {
            "dimensions": ["IDR", "IDP", "DRQ", "FVC"],
            "excluded": ["DC", "ETD"],
            "rationale": "ETD excluded: ensemble has no adversarial exchange. DC excluded: ensemble has no Defender role. This answers: does adversarial role structure improve issue identification and verdict quality beyond parallel independent passes?"
        },
        "debate_conditions_vs_each_other": {
            "conditions": ["isolated_debate", "multiround", "forced_multiround"],
            "dimensions": ["IDR", "IDP", "DC", "DRQ", "ETD", "FVC"],
            "note": "All three have the same adversarial exchange structure; ETD and DC are both applicable"
        }
    },
    "point_resolution_rate": {
        "definition": "(points_resolved_by_concession_or_empirical_agreement) / (total_contested_points_in_DEBATE.md)",
        "extraction": "Count DEBATE.md entries with status 'Resolved: critic wins', 'Resolved: defender wins', or 'Resolved: empirical_test_agreed' vs total contested points",
        "scope": "multiround and forced_multiround conditions only",
        "note": "Replaces v3 convergence_metric (critic/defender verdict comparison, which was not computable). Diagnostic only — not used in pass/fail determination."
    },
    "failure_attribution_values": {
        "agent": "Traceable to specific agent output (Critic missed issue; Defender reasoning/label disconnect)",
        "protocol": "In debate structure (correct resolution not reached despite agents performing roles)",
        "ambiguous": "Cannot distinguish agent vs protocol from outputs alone",
        "none": "Case passed — no failure to attribute"
    },
    "per_case_pass_criterion": "mean(non-null PRIMARY dimensions: IDR/IDP/DRQ/ETD/FVC) >= 0.65 AND all applicable primary dimensions >= 0.5. DC is diagnostic-only and excluded.",
    "n_runs_per_case": 3,
    "forced_multiround_scope": "hard cases only (difficulty == 'hard'); minimum 2 rounds"
}

with open('PREREGISTRATION.json', 'w') as f:
    json.dump(preregistration, f, indent=2)

rubric = {
    "scoring_dimensions": {
        "IDR": "Fraction of scoring_targets.must_find_issue_ids correctly identified (fractional). N/A on defense_wins.",
        "IDP": "Fraction of claimed issues that are valid; must_not_claim items are explicit false positives (0.0/0.5/1.0). N/A on defense_wins.",
        "DC": "DIAGNOSTIC ONLY — excluded from per-case mean and pass/fail criterion. Whether defense correctly reached verdict type (0.0/0.5/1.0). N/A for baseline (no Defender role). N/A on defense_wins cases. Reported as DC/FVC divergence diagnostic in summary.",
        "DRQ": "Whether typed verdict matches expected resolution (0.0/0.5/1.0). No structural cap or override for any condition.",
        "ETD": "Empirical test has condition + supports_critique_if + supports_defense_if (0.0/0.5/1.0). N/A when ideal is critique_wins or defense_wins. N/A for ensemble and baseline conditions.",
        "FVC": "Verdict in scoring_targets.acceptable_resolutions (1.0); adjacent to ideal (0.5); wrong (0.0).",
    },
    "pass_fail_rule": "mean(non-null PRIMARY dimensions: IDR/IDP/DRQ/ETD/FVC) >= 0.65 AND all applicable primary dimensions >= 0.5. DC is diagnostic-only and excluded from pass/fail.",
    "notes": "Rubric fixed before any agent run. Do not modify after execution begins."
}

with open('evaluation_rubric.json', 'w') as f:
    json.dump(rubric, f, indent=2)

print("Pre-registration and rubric written and locked.")
