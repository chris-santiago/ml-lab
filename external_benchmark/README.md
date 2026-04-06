# external_benchmark/

This directory contains a post-hoc external validity experiment run after the v2 self-debate benchmark (`self_debate_experiment_v2/`) was completed. It was not part of the pre-registered v2 experiment design.

## Purpose

The internal v2 benchmark used synthetically constructed cases whose ground truth was established by the protocol designer. This experiment tested whether the debate protocol generalizes to cases drawn from real published ML papers, where ground truth is established by the published record rather than by the experimenter.

## Contents

| File | Description |
|---|---|
| `cases.json` | 10 benchmark cases derived from published ML papers. All critique or mixed position. Schema predates v3 (no `ground_truth.*` nesting, no `scoring_targets.*` nesting). |
| `results.json` | Evaluation results for all 10 cases under debate and baseline conditions. Includes per-case scores, verdicts, and metadata. |
| `DEFENSE.md` | Defense agent output for one case (ext_metric_mismatch_002 / GLUE human baseline). |

## Case sources

All 10 cases are grounded in published ML research:

| Case ID | Source |
|---|---|
| ext_broken_baseline_001 | Dacrema et al. (2019) — Are We Really Making Much Progress? RecSys |
| ext_broken_baseline_002 | Li & Talwalkar (2020) — Random Search and Reproducibility for NAS. UAI |
| ext_broken_baseline_003 | Rendle et al. (2020) — Neural CF vs. Matrix Factorization Revisited. RecSys |
| ext_metric_mismatch_001 | Obermeyer et al. (2019) — Dissecting racial bias in a health algorithm. Science |
| ext_metric_mismatch_002 | Wang et al. (2019); Nangia & Bowman (2019) — GLUE/SuperGLUE human baseline |
| ext_metric_mismatch_003 | Brock et al. (2019) BigGAN; Sajjadi et al. (2018); Naeem et al. (2020) |
| ext_hidden_confounding_001 | DeGrave et al. (2021) — COVID-19 detection selects shortcuts. Nature MI |
| ext_hidden_confounding_002 | Gururangan et al. (2018) — Annotation Artifacts in NLI Data. NAACL |
| ext_scope_intent_misunderstanding_001 | Jia & Liang (2017) — Adversarial Examples for Reading Comprehension. EMNLP |
| ext_broken_baseline_004 | Zeng et al. (2023) — Are Transformers Effective for Time Series? AAAI |

## Protocol note

This experiment ran with a protocol deviation: Defenders produced independent assessments and did not read the Critic's output before responding. This is not the standard ml-lab debate protocol (where the Defender sees the Critique). The deviation means DC and DRQ scores may not reflect true adversarial exchange dynamics. See `results.json` metadata for the full note.

## Relationship to v2

These results contributed to v2's Issue 19 resolution (external exoneration cases) but are distinct from `external_exoneration_results.json` in the v2 directory, which contains 3 defense_wins cases from published papers run under the full debate protocol.

## Relationship to v3

The v3 experiment (`self_debate_experiment_v3/`) directly incorporates an external benchmark as a first-class component rather than a post-hoc addition. All 10 cases from this directory have been converted to v3 schema and added to `self_debate_experiment_v3/external_cases_v3.json`, along with 6 defense_wins cases (3 from `external_exoneration_results.json` and 3 from `new_benchmark_cases.json`). In v3, external cases run in Phase 6.5 alongside the main 50-case benchmark and are reported as a separate validation stratum in CONCLUSIONS.md.

The v3 schema conversion applied to these cases:
- Moved `must_find` → `scoring_targets.must_find_issue_ids`
- Moved `correct_position` → `ground_truth.correct_position`
- Added `ground_truth.final_verdict`, `ground_truth.required_empirical_test`
- Added `scoring_targets.must_not_claim`, `scoring_targets.acceptable_resolutions`
- Added `planted_issues`, `ideal_critique`, `ideal_defense`, `ideal_debate_resolution`
- Added `provenance` with `source_type: "published_paper"` and `paper_citation`
- Assigned `difficulty` based on whether the case was rewritten to obscure telegraphed flaws
