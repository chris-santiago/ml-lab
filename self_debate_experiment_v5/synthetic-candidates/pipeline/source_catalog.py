# /// script
# requires-python = ">=3.10"
# ///
"""
Source catalog for Stage 1 mechanism extraction.

Defines all 19 source references (16 critique sources + 3 defense patterns)
and the selection algorithm that assigns sources to batch slots.

Code — not the prompt — controls which sources are used and in what quantity.
"""

import random
from typing import TypedDict


class SourceEntry(TypedDict):
    id: str           # e.g. "source_01" or "pattern_d"
    label: str        # e.g. "Source 1 — Dacrema et al. (2019), RecSys"
    source_type: str  # "critique" or "defense"
    flaw_type: str | None
    text: str         # markdown block injected into the Stage 1 prompt


class Assignment(TypedDict):
    mechanism_id: str     # "mech_001"
    source: SourceEntry
    case_type: str        # "critique" | "mixed" | "defense_wins"


class BenchmarkAssignment(TypedDict):
    mechanism_id: str     # "mech_001"
    category: str         # "broken_baseline" | "metric_mismatch" | ...
    flaw_type: str | None # None for defense_wins
    case_type: str        # "critique" | "mixed" | "defense_wins"


# ---------------------------------------------------------------------------
# Benchmark category catalog
# ---------------------------------------------------------------------------

# (category_name, min_per_15, max_per_15, case_type)
BENCHMARK_CATEGORIES: list[tuple[str, int, int, str]] = [
    ("broken_baseline",               2, 3, "critique"),
    ("metric_mismatch",               1, 2, "critique"),
    ("hidden_confounding",            2, 3, "critique"),
    ("scope_intent_misunderstanding", 1, 2, "critique"),
    ("defense_wins",                  2, 3, "defense_wins"),
    ("real_world_framing",            1, 2, "critique"),
]

BENCHMARK_FLAW_TYPES: list[str] = [
    "assumption_violation",
    "quantitative_error",
    "critical_omission",
    "wrong_justification",
]

# Lowest-priority categories to trim when rounding produces excess
_BENCHMARK_DROP_ORDER: list[str] = [
    "scope_intent_misunderstanding",
    "real_world_framing",
    "metric_mismatch",
]


# ---------------------------------------------------------------------------
# Source library
# ---------------------------------------------------------------------------

CRITIQUE_SOURCES: list[SourceEntry] = [
    {
        "id": "source_01",
        "label": "Source 1 — Dacrema et al. (2019), RecSys",
        "source_type": "critique",
        "flaw_type": "critical_omission",
        "text": (
            "### Source 1 — Dacrema et al. (2019), RecSys\n"
            "**Abstract mechanism:** A challenger model is compared to baselines using asymmetric "
            "hyperparameter tuning — the challenger receives tuning, the baselines do not. The claimed "
            "performance gain disappears or reverses when baselines receive equivalent tuning.\n"
            "**Flaw type:** `critical_omission`\n"
            "**Transpose to:** Any model comparison domain where a new complex method is compared to a "
            "legacy baseline — churn prediction, fraud scoring, clinical risk stratification, document classification"
        ),
    },
    {
        "id": "source_02",
        "label": "Source 2 — Obermeyer et al. (2019), Science",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 2 — Obermeyer et al. (2019), Science\n"
            "**Abstract mechanism:** A proxy variable is used to measure an unobservable target quantity, "
            "under the assumption that the proxy-target correlation is uniform across subgroups. The assumption "
            "fails because a systemic factor affects the proxy but not the target differently across subgroups.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Any domain using an observable quantity as proxy for an unobservable target "
            "where the proxy relationship may differ across subgroups — maintenance cost as proxy for equipment "
            "condition, service frequency as proxy for customer need"
        ),
    },
    {
        "id": "source_03",
        "label": "Source 3 — DeGrave et al. (2021), Nature Machine Intelligence",
        "source_type": "critique",
        "flaw_type": "critical_omission",
        "text": (
            "### Source 3 — DeGrave et al. (2021), Nature Machine Intelligence\n"
            "**Abstract mechanism:** A model is trained on multi-site data where site membership is confounded "
            "with label prevalence. No cross-site validation is performed. The model learns site-specific "
            "artifacts as shortcuts to the label.\n"
            "**Flaw type:** `critical_omission`\n"
            "**Transpose to:** Multi-site models — enterprise network monitoring across business units, "
            "manufacturing defect detection across factories, retail fraud trained on merchant-category data"
        ),
    },
    {
        "id": "source_04",
        "label": "Source 4 — Lazer et al. (2014), Science",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 4 — Lazer et al. (2014), Science\n"
            "**Abstract mechanism:** A model assumes that the relationship between behavioral signals and the "
            "target variable is stationary. The signal-generating process changes independently of the target "
            "variable, violating stationarity and producing systematic bias.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Any model trained on user-generated behavioral signals — app usage as proxy for "
            "customer health, click-through as proxy for content quality, support ticket volume as proxy for "
            "product defect rate"
        ),
    },
    {
        "id": "source_05",
        "label": "Source 5 — Zech et al. (2018), PLOS Medicine",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 5 — Zech et al. (2018), PLOS Medicine\n"
            "**Abstract mechanism:** A model trained and evaluated within a single organization is presented "
            "as demonstrating generalization. Site-level confounders invisible to internal validation appear "
            "when the model is deployed externally.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Single-organization models presented as generalizable — HR attrition on one "
            "company's employees, credit default on one lender's portfolio, product failure on one factory's "
            "production line"
        ),
    },
    {
        "id": "source_06",
        "label": "Source 6 — Recht et al. (2019), ICML",
        "source_type": "critique",
        "flaw_type": "critical_omission",
        "text": (
            "### Source 6 — Recht et al. (2019), ICML\n"
            "**Abstract mechanism:** A benchmark is used for iterative model selection over many years. The "
            "models improve on the benchmark but do not improve proportionally on fresh data from the same "
            "distribution, indicating implicit overfit to the benchmark's idiosyncratic properties.\n"
            "**Flaw type:** `critical_omission`\n"
            "**Transpose to:** Any long-lived benchmark used for iterative model selection — leaderboard-driven "
            "competitions, clinical risk scores validated on the same cohort over many years"
        ),
    },
    {
        "id": "source_07",
        "label": "Source 7 — Hooker et al. (2019), NeurIPS",
        "source_type": "critique",
        "flaw_type": "wrong_justification",
        "text": (
            "### Source 7 — Hooker et al. (2019), NeurIPS\n"
            "**Abstract mechanism:** An evaluation protocol for measuring property X modifies the system being "
            "evaluated in a way that changes which property is actually being measured. The justification "
            "describes the intent correctly (measuring X) but the implementation measures a different quantity "
            "(X' ≠ X).\n"
            "**Flaw type:** `wrong_justification`\n"
            "**Transpose to:** Any evaluation where the measurement procedure modifies the system — A/B tests "
            "that change user behavior, benchmark contamination, calibration assessment using calibration "
            "procedure to generate ground-truth labels"
        ),
    },
    {
        "id": "source_08",
        "label": "Source 8 — SMOTE Before Cross-Validation",
        "source_type": "critique",
        "flaw_type": "wrong_justification",
        "text": (
            "### Source 8 — SMOTE Before Cross-Validation\n"
            "**Abstract mechanism:** A data augmentation or preprocessing step is applied to the full dataset "
            "before train-test splitting. Splitting must occur before augmentation for estimates to be unbiased; "
            "the justification describes the correct intent but the implementation order is wrong.\n"
            "**Flaw type:** `wrong_justification`\n"
            "**Transpose to:** Any preprocessing that generates new data before splitting — feature scaling fit "
            "on combined data, augmentation before split, imputation using full-dataset statistics"
        ),
    },
    {
        "id": "source_09",
        "label": "Source 9 — Caruana et al. (2015), KDD",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 9 — Caruana et al. (2015), KDD\n"
            "**Abstract mechanism:** A model is trained on historical outcomes that were shaped by an existing "
            "intervention. High-risk entities received differential treatment that improved their observed "
            "outcomes, so the model learns the treatment selection rule rather than the underlying risk.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Any model trained on historical data where outcomes were affected by an existing "
            "intervention — fraud detection trained on data where suspicious transactions were reviewed and "
            "blocked, predictive maintenance trained where high-risk equipment was proactively replaced"
        ),
    },
    {
        "id": "source_10",
        "label": "Source 10 — Time Series Leakage via Pre-Generated Sequences",
        "source_type": "critique",
        "flaw_type": "critical_omission",
        "text": (
            "### Source 10 — Time Series Leakage via Pre-Generated Sequences\n"
            "**Abstract mechanism:** Derived records (sequence windows, patches, event windows) are generated "
            "from a time-ordered source, and the train-test split is performed on the derived records rather "
            "than on the original source. Adjacent windows from the original sequence appear in both train and "
            "test sets.\n"
            "**Flaw type:** `critical_omission`\n"
            "**Transpose to:** Session-based models from user logs, image patch models from video, event "
            "prediction from longitudinal records"
        ),
    },
    {
        "id": "source_11",
        "label": "Source 11 — Offline-Online Gap in Recommendation Systems",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 11 — Offline-Online Gap in Recommendation Systems\n"
            "**Abstract mechanism:** An offline evaluation uses a static historical dataset where test items "
            "are sampled uniformly from each entity's history. The deployment setting requires predicting future "
            "behavior from past behavior. The evaluation measures reconstruction of a static snapshot, not "
            "forecasting, and the two distributions diverge.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Any static offline evaluation used to justify an online deployment — surrogate "
            "A/B tests trained on historical data, predictive models for future conditions calibrated on past data"
        ),
    },
    {
        "id": "source_12",
        "label": "Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)\n"
            "**Abstract mechanism:** A model is optimized against a surrogate metric (reward model, proxy "
            "target) and evaluated on the same surrogate. The model learns to exploit gaps between the surrogate "
            "and the true objective. The evaluation cannot detect reward hacking that generalizes within the "
            "evaluation distribution.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Any surrogate optimization evaluated by the same surrogate — click-through "
            "optimization evaluated on CTR, safety classifiers fine-tuned on their own outputs, model "
            "compression evaluated on the benchmark it was compressed for"
        ),
    },
    {
        "id": "source_13",
        "label": "Source 13 — Informative Censoring in Survival Analysis",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 13 — Informative Censoring in Survival Analysis\n"
            "**Abstract mechanism:** In time-to-event modeling, observations are censored before the event "
            "occurs. Standard methods assume censoring is independent of the event (non-informative). The "
            "assumption is violated when the censoring mechanism is correlated with event severity — the most "
            "at-risk entities are removed before their event is recorded.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** Equipment lifetime prediction where failing units are taken offline early; "
            "employee attrition where high-risk employees receive retention packages before unplanned departure; "
            "subscription churn where churning users stop logging events before cancellation"
        ),
    },
    {
        "id": "source_14",
        "label": "Source 14 — Aggregated Performance Masking Stratum-Specific Degradation",
        "source_type": "critique",
        "flaw_type": "metric_mismatch",
        "text": (
            "### Source 14 — Aggregated Performance Masking Stratum-Specific Degradation\n"
            "**Abstract mechanism:** A population-weighted aggregate metric is used to justify a deployment "
            "claim of 'works across all populations.' The aggregate is dominated by the majority stratum. "
            "Minority strata perform below any acceptable threshold but are masked by the majority volume.\n"
            "**Flaw type:** `metric_mismatch`\n"
            "**Transpose to:** Multi-warehouse demand forecasting reported as single MAPE; content moderation "
            "across language communities; fraud detection across merchant categories"
        ),
    },
    {
        "id": "source_15",
        "label": "Source 15 — Calibration Circularity in Model Validation",
        "source_type": "critique",
        "flaw_type": "wrong_justification",
        "text": (
            "### Source 15 — Calibration Circularity in Model Validation\n"
            "**Abstract mechanism:** A post-hoc calibration step (Platt scaling, isotonic regression, "
            "temperature scaling) is fitted and evaluated on the same held-out set. The calibration method "
            "was selected because it performed well on that set. The evaluation is circular — the set both "
            "guided the selection and now certifies the result.\n"
            "**Flaw type:** `wrong_justification`\n"
            "**Transpose to:** Any post-hoc adjustment fitted and evaluated on the same set — threshold "
            "selection evaluated on the threshold-selection set, normalization evaluated on the normalization sample"
        ),
    },
    {
        "id": "source_16",
        "label": "Source 16 — Instance-Filtering Bias from Quality-Based Data Curation",
        "source_type": "critique",
        "flaw_type": "assumption_violation",
        "text": (
            "### Source 16 — Instance-Filtering Bias from Quality-Based Data Curation\n"
            "**Abstract mechanism:** Training data is filtered for high-confidence instances using a quality "
            "score. The model is trained and evaluated on the filtered distribution. The deployment distribution "
            "includes all incoming instances (including those filtered out), and performance on the excluded "
            "tail is unknown.\n"
            "**Flaw type:** `assumption_violation`\n"
            "**Transpose to:** NLP models trained on high-agreement annotations; medical imaging trained on "
            "high-quality scans; anomaly detection trained on confirmed labels ignoring ambiguous cases"
        ),
    },
]

DEFENSE_PATTERNS: list[SourceEntry] = [
    {
        "id": "pattern_d",
        "label": "Pattern D — Conservative Evaluation Producing Lower Headline Metrics",
        "source_type": "defense",
        "flaw_type": None,
        "text": (
            "### Pattern D — Conservative Evaluation Producing Lower Headline Metrics\n"
            "**Sound practice:** Using a more demanding evaluation protocol (stricter split, harder test set, "
            "harder baseline) that intentionally yields lower scores than the easier alternative.\n"
            "**False concern surface:** The published number is lower than what the team could have reported. "
            "Critics interpret this as underperformance or a methodological problem.\n"
            "**External knowledge for exoneration:** Harder evaluation protocols are a mark of rigor when the "
            "claim is calibrated to match the evaluation scope. Lower score under correct validation is honest "
            "performance, not weakness."
        ),
    },
    {
        "id": "pattern_e",
        "label": "Pattern E — Nested Cross-Validation Yielding Lower Performance Than Simple CV",
        "source_type": "defense",
        "flaw_type": None,
        "text": (
            "### Pattern E — Nested Cross-Validation Yielding Lower Performance Than Simple CV\n"
            "**Sound practice:** Using nested CV (inner loop for hyperparameter selection, outer loop for "
            "performance estimation).\n"
            "**False concern surface:** The reported performance is lower than simple CV would produce. The "
            "team appears to have found a worse model.\n"
            "**External knowledge for exoneration:** Single-loop CV is the biased estimator. Nested CV is the "
            "correct approach when the same dataset is used for both model selection and performance reporting."
        ),
    },
    {
        "id": "pattern_f",
        "label": "Pattern F — Acknowledged Limitation Properly Scoped to a Narrow Claim",
        "source_type": "defense",
        "flaw_type": None,
        "text": (
            "### Pattern F — Acknowledged Limitation Properly Scoped to a Narrow Claim\n"
            "**Sound practice:** Explicitly identifying a constraint on generalizability and correctly limiting "
            "the deployment claim to within the validated scope.\n"
            "**False concern surface:** The team acknowledges a limitation. Critics treat disclosed limitations "
            "as admissions of fatal flaws or post-hoc goalpost-moving.\n"
            "**External knowledge for exoneration:** In rigorous applied science, explicitly scoped claims are "
            "stronger than vague claims of generalizability. A team that acknowledges 'we do not claim "
            "generalizability to other institutions' is being honest."
        ),
    },
]

ALL_SOURCES: list[SourceEntry] = CRITIQUE_SOURCES + DEFENSE_PATTERNS  # 19 total


# ---------------------------------------------------------------------------
# Source selection algorithm
# ---------------------------------------------------------------------------

def select_sources(
    batch_size: int,
    previous_usage: dict,
    seed: int = 42,
) -> list[Assignment]:
    """
    Select batch_size sources from the catalog and assign case_type to each.

    Args:
        batch_size: Number of cases to generate.
        previous_usage: Dict mapping source label -> number of times used in prior batches.
                        e.g. {"Source 1 — Dacrema et al. (2019), RecSys": 1}
        seed: RNG seed for reproducibility.

    Returns:
        List of Assignment dicts, one per case, ordered by mechanism_id.

    Raises:
        ValueError: If batch_size cannot be satisfied given available sources.
    """
    rng = random.Random(seed)

    # Target: ~35-40% defense_wins, rest critique/mixed
    n_defense = min(round(batch_size * 0.37), len(DEFENSE_PATTERNS) * 2)
    n_critique = batch_size - n_defense

    # Within critique: at least 4 mixed (or all critique if fewer than 4 total)
    n_mixed = min(max(4, round(n_critique * 0.45)), n_critique)
    n_pure_critique = n_critique - n_mixed

    # Build pools respecting "no source used more than 2x" rule
    def build_pool(sources: list[SourceEntry]) -> list[SourceEntry]:
        pool = []
        for src in sources:
            times_used = previous_usage.get(src["label"], 0)
            remaining_uses = max(0, 2 - times_used)
            pool.extend([src] * remaining_uses)
        return pool

    critique_pool = build_pool(CRITIQUE_SOURCES)
    defense_pool = build_pool(DEFENSE_PATTERNS)

    if len(critique_pool) < n_critique:
        raise ValueError(
            f"Cannot select {n_critique} critique sources: only {len(critique_pool)} slots available "
            f"(16 sources × 2 uses, minus prior batch usage). "
            f"Reduce --batch-size or reset --previous-batch-usage."
        )
    if len(defense_pool) < n_defense:
        raise ValueError(
            f"Cannot select {n_defense} defense patterns: only {len(defense_pool)} slots available "
            f"(3 patterns × 2 uses, minus prior batch usage). "
            f"Reduce --batch-size or pass fewer defense slots."
        )

    # Critique sources: unique within a batch (16 sources × 2 cross-batch uses = plenty of headroom)
    def sample_unique(pool: list[SourceEntry], n: int) -> list[SourceEntry]:
        seen_ids: set[str] = set()
        unique_pool = []
        for src in pool:
            if src["id"] not in seen_ids:
                unique_pool.append(src)
                seen_ids.add(src["id"])
        if len(unique_pool) < n:
            raise ValueError(f"Not enough unique critique sources: need {n}, have {len(unique_pool)}")
        return rng.sample(unique_pool, n)

    # Defense patterns: only 3 exist so allow reuse within a batch (sample from full pool)
    def sample_pool(pool: list[SourceEntry], n: int) -> list[SourceEntry]:
        if len(pool) < n:
            raise ValueError(
                f"Not enough defense pattern slots: need {n}, have {len(pool)} "
                f"(3 patterns × 2 cross-batch uses, minus prior usage)"
            )
        return rng.sample(pool, n)

    critique_selected = sample_unique(critique_pool, n_critique)
    defense_selected = sample_pool(defense_pool, n_defense)

    # Assign case_type
    assignments_raw: list[tuple[SourceEntry, str]] = []
    mixed_remaining = n_mixed
    for src in critique_selected:
        if mixed_remaining > 0:
            assignments_raw.append((src, "mixed"))
            mixed_remaining -= 1
        else:
            assignments_raw.append((src, "critique"))
    for pat in defense_selected:
        assignments_raw.append((pat, "defense_wins"))

    rng.shuffle(assignments_raw)

    return [
        Assignment(
            mechanism_id=f"mech_{i + 1:03d}",
            source=src,
            case_type=ct,
        )
        for i, (src, ct) in enumerate(assignments_raw)
    ]


def usage_from_blueprints(blueprints: list[dict]) -> dict:
    """Build a previous_usage dict from an existing stage1_blueprints.json."""
    usage: dict[str, int] = {}
    for bp in blueprints:
        ref = bp.get("source_reference", "")
        if ref:
            usage[ref] = usage.get(ref, 0) + 1
    return usage


def select_benchmark_assignments(
    batch_size: int,
    previous_usage: dict,
    seed: int = 42,
) -> list[BenchmarkAssignment]:
    """
    Allocate batch_size benchmark case slots across categories.

    Args:
        batch_size: Number of cases to generate.
        previous_usage: Dict of "category:NAME" -> count and "domain:..." -> count
                        entries from prior batches (for LLM domain-diversity guidance).
        seed: RNG seed for reproducibility.

    Returns:
        List of BenchmarkAssignment dicts, one per case, ordered by mechanism_id.
    """
    rng = random.Random(seed)
    scale = batch_size / 15.0

    # Start each category at its scaled minimum (floor, min 0)
    counts: dict[str, int] = {}
    for name, min_n, _max_n, _ct in BENCHMARK_CATEGORIES:
        counts[name] = int(min_n * scale)  # floor

    # Fill remaining slots by distributing to categories with headroom
    remaining = batch_size - sum(counts.values())
    while remaining > 0:
        added = False
        for name, _min_n, max_n, _ct in sorted(
            BENCHMARK_CATEGORIES,
            key=lambda c: max(1, round(c[2] * scale)) - counts[c[0]],
            reverse=True,
        ):
            scaled_max = max(1, round(max_n * scale))
            if counts[name] < scaled_max and remaining > 0:
                counts[name] += 1
                remaining -= 1
                added = True
        if not added:
            # All categories at max; force into widest-range category
            counts[BENCHMARK_CATEGORIES[0][0]] += 1
            remaining -= 1

    # Trim excess (can arise from ceiling rounding)
    excess = sum(counts.values()) - batch_size
    for cat_name in _BENCHMARK_DROP_ORDER:
        while excess > 0 and counts[cat_name] > 0:
            counts[cat_name] -= 1
            excess -= 1

    # Build (category, flaw_type, case_type) triples
    flaw_type_counts: dict[str, int] = {}
    triples: list[tuple[str, str | None, str]] = []

    for name, _min_n, _max_n, default_ct in BENCHMARK_CATEGORIES:
        for _ in range(counts[name]):
            if default_ct == "defense_wins":
                triples.append((name, None, "defense_wins"))
            else:
                # Pick flaw type; no type may appear more than 3× per batch
                available = [ft for ft in BENCHMARK_FLAW_TYPES
                             if flaw_type_counts.get(ft, 0) < 3]
                if not available:
                    available = list(BENCHMARK_FLAW_TYPES)
                ft = rng.choice(available)
                flaw_type_counts[ft] = flaw_type_counts.get(ft, 0) + 1
                triples.append((name, ft, "critique"))

    # Upgrade ~35% of critique slots to mixed
    critique_indices = [i for i, (_, _, ct) in enumerate(triples) if ct == "critique"]
    n_mixed = min(max(3, round(len(critique_indices) * 0.35)), len(critique_indices))
    for i in rng.sample(critique_indices, n_mixed):
        cat, ft, _ = triples[i]
        triples[i] = (cat, ft, "mixed")

    rng.shuffle(triples)

    return [
        BenchmarkAssignment(
            mechanism_id=f"mech_{i + 1:03d}",
            category=cat,
            flaw_type=ft,
            case_type=ct,
        )
        for i, (cat, ft, ct) in enumerate(triples)
    ]


def usage_from_benchmark_blueprints(blueprints: list[dict]) -> dict:
    """Build a previous_usage dict from an existing benchmark stage1_blueprints.json."""
    usage: dict[str, int] = {}
    for bp in blueprints:
        cat = bp.get("category", "")
        domain = bp.get("target_domain", "")
        if cat:
            key = f"category:{cat}"
            usage[key] = usage.get(key, 0) + 1
        if domain:
            key = f"domain:{domain}"
            usage[key] = usage.get(key, 0) + 1
    return usage
