# Scoring

## The Problem with v7 Scoring

v7 used FVC (Flawed Verdict Coefficient): `defense_wins`=1.0, `empirical_test_agreed`=0.5, `critique_wins`=0.0 on defense cases. This has no penalty for being confidently wrong. Hedging is the safe strategy — a system that always outputs `empirical_test_agreed` scores 0.5 everywhere. The scoring function rewards cowardice.

## Penalty-Aware Scoring Function

**Per-case score by stratum and verdict:**

| Case type | `defense_wins` | `empirical_test_agreed` | `critique_wins` |
|---|---|---|---|
| Defense (sound methodology) | +1.0 | −0.25 | −0.5 |
| Regular (flawed methodology) | −0.5 | −0.25 | +1.0 |
| Mixed (ambiguous) | 0.0 | 0.0 | 0.0 |

**Rationale per cell:**
- `empirical_test_agreed` on clear cases: always an experiment recommendation. On stratum-clear cases (defense + regular), that recommendation is unnecessary — penalized at −0.25.
- `critique_wins` on a sound case: false alarm — penalized at −0.5, not just scored 0.
- `defense_wins` on a flawed case: missed a real flaw — penalized at −0.5.
- Mixed cases score 0 for all verdicts. They are diagnostic only — measuring calibration (ARR), not accuracy. This is intentional, not a bug. The system cannot be gamed on mixed cases by guessing.

**Score range:**
- Worst possible (all false alarms on defense, all misses on regular): −0.5
- Pure coward (always hedge): −0.25
- Perfect: +1.0

Hedging now costs −0.25, making it worse than random guessing on clear cases. The system has a reason to be confident.

## Finding-Level Scoring — Separate Critic and Defender Losses

The verdict-level function scores the debate *outcome*. It cannot attribute failure: a critic that raised severity-9 findings and a critic that raised severity-2 findings both produce `critique_wins` and both score −0.5. And a defender that correctly dismissed findings vs. one that capitulated are invisible at the verdict level — both flow into the same case score.

The finding-level layer gives each agent its own Brier loss, computed against the same ground truth.

### Interpretation

Both the critic and defender make probability estimates about the same ground truth:

- **Critic:** `original_severity / 10` = P(genuine flaw at this magnitude)
- **Defender:** `adjusted_severity / 10` = P(genuine flaw remains after defense analysis)
- **Ground truth:** 0 (defense case — no genuine flaw) or 1 (regular case — has flaw)

### Critic Brier Score

```
critic_brier(F_i, stratum) =

  regular case:   +[1 − (1 − original_severity/10)²]    # rewards confident correct findings
  defense case:   −(original_severity/10)²               # penalizes confident false alarms
  mixed case:     not scored
```

### Defender Brier Score

```
defender_brier(F_i, stratum) =

  regular case:   +[1 − (1 − adjusted_severity/10)²]    # rewards not over-reducing real flaws
  defense case:   −(adjusted_severity/10)²               # penalizes failing to dismiss
  mixed case:     not scored
```

**The key difference from the old design:** `defender_brier` uses `adjusted_severity` — the severity after the defender's rebuttal. A defender that correctly rebuts a severity-8 false alarm down to adjusted severity 1 earns near-zero loss. A defender that concedes gets the same penalty as the critic who overclaimed.

### Score Table (Defense Case)

| Original severity | Critic score | After rebuttal (adj sev) | Defender score |
|---|---|---|---|
| 8 | −0.64 | 1 (good rebuttal) | −0.01 |
| 8 | −0.64 | 8 (conceded) | −0.64 |
| 4 | −0.16 | 0 (REBUT-IMMATERIAL) | 0.00 |
| 4 | −0.16 | 4 (conceded) | −0.16 |
| 2 (MINOR) | −0.04 | 1 (brief REBUT-IMMATERIAL) | −0.01 |
| 2 (MINOR) | −0.04 | 2 (conceded) | −0.04 |

NIT findings (score 0) are suppressed before forwarding — no Brier loss in either direction.

### Aggregation: Finding-Level Ground Truth (Primary Path)

v8 benchmark cases are **designed** — each regular case was built to test a specific flaw, recorded in the case metadata:

```json
{
  "must_find": "signal leakage between train and evaluation sets",
  "correct_position": "critique_wins",
  "flaw_category": "signal_leakage"
}
```

This gives **finding-level ground truth**, not just bag-level. Each critic finding can be matched against `must_find`:

- **Matches `must_find`:** `y = 1` — the real flaw
- **Does not match:** `y = 0` — spurious (false alarm on a regular case)

With per-finding `y`, standard **mean pooling** applies across all findings for both critic and defender:

```
critic_case_score   = mean(critic_brier(F_i, y_i)   for all findings)
defender_case_score = mean(defender_brier(F_i, y_i) for all findings)
```

This is strictly more informative than bag-level MIL: the critic is penalized for high-severity spurious findings on regular cases, rewarded for finding the right flaw at high severity. The defender is rewarded for dismissing spurious findings and penalized for dismissing the real one.

**Matching method:** use structured flaw category tags (from the 16-category taxonomy in CASES.md) for deterministic exact-match. Avoid semantic matching via LLM — it adds another model to the scoring chain and makes the scorer non-deterministic.

**Defense cases** are unchanged — all findings have `y = 0` (no genuine flaw), mean pooling.

---

### Aggregation: MIL Fallback (When Finding-Level Ground Truth Unavailable)

For cases without `must_find` metadata, or if the matching step is unreliable, fall back to bag-level supervision using MIL pooling:

**Defense cases — mean pooling:** all findings are false alarms; mean Brier score across findings.

**Regular cases — max pooling for critic, mean pooling for defender:**
- *Critic max pooling:* `critic_case_score = max(critic_brier(F_i))` — rewards the critic for finding at least one high-severity flaw, without penalizing for additional findings whose per-instance ground truth is unknown. Derived from the MIL bag assumption: a bag is positive if at least one instance is positive.
- *Defender mean pooling:* the defender should not over-reduce any finding on a regular case. Mean pooling penalizes false rebuttals regardless of which finding is targeted.

**When to use this path:** unstructured or free-text benchmark cases, third-party case libraries, or cases where `must_find` was not recorded at generation time. Flag these cases in results — MIL-scored cases have wider Brier variance than finding-level-scored cases and should be reported separately if mixed.

### Combined Scoring Function

```
case_score = w_v × verdict_score
           + w_c × agg(critic_brier per finding)
           + w_d × agg(defender_brier per finding)
```

Starting weights: `w_v = 0.50`, `w_c = 0.25`, `w_d = 0.25`

**Weight rationale:** verdict accuracy is still the primary signal, but each agent now has equal finding-level accountability. Weights are starting points — recalibrate after Phase 0.5 once the relative variance of each component is known.

**Intervention-to-loss mapping:**

| Intervention | Primary loss target | Expected direction |
|---|---|---|
| A — critic severity threshold | `critic_brier` on defense cases | ↑ (less overclaiming) |
| B — defender exoneration path | `defender_brier` on defense cases | ↑ (less conceding) |
| C — adjudicator cost model | `verdict_score` | ↑ (fewer false hedges) |

If Intervention A runs and `critic_brier` improves but `defender_brier` stays flat, the critic is calibrating but the defender still capitulates — a precise diagnosis. Previously both signals were entangled in a single finding score.

**Combined score range (defense case):**
- Best: critic severity low, defender rebuts well, verdict `defense_wins` → near +1.00
- Worst: critic severity 9, defender concedes, verdict `critique_wins` → −0.50 − 0.81×0.25 − 0.81×0.25 ≈ −0.91
- Hedge with low-severity findings: verdict `empirical_test_agreed`, severities 3/2 → −0.25 − small penalties ≈ −0.28

### Severity Clamp

Score 10 is reserved for flaws empirically observed to cause wrong results — not inferred or hypothesized. This keeps the squared penalty from creating an extreme cliff at the top of the scale.

**Prompt language (add to Intervention A):**
> "Severity 10 is reserved for flaws you can trace to an observed wrong result in the PoC output. Inferred or plausible flaws max out at severity 9."

### Interaction with Stability Weighting

All three components (verdict, critic Brier, defender Brier) are computed per run, averaged across runs, then multiplied by VS:

```
weighted_case_score = mean(case_score across runs) × VS
```

High variance in adjusted severity across model draws (one defender model concedes, another rebuts) is absorbed by VS. A defender that consistently rebuts across all 3 model draws gets full stability credit.

---

## Stability-Weighted Scoring

Raw scores are multiplied by verdict stability across model draws:

```
weighted_score(case) = raw_score(case) × VS(case)
```

Where VS = fraction of runs agreeing with majority verdict (3:0 → 1.0, 2:1 → 0.67, all different → 0.33).

**Effect:** A stable correct verdict gets full credit. A lucky correct verdict with high model-draw variance gets discounted. This prevents prompt changes that happen to get the right answer for the wrong reasons from appearing as improvements.

**DER with stability weighting:**
```
weighted_DER = mean(raw_score × VS) across defense cases
```

This is the primary metric for the iteration loop.

## v7 Comparability — Critical Prerequisite

The v7 scoring function (FVC) is not comparable to the penalty-aware function. Claiming "DER improved from 0.00" requires re-running the v7 prompts through the new scoring function first. Without this, the baseline is on a different scale.

**Pre-run step:** Before the first canary iteration, run v7 prompts (no changes) on the v7 benchmark cases under the new scoring function. Record the new baseline scores for DER, IDR, FHR, ARR. These become the v8 comparison points, not the v7 FVC-based results.

## Statistical Interpretation of DER 0.30

With 40 defense cases × 3 runs = 120 evaluations, at target DER 0.30:
- Point estimate: 36 defense_wins out of 120
- Standard error: `sqrt(0.30 × 0.70 / 120)` ≈ 0.042
- 95% CI: approximately [0.218, 0.382]

The lower bound of the confidence interval barely clears 0.22. This is a wide band.

**Open question:** Is DER > 0.30 (point estimate) the right target, or should the target be defined such that the lower CI bound clears a meaningful threshold (e.g., lower bound > 0.25)?

**Practical implication:** With n=120, a result of DER = 0.32 and DER = 0.28 are not distinguishable from each other. The iteration loop should treat canary-set differences of < 0.05 as noise, not signal. Define a minimum meaningful delta (MMD) of 0.05-0.10 before the loop starts.

## Minimum Meaningful Delta (MMD)

For the canary iteration loop (n=40 cases × 3 runs = 120 evaluations per condition):

| Metric | MMD |
|---|---|
| DER | 0.08 (approximately 2 SE) |
| IDR | 0.05 |
| FHR | 0.05 |
| ARR | 0.05 |

Changes smaller than the MMD are within noise and should not trigger acceptance or rejection. Require at least MMD improvement in the primary metric before accepting a prompt change.
