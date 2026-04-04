# Open Issues — Post-Adversarial Review

Raised by ml-critic and ml-defender during the meta-debate on v2 findings (2026-04-04).
Ordered by expected impact on the core claim.

---

## Priority 1 — Addresses the Core Lift Claim

### 1. Budget-Matched Ensemble Baseline

**Issue:** The debate protocol runs 3-4× more tokens than the single-pass baseline (Critic + Defender + Judge vs. one call). The reported lift may be partly a compute/chain-of-thought aggregation effect rather than an adversarial role structure effect.

**Test:** Run a compute-matched ensemble baseline — three independent single-pass responses per case synthesized by a fourth call, with no Critic/Defender role differentiation. Compare to the debate protocol on the same 20 cases.

**Verdict criteria:**
- If ensemble ≈ debate on non-defense_wins cases → compute budget explains the non-defense_wins lift; role structure does not
- If ensemble < debate on defense_wins cases specifically → isolation architecture is the load-bearing mechanism (expected, since no single-pass system can structurally challenge adversarial framing)
- If ensemble ≈ debate on defense_wins cases → the finding is weaker than claimed

**Effort:** ~80 API calls (4 per case × 20 cases). New script needed: `self_debate_ensemble_baseline.py`.

---

### 2. Recover or Regenerate Raw Transcript Scores (DRQ Cap Effect)

**Issue:** `self_debate_transcripts.py` is missing — it was never committed. The raw baseline DRQ scores before the cap was applied are unknown. Nine cases have DRQ=0.5, which is exactly at the cap ceiling; it's unknown whether these were naturally 0.5 or capped from something higher.

**Fix (Option A — Preferred):** Locate the original investigation session context where transcripts were generated and recover the file. Commit it.

**Fix (Option B):** Re-run the baseline scorer for the 9 DRQ=0.5 cases using the embedded baseline transcript text from `self_debate_results.json` (the `transcripts.baseline` field is present in the JSON). Extract the natural DRQ score without the cap applied.

**Verdict criteria:** If any natural DRQ > 0.5 is found, recompute baseline aggregate with the cap removed and report alongside current figures.

**Effort:** Low (Option B — baseline transcripts are already in the JSON).

---

### 3. Fix Stale Baseline Pass Flags in self_debate_results.json

**Issue:** `broken_baseline_001` and `metric_mismatch_002` are marked `baseline_pass: true` in the JSON, but their stored baseline scores have DC=0.0, which fails the per-dimension floor check (all applicable dims ≥ 0.5). The pass flags were set before the DC override was applied.

**Fix:** After resolving issues 1–2 above, re-run `self_debate_poc.py` to regenerate a consistent `self_debate_results.json`. Until then, note the inconsistency in `CONCLUSIONS.md` and `REPORT.md`.

**Impact:** The reported "baseline pass count = 2" is wrong. With DC=0.0, the correct baseline pass count is 0. With DC=0.5, it's 8. Neither matches the reported 2.

**Effort:** Trivial code fix once the root causes above are addressed.

---

## Priority 2 — Addresses External Validity

### 4. Two-Pass Defender Fix for Reasoning/Label Disconnect

**Issue:** `real_world_framing_001` failed because the Defender correctly identified all critical flaws in analysis text but labeled the verdict `defense_wins` — a reasoning-to-label translation error. The proposed fix (require analysis pass before verdict selection) has not been tested.

**Test:** Modify the `ml-defender` prompt to require a two-pass structure:
1. Analysis pass: identify all issues, concessions, and sound aspects
2. Verdict pass: "Given your analysis above, if you identified critical unaddressed flaws, your verdict is `empirical_test_agreed` or `critique_wins` — not `defense_wins`."

Re-run the 3 failed/partial cases (`real_world_framing_001`, `defense_wins_003`, `defense_wins_005`). If failure rate drops from 3/3 to 0/3, the fix is tractable and should be merged into `~/.claude/agents/ml-defender.md`.

**Effort:** Prompt edit + 3 targeted re-runs (~18 API calls).

---

### 5. Cross-Model Scorer Validation

**Issue:** The Scorer agent is claude-sonnet-4-6 — the same model family that played Critic, Defender, Judge, and Baseline. A model scoring its own outputs against ground truth it effectively generated may exhibit self-consistency bias: recognizing its own phrasing and mapping it to expected labels. The 1.000 IDR across 15 applicable cases is consistent with this effect.

**Test:** Have a different model family (GPT-4o or Gemini 1.5 Pro) score the same embedded transcripts against the same rubric, without access to `must_find` labels. Compare IDR scores. If IDR shifts by >±0.1 on average, self-scoring bias is material.

**Effort:** ~30 scorer calls via a different API. Requires a scoring script that accepts an external model endpoint.

---

### 6. Independent Benchmark Construction

**Issue:** The benchmark designer knew the planted flaws and wrote the prompts. All 20 cases have determinate answers and no missing information as the primary challenge — the designer may unconsciously have made flaws discoverable by the kind of reasoning they knew the model could do. Internal validity is established; external validity is not.

**Test:** Construct a parallel 10-case benchmark from external sources:
- Published ML paper retractions (NeurIPS/ICML reproducibility track)
- Kaggle competition post-mortems with documented evaluation failures
- Ground truth established by domain consensus, not the protocol designer

Run the same protocol and report IDR. If it drops below 0.85, benchmark construction leakage was material.

**Effort:** Significant. Requires sourcing and authoring cases from external materials; estimate 5-10 hours of case construction.

---

## Priority 3 — Statistical Rigor

### 7. Convergence Hypothesis — Adequate Sample Sizes

**Issue:** The secondary hypothesis ("convergence rate decreases with difficulty") was tested with 3 easy cases, 10 medium cases, and 7 hard cases. The easy=0.833 estimate is driven by a single data point (defense_wins_003, conv=0.5). No confidence intervals were reported. The hypothesis is neither confirmed nor refuted — it is underpowered.

**Fix:** Expand the benchmark to ≥10 cases per difficulty tier before re-testing the convergence hypothesis. Alternatively, report CIs on the current per-tier estimates and acknowledge the easy-tier estimate is n=3.

**Effort:** Requires adding ~17 new benchmark cases (7 easy cases minimum). This is also an opportunity to expand the `real_world_framing` category, which is currently 2 cases.

---

## Status Tracking

| # | Issue | Priority | Status | Blocking |
|---|-------|----------|--------|---------|
| 1 | Budget-matched ensemble baseline | P1 | **Resolved** 2026-04-04 (clean re-run complete; defense_wins isolation hypothesis definitively tested) | Core lift claim |
| 2 | Recover/recompute raw DRQ scores | P1 | **Resolved** 2026-04-04 | — |
| 3 | Fix stale baseline pass flags | P1 | **Resolved** 2026-04-04 (noted in CONCLUSIONS.md; full JSON rerun pending #1) | #1 |
| 4 | Two-pass Defender fix + retest | P2 | **Resolved** 2026-04-04 | — |
| 5 | Cross-model scorer validation | P2 | Open | None |
| 6 | Independent benchmark | P2 | Open | None |
| 7 | Convergence — adequate n per tier | P3 | Open | None |

## Resolution Notes

**Issue 2 (2026-04-04):** DRQ cap confirmed binding on all 9 DRQ=0.5 cases. Baseline scorer agent re-run on all 9 cases using original benchmark prompts — natural DRQ=1.0 in every case. The cap suppressed correct resolution-type identification, not incorrect. Full sensitivity updated in `SENSITIVITY_ANALYSIS.md`: honest lift range is +0.335 to +0.441 (vs. headline +0.586).

**Issue 3 (2026-04-04):** Correction note added to `CONCLUSIONS.md`. Correct baseline pass count is 0/20 with DC=0.0 enforced consistently (reported as 2 due to stale flags). Full JSON fix deferred until Issue 1 (ensemble baseline rerun) generates a clean results file.

**Issue 4 (2026-04-04):** Two-pass defender prompt change applied to `agents/ml-defender.md`. Retested on 3 failed/partial cases:
- `real_world_framing_001`: flipped from `defense_wins` (wrong) → `critique_wins` (correct). DC=1.0.
- `defense_wins_003`: held at `defense_wins` (correct). DC=1.0.
- `defense_wins_005`: held at `defense_wins` (correct). DC=1.0.
Fix is confirmed tractable. Change should be merged into `~/.claude/agents/ml-defender.md`.

**Issue 1 (2026-04-04 — partial):** Compute-matched ensemble baseline run across all 20 cases (3 assessors + 1 synthesizer per case, no DC/DRQ structural overrides). Results: `ensemble_results.json`, full analysis in `ENSEMBLE_ANALYSIS.md`.

- **Non-defense_wins (15 cases):** Ensemble scored 1.000 (15/15 passes) vs. debate 0.982 (15/15 passes). Ensemble matches or exceeds debate at ceiling. Compute confound hypothesis **confirmed** for non-defense_wins cases — additional compute budget alone achieves ceiling performance without adversarial role structure.
- **Defense_wins (5 cases):** Results are **contaminated**. Agent prompts included an explicit "correct analysis" section coaching assessors toward the defense_wins verdict before independent analysis. Cannot conclude from these results whether a clean ensemble would exonerate valid work. Isolation mechanism hypothesis remains untested.

**Issue 1 (2026-04-04 — final):** Clean two-phase ensemble re-run complete. Phase 1 assessors received only task prompts (no labels, no coaching). Phase 2 scorer received synthesized output + must-find labels separately. Results: `clean_ensemble_results.json`, analysis updated in `ENSEMBLE_ANALYSIS.md`.

- **Overall:** ensemble mean 0.754 vs. debate 0.970. Pass count 11/20 (55%) vs. debate 19/20 (95%). The contaminated run's "all 1.0" scores were entirely artifact.
- **Defense_wins isolation hypothesis:** DC≥0.5 on 4/5 cases. **Pre-specified criterion triggered: compute budget partially explains defense_wins advantage.** Isolation architecture is not uniquely necessary. 4/5 valid work cases correctly exonerated by 3 independent views + synthesis, without structural isolation.
- **Debate protocol's remaining structural advantage:** ETD=0.0 on 9 of 20 ensemble cases. The ensemble correctly identifies issues and reaches correct verdict direction, but does not propose empirical tests. The debate protocol's adversarial forcing function (Critic/Defender must agree on a specific test when they disagree) generates ETD=1.0 that a parallel ensemble cannot produce without explicit output constraints.
- **Revised lift decomposition:** ensemble vs. debate gap (-0.216) is explained almost entirely by ETD and DRQ degradation from the missing test-design forcing function, not from issue detection or verdict calibration failure.
