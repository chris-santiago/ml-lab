# Evolutionary ml-lab — Per-Problem Contract Design Spec

## 1. Scope

The init-time **contract** for a single evolutionary ml-lab run: the declarative
interface a user fills in to launch a closed-loop, synchronous, generational search
where each candidate design is evaluated by a full ml-lab investigation and a
non-dominated champion set ratchets forward. This spec defines the contract artifact,
its schema, the sub-contracts it pins down (phenotype I/O, objective/dominance,
data/splits, fitness verdict gating), and its launch-time validation. The evolutionary
**engine** that consumes the contract is out of scope here (see Non-goals); this spec
is the seam between user intent and that engine.

## 2. Goals

- Minimum viable contract is **three fields**: `goal.statement`, `data.path`, and at
  least one `[[objective]]`. Everything else has a defensible default.
- The user declares only the **problem** and what "**better**" means. The engine builds
  every design, the generation-0 baseline included.
- **Declarative by default** (TOML). User code is confined to an optional `hooks.py`
  module at two named seams.
- Objective declaration is **generic over a dominance relation**: a single objective
  yields a single champion (total order); multiple objectives yield a Pareto frontier
  (partial order). One engine path, selected by the data shape.
- **Fitness integrity**: every design is evaluated on engine-fixed splits, a sealed test
  holdout is never touched during the run, and the adversarial debate certifies a gain
  before any metric is allowed to rank it.
- **Closed-loop safety**: hard caps on generations and cost, convergence early-stop, and
  fail-fast validation before any agent spawns or any dollar is spent.

## 3. Non-goals

Out of scope for this spec (each has its own spec or already exists):

- The generational loop, genome generator, lineage/phylogeny store, and tabu/lesson store
  — **engine spec**.
- The generation-0 **bootstrap algorithm**. The contract only declares whether to
  bootstrap or warm-start; how the engine synthesizes the baseline is engine-spec.
- ml-lab's internal debate protocol — **already delivered by v8**.
- The headless-session launcher and worktree management — **engine spec**.
- Cross-run portfolio management over multiple problems — **future**.

## 4. System behavior

**At launch**, the engine validates the contract. If invalid, it aborts with specific
errors and **zero spend**. If valid, it seals the test holdout, materializes the CV fold
index files, and establishes the generation-0 champion — either the user's
`baseline.warm_start` or, if absent, an engine-synthesized baseline.

**Per generation** (engine mechanism, governed by this contract): the genome generator
proposes a population from the goal, surviving champions, and accumulated lessons; every
design is run through a full ml-lab investigation; any `empirical_test_agreed` verdict is
handled per `on_empirical_test_agreed`; selection is applied (disqualify hard-constraint
violators → verdict gate → Pareto pass); the champion frontier is updated; and every
eliminated design is distilled into tabu entries and lessons for the next generation.

**Termination**: the run stops at convergence (`converge_after_barren_gens` generations
with no frontier improvement) or when a hard cap (`max_generations`, `max_cost_usd`) is
hit, whichever fires first. **Finally**, the champion frontier is scored once on the
sealed holdout to produce the honest generalization report.

## 5. Architecture

Three artifacts, one consumer:

- **`contract.toml`** — declarative intent. The sole interface between the user and the
  engine. Holds the goal, baseline policy, phenotype I/O sub-contract, objectives, data
  and split policy, fitness verdict policy, run-control limits, and search dynamics.
- **Validator** — a launch-time gate that checks structure, ranges, and cross-references,
  and fails fast before any spend.
- **`hooks.py`** (optional) — the only place user code enters. Two extension points:
  a custom dominance relation and custom genome-generator priors.

The **phenotype I/O sub-contract** defines the design ⇄ engine boundary: a design is a
self-contained PEP 723 `uv` script that reads injected inputs on stdin and emits a metric
JSON on stdout. The champion is the current best such script (or the Pareto set of them).

## 6. Canonical interfaces / data contracts

### Contract file

```toml
[run]
name = "churn-auc-2026"      # run id; names the output/lineage dir
seed = 1337                  # global seed: folds, sampling, reproducibility

[goal]
statement = "Improve AUC on the churn dataset without exceeding 50ms p99 inference."
seed_hypotheses = ["FastText-encode device IDs as features"]   # OPTIONAL

[baseline]
warm_start = "./baseline_gen0.py"   # OPTIONAL. If omitted, engine synthesizes gen-0.

[phenotype]
invoke = "uv run {script}"
stdin  = ["data_path", "train_idx", "eval_idx", "seed", "mode"]   # engine injects
stdout = "metrics_json"             # design emits {"metrics": {...}}

[[objective]]                       # length-1 ⇒ single champion (total order)
metric = "auc"                      # length-N ⇒ Pareto frontier (partial order)
dir    = "max"
[[objective]]
metric   = "latency_p99_ms"
dir      = "min"
hard_max = 50                       # violation ⇒ disqualified, not merely dominated

[data]                              # nested: sealed holdout + inner CV
path         = "./churn.parquet"
test_holdout = 0.15                 # sealed; spent once on the final frontier only
cv_folds     = 5                    # inner CV on the rest; selection metric = CV mean

[fitness]                           # full ml-lab debate on EVERY design
review_mode   = "debate"            # v8-calibrated certifying referee
report_mode   = "conclusions_only"  # per-design; skip report/peer review
pass_verdicts = ["defense_wins"]    # terminal-pass verdicts
on_empirical_test_agreed = "resolve"  # resolve | accept | reject (default: resolve)

[limits]                            # safety rails for the closed, unattended loop
population_per_gen         = 8
max_generations            = 20     # hard cap
max_cost_usd               = 500    # hard cap
converge_after_barren_gens = 3      # early stop: no frontier improvement

[search]
diversity      = "off"              # optional novelty preservation (scalar runs)
max_concurrent = 100                # headless ml-lab sessions in flight

[hooks]
module = "./hooks.py"               # OPTIONAL: dominates(a, b), genome_priors()
```

### Phenotype I/O

Engine injects per invocation (stdin, JSON):

```json
{ "data_path": "./churn.parquet",
  "train_idx": "<fold train index file>",
  "eval_idx":  "<fold eval index file>",
  "seed": 1337,
  "mode": "cv_fold" }              // or "final_test" (champion only)
```

Design emits (stdout, JSON):

```json
{ "metrics": { "auc": 0.834, "latency_p99_ms": 12 } }
```

### Objective → dominance

- Each `[[objective]]` is `{ metric, dir: max|min, hard_max?|hard_min? }`.
- **Hard-constraint violation is disqualification** (the design is removed), distinct from
  being Pareto-dominated.
- `A` dominates `B` iff `A` is at least as good on every objective and strictly better on
  at least one, evaluated on the per-objective CV-mean vector.
- A single objective makes the relation a total order, so the non-dominated set has
  cardinality one — the single champion, with no special case.

### Fitness verdict gate

A design carries a CV-mean metric vector and an ml-lab `case_verdict ∈ {critique_wins,
defense_wins, empirical_test_agreed}`. Selection applies, in order:

1. Disqualify hard-constraint violators.
2. **Verdict gate.** `critique_wins` is killed regardless of metric. `empirical_test_agreed`
   is handled per `on_empirical_test_agreed`:
   - `resolve` (default): run the deferred `evidence_test` for the unresolved finding,
     re-derive the verdict to `defense_wins` or `critique_wins`, then apply the gate.
   - `accept`: treat as a pass, trusting the CV metric.
   - `reject`: discard the design.
   A verdict in `pass_verdicts` (default `["defense_wins"]`) is frontier-eligible.
3. **Pareto pass.** Over surviving designs plus the incumbent frontier, compute the
   non-dominated set on the CV-mean vector. That set is the new champion frontier.

## 7. Invariants and constraints

- **Required surface**: `goal.statement`, `data.path`, and ≥1 `[[objective]]` must be
  present; all else defaults.
- **Sealed test**: the `test_holdout` partition is never read during the run; it is spent
  exactly once, scoring the final frontier.
- **Fold determinism**: CV folds are engine-materialized from `run.seed` and are
  byte-identical across every design in every generation. Comparability is guaranteed by
  the caller, not trusted to the design.
- **Selection is an AND**: a design must both survive the verdict gate and be Pareto
  non-dominated to enter the frontier. Metric without certification, or certification
  without dominance, is insufficient.
- **`critique_wins` always kills.** `empirical_test_agreed` is resolved (default) before
  the gate, never silently accepted.
- **Elitism**: incumbent champions persist until dominated and are not re-debated (folds
  are fixed and they are already certified). The certified frontier score cannot drift
  backward.
- **Failed phenotype**: a design that crashes, times out, emits invalid JSON, or omits a
  declared objective metric goes extinct that generation with its failure logged as a
  lesson. One broken design never stalls a generation.
- **Fail-fast validation**: an invalid contract aborts before any agent spawns or any API
  cost is incurred.

## 8. Key decisions and tradeoffs

- **Phenotype = self-contained `uv` script** (vs. typed config + fixed harness, or
  free-form repo). Chosen for runnable isolation, parallelism without coordination,
  natural versionability, and fit with the repo's PEP 723 convention. The user never
  writes ML code; the engine writes and mutates scripts.
- **Objective = metric vector + directions + hard constraints** (vs. scalar-only, or a
  user comparator). Chosen because it covers scalar as the degenerate length-1 case and
  multi-objective uniformly, with no user code, and the engine stays generic over a
  derived dominance relation. A custom comparator remains available via `hooks.dominates`.
- **Seeding = goal-driven and lean** (vs. user-enumerated population, or charter-bounded).
  The engine invents hypotheses from the goal using its ML priors; seed hypotheses only
  bias generation 1. This is what makes "any ML problem" tractable: a smart mutation
  operator over a small population, not blind sampling.
- **Baseline = engine-synthesized** (vs. required from the user). Generation 0 is the
  engine's job; the user supplies only the problem. A strong existing baseline can still
  warm-start. Generation 0 is the one generation that produces a champion rather than
  competing against one.
- **Fitness = full ml-lab debate on every design** (vs. screen-then-certify, or
  certify-champion-only). Maximal rigor: the adversarial referee vets every candidate, so
  metric can only rank designs already certified non-artifactual. Cost scales as
  population × generations × debate; `population_per_gen` and the budget caps are the
  governors.
- **`empirical_test_agreed` → resolve** (vs. accept or reject by default). Per
  `derive_verdict.py`, this verdict flags a material/FATAL finding that argument could not
  put to rest (`DEFER`, or high residual after `REBUT*`), and case aggregation makes a
  single such finding dominate the whole case — so it will be common. It is a *request for
  a specific experiment*, which an evolutionary engine is uniquely able to run. The CV
  metric does not automatically resolve it (the concern may be leakage or shift the metric
  can't see), so the default runs the deferred test rather than discarding the design or
  trusting the metric.
- **Run control = budget + caps, stop on convergence** (vs. fixed schedule, or
  convergence-first). Hard caps are the runaway backstop for an unattended closed loop;
  convergence is the natural early stop when the strengthening champion baseline lifts the
  bar beyond what new designs clear.
- **Data = sealed outer holdout + inner k-fold CV** (vs. design-controlled splitting, or
  CV with no seal). Nested evaluation: inner CV is the fitness signal the loop optimizes,
  the outer seal is the unbiased final report. The seal is what stops a many-generation
  closed loop from overfitting selection to the test set.
- **Contract form = declarative file + optional hooks** (vs. pure Python module, or pure
  file). Declarative for the inspectable, diffable 90%; a tiny, additive hook surface for
  the two seams that genuinely need code. Keeps configuration and judgment separated.

## 9. Acceptance criteria

- A contract containing only the three required fields validates and launches.
- A contract missing any required field, or declaring an objective `metric` the phenotype
  cannot emit, fails validation with a specific error and zero spend.
- Given an identical contract and seed, any two designs train and evaluate on
  byte-identical fold index files.
- A design violating a `hard_max`/`hard_min` is absent from the champion frontier.
- A `critique_wins` design never enters the frontier, regardless of its metric.
- Under `on_empirical_test_agreed = "resolve"`, an `empirical_test_agreed` design triggers
  the deferred `evidence_test` and verdict re-derivation before any incorporation decision.
- The sealed holdout partition is read exactly once, after termination, scoring the final
  frontier.
- A single-objective contract produces a single champion; a multi-objective contract
  produces a Pareto frontier — through the same selection path.
- The run halts at `converge_after_barren_gens`, `max_generations`, or `max_cost_usd`,
  whichever is reached first.

## 10. Validation strategy

- **Validator unit tests**: presence of required fields; ranges (`test_holdout ∈ (0,1)`,
  `cv_folds ≥ 2`, positive limits); objective well-formedness; objective-metric ⊆
  phenotype-stdout cross-check; `hooks.module` import and declared-symbol presence.
- **Phenotype conformance**: a smoke run of `baseline.warm_start` (or a stub) confirms the
  stdin→stdout contract and that all declared objective metrics are emitted.
- **Determinism**: the same contract and seed produce identical fold index files; the
  sealed-holdout partition is reproducible.
- **Verdict-gate logic**: tested against representative `derive_verdict.py` outputs —
  `defense_wins` passes, `critique_wins` kills, `empirical_test_agreed` routes per policy.
- **Selection semantics**: scalar contract collapses to a size-one non-dominated set;
  hard-constraint violators are excluded; the gate-and-Pareto AND holds.

## 11. Open questions

- **`resolve` cost bound**: resolving `empirical_test_agreed` adds a targeted experiment
  per deferred finding, which can multiply cost. Does this need its own cap
  (e.g. `max_resolve_tests_per_design`), or does folding it into `max_cost_usd` suffice?
  Default assumption: folds into the global budget cap.
- **`search.diversity` semantics**: the interface is named (relevant for scalar runs where
  a size-one frontier offers no built-in diversity), but the novelty-preservation
  mechanism itself is deferred to the engine spec.
