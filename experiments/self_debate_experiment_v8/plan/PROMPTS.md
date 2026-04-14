# Prompts

## Baseline Audit

### Critic (ml-critic.md, 106 lines)

**Goal (Mode 1):** "Identify every claim the PoC makes implicitly but has not tested." — Exhaustive enumeration. No significance filter.

**Structure:** Numbered findings organized by root cause, not severity. No severity classification required.

**Instruction ratio:**

| Type | Count |
|---|---|
| Exhaustive enumeration pressure | ~10 ("every claim," 8 what-to-critique bullets) |
| Noise prevention / significance filter | ~3 (buried in persona calibration) |
| Exoneration exit with output format | 0 |

**Key weakness:** Persona calibration (lines 103-105) has good anti-noise instructions ("if you cannot find fundamental flaws, say so," "a short critique is more valuable than a long one that manufactures concerns") but these fight the main goal and lose. The goal is structural; persona calibration is advisory.

---

### Defender (ml-defender.md, 93 lines)

**Concession instructions (5):**
- Line 31: "Concede — the critique is correct."
- Line 49: "Concede — the critic's sharpened argument is convincing."
- Line 57: "You must concede when the critic makes a genuinely good point."
- Line 76: "If it didn't, concede."
- Line 89: "If the critic identifies a genuine flaw, concede immediately."

**Exoneration instructions:** 0.

**Anti-exoneration (line 35):** "...your overall verdict must be `empirical_test_agreed` or `critique_wins` — not `defense_wins`." The only mention of `defense_wins` is a prohibition.

**Hidden bias (line 26):** Implementation soundness check runs before any defense analysis. The defender scans for implementation problems before reading the first critique point. Primes toward finding issues.

**Instruction ratio:**

| Type | Count |
|---|---|
| Concession instructions | 5 explicit |
| Exoneration instructions | 0 |
| `defense_wins` mentions | 1 — prohibition only |

---

### Adjudicator (ml-lab.md, Step 5 orchestration)

**Resolution logic:** After each debate round, the orchestrator checks whether each point is resolved:
- Critique wins — defender conceded
- Defense wins — critic conceded
- Empirical test agreed — both agree on a test
- Unresolved — another round

**Force-resolve (line 357):** "Force-resolve any remaining unresolved points as 'empirical test required' — the safest default when theoretical argument cannot converge." No cost evaluation. No severity filter. Always defaults to experiment recommendation.

**Pre-flight extraction:** Extracts "every item with verdict `Concede` or `Rebut (partial concede)`" for the checklist. No severity filter — a NIT concession generates the same checklist item as a FATAL concession.

**Instruction ratio:**

| Type | Count |
|---|---|
| Paths to `critique_wins` / `empirical_test_agreed` | 3 |
| Paths to `defense_wins` | 1 (only if critic explicitly concedes) |
| Cost evaluation before experiment recommendation | 0 |
| Significance filter on concessions | 0 |

---

## Interventions

### Intervention A — Critic Significance Threshold

**Target:** Mode 1, after the numbered findings structure, before the artifact line.

**Add:**
> "After producing your numbered findings, classify each:
> - **FATAL** — invalidates conclusions if unaddressed
> - **MATERIAL** — weakens a central claim but does not invalidate
> - **MINOR** — worth noting, does not affect the main verdict
> - **NIT** — stylistic, theoretical, or edge case
>
> Include FATAL, MATERIAL, and MINOR findings in CRITIQUE.md. Suppress NIT findings — they are logged internally but require no rebuttal and carry no weight in adjudication. If all findings are NIT, output a single line: 'No findings above NIT threshold identified.' This is a valid and important critique result — not a failure to find problems."

**What this does:** Gates only NIT findings — purely stylistic or hypothetical observations. MINOR findings advance so the defender can explicitly dismiss them, building a complete exoneration record. NIT suppression still forces the critic to self-calibrate and prevents purely theoretical concerns from cluttering the debate. The adjudicator's pre-flight filter (Intervention C) is responsible for ensuring MINOR concessions do not generate PENDING checklist items.

**Leading indicator:** NIT-suppression rate on defense cases — fraction of findings classified NIT and suppressed. If suppression rate is near zero, the critic is not applying the gate. CER (proportion of non-NIT findings) should stay informative on both defense and regular cases; a CER near 1.0 on defense cases after Intervention A means the critic is still over-classifying — a calibration problem requiring a separate diagnostic pass.

---

### Intervention B — Defender Exoneration Path

**Two additions.**

**Addition 1 — Pass 2 verdict selection:** After the existing Concede / Rebut / Mark as empirically open options, add:

> "**Exonerate** — if after rebuttal ALL advancing findings have adjusted severity ≤ 3 (no FATAL or MATERIAL finding survives), your verdict MUST be `defense_wins`. MINOR findings that you have rebutted with REBUT-IMMATERIAL or REBUT-SCOPE qualify automatically. Do not hedge to `empirical_test_agreed` when no material finding survives rebuttal. Recommending an unnecessary experiment when the methodology is sound wastes resources and trains users to ignore the system."

**Addition 2 — Persona calibration:** Add one line after the five concession instructions:

> "If the critic raises only minor concerns or theoretical edge cases, dismiss them firmly and label your verdict `defense_wins`. Conceding to immaterial critique is not rigor — it is the same failure mode as a false alarm, just from the defender's side."

**What this does:** Balances 5 concession instructions with explicit exoneration guidance. Creates a path to `defense_wins` where none existed.

**Leading indicator:** DCR drops on defense cases. If DCR drops but DER stays flat, the adjudicator is overriding correct defender verdicts — Intervention C is next.

---

### Intervention C — Adjudicator Cost-Weighted Logic

**Three targets, ordered by leverage.**

**Target 2 (highest leverage) — pre-flight significance filter:**

Add before compiling the pre-flight checklist:

> "Before adding a concession to the pre-flight checklist, evaluate its severity. MINOR and NIT concessions are logged as INFORMATIONAL — they are noted but do not generate experiment requirements or PENDING checklist items. Only FATAL and MATERIAL concessions become PENDING items. If the defender conceded on a minor point, that concession does not constitute evidence of a methodology flaw requiring experimental resolution."

**Target 1 — force-resolve rule:**

Replace: "Force-resolve any remaining unresolved points as 'empirical test required'"

With: "Force-resolve remaining unresolved points based on the severity of the contested claim: if FATAL or MATERIAL, force-resolve as 'empirical test required.' If MINOR or NIT, force-resolve as 'defense wins' — a debate that cannot converge on a minor point has not identified a methodology problem worth testing."

**Target 3 — experiment proposal gate:**

Add before any empirical test is proposed:

> "Before proposing an experiment, answer: if this experiment runs and confirms the critique, does it change the recommendation? If the answer is no — the finding is too minor to affect conclusions regardless of experimental outcome — do not propose the experiment. Mark the point resolved as 'defense wins' and note: 'finding below experiment threshold.'"

**Leading indicator:** Pre-flight checklist length on defense cases drops. Directly observable from structured output before scoring.

---

## Intervention Ordering

Run in sequence: **A → B → C**. Never combine interventions in a single canary run.

**Rationale:** A feeds B feeds C. A critic that self-prunes to FATAL/MATERIAL gives the defender less to concede. A defender that correctly dismisses minor findings gives the adjudicator fewer concessions to escalate. Each layer reduces noise load for the next. Running them in order lets you measure the marginal contribution of each.

**If A and B both show canary improvement:** Do not combine before running C. Test C in isolation against the A+B combined baseline. Only combine all three for the full benchmark run.

---

## Prompt Changelog Template

```
Version:       [agent]-v{N}           e.g. defender-v3
Change:        {one-sentence description of what text changed}
Hypothesis:    {which failure mode this addresses}
Interaction:   {which existing instructions this change interacts with}
Canary DER:    {before} → {after}
Canary IDR:    {before} → {after}
Canary FHR:    {before} → {after}
Canary ARR:    {before} → {after}
Leading indicator moved: yes / no
Verdict:       ACCEPT / REJECT
Journal ID:    {entry id}
```

For multi-prompt changes (A+B combined):
```
Version:       combined-A+B-v{N}
Changes:       [list each change]
...
```

---

## Acceptance Criteria (Open — Thresholds TBD)

**Current definition (insufficient):** "Accept if primary metric improves without regressions."

**Required definition before starting:**

| Metric | Minimum improvement to accept | Maximum regression to accept |
|---|---|---|
| DER (primary) | ≥ 0.08 (1 MMD) | — |
| IDR | — | ≤ 0.05 drop |
| FHR | — | ≤ 0.05 increase |
| ARR | — | ≤ 0.05 drop |

Note: with n=40 canary cases, most differences are not statistically significant. Use MMD (minimum meaningful delta from SCORING.md) as the threshold, not statistical significance. Statistical significance is assessed at the full benchmark run only.

**Prompt holism note:** Track which existing instructions interact with each change. A new instruction that counterbalances 5 existing instructions is not equivalent to a standalone addition. Document interaction surface in each changelog entry.
