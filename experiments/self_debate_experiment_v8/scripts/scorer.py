# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=2.0",
#   "scikit-learn>=1.5",
#   "statsmodels>=0.14",
# ]
# ///
"""
v8 scoring pipeline.

OBJECTIVE
---------
ml-lab is a three-outcome hypothesis review system. The correct verdict depends
on the nature of the case, not just on which agent "wins":

  defense_wins           — sound methodology, critic raised non-issues
  empirical_test_agreed  — genuine ambiguity; experiment needed to settle it
  critique_wins          — undeniable flaw; no valid defense exists

The pipeline is a 3-class classifier scored against per-case ground truth
(correct_position from canary_cases.json), not against stratum alone. Some
"regular" (flawed) cases have correct_position=empirical_test_agreed because
their flaw is real but a competent defender can partially rebut it — empirical
resolution is the right outcome, not a debate win for either side.

VERDICT QUALITY SCORING (correct_position-aware)
-------------------------------------------------
  correct_position=defense_wins:
    defense_wins:          +1.00   exonerated correctly
    empirical_test_agreed: −0.25   over-hedged on sound case
    critique_wins:         −0.50   false alarm

  correct_position=empirical_test_agreed:
    defense_wins:          −0.25   missed ambiguity, false exoneration
    empirical_test_agreed: +1.00   correct outcome
    critique_wins:          0.00   over-stated certainty (flaw real, but not undeniable)

  correct_position=critique_wins:
    defense_wins:          −0.50   missed undeniable flaw
    empirical_test_agreed: +0.50   flaw surfaced, certainty under-stated (partial credit)
    critique_wins:         +1.00   correct outcome

PRIMARY METRIC: MCC (Matthews Correlation Coefficient). DER alone can be gamed
by exonerating everything; MCC accounts for all 9 cells of the confusion matrix.
MMD = 0.06 at canary scale (n=120). Changes below MMD are noise.

KEY METRICS (post re-labeling pass 2026-04-18)
-----------------------------------------------
  DER  — Defense Exoneration Rate: rate of defense_wins on cases with
          correct_position=defense_wins. Target > 0.30.

  FDR  — Flaw Detection Rate: rate of NOT defense_wins on cases with
          correct_position ≠ defense_wins. Both critique_wins and
          empirical_test_agreed count as flaw detection. Floor ≥ 0.60.

  IDR  — (legacy) Undeniable Flaw Rate: rate of critique_wins specifically on
          cases with correct_position=critique_wins (the 5 undeniable-flaw cases).

  AER  — Ambiguity Exoneration Rate: rate of empirical_test_agreed on cases with
          correct_position=empirical_test_agreed. The system should produce ETA
          on genuinely ambiguous cases, not force a winner. Floor ≥ 0.50.

  FAR  — False Alarm Rate: rate of critique_wins on cases with
          correct_position=defense_wins. The worst error mode. Floor ≤ 0.10.

  FHR  — False Hedge Rate: proportion of cases with correct_position in
          {defense_wins, critique_wins} predicted empirical_test_agreed.
          Floor ≤ +0.05 increase vs baseline.

INTERVENTION DIAGNOSTIC CHAIN
------------------------------
  Intervention A — Critic significance threshold (NIT filter):
    Leading:  CER_defense ↓, critic_brier_defense → 0
    Lagging:  DER ↑

  Intervention B — Defender exoneration path (anti-sycophancy):
    Leading:  wDCR ↓ on defense cases, defender_brier_defense → 0
    Lagging:  DER ↑

  AOR measures defender self-consistency: how often the defender's claimed
  overall_verdict disagrees with derive_verdict() output.

Usage:
    uv run scripts/scorer.py --results-dir <dir> [--cases-file canary_cases.json] \\
        [--output scores.json] [--label name]
    uv run scripts/scorer.py --results-dir <candidate> --compare <baseline>  # McNemar's test

Input format (one JSON file per run, named arbitrarily):
    {
      "case_id":    str,
      "stratum":    "defense" | "regular" | "mixed",
      "flaw_category": str | null,   // regular cases only; matches critic finding
      "run_id":     int,
      "model_assignments": {"critic": str, "defender": str, "adjudicator": str},
      "critic_output": {
        "findings": [
          {
            "finding_id": str,
            "severity": int,          // 0-10
            "severity_label": str,    // FATAL|MATERIAL|MINOR|NIT
            "suppressed": bool,       // true if NIT
            "flaw_category": str | null
          }
        ],
        "no_material_findings": bool
      },
      "defender_output": {
        "rebuttals": [
          {
            "finding_id": str,
            "original_severity": int,
            "rebuttal_type": str,     // CONCEDE|REBUT-*|DEFER|EXONERATE
            "severity_adjustment": int,
            "adjusted_severity": int
          }
        ],
        "overall_verdict": str
      },
      "adjudicator_output": {           // populated by derive_verdict() — no LLM call
        "point_verdicts": [
          {
            "finding_id": str,
            "adjusted_severity": int,
            "rebuttal_type": str,
            "point_verdict": str,     // defense_wins|critique_wins|empirical_test_agreed
            "rule_applied": str       // which row of the verdict table was applied
          }
        ],
        "case_verdict": str           // defense_wins|empirical_test_agreed|critique_wins
      }
    }
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    log_loss,
    matthews_corrcoef,
)
from statsmodels.stats.contingency_tables import mcnemar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERDICT_MAP = {
    "defense_wins":          0,
    "empirical_test_agreed": 1,
    "critique_wins":         2,
}

LABEL_MAP = {
    "defense": 0,
    "mixed":   1,
    "regular": 2,
}

# Penalty-aware verdict scores keyed by correct_position.
# Used when canary_cases.json ground truth is loaded (preferred).
CORRECT_POSITION_SCORES: dict[str, dict[str, float]] = {
    "defense_wins": {
        "defense_wins":          +1.00,  # correct exoneration
        "empirical_test_agreed": -0.25,  # over-hedged on sound case
        "critique_wins":         -0.50,  # false alarm
    },
    "empirical_test_agreed": {
        "defense_wins":          -0.25,  # missed ambiguity, false exoneration
        "empirical_test_agreed": +1.00,  # correct outcome
        "critique_wins":          0.00,  # over-stated certainty (flaw real but not undeniable)
    },
    "critique_wins": {
        "defense_wins":          -0.50,  # missed undeniable flaw
        "empirical_test_agreed": +0.50,  # flaw surfaced, certainty under-stated (partial credit)
        "critique_wins":         +1.00,  # correct outcome
    },
}

# Legacy stratum-based scores — used as fallback when correct_position not available.
VERDICT_SCORES = {
    "defense": {
        "defense_wins":          +1.00,
        "empirical_test_agreed": -0.25,
        "critique_wins":         -0.50,
    },
    "regular": {
        "defense_wins":          -0.50,
        "empirical_test_agreed": -0.25,
        "critique_wins":         +1.00,
    },
    "mixed": {
        "defense_wins":          -0.25,
        "empirical_test_agreed": +1.00,
        "critique_wins":          0.00,
    },
}

# ---------------------------------------------------------------------------
# Finding-level Brier scoring
# ---------------------------------------------------------------------------

def brier(p: float, y: int) -> float:
    """Asymmetric proper scoring rule. y ∈ {0, 1}.
    y=1 (real flaw): rewards confident high-severity; penalizes low severity.
    y=0 (false alarm): penalizes confident high-severity.
    """
    return 1 - (1 - p) ** 2 if y == 1 else -(p ** 2)


def get_finding_y(finding: dict, case_flaw_category: str | None, stratum: str) -> int:
    """Per-finding ground truth label.

    defense  → 0 (all findings are false alarms by definition)
    regular  → 1 if finding flaw_category matches case flaw_category, else 0
    mixed    → -1 (not scored at finding level)
    """
    if stratum == "defense":
        return 0
    if stratum == "regular":
        if case_flaw_category and finding.get("flaw_category"):
            return 1 if finding["flaw_category"] == case_flaw_category else 0
        return -1  # no category metadata — use MIL fallback
    return -1  # mixed


def aggregate_findings(
    findings: list[dict],
    rebuttals: list[dict],
    case_flaw_category: str | None,
    stratum: str,
) -> tuple[float, float]:
    """Returns (critic_brier, defender_brier) for the case.

    Primary path: finding-level ground truth via flaw_category match.
    MIL fallback: bag-level supervision when category metadata absent.
    """
    rebuttal_map = {r["finding_id"]: r for r in rebuttals}
    advancing = [f for f in findings if not f.get("suppressed", False)]

    if not advancing:
        return 0.0, 0.0

    # Decide path: primary if all advancing findings have flaw_category AND
    # case has flaw_category AND stratum is defense or regular
    use_primary = (
        stratum in ("defense", "regular")
        and (stratum == "defense" or case_flaw_category is not None)
    )

    cb_scores, db_scores = [], []

    for f in advancing:
        y = get_finding_y(f, case_flaw_category, stratum)
        if y == -1:
            use_primary = False
            break
        rb = rebuttal_map.get(f["finding_id"])
        adj_sev = rb["adjusted_severity"] if rb else f["severity"]

        cb_scores.append(brier(f["severity"] / 10.0, y))
        db_scores.append(brier(adj_sev / 10.0, y))

    if use_primary and cb_scores:
        return mean(cb_scores), mean(db_scores)

    # MIL fallback
    return _aggregate_mil(advancing, rebuttal_map, stratum)


def _aggregate_mil(
    advancing: list[dict],
    rebuttal_map: dict,
    stratum: str,
) -> tuple[float, float]:
    """Bag-level MIL fallback when per-finding ground truth unavailable."""
    if stratum == "defense":
        cb = mean([brier(f["severity"] / 10.0, 0) for f in advancing])
        db_vals = []
        for f in advancing:
            rb = rebuttal_map.get(f["finding_id"])
            adj = rb["adjusted_severity"] if rb else f["severity"]
            db_vals.append(brier(adj / 10.0, 0))
        return cb, mean(db_vals)

    if stratum == "regular":
        # critic: max pooling (reward finding ≥1 high-severity flaw)
        cb = max(brier(f["severity"] / 10.0, 1) for f in advancing)
        # defender: mean pooling (penalize over-reduction on any finding)
        db_vals = []
        for f in advancing:
            rb = rebuttal_map.get(f["finding_id"])
            adj = rb["adjusted_severity"] if rb else f["severity"]
            db_vals.append(brier(adj / 10.0, 1))
        return cb, mean(db_vals)

    return 0.0, 0.0


def combined_case_score(
    verdict: str,
    findings: list[dict],
    rebuttals: list[dict],
    case_flaw_category: str | None,
    stratum: str,
    w_v: float = 0.50,
    w_c: float = 0.25,
    w_d: float = 0.25,
) -> float:
    """Weighted combination of verdict score and finding-level Brier losses."""
    vs = VERDICT_SCORES[stratum][verdict]
    cb, db = aggregate_findings(findings, rebuttals, case_flaw_category, stratum)
    return w_v * vs + w_c * cb + w_d * db


# ---------------------------------------------------------------------------
# Verdict stability
# ---------------------------------------------------------------------------

def verdict_stability(run_verdicts: list[str]) -> float:
    """Per-case verdict stability: fraction of runs agreeing with the majority.

    3/3 agree → 1.00 | 2/3 agree → 0.67 | all differ → 0.33
    Used as a per-case stability weight on the combined case score.
    Cohen's Kappa (chance-corrected) is computed globally across all cases
    via compute_global_vs(), not per-case, because kappa requires n > 1.
    """
    if len(run_verdicts) < 2:
        return 1.0
    majority = max(set(run_verdicts), key=run_verdicts.count)
    return run_verdicts.count(majority) / len(run_verdicts)


def compute_global_vs(cases: list[dict]) -> float:
    """Global verdict stability via Cohen's Kappa averaged over run pairs.

    Compares run A verdicts vs run B verdicts across all cases — requires
    at least 2 labels to avoid divide-by-zero. Returns nan if insufficient
    cases or all runs agree perfectly.
    """
    n_runs = max((len(c["runs"]) for c in cases), default=0)
    if n_runs < 2:
        return float("nan")

    run_arrays: dict[int, list[int]] = defaultdict(list)
    for case in cases:
        for i, v in enumerate(case["runs"]):
            run_arrays[i].append(VERDICT_MAP[v])

    pairs = list(combinations(range(n_runs), 2))
    kappas = []
    for a, b in pairs:
        arr_a, arr_b = run_arrays[a], run_arrays[b]
        if len(set(arr_a)) < 2 and len(set(arr_b)) < 2:
            # All verdicts identical — perfect agreement, kappa undefined
            kappas.append(1.0)
            continue
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                k = cohen_kappa_score(arr_a, arr_b)
            kappas.append(k)
        except ValueError:
            kappas.append(1.0)

    return mean(kappas) if kappas else float("nan")


def soft_probs(run_verdicts: list[str]) -> list[float]:
    """[p_sound, p_ambig, p_flawed] from 3 run verdicts."""
    counts = Counter(run_verdicts)
    n = len(run_verdicts)
    return [counts["defense_wins"] / n, counts["empirical_test_agreed"] / n, counts["critique_wins"] / n]


# ---------------------------------------------------------------------------
# Secondary metrics
# ---------------------------------------------------------------------------

def compute_wdcr(cases: list[dict]) -> float:
    """Severity-weighted Defender Concession Rate on defense cases.

    wDCR = sum(original_severity × 1{CONCEDE}) / sum(original_severity)
    """
    numerator = denominator = 0.0
    for case in cases:
        if case["stratum"] != "defense":
            continue
        for run in case["runs_data"]:
            for rb in run.get("defender_output", {}).get("rebuttals", []):
                sev = rb.get("original_severity", 0)
                denominator += sev
                if rb.get("rebuttal_type") == "CONCEDE":
                    numerator += sev
    return numerator / denominator if denominator > 0 else 0.0


def compute_cer(cases: list[dict]) -> dict:
    """Critique Escalation Rate: fraction of non-NIT findings over all findings.

    Reported separately for defense and regular cases.
    """
    result = {}
    for stratum in ("defense", "regular"):
        total = non_nit = 0
        for case in cases:
            if case["stratum"] != stratum:
                continue
            for run in case["runs_data"]:
                for f in run.get("critic_output", {}).get("findings", []):
                    total += 1
                    if not f.get("suppressed", False):
                        non_nit += 1
        result[stratum] = non_nit / total if total > 0 else 0.0
    return result


def compute_adjudicator_override_rate(cases: list[dict]) -> float:
    """Fraction of defense-case runs where defender said defense_wins but
    adjudicator changed it to empirical_test_agreed or critique_wins.

    A non-zero AOR with flat DER after Intervention B confirms the adjudicator
    is the bottleneck — Intervention C is the next target.
    """
    total = overridden = 0
    for case in cases:
        if case["stratum"] != "defense":
            continue
        for run in case["runs_data"]:
            defender_verdict = run.get("defender_output", {}).get("overall_verdict")
            adjudicator_verdict = run.get("adjudicator_output", {}).get("case_verdict")
            if defender_verdict == "defense_wins":
                total += 1
                if adjudicator_verdict != "defense_wins":
                    overridden += 1
    return overridden / total if total > 0 else float("nan")


def compute_nit_suppression_rate(cases: list[dict]) -> float:
    """Fraction of findings classified NIT and suppressed over all findings."""
    total = suppressed = 0
    for case in cases:
        for run in case["runs_data"]:
            for f in run.get("critic_output", {}).get("findings", []):
                total += 1
                if f.get("suppressed", False):
                    suppressed += 1
    return suppressed / total if total > 0 else 0.0


def compute_fce(cases: list[dict]) -> float:
    """Finding Calibration Error: mean absolute deviation from diagonal.

    Uses severity/10 as the probability estimate and stratum (regular vs.
    defense) as the binary ground truth (1=regular, 0=defense).
    Mixed cases are excluded.
    """
    severities, labels = [], []
    for case in cases:
        if case["stratum"] == "mixed":
            continue
        y = 1 if case["stratum"] == "regular" else 0
        for run in case["runs_data"]:
            for f in run.get("critic_output", {}).get("findings", []):
                if not f.get("suppressed", False):
                    severities.append(f["severity"] / 10.0)
                    labels.append(y)

    if len(set(labels)) < 2 or not severities:
        return float("nan")

    fraction_pos, mean_pred = calibration_curve(
        labels, severities, n_bins=4, strategy="quantile"
    )
    return float(np.mean(np.abs(fraction_pos - mean_pred)))


# ---------------------------------------------------------------------------
# Main evaluate()
# ---------------------------------------------------------------------------

def _compute_fdr(cases: list[dict]) -> float:
    """Flaw Detection Rate: fraction of flawed cases (correct_position ≠ defense_wins)
    where majority verdict ≠ defense_wins. Both critique_wins and empirical_test_agreed
    count as flaw detection.
    """
    total = detected = 0
    for case in cases:
        cp = case.get("correct_position")
        if cp == "defense_wins":
            continue
        total += 1
        majority = max(set(case["runs"]), key=case["runs"].count)
        if majority != "defense_wins":
            detected += 1
    return detected / total if total > 0 else float("nan")


def _compute_aer(cases: list[dict]) -> float:
    """Ambiguity Exoneration Rate: fraction of empirical_test_agreed cases
    (correct_position=empirical_test_agreed) where majority verdict = empirical_test_agreed.
    Measures whether the system correctly identifies genuine ambiguity vs. forcing a winner.
    """
    total = correct = 0
    for case in cases:
        if case.get("correct_position") != "empirical_test_agreed":
            continue
        total += 1
        majority = max(set(case["runs"]), key=case["runs"].count)
        if majority == "empirical_test_agreed":
            correct += 1
    return correct / total if total > 0 else float("nan")


def _compute_idr_strict(cases: list[dict]) -> float:
    """Undeniable Flaw Rate: fraction of critique_wins cases (correct_position=critique_wins)
    where majority verdict = critique_wins. These are the 5 undeniable-flaw cases
    (leakage, test contamination, direct metric mismatch).
    """
    total = correct = 0
    for case in cases:
        if case.get("correct_position") != "critique_wins":
            continue
        total += 1
        majority = max(set(case["runs"]), key=case["runs"].count)
        if majority == "critique_wins":
            correct += 1
    return correct / total if total > 0 else float("nan")


def _compute_far_strict(cases: list[dict]) -> float:
    """False Alarm Rate: fraction of defense_wins cases where majority verdict = critique_wins.
    The worst error mode — claiming undeniable flaw on a sound methodology.
    """
    total = false_alarms = 0
    for case in cases:
        if case.get("correct_position") != "defense_wins":
            continue
        total += 1
        majority = max(set(case["runs"]), key=case["runs"].count)
        if majority == "critique_wins":
            false_alarms += 1
    return false_alarms / total if total > 0 else float("nan")


def _false_hedge_rate_cp(cases: list[dict]) -> float:
    """FHR (correct_position-aware): fraction of clear cases (correct_position in
    {defense_wins, critique_wins}) predicted empirical_test_agreed.
    """
    total = hedged = 0
    for case in cases:
        cp = case.get("correct_position")
        if cp not in ("defense_wins", "critique_wins"):
            continue
        total += 1
        majority = max(set(case["runs"]), key=case["runs"].count)
        if majority == "empirical_test_agreed":
            hedged += 1
    return hedged / total if total > 0 else float("nan")


def evaluate(cases: list[dict]) -> dict:
    """Compute all v8 evaluation metrics from aggregated case data.

    Each element of `cases` must have:
      case_id, stratum, correct_position (or None), flaw_category (or None),
      runs (list of verdict strings), runs_data (list of full per-run dicts)

    correct_position (from canary_cases.json ground truth) is used for verdict
    scoring and new metrics. When absent, falls back to stratum-based scoring.
    """
    # Build y_true / y_pred using correct_position → VERDICT_MAP
    y_true, y_pred, y_prob = [], [], []
    combined_scores_by_cp: dict[str, list[float]] = defaultdict(list)
    combined_scores_by_stratum = defaultdict(list)  # legacy, kept for backward compat
    vs_scores = []

    critic_brier_by_stratum:   dict[str, list[float]] = defaultdict(list)
    defender_brier_by_stratum: dict[str, list[float]] = defaultdict(list)

    for case in cases:
        stratum = case["stratum"]
        cp = case.get("correct_position") or {"defense": "defense_wins",
            "mixed": "empirical_test_agreed", "regular": "critique_wins"}[stratum]
        run_verdicts = case["runs"]
        gt = VERDICT_MAP[cp]  # ground truth label = expected verdict class
        run_labels = [VERDICT_MAP[v] for v in run_verdicts]
        majority = max(set(run_labels), key=run_labels.count)
        y_true.append(gt)
        y_pred.append(majority)
        y_prob.append(soft_probs(run_verdicts))

        vs = verdict_stability(run_verdicts)
        vs_scores.append(vs)


        # Per-run: combined score + separate Brier components
        per_run_scores = []
        per_run_cb, per_run_db = [], []
        for run in case["runs_data"]:
            verdict = run["adjudicator_output"]["case_verdict"]
            findings = run.get("critic_output", {}).get("findings", [])
            rebuttals = run.get("defender_output", {}).get("rebuttals", [])
            cb, db = aggregate_findings(
                findings, rebuttals, case.get("flaw_category"), stratum
            )
            # Use correct_position-aware scores
            vs_score = CORRECT_POSITION_SCORES[cp][verdict]
            score = 0.50 * vs_score + 0.25 * cb + 0.25 * db
            per_run_scores.append(score)
            per_run_cb.append(cb)
            per_run_db.append(db)

        weighted_score = mean(per_run_scores) * vs
        combined_scores_by_cp[cp].append(weighted_score)
        combined_scores_by_stratum[stratum].append(weighted_score)

        # Case-mean Brier (not stability-weighted — raw signal per agent)
        if stratum != "mixed":
            critic_brier_by_stratum[stratum].append(mean(per_run_cb))
            defender_brier_by_stratum[stratum].append(mean(per_run_db))

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    # 3-class confusion matrix and report using VERDICT_MAP labels
    report = classification_report(
        y_true, y_pred,
        labels=[0, 1, 2],
        target_names=["defense_wins", "emp_test_agreed", "critique_wins"],
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    present_classes = sorted(set(y_true))
    ll = log_loss(y_true, y_prob[:, present_classes], labels=present_classes) if len(present_classes) > 1 else float("nan")

    cer = compute_cer(cases)

    # Count cases by correct_position
    n_by_cp = Counter(case.get("correct_position", "unknown") for case in cases)

    return {
        # Primary
        "mcc": float(matthews_corrcoef(y_true, y_pred)),

        # Verdict-level metrics (correct_position-aware)
        "DER":  float(report.get("defense_wins",    {}).get("recall", 0.0)),
        "FDR":  _compute_fdr(cases),       # NOT defense_wins on all flawed cases
        "IDR":  _compute_idr_strict(cases), # critique_wins on undeniable-flaw cases only
        "AER":  _compute_aer(cases),        # emp_test_agreed on genuinely ambiguous cases
        "FAR":  _compute_far_strict(cases), # critique_wins on sound cases (worst error)
        "FHR":  _false_hedge_rate_cp(cases),# emp_test_agreed on clear cases

        # Stability
        "VS_mean":  float(mean(vs_scores)) if vs_scores else float("nan"),
        "VS_kappa": compute_global_vs(cases),

        # Combined weighted scores by correct_position
        "weighted_score_defense_wins":          float(mean(combined_scores_by_cp["defense_wins"]))          if combined_scores_by_cp["defense_wins"]          else float("nan"),
        "weighted_score_empirical_test_agreed": float(mean(combined_scores_by_cp["empirical_test_agreed"])) if combined_scores_by_cp["empirical_test_agreed"] else float("nan"),
        "weighted_score_critique_wins":         float(mean(combined_scores_by_cp["critique_wins"]))         if combined_scores_by_cp["critique_wins"]         else float("nan"),

        # Separate Brier losses per agent per stratum (raw, not stability-weighted)
        "critic_brier_defense":   float(mean(critic_brier_by_stratum["defense"]))   if critic_brier_by_stratum["defense"]   else float("nan"),
        "critic_brier_regular":   float(mean(critic_brier_by_stratum["regular"]))   if critic_brier_by_stratum["regular"]   else float("nan"),
        "defender_brier_defense": float(mean(defender_brier_by_stratum["defense"])) if defender_brier_by_stratum["defense"] else float("nan"),
        "defender_brier_regular": float(mean(defender_brier_by_stratum["regular"])) if defender_brier_by_stratum["regular"] else float("nan"),

        # Finding-level diagnostics
        "AOR":      compute_adjudicator_override_rate(cases),
        "wDCR":     compute_wdcr(cases),
        "CER_defense": cer.get("defense", float("nan")),
        "CER_regular": cer.get("regular", float("nan")),
        "NIT_suppression_rate": compute_nit_suppression_rate(cases),
        "FCE":      compute_fce(cases),

        # Log loss
        "log_loss": ll,

        # Raw structures for downstream use
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "n_cases": len(cases),
        "n_defense_wins":          n_by_cp.get("defense_wins",          0),
        "n_empirical_test_agreed": n_by_cp.get("empirical_test_agreed", 0),
        "n_critique_wins":         n_by_cp.get("critique_wins",         0),
        # Legacy stratum counts
        "n_defense": sum(1 for c in cases if c["stratum"] == "defense"),
        "n_mixed":   sum(1 for c in cases if c["stratum"] == "mixed"),
        "n_regular": sum(1 for c in cases if c["stratum"] == "regular"),
    }


# ---------------------------------------------------------------------------
# McNemar's test (full benchmark comparison only)
# ---------------------------------------------------------------------------

def mcnemar_compare(
    cases_a: list[dict],
    cases_b: list[dict],
) -> dict:
    """McNemar's test comparing two prompt configurations on the same cases.

    Both lists must contain the same case_ids in the same order.
    Returns p-value and contingency table.
    """
    assert len(cases_a) == len(cases_b), "Case lists must be the same length"

    def is_correct(case: dict) -> bool:
        majority_verdict = max(set(case["runs"]), key=case["runs"].count)
        # Use correct_position from canary_cases.json ground truth when present;
        # fall back to stratum-based heuristic only when correct_position is absent.
        cp = case.get("correct_position")
        if cp is None:
            cp = {"defense": "defense_wins", "mixed": "empirical_test_agreed",
                  "regular": "critique_wins"}[case["stratum"]]
        return majority_verdict == cp

    both_correct = a_only = b_only = both_wrong = 0
    for ca, cb in zip(cases_a, cases_b):
        a_ok, b_ok = is_correct(ca), is_correct(cb)
        if a_ok and b_ok:     both_correct += 1
        elif a_ok and not b_ok: a_only += 1
        elif b_ok and not a_ok: b_only += 1
        else:                 both_wrong += 1

    table = [[both_correct, a_only], [b_only, both_wrong]]
    result = mcnemar(table, exact=False)

    return {
        "p_value": float(result.pvalue),
        "statistic": float(result.statistic),
        "contingency": table,
        "b_vs_c": {"b": a_only, "c": b_only},
    }


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_runs(results_dir: Path) -> list[dict]:
    """Load all JSON run files from a directory."""
    runs = []
    for path in sorted(results_dir.glob("*.json")):
        with open(path) as f:
            runs.append(json.load(f))
    return runs


def load_ground_truth(cases_file: Path) -> dict[str, str]:
    """Load case_id → correct_position mapping from canary_cases.json."""
    raw = json.loads(cases_file.read_text(encoding="utf-8"))
    return {
        c["case_id"]: c["ground_truth"]["correct_position"]
        for c in raw
        if "ground_truth" in c and "correct_position" in c["ground_truth"]
    }


def group_by_case(
    runs: list[dict],
    ground_truth: dict[str, str] | None = None,
) -> list[dict]:
    """Group individual run dicts into case-level dicts with 3 runs each.

    ground_truth: optional case_id → correct_position lookup from canary_cases.json.
    When provided, `correct_position` is stored on each case and used for
    verdict scoring and confusion matrix labels instead of stratum.
    """
    by_case: dict[str, list[dict]] = defaultdict(list)
    for run in runs:
        by_case[run["case_id"]].append(run)

    cases = []
    for case_id, case_runs in by_case.items():
        case_runs.sort(key=lambda r: r.get("run_id", 0))
        first = case_runs[0]
        verdicts = [r["adjudicator_output"]["case_verdict"] for r in case_runs]
        cp = (ground_truth or {}).get(case_id)
        # Fallback: infer correct_position from stratum when GT not available
        if cp is None:
            cp = {"defense": "defense_wins", "mixed": "empirical_test_agreed",
                  "regular": "critique_wins"}.get(first["stratum"])
        cases.append({
            "case_id": case_id,
            "stratum": first["stratum"],
            "flaw_category": first.get("flaw_category"),
            "correct_position": cp,
            "runs": verdicts,
            "runs_data": case_runs,
        })

    return cases


def _fmt(v: float, fmt: str = ".4f") -> str:
    """Format a metric value; return '  n/a' for NaN."""
    return f"{v:{fmt}}" if v == v else "   n/a"


def print_report(metrics: dict, label: str = "") -> None:
    header = f"  v8 Scoring Report{' — ' + label if label else ''}  "
    print("=" * (len(header) + 4))
    print(f"  {header}")
    print("=" * (len(header) + 4))

    ndw  = metrics.get("n_defense_wins",          0)
    neta = metrics.get("n_empirical_test_agreed", 0)
    ncw  = metrics.get("n_critique_wins",          0)
    nd   = metrics.get("n_defense",  0)
    nm   = metrics.get("n_mixed",    0)
    nr   = metrics.get("n_regular",  0)
    print(f"\n  Cases: {metrics['n_cases']}")
    print(f"    by correct_position: defense_wins={ndw}, empirical_test_agreed={neta}, critique_wins={ncw}")
    print(f"    by stratum:          defense={nd}, mixed={nm}, regular={nr}\n")

    print("  ── Primary ─────────────────────────────────────────────")
    print(f"  MCC                          {_fmt(metrics['mcc'], '+.4f')}   (target: > baseline + 0.06 MMD)")
    print()
    print("  ── Verdict-Level (correct_position-aware) ──────────────")
    print(f"  DER  (defense_wins recall)   {_fmt(metrics['DER'])}   (target: > 0.30)")
    print(f"  FDR  (flaw detection rate)   {_fmt(metrics['FDR'])}   (floor:  ≥ 0.60 — ≠defense_wins on flawed)")
    print(f"  AER  (ambiguity recognition) {_fmt(metrics['AER'])}   (floor:  ≥ 0.50 — emp_test_agreed on ETA cases)")
    print(f"  IDR  (undeniable flaw rate)  {_fmt(metrics['IDR'])}   (critique_wins on critique_wins cases only)")
    print(f"  FAR  (false alarm rate)      {_fmt(metrics['FAR'])}   (floor:  ≤ 0.10 — critique_wins on sound cases)")
    print(f"  FHR  (false hedge rate)      {_fmt(metrics['FHR'])}   (floor:  ≤ 0.05 increase vs baseline)")
    print()
    print("  ── Stability & Weighted Score ──────────────────────────")
    print(f"  VS   (majority fraction)     {_fmt(metrics['VS_mean'])}   kappa={_fmt(metrics.get('VS_kappa', float('nan')))}")
    print(f"  Wtd score  defense_wins      {_fmt(metrics['weighted_score_defense_wins'],         '+.4f')}")
    print(f"  Wtd score  emp_test_agreed   {_fmt(metrics['weighted_score_empirical_test_agreed'], '+.4f')}")
    print(f"  Wtd score  critique_wins     {_fmt(metrics['weighted_score_critique_wins'],         '+.4f')}")
    print()
    print("  ── Brier Losses (raw, per agent) ───────────────────────")
    print(f"  {'':30s}  defense        regular")
    cbd  = metrics.get("critic_brier_defense",   float("nan"))
    cbr  = metrics.get("critic_brier_regular",   float("nan"))
    dbd  = metrics.get("defender_brier_defense", float("nan"))
    dbr  = metrics.get("defender_brier_regular", float("nan"))
    print(f"  Critic   brier              {_fmt(cbd, '+.4f')}         {_fmt(cbr, '+.4f')}")
    print(f"  Defender brier              {_fmt(dbd, '+.4f')}         {_fmt(dbr, '+.4f')}")
    print(f"  (defense: negative = false alarm cost; regular: positive = real flaw found)")
    print()
    print("  ── Finding-Level Diagnostics ───────────────────────────")
    aor_str = _fmt(metrics.get("AOR", float("nan")))
    print(f"  AOR  (adjudicator override)  {aor_str}   (defender→defense_wins, adj changed it)")
    print(f"  wDCR (sev-wtd concede)       {_fmt(metrics['wDCR'])}   (healthy: 0.30–0.50 on defense cases)")
    print(f"  CER  defense                 {_fmt(metrics['CER_defense'])}   (non-NIT / all findings)")
    print(f"  CER  regular                 {_fmt(metrics['CER_regular'])}")
    print(f"  NIT suppression rate         {_fmt(metrics['NIT_suppression_rate'])}")
    print(f"  FCE  (calibration err)       {_fmt(metrics['FCE'])}   (target: < 0.15)")
    print()
    print("  ── Confusion Matrix ────────────────────────────────────")
    print("                       pred defense_wins  pred emp_test  pred critique")
    row_labels = ["true defense_wins  ", "true emp_test_agr  ", "true critique_wins "]
    for row_label, row in zip(row_labels, metrics["confusion_matrix"]):
        print(f"  {row_label}       {row[0]:>8d}       {row[1]:>8d}       {row[2]:>8d}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="v8 scoring pipeline")
    parser.add_argument("--results-dir", required=True, type=Path,
                        help="Directory containing per-run JSON files")
    parser.add_argument("--output", type=Path, default=None,
                        help="Save metrics JSON to this path")
    parser.add_argument("--label", default="",
                        help="Label for this run (e.g. 'defender-v2')")
    parser.add_argument("--cases-file", type=Path, default=None,
                        help="canary_cases.json path — loads correct_position ground truth")
    parser.add_argument("--compare", type=Path, default=None,
                        help="Results dir for baseline config — runs McNemar comparison")
    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"ERROR: results dir not found: {args.results_dir}", file=sys.stderr)
        sys.exit(1)

    ground_truth: dict[str, str] | None = None
    if args.cases_file:
        if not args.cases_file.exists():
            print(f"ERROR: cases file not found: {args.cases_file}", file=sys.stderr)
            sys.exit(1)
        ground_truth = load_ground_truth(args.cases_file)

    runs = load_runs(args.results_dir)
    if not runs:
        print(f"ERROR: no JSON files found in {args.results_dir}", file=sys.stderr)
        sys.exit(1)

    cases = group_by_case(runs, ground_truth=ground_truth)
    metrics = evaluate(cases)
    print_report(metrics, label=args.label)

    if args.compare:
        baseline_runs = load_runs(args.compare)
        baseline_cases = group_by_case(baseline_runs, ground_truth=ground_truth)
        result = mcnemar_compare(baseline_cases, cases)
        print("  ── McNemar's Test (vs baseline) ────────────")
        print(f"  p-value:    {result['p_value']:.4f}")
        print(f"  statistic:  {result['statistic']:.4f}")
        print(f"  b (baseline only correct): {result['b_vs_c']['b']}")
        print(f"  c (candidate only correct): {result['b_vs_c']['c']}")
        print()

    if args.output:
        with open(args.output, "w") as f:
            json.dump({k: v for k, v in metrics.items() if k != "classification_report"}, f, indent=2)
        print(f"  Saved metrics → {args.output}")


if __name__ == "__main__":
    main()
