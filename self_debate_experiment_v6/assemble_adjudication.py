#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Assemble adjudication output for chunk_0_run1.json (ISOLATED_DEBATE condition).
All adjudication decisions are hard-coded below; verbatim fields are copied from source.
"""

import json
import sys
from pathlib import Path

INPUT = Path("/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_interim_isolated/chunk_0_run1.json")
OUTPUT = Path("/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_adjudicated_isolated/chunk_0_run1_adjudicated.json")

# Hard-coded adjudication decisions per case_id.
# Value: list of issue indices (0-based) that SURVIVE the defender's independent assessment.
# All cases: critique_wins (all issues survive unless explicitly dropped).
ADJUDICATION = {
    "rc_rescience_2020_menon2021re_journal": {
        "surviving_indices": [0, 1, 2, 3],
        # Issue 0: subtle anomaly false negatives — defender never addresses near-normal anomaly failure mode
        # Issue 1: PSNR+L2 calibration/weighting unspecified, can move opposite directions — defender says "complementary failure modes" but doesn't address calibration
        # Issue 2: test-time contamination — defender's "confirmed-normal by design" is circular (assumes system already working)
        # Issue 3: frame-level vs video-level AUC unspecified — defender never addresses this
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_nilsson2022replicating_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: w-space traversal entanglement not eliminated — "empirically more disentangled" ≠ geometrically consistent pseudo-views
        # Issue 1: all four categories have dedicated high-quality StyleGAN2 models — defender's "structural regularity varies" doesn't address the confound
        # Issue 2: no quantitative geometric metric — downstream tasks don't validate metric accuracy
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_drabent2022replication_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: S_pri defined against unspecified attack; multi-attack claim doesn't resolve whether evaluation uses same attacks as search
        # Issue 1: accuracy on original vs transformed test data — never addressed
        # Issue 2: 'negligible efficiency impact' unqualified — never specified
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_rucks2022re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: generalization to unseen distributions unsubstantiated — defender doesn't specify what unseen distributions are
        # Issue 1: shift/rotation robustness may be trivial Fourier mathematical property — defender doesn't rebut the triviality claim
        # Issue 2: number of unrolled iterations selection not described — potential leakage never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2020_rodas2021rehamiltonian_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: variational objective ≠ symplectic structure — defender says "bridge to latent Hamiltonian structure" but doesn't enforce geometric validity
        # Issue 1: all systems dissipation-free, 'no restrictive assumptions' untested — analytical solution advantage doesn't address friction/dissipation gap
        # Issue 2: backward rollout is partial but reconstruction loss still can't distinguish energy drift from visual degradation — no energy metric provided
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_stropnik2022re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: only synthetic datasets — "defensible for architectural primitive" is contextual, not counter-evidence
        # Issue 1: scalability claim graph sizes/density unspecified — defender confirms scalability was tested but doesn't specify the regimes
        # Issue 2: edit operation vocabulary and edit-distance optimality unspecified — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2020_verhoeven2021replication_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: causal graph assumed/hand-specified, never validated — defender justifies the framing but doesn't address ground-truth validation
        # Issue 1: MNIST/fMNIST don't distinguish causal decomposition from visual feature highlighting — "appropriate proof-of-concept" doesn't rebut the confound
        # Issue 2: sensitivity to generative model quality not analyzed — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_shukla2022from_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: compounding error in two-stage architecture, ADE/FDE can't separate — defender gives design rationale but doesn't address error propagation analysis
        # Issue 1: scene-specific segmentation maps, no OOD evaluation — two-dataset evaluation doesn't constitute OOD test
        # Issue 2: best-of-K FDE metrics, K unspecified — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_kolkman2022strategic_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: user response model unspecified — defender justifies the approach but never specifies the assumed model
        # Issue 1: regularization strength selection unspecified, normative — defender justifies regularization need but doesn't address selection procedure
        # Issue 2: comparison against non-strategic baselines is expected by construction — defender doesn't address the baseline inadequacy
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_warmerdam2022re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: privacy against specific attack; adaptive/augmentation-invariant attacks not addressed
        # Issue 1: search strategy unspecified, no Pareto-optimality guarantee — defender justifies search need but not optimality
        # Issue 2: cross-dataset transferability may reflect shared domain statistics — defender agrees transfer testing is necessary but doesn't address same-domain limitation
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_matsumoto2022re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: perturbation class (low-rank vs dense) unspecified — "common condition" framing doesn't specify what is supported
        # Issue 1: baselines unspecified; defender argues full recomputation is correct baseline but doesn't address established incremental methods
        # Issue 2: SVD drift across many sequential updates not analyzed — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_korporaal2022replication_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: StyleSpace dimensions not fully disentangled — "more disentangled than W/W+" is relative, not a full disentanglement proof
        # Issue 1: domain shift between real classifier training data and GAN synthetic images — never addressed
        # Issue 2: explanation metrics can't distinguish semantic from GAN artifact sensitivity — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_wang2022replication_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: DAG specification problem (incorrect if provided, biased if learned) — defender motivates DAG use but doesn't address the specification/learning trap
        # Issue 1: GAN mode collapse harms minority groups — never addressed
        # Issue 2: fairness improvement may reflect distributional simplification, not causal debiasing — no ablation described
        "verdict": "critique_wins",
    },
    "rc_rescience_2020_sundar2021reproducibility_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: methodology too vague to identify specific algorithm — defender interprets as RigL but description ambiguity remains
        # Issue 1: 'universal applicability' unbounded — "multiple architectures" doesn't bound or specify coverage
        # Issue 2: 'successful training' undefined — never specified
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_bagad2022reproducibility_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: consistency axiom not validated, conditional generation ≠ counterfactual — defender says "additional metrics close evaluation gap" but doesn't rebut consistency axiom concern
        # Issue 1: IS/FID insensitive to mode dropping — defender CONCEDES this, validating the issue
        # Issue 2: latent smoothness for unseen counterfactual queries not validated — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2020_garg2021re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: binarization mapping from continuous posterior to binary weights unspecified — defender mentions posterior framework but not the binarization mapping
        # Issue 1: posterior approximation quality unspecified, overconfidence in discrete space — "uncertainty quantification is valuable" doesn't validate approximation quality
        # Issue 2: training overhead vs inference savings not analyzed — defender argues for joint objective but not the comparative analysis
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_burger2022reproducibility_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: explanation metrics unspecified, can be gamed — defender advocates quantitative metrics but doesn't specify which ones
        # Issue 1: accuracy comparison against same backbone is trivially expected — defender gives rationale but doesn't rebut the construction triviality
        # Issue 2: positive/negative slot polarity stability not enforced — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_brivio2022reproducibility_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: sentiment may be anti-correlated with hate speech (neutral/positive tone) — defender gives theoretical motivation but doesn't address anti-correlation case
        # Issue 1: category embedding coverage gap for coded language/dog whistles — "validates domain knowledge" doesn't address coverage gap
        # Issue 2: dataset annotation differences may confound performance differences — defender justifies multi-dataset but doesn't address annotation divergence
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_peters2022reproducing_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: abstention rate disparities can mask precision parity — defender defends coverage-scale evaluation but doesn't address group-level abstention rate confound
        # Issue 1: MI estimator and regularization strength tuning unspecified — "principled mechanism" doesn't specify estimator choice
        # Issue 2: datasets not characterized by sensitive attribute correlation structure, no adversarial stress test — never addressed
        "verdict": "critique_wins",
    },
    "rc_rescience_2021_tersek2022re_journal": {
        "surviving_indices": [0, 1, 2],
        # Issue 0: test-time adaptation supervision signal unspecified, may leak ground-truth count — defender describes two-phase design but doesn't address supervision signal
        # Issue 1: detector comparison doesn't specify in-distribution vs OOD — defender argues for exemplar approach but doesn't address evaluation confound
        # Issue 2: 'more exemplars reduce error' expected by construction, saturation not analyzed — defender defends doing the test but not analyzing the non-triviality
        "verdict": "critique_wins",
    },
}


def main():
    with open(INPUT) as f:
        cases = json.load(f)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    output = []
    for case in cases:
        case_id = case["case_id"]
        decisions = ADJUDICATION.get(case_id)
        if decisions is None:
            print(f"WARNING: No adjudication decision for {case_id}", file=sys.stderr)
            continue

        all_issues = case["all_issues_raised"]
        surviving = [all_issues[i] for i in decisions["surviving_indices"]]

        output.append({
            "case_id": case_id,
            "condition": "isolated_debate",
            "run_idx": 1,
            "critic_raw": case["critic_raw"],
            "defender_raw": case["defender_raw"],
            "all_issues_raised": all_issues,
            "all_issues_adjudicated": surviving,
            "verdict": decisions["verdict"],
        })

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Written {len(output)} adjudicated cases to {OUTPUT}")
    # Quick sanity check
    verdicts = [r["verdict"] for r in output]
    print(f"Verdicts: critique_wins={verdicts.count('critique_wins')}, defense_wins={verdicts.count('defense_wins')}")


if __name__ == "__main__":
    main()
