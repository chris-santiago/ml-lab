#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///

import json
from pathlib import Path

LABELS = {
    # --- REGULAR CASES ---
    "eval_scenario_705": {
        "flaw_category": "signal_leakage",
        "canary_difficulty": "medium",
        "label_rationale": "Preprocessing transformers fit on full 18-month corpus before temporal splitting allows future data trends to contaminate training, invalidating temporal separation as the primary flaw.",
    },
    "hyp_016_case_1": {
        "flaw_category": "metric_limitations",
        "canary_difficulty": "medium",
        "label_rationale": "Patient-level AUC-ROC using maximum predicted risk across the full window conflates general sepsis risk stratification with the 6-hour horizon-specific prediction the hypothesis requires.",
    },
    "hyp_037_stage4": {
        "flaw_category": "signal_leakage",
        "canary_difficulty": "medium",
        "label_rationale": "Preprocessing statistics and embedding initialization derived from the full modeling corpus (including validation and test) leak future data into the feature representation, with broken baseline as a secondary flaw.",
    },
    "eval_scenario_773": {
        "flaw_category": "missing_baselines",
        "canary_difficulty": "medium",
        "label_rationale": "The baseline uses a fixed, untuned hyperparameter configuration while the proposed model undergoes full grid search, making any performance difference uninterpretable as feature contribution.",
    },
    "eval_scenario_777": {
        "flaw_category": "distribution_shift",
        "canary_difficulty": "medium",
        "label_rationale": "Restricting the cohort to patients with 12+ months of prior history excludes sparse-record patients and creates a deployment mismatch between evaluation population and real-world application.",
    },
    "eval_scenario_801": {
        "flaw_category": "signal_leakage",
        "canary_difficulty": "medium",
        "label_rationale": "Stratified random sampling across all terms instead of chronological splitting allows future-term data to influence training, violating temporal integrity as the primary compound flaw.",
    },
    "eval_scenario_812": {
        "flaw_category": "metric_limitations",
        "canary_difficulty": "medium",
        "label_rationale": "Report-level recall replaces the hypothesis-specified span-level F1, so the evaluation measures whether a recommendation exists rather than whether spans are correctly identified.",
    },
    "eval_scenario_852": {
        "flaw_category": "eval_inflation",
        "canary_difficulty": "medium",
        "label_rationale": "Using the first half of the test period as a deployment-readiness confirmation pass contaminates the final holdout's independence, inflating reported performance.",
    },
    "eval_scenario_185": {
        "flaw_category": "metric_limitations",
        "canary_difficulty": "medium",
        "label_rationale": "Labels based on analyst escalation within 24 hours measure workflow decisions rather than confirmed intrusions, misaligning evaluation with the hypothesis of surfacing verified high-severity incidents.",
    },
    "rc_rescience_2021_wang2022replication_journal": {
        "flaw_category": "silent_misconfig",
        "canary_difficulty": "hard",
        "label_rationale": "The methodology was so underspecified that reproduction required rewriting large code sections and produced non-matching fairness metrics, indicating plausible-looking results that cannot be independently verified to measure the same quantities.",
    },
    # --- MIXED CASES ---
    "hyp_211": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "Whether NDCG@20 adequately reflects analyst review budget requires measuring the actual historical alerts-per-queue, making validity dependent on unstated operational data.",
    },
    "eval_scenario_912": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "AUPRC is defensible under extreme imbalance, but whether it aligns with the bank's investigator capacity cutoff and regulatory recall targets is an empirical question about deployment thresholds.",
    },
    "eval_scenario_914": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "Precision@20 is appropriate only if analyst queues consistently contain ~20 alerts per cycle; validity hinges on empirically auditing 30 days of production triage logs.",
    },
    "eval_scenario_915": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "AUPRC captures ranking under imbalance but whether it mirrors the dominant operational alert volume threshold requires analysis of 3 months of production day thresholds.",
    },
    "eval_scenario_919": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "PR-AUC is the primary metric but whether the transformer's gain translates to operational precision at the fixed 90% recall threshold requires empirical verification at the deployment operating point.",
    },
    "hyp_240": {
        "flaw_category": "context_dependent",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "Average precision is appropriate for ranking under imbalance, but whether the model with higher AP also dominates at the operational precision floor and top-K budget requires empirical comparison.",
    },
    "rc_rescience_2020_menon2021re_journal": {
        "flaw_category": "ambiguous_evidence",
        "canary_difficulty": "high_ambiguity",
        "label_rationale": "The memory module sometimes hurt performance (ShanghaiTech), hyperparameter tuning was underdocumented, and component attribution was unclear, creating genuine disagreement about whether the method's claims hold.",
    },
    "rc_rescience_2020_p2021embedkgqa_journal": {
        "flaw_category": "ambiguous_evidence",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "Most benchmark results were reproduced within margin but anomalies on MetaQA-KG-Full 3-hop and WebQSP-KG-Full and the contested RM module prevent a clear verdict.",
    },
    "rc_rescience_2021_tersek2022re_journal": {
        "flaw_category": "fixable_flaw",
        "canary_difficulty": "low_ambiguity",
        "label_rationale": "The density-map generation procedure was incorrectly described and code was missing, but the main empirical claims were largely supported after reconstruction, so the flaw is real but fixable without invalidating the core hypothesis.",
    },
    "rc_rescience_2022_11": {
        "flaw_category": "ambiguous_evidence",
        "canary_difficulty": "medium_ambiguity",
        "label_rationale": "One main claim did not generalize beyond original experimental settings and one experiment failed to reproduce on the graph dataset, creating dataset-specific robustness gaps.",
    },
    # --- DEFENSE CASES ---
    "eval_scenario_703": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Mean pooling of BioBERT embeddings and the 50% documentation completeness exclusion threshold are unconventional choices that critics may flag, though both are methodologically justified.",
    },
    "eval_scenario_707": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, training-only preprocessing, and equivalent BM25 tuning effort represent conventional, well-justified search evaluation methodology with nothing to flag.",
    },
    "hyp_010": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Patient-level temporal split with proper preprocessing, strong dual baselines, and explicit success criteria represent a rigorously conventional EHR readmission design.",
    },
    "eval_scenario_hyp_017": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, 120-day chargeback exclusion window for censored labels, and equal 50-trial tuning budget are all standard and well-justified fraud detection practices.",
    },
    "eval_scenario_766": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Group-based temporal split, training-only preprocessing, and equivalent tuning for both models represent a clean conventional churn prediction design.",
    },
    "eval_scenario_819": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Chronological split with site and outcome stratification, frozen pre-trained embeddings, and identical model architectures ensure a sound conventional multimodal ED triage comparison.",
    },
    "eval_scenario_hyp132": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, ticket-creation-time-only text extraction, and training-only preprocessing represent well-justified standard SLA breach prediction methodology.",
    },
    "eval_scenario_hyp_140_0": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Retraining the final model on train+validation data after hyperparameter selection is an unusual but operationally defensible choice to maximize data use before test evaluation.",
    },
    "eval_scenario_845": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Task prompt contains placeholder text so full methodology cannot be assessed, but the defense category and absence of planted issues remain; difficulty assessed as medium due to incomplete prompt.",
    },
    "eval_scenario_848": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, 30-day label grace period for delayed detections, and training-only preprocessing represent sound, standard phishing detection methodology.",
    },
    "hyp_155": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Freezing the communication graph at the training boundary is an explicit operational constraint that simulates deployment but critics may flag the inability to adapt to new sender patterns.",
    },
    "eval_scenario_858": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, training-only IDF and vocabulary fitting, and equivalent BM25 hyperparameter tuning represent clean conventional information retrieval evaluation methodology.",
    },
    "eval_scenario_862": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "16-quarter temporal split, proper preprocessing fit, and deliberate feature orthogonality between models represent sound conventional phishing detection methodology.",
    },
    "eval_scenario_868": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split with campaign-level stratification, frozen reputation scores, and proper ablation baselines represent sound conventional spear-phishing detection methodology.",
    },
    "hyp_003_regular": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Temporal split, Cox partial likelihood for survival analysis, and equivalent tuning effort for both models represent standard well-justified SaaS churn prediction methodology.",
    },
    "hyp_004_regular": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Treating death as a censoring event rather than negative outcome is correct for competing risks but may be flagged by critics unfamiliar with survival analysis conventions.",
    },
    "rc_rescience_2020_harrison2021learning_journal": {
        "flaw_category": None,
        "canary_difficulty": "hard",
        "label_rationale": "Deliberately penalizing attention to impermissible tokens while keeping those tokens in the input appears methodologically backwards to critics who don't grasp that the design's purpose is to test whether attention can be manipulated independently of feature use.",
    },
    "rc_rescience_2020_verhoeven2021replication_journal": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Using 'causal' terminology for variables defined relative to the classifier rather than real-world causal relationships may trigger critics who conflate operational causal explanation with formal causal identification.",
    },
    "rc_rescience_2021_ahmed2022re_journal": {
        "flaw_category": None,
        "canary_difficulty": "easy",
        "label_rationale": "Isolating individual nondeterminism sources through controlled multi-run experiments is a principled and conventional design for studying training variability.",
    },
    "rc_rescience_2022_16": {
        "flaw_category": None,
        "canary_difficulty": "medium",
        "label_rationale": "Applying influence-style example-importance methods and feature saliency in a fully unsupervised regime without class labels is unusual and critics may claim it's ill-defined, though the paper's framework explicitly defines the explanation target as the learned representation.",
    },
}

def main():
    src = Path("/Users/chrissantiago/Dropbox/GitHub/ml-lab/experiments/self_debate_experiment_v8/canary_full.json")
    dst = Path("/Users/chrissantiago/Dropbox/GitHub/ml-lab/experiments/self_debate_experiment_v8/canary_cases.json")

    with src.open() as f:
        cases = json.load(f)

    labeled = []
    missing = []
    for case in cases:
        cid = case["case_id"]
        if cid not in LABELS:
            missing.append(cid)
            labeled.append(case)
            continue
        labeled_case = dict(case)
        lbl = LABELS[cid]
        labeled_case["flaw_category"] = lbl["flaw_category"]
        labeled_case["canary_difficulty"] = lbl["canary_difficulty"]
        labeled_case["label_rationale"] = lbl["label_rationale"]
        labeled.append(labeled_case)

    if missing:
        print(f"WARNING: {len(missing)} cases had no label entry: {missing}")

    with dst.open("w") as f:
        json.dump(labeled, f, indent=2)

    print(f"Wrote {len(labeled)} cases to {dst}")
    # Verify all three fields present
    for c in labeled:
        if "flaw_category" not in c or "canary_difficulty" not in c or "label_rationale" not in c:
            print(f"  MISSING FIELDS in case {c['case_id']}")
    print("Done.")

if __name__ == "__main__":
    main()
