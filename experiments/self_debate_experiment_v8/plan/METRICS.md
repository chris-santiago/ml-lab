# Metrics

## Retired

**FVC (Flawed Verdict Coefficient)** — weighted score: `defense_wins`=1, `empirical_test_agreed`=0.5, `critique_wins`=0. Retired because it rewards hedging. A system that always outputs `empirical_test_agreed` scores 0.5 everywhere — not a calibrated system, a coward. Replaced by FHR and the penalty-aware scoring function.

**FVC_mixed** — FVC applied to mixed cases. Retired alongside FVC. See mixed-case calibration metric below.

---

## Kept from v7

**DER — Defense Exoneration Rate**
Definition: proportion of defense cases receiving `defense_wins` verdict.
Formula: `DER = count(defense_wins on defense cases) / total defense case evaluations`
v7 baseline: 0.00. Primary metric for v8.

**IDR — Issue Detection Rate**
Definition: proportion of regular (flawed) cases correctly receiving `critique_wins`.
Formula: `IDR = count(critique_wins on regular cases) / total regular case evaluations`
v7 baseline: 0.803 (ensemble), 0.634 (multiround). Must not fall below 0.75.

**FAR — False Alarm Rate**
Definition: proportion of sound cases receiving `critique_wins` (false positive).
Formula: `FAR = count(critique_wins on defense cases) / total defense case evaluations`
Note: FAR = 1 − DER − hedge_rate. Complement to DER.
v7 baseline: 1.00 (multiround). Target: < 0.50.

---

## New Metrics

**FHR — False Hedge Rate** *(replaces FVC)*
Definition: proportion of stratum-clear cases (defense + regular) receiving `empirical_test_agreed`.
Formula: `FHR = count(empirical_test_agreed on defense + regular cases) / total clear case evaluations`
Rationale: `empirical_test_agreed` is always an experiment recommendation. On clear cases, that recommendation is unnecessary. FHR penalizes cowardice on unambiguous cases rather than crediting it.

**VS — Verdict Stability**
Definition: across 3 runs of the same case with different model draws, fraction that agree with the majority verdict.
Formula: if 2/3 runs agree: VS = 0.67; if 3/3 agree: VS = 1.0; if all differ: VS = 0.33.
Rationale: low VS means the verdict is model-driven, not case-driven. The most important new metric enabled by model randomization.

**MES — Model Effect Size**
Definition: proportion of verdict variance attributable to model assignment vs. case characteristics.
Estimation: mixed-effects model `verdict ~ case_stratum + (1|model_assignment)`. Report variance components.
Rationale: if MES is high, the experiment is measuring model preferences, not methodology quality. Prompt changes that increase MES are bad even if mean DER improves.

**CMDD — Cross-Model Debate Delta**
Definition: DER difference when critic and defender are from different provider families vs. same family.
Formula: `CMDD = DER(cross-provider pairs) − DER(same-provider pairs)`
Rationale: same-provider pairs may share sycophancy patterns. CMDD quantifies how much cross-model pairing breaks the defender's capitulation reflex.

**CER — Critique Escalation Rate**
Definition: proportion of critique points that advance past the NIT filter (Intervention A) — i.e., findings classified FATAL, MATERIAL, or MINOR.
Formula: `CER = count(FATAL + MATERIAL + MINOR findings) / count(all findings)`
Expected behavior: CER on defense cases reflects how many concerns the critic raises that require any rebuttal. A well-calibrated critic on a sound case should have low average severity — CER alone is less informative than the severity distribution. Track CER alongside mean finding severity on defense cases: high CER + low mean severity = critic is thorough but calibrated; high CER + high mean severity = critic is overclaiming.

**NIT suppression rate** (the sharper leading indicator for Intervention A):
Formula: `NIT_rate = count(NIT findings suppressed) / count(all findings)`
Expected: NIT_rate > 0 on defense cases after Intervention A (critic is correctly recognizing and suppressing purely stylistic concerns). NIT_rate ≈ 0 means the gate is not activating.

**DCR — Defender Concession Rate**
Definition: point-level (not verdict-level). Proportion of critique points where the defender's rebuttal type is `CONCEDE`.
Formula (raw): `DCR = count(CONCEDE labels) / count(all rebuttal labels on defense cases)`
Formula (severity-weighted): `wDCR = sum(severity_score × 1{CONCEDE}) / sum(severity_score across all findings)`
Rationale: directly measures whether Intervention B changes the defender's reasoning mid-stream, independent of the final verdict label. Leading indicator for DER. Severity-weighted version prevents gaming — conceding a score-9 finding is not equivalent to conceding a score-2 finding.

---

## Unified Taxonomy

All critique points, rebuttals, and adjudications use a shared three-layer schema. Structured labels replace free-text parsing for all downstream metrics (DCR, CER, ARR).

### Layer 1 — Finding (Critic Output)

Each critique point carries three fields:
- `finding_id`: sequential within the critique (F1, F2, ...)
- `severity`: integer 0–10 (see scale below)
- `severity_label`: FATAL / MATERIAL / MINOR / NIT (derived from score)

### Severity Scale (0–10)

| Score | Label | Definition | Example |
|---|---|---|---|
| 9–10 | FATAL | Invalidates conclusion regardless of context | Train-test leakage: model has seen test labels |
| 7–8 | FATAL | Likely fatal — invalidates under most deployment conditions | Evaluation metric tracks proxy, not the actual objective |
| 5–6 | MATERIAL | Weakens a central claim but does not invalidate | Sample size too small for stated confidence level |
| 3–4 | MATERIAL | Minor weakening — noted but doesn't change recommendation | Missing one obvious baseline |
| 1–2 | MINOR | Edge case, context-dependent | "Results may not hold on non-English data" with no evidence of non-English use |
| 0 | NIT | Stylistic, theoretical, or hypothetical | "You could have also tried X" |

**Calibration anchors:**
- Score 10 (reserved): the flaw exists in the code and has been empirically observed to cause wrong results
- Score 7: methodological gap a reviewer would require addressed before publication
- Score 4: "I'd recommend" not "must fix before deployment"
- Score 1: a concern worth a footnote

**Severity label derivation:**
- Score 7–10 → FATAL
- Score 4–6 → MATERIAL
- Score 1–3 → MINOR
- Score 0 → NIT

FATAL, MATERIAL, and MINOR findings advance to DEFENSE.md and the adjudication step. NIT findings are logged in CRITIQUE.md but suppressed before forwarding — they require no rebuttal and carry no adjudication weight.

**Rationale:** MINOR findings advance because the defender needs them to build a complete exoneration. An explicit REBUT-IMMATERIAL on a MINOR finding is stronger evidence of sound methodology than silence. The adjudicator's pre-flight filter (Intervention C) ensures MINOR concessions do not escalate to PENDING checklist items — severity gating on *consequences* happens at the adjudicator, not at the critic output.

---

### Layer 2 — Rebuttal (Defender Output)

Each rebuttal maps one-to-one to an advancing finding (FATAL, MATERIAL, or MINOR). Fields:
- `finding_id`: matches the source finding
- `rebuttal_type`: one of seven labels (see table)
- `rebuttal_severity_adjustment`: integer offset applied to the original severity score

| Rebuttal Type | When to Use | Severity Adjustment |
|---|---|---|
| `CONCEDE` | Finding is correct and significant | 0 (accepted at face value) |
| `REBUT-DESIGN` | Flaw is real but the design choice was deliberate and justified | −3 to −5 |
| `REBUT-SCOPE` | Finding is valid in a different context but not the stated experiment scope | −4 to −6 |
| `REBUT-EVIDENCE` | Critique makes an empirical claim not supported by the PoC output | −5 to −7 |
| `REBUT-IMMATERIAL` | Finding is real but below significance for the experiment's conclusions | −6 to −8 |
| `DEFER` | Both parties agree to an empirical test — question stays open | 0 (unresolved) |
| `EXONERATE` | After rebuttal, ALL advancing findings have adjusted severity ≤ 3 — no FATAL or MATERIAL finding survives. MINOR findings rebutted via REBUT-IMMATERIAL or REBUT-SCOPE qualify automatically. | Resets effective severity to 0 on all findings |

**Severity floor:** adjusted score cannot go below 0.

**EXONERATE conditions (strict):**
- Every advancing finding must have adjusted severity ≤ 3 after rebuttal.
- MINOR findings (original score 1–3) satisfy this automatically — no rebuttal adjustment needed, though an explicit REBUT-IMMATERIAL is preferred for a complete exoneration record.
- FATAL and MATERIAL findings must be actively rebutted (REBUT-DESIGN, REBUT-SCOPE, REBUT-EVIDENCE, or REBUT-IMMATERIAL) with sufficient adjustment to bring adjusted severity ≤ 3.
- If even one finding remains above adjusted score 3, EXONERATE is not available. Use `DEFER` or `CONCEDE` on that finding.

---

### Layer 3 — Adjudication (Adjudicator Output)

For each rebuttal, the adjudicator assigns a `point_verdict`:
- `critique_wins`: critic finding stands — adjustment not accepted or insufficient
- `defense_wins`: rebuttal accepted — finding dismissed or severity reduced below threshold
- `empirical_test_agreed`: both parties accepted DEFER — open empirical question

**Threshold rule for point_verdict:**
- If adjusted severity ≤ 3 after rebuttal: `defense_wins` on this point
- If adjusted severity 4–6: adjudicator evaluates quality of justification — `defense_wins` requires explicit design rationale
- If adjusted severity ≥ 7: `critique_wins` unless rebuttal provides direct empirical counter-evidence

**Case verdict derivation from point verdicts:**
- `defense_wins`: max adjusted severity across all points ≤ 3
- `critique_wins`: any point with adjusted severity ≥ 7 and `critique_wins` point verdict
- `empirical_test_agreed`: no point at ≥ 7, but ≥ 1 DEFER point

**Constitutional constraints (cannot be overridden by prompting):**
- Critic: must produce ≥ 1 finding on regular cases (score ≥ 1). If zero findings, evaluation is invalid.
- Defender: EXONERATE verdict requires all advancing findings to have adjusted score ≤ 3.
- Adjudicator: `defense_wins` case verdict impossible if any point has unadjusted severity ≥ 7 and rebuttal_type is `CONCEDE`.

---

## Structured DCR Reference

**Raw DCR** (count-based):
```
DCR = count(CONCEDE labels on defense cases) / count(all rebuttal labels on defense cases)
```

**Severity-weighted DCR** (wDCR — primary):
```
wDCR = sum(original_severity × 1{rebuttal_type == CONCEDE}) / sum(original_severity across all findings on defense cases)
```

**Interpretation:**
- wDCR 0.00 after Intervention B: defender is dismissing all critique points — check for over-correction (EXONERATE on regular cases)
- wDCR 0.30–0.50: healthy range — conceding FATAL findings, dismissing MINOR
- wDCR > 0.70: defender is still capitulating; Intervention B did not activate

**Leading indicator signal:** if Intervention B is working, wDCR drops on defense cases while IDR stays stable on regular cases. A wDCR drop paired with IDR drop is a regression — the defender is dismissing real flaws too.

**FCE — Finding Calibration Error**
Definition: measures whether the critic's severity scores are calibrated against ground truth. Analogous to Expected Calibration Error (ECE) in probabilistic classification.
Formula:
```
FCE = mean over severity bins | P(flaw exists | bin) − empirical flaw rate in bin |
```
Bins: [0–2], [3–5], [6–8], [9–10]. For each bin, compare the fraction of findings in that bin that were on genuinely flawed cases vs. the mean severity/10 (the implicit probability claim).

**What well-calibrated looks like:**
- Score-8 findings should appear on genuinely flawed cases ~80% of the time
- Score-2 findings may appear on both defense and regular cases — appropriately uncertain
- Defense-case findings should cluster in [0–3]; regular-case findings in [6–10]

**What miscalibration looks like:**
- Score-9 findings on defense cases (overconfident false alarms) → high FCE
- Score-2 findings on regular cases with real FATAL flaws (underconfident) → high FCE

**FCE target:** < 0.15 (analogous to acceptable ECE in well-calibrated classifiers). Baseline FCE will be estimated from v7 prompts in Phase 0.5.

**Relationship to other metrics:**
- FCE ↑ on defense cases while CER stays high → critic is overconfident about false alarms
- FCE ↓ after Intervention A → severity gate is inducing better calibration, not just fewer findings
- FCE is the only metric that penalizes the critic for being right by accident (high severity, lucky defense_wins)

---

## Mixed-Case Calibration Metric (Open — Must Define Before Running)

FVC_mixed tracked whether the system appropriately hedged on ambiguous cases. Retiring FVC_mixed without a replacement means over-correction from Interventions A/B/C (system starts outputting `defense_wins` on genuinely ambiguous cases) is invisible.

**Proposed replacement — Ambiguity Recognition Rate (ARR):**
Definition: proportion of mixed cases where the system outputs `empirical_test_agreed` (appropriate uncertainty).
Formula: `ARR = count(empirical_test_agreed on mixed cases) / total mixed case evaluations`
Target: ARR >= 0.60 (must not drop significantly from v7 FVC_mixed of 0.731 on multiround).

Note: ARR rewards hedging on mixed cases (correct behavior) and penalizes confident wrong verdicts on ambiguous cases. This is the inverse of FHR — FHR penalizes hedging on clear cases, ARR rewards it on ambiguous cases. Together they define the calibration corridor.

---

## Leading vs. Lagging Indicators Per Intervention

| Intervention | Leading indicator | Lagging indicator | Regression check |
|---|---|---|---|
| A (critic threshold) | CER on defense cases ↓, FCE on defense cases ↓ | DER ↑ | CER on regular cases stable, FCE on regular cases stable |
| B (defender exoneration) | wDCR on defense cases ↓ | DER ↑ | IDR on regular cases stable |
| C (adjudicator cost model) | Pre-flight checklist length on defense cases ↓ | DER ↑, FHR ↓ | IDR stable |

**FCE as Intervention A's primary diagnostic:** CER tells you whether the severity gate is blocking findings. FCE tells you whether the remaining findings are *correctly confident*. CER could drop because the critic stops reporting everything — FCE confirms whether what remains is well-calibrated. A CER drop without FCE improvement means the critic is removing findings indiscriminately, not applying the severity gate correctly.

If the leading indicator does not move, the prompt change did not activate the intended mechanism. Do not wait for the lagging indicator to confirm failure.
