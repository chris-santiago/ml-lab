# ml-lab Metaflow-Pipeline Integration Design Spec

## 1. Scope

Extract a reusable Metaflow-pipeline standard into the ml-lab plugin so that any investigation which outgrows a single-cell proof-of-concept is *promoted* onto a config-driven Metaflow flow that cannot drift from the verified toolchain wiring and reproduction-fidelity rules. The standard is derived from — but genericized away from — a validated reference build (the PAUCAtBudgetLoss flow). Integration adds a promotion step to the existing 13-step investigation workflow plus a small bundle of authoring assets and two enforcement mechanisms (a deterministic linter, a judgment reviewer). The defining constraint: strictness is concentrated in the small invariant core where prose-only guidance demonstrably fails, and generosity is preserved everywhere the investigation legitimately varies. This is design only; building the artifacts is a follow-up.

## 2. Goals

- A promoted investigation starts from the invariant shell + component contract + a readable reference flow, and **cannot drift** from the load-bearing wiring (repo-src path, Hydra↔Metaflow `Config` wiring, lazy-metaflow import guard).
- Best-practice enforcement is **wired, not optional**: a deterministic lint and a judgment review run as a gate on every promoted flow, the same way the existing workflow mandates adversarial critique.
- The promoted flow is a **single source of truth**: it embodies only the final, debated methodology and never validates against or carries forward the throwaway PoC's numbers or assumptions.
- The flow's reproducibility is a **declared determinism contract** the prove layer verifies — not a reproduce-the-PoC check.
- The durable, reusable surface — the `experiment/` config schema, the component-role contract, and the data-axis/training-axis split — is pinned as a contract that survives any specific domain.
- Quick single-cell PoCs remain **untouched**: no Metaflow tax on a hypothesis that only needs one number.
- Enforcement guards **invariants and declared determinism**, never a specific DAG shape: a legitimately different flow shape still passes if it honors the invariants.

## 3. Non-goals

- Building the five artifacts (this spec drives a plan + subagent build).
- A monolithic fill-in `flow_template.py`, a runnable toy investigation, or any rot-prevention machinery (CI, smoke test).
- Hydra multirun / `Runner` launcher; cloud or remote execution; `@pypi`/`@conda` environments.
- Modifying the PAUC reference build itself.
- Replacing the minimal Step-1 PoC with a flow.
- A reproduce-the-PoC gate. The PoC is throwaway debate fodder; validating against it would enshrine pre-debate assumptions and carry potentially-wrong work into the source-of-truth pipeline. The investigation journal owns the audit trail of abandoned assumptions; the flow does not.

## 4. System behavior

**Below the promotion threshold.** The investigation workflow is unchanged. Step 1 produces a single-script PoC that runs in one command and produces a number. No flow, no `conf/`, no Metaflow.

**At promotion.** After the experiment plan is fixed (the workflow's design/experiment-planning steps), the orchestrator judges whether the investigation has outgrown one cell. The **default signal** is "more than one cell, or more than one analysis/diagnostic." This is a recommendation in workflow prose, **not a hard rule** — the orchestrator may promote earlier or stay ad-hoc when judgment warrants. On promotion, the orchestrator invokes the promotion skill, which:

- stamps the authoring bundle (shell snippet, reference flow, component contract, `conf/` scaffold) into the investigation directory;
- migrates the PoC's data-generation, training, and metric logic into the component-role seams;
- preserves the canonical investigation artifacts (the hypothesis document and the append-only investigation log); the Metaflow datastore supersedes loose `stats_*.json` / `results_*.jsonl` result files.

**On every promoted flow, before it is run.** A deterministic linter runs and a judgment reviewer is dispatched as a **blocking gate**. The flow is not run until both pass (or the user explicitly overrides a finding).

**Prove phase (determinism).** The flow declares a reproducibility contract (`experiment.determinism`: `order_independent` | `single_worker` | `nondeterministic`); the prove layer verifies the flow holds the contract it declared by diffing two runs' aggregated outputs. It validates the flow against itself, never against the PoC. The escape hatch (`nondeterministic`) is an explicit, recorded declaration for experiments that genuinely cannot be deterministic under parallelism (e.g. gensim in the ATO investigation). The experiment's *findings* are certified by the existing ml-lab machinery (verdicts, baselines, bootstrap CIs, debate, peer review), not by this gate.

**What the user sees.** For a one-number hypothesis: today's experience, unchanged. For a multi-cell hypothesis: a scaffolded flow they (or the agent) fill at the component seams, a lint/review gate that catches fidelity traps at authoring time, and a one-command determinism check.

## 5. Architecture

Five artifacts, all inside the ml-lab plugin, organized by the per-seam treatment in §6:

- **A promotion skill** (orchestrator-invoked) that owns scaffolding and the authoring guidance (when to promote, the canonical DAG as a default, the seam treatments). It carries the deterministic linter and the authoring-asset bundle.
- **An authoring-asset bundle**: (a) the strict shell snippet, (b) an annotated, non-runnable reference flow, (c) a component-contract document, (d) a `conf/` scaffold plus its schema documentation (config contract + run output contract).
- **A deterministic lint** that statically detects mechanical anti-patterns, plus a small **determinism-check** helper (the prove layer) that diffs two runs' aggregates against the declared contract.
- **A judgment-reviewer agent** dispatched as the blocking gate for the fidelity traps that require reading intent, not pattern-matching.
- **A modification to the orchestrator workflow** that inserts the promotion step and wires the lint + review + determinism gate.

**Where computation lives.** All torch/training work lives in the flow's `train` step. Analyses consume `train` artifacts and never retrain. The bootstrap/paired-lift aggregation lives in the flow's `aggregate` step. The lint is pure static analysis (no execution). The reviewer reads source + the investigation's source-of-truth and reasons; it does not run the flow. The determinism-check uses the Metaflow client to pull two runs' aggregate artifacts and diff them for equality, gated by the declared determinism contract.

**Division of responsibility.** Deterministic checks are scripts; judgment is an agent prompt — the same boundary the plugin already uses for its other deterministic helpers vs. its critic/defender agents.

## 6. Canonical interfaces / data contracts

Genericization works by **roles + a config-named registry**: config names a plugin, the flow dispatches to it. The five seams and their durable contracts:

### Seam 1 — Toolchain shell (strict, copyable; 100% invariant)
Fixed wiring every promoted flow copies verbatim: PEP 723 inline-dependency header; a `sys.path` insert of the repo source root **anchored to `__file__`** (not CWD); the Hydra→Metaflow `Config(parser=…)` wiring that composes config groups; a lazy-metaflow import guard so the module imports for unit tests without Metaflow installed. Carries a single version-stamp comment ("verified against metaflow 2.19.x"). Prose-only guidance is insufficient here by direct evidence (script-mode import failure and CWD-relative `Config` default both broke in the reference build).

### Seam 2 — DAG skeleton (default shape, not a mandate)
Canonical spine:
```
start → foreach(dataset) → train → join → [select_by_val?] → aggregate
      → branch(an_1 … an_k) → join_analyses → report → end
```
- `select_by_val` is **optional** — present only when methods carry internal sweeps requiring validation selection.
- The analysis branch set `an_1 … an_k` is **domain-specific** in count and content; the reference shows ≥2 branches and the author adds/removes.
- **Invariants the skeleton enforces** (these, not the specific DAG, are what lint/review check):
  - train→analyze separation: diagnostics consume `train` artifacts, never run inside `train`;
  - dataset-keyed `foreach` with the data-axis/training-axis split (Seam 4);
  - a `join` after a model-carrying branch reads `inputs[0]` and never `merge_artifacts` over an `nn.Module`;
  - `aggregate` owns the bootstrap and the paired lifts.

### Seam 3 — Component-role contract (signatures you implement; bodies live in the reference)
```
make_data(data_spec, data_axes, seed)            -> Dataset
build_model(model_spec)                          -> nn.Module
train_arm(method_spec, data, seed, train_cfg)    -> TrainResult(model, scores, val_score)
        # dispatched on method_spec.kind (registry pattern)
metric(scores, labels, **cfg)                    -> float
```
- `metric` **binds to the workflow's existing primary-evaluation-metric** (collected before any code is written) — it is not a new concept, only a code home for it.
- **Library-provided (generic, not seams):** the bootstrap-CI routine and the per-config **record schema** (what each trained config emits).
- **Diagnostics** (gradient-mass, representation-probe, etc.) are **DAG analysis branches (Seam 2)**, not reusable components.

### Seam 4 — `conf/` schema (the durable crown jewel)
Generic config-group names: `data/`, `method/`, `experiment/`, `training/`. The `experiment/` group is the most durable artifact and pins these keys:
```
name, axes, data_axes, methods, method_overrides,
split_convention, diagnostics, requests_model, requests_scores, determinism
```
- **`determinism`** declares the flow's reproducibility contract (`order_independent` default | `single_worker` | `nondeterministic`); the prove layer verifies the flow holds it. The flow echoes the value as a run artifact.
- **Data-axis vs training-axis split** (the subtlest generic mechanism): each axis is tagged data-affecting or training-affecting. The `foreach` keys on `(data_axes + seed)`, so the dataset is generated **once per branch** and every method sharing it trains in-process.
- **Axis-agnostic vs axis-dependent methods** (generalizes the reference's budget-agnostic/-dependent arms): classified by `method.kind`. An axis-agnostic method (a plain baseline) trains **once** and is evaluated across all training-axis values; an axis-dependent method retrains per value. **Raise on an unknown `kind`** — never silently default the classification.
- This split is simultaneously a performance win (no redundant data-gen, fewer branches) **and** a fidelity guarantee (axis-agnostic methods train exactly once, matching ad-hoc originals).
- **Merge priority:** the `training/` group is authoritative over any method-specific `epochs`/`lr`/`batch`; a `method/` config carries only method-specific parameters.

**Run output contract — the SSOT read-surface (pinned in `conf/SCHEMA.md`).** A finished promoted run exposes its results in a pinned shape so the `report` step, the `an_*` branches, the determinism-check, and any human reading the run via the Metaflow client can find the conclusions **without reading flow code**. The config schema pins what goes *in*; this pins what a trustworthy finished run exposes *out*. Generic field names (the reference's `arm`/`coverage` become `method`/`<primary_metric>`):
```
aggregate.lift_results     -> [{cell: dict, lift_mean, lift_lo, lift_hi, ci_excludes_zero: bool, n_seeds}]
aggregate.aggregate_results-> [{cell: dict, method: str, <primary_metric>_mean}]
an_<name>.an_result        -> {experiment, rows: [...]}   # or {result: {...}} for scalar diagnostics
determinism                -> str   # the declared contract, echoed as a run artifact
```
- `cell` is the canonicalized `(data_axes + seed)`/training-axis key. `method` replaces the reference's `arm`. `<primary_metric>_mean` binds to Seam 3's `metric`.

### Seam 5 — Fidelity rules (guidance + lint + review; not code)
- **Mechanical (deterministic lint):** module-global constants driving experiment behavior; per-config `foreach` grain; an `nn.Module` reaching `merge_artifacts`; a CWD-relative `Config` default; a bare project-package import under script mode.
- **Judgment (reviewer agent):** split convention (sequential vs independent data-generating streams); per-epoch reshuffle symmetry across all methods; experiment axes matching the source; same-name/different-quantity metrics (e.g. fraction-of-band-that-is-decoy vs fraction-of-decoys-in-band); per-experiment sweep-override inflation (validation selection where the source used a single fixed config).

### Enforcement: the prove layer (determinism gate — not a seam)
The four-layer model is **prevent → lint → review → prove**. Prevent/lint/review map to Seams 1–5. The **prove** layer is the determinism gate, a generic `determinism-check` helper (not a per-investigation seam):
- **What it does:** pulls two runs' aggregate artifacts via the Metaflow client and diffs them for exact equality (order-insensitive over cells), gated by the run's declared `experiment.determinism`. It validates the flow **against itself**, never against the PoC.
- **Contract semantics:** `order_independent` → identical across worker counts (run at two `--max-workers`); `single_worker` → identical run-twice at one worker (cross-worker not claimed); `nondeterministic` → gate self-skips (the explicit, recorded escape hatch for genuinely-nondeterministic dependencies such as gensim).
- **No PoC anchor, no `TARGETS`.** There is no reproduce-the-PoC comparison (see §3). The experiment's findings are owned by the existing ml-lab verdict/baseline/CI/debate/peer-review machinery; the determinism gate only proves the pipeline's numbers are execution-invariant as declared.
- **Generic, not copied per investigation.** The helper ships once in the plugin (`scripts/determinism-check.py`); the only per-investigation surface is the one-line `determinism` declaration in the experiment config.

## 7. Invariants and constraints

- **Strictness only in the invariant core.** The verbatim-copy surface is the shell (Seam 1) and the enforced skeleton invariants (Seam 2). Everything domain-specific is contract + example, never a fill-in template.
- **Enforcement guards invariants + declared determinism, never a DAG shape.** A flow with a legitimately different shape passes if it honors the Seam-2 invariants, lints clean, reviews clean, and holds its declared determinism contract.
- **Promotion is judgment-triggered, never forced.** The threshold is a default signal in prose; the orchestrator decides.
- **Separate-repo constraint.** ml-lab is a standalone public plugin and cannot point at the gitignored, domain-specific reference build; it ships its own genericized reference.
- **uv-native.** Dependencies via PEP 723 inline metadata; no `pip install` step.
- **Determinism is a declared contract, exact-equality checked.** The flow declares `order_independent` / `single_worker` / `nondeterministic`; the gate verifies the declared contract holds by exact aggregate equality across two runs (no tolerance — nondeterminism produces real differences). The escape hatch keeps an honestly-nondeterministic experiment (e.g. gensim under parallelism) from being falsely invalidated.
- **The agent never executes the reference flow.** "Runnable" is therefore not a requirement; drift against the Metaflow API is caught when a real investigation's flow is first run (and by the determinism gate on every real investigation).

## 8. Key decisions and tradeoffs

- **Promotion step, not Step-1 replacement.** Replacing the minimal PoC with a flow would tax every quick hypothesis and contradict the PoC's purpose. A judgment-triggered promotion preserves cheap PoCs while preventing the script-sprawl that motivated the standard. Rejected: scaffold-at-Step-1 (too heavy for one-number checks); opt-in-only skill (no "throughout all experiments" guarantee).
- **Per-seam treatment, not a monolithic template.** Investigations are heterogeneous; a fill-in flow would cage them. Treatment is matched to each seam's invariance: strict snippet where identical everywhere, contract + example where domain-specific, guidance + gate where the concern is a correctness judgment. Rejected: one `flow_template.py` (straitjacket; also dead code that rots).
- **No runnable toy / no rot machinery.** The agent reads the reference, never runs it, so "runnable" buys it nothing; rot against the Metaflow API surfaces when any real investigation's flow is first run, so a dedicated smoke test would duplicate an existing check at the cost of dragging heavy ML deps into a prompt repo's CI. Residue: a version-stamp comment as a breadcrumb. Rejected: runnable CI'd toy investigation.
- **No reproduce-the-PoC gate (the design's central correction).** The original PAUC build had a `validate.py` that reproduced a complete *independently-produced* prior table — porting fidelity. In a fresh ml-lab promotion the only prior artifact is the throwaway single-cell PoC, and promotion *migrates its code into the seams*, so anchoring a gate to it (a) enshrines the pre-debate assumptions the critic/defender phase exists to overturn, (b) anchors fidelity to the least-rigorous artifact, and (c) is circular (shared code reproduces its own bug). The flow is a single source of truth that should contain only final validated methodology; the journal owns the audit trail of bad assumptions. Rejected: anchor reproduction / `TARGETS` / `validate.py`.
- **Four-layer enforcement mirrors the existing critique gate.** Prevent (template) → Lint (deterministic) → Review (judgment) → Prove (determinism contract). The lint/review split follows the global "deterministic logic → script, judgment → prompt" rule; reusing the gate pattern the workflow already mandates makes enforcement non-optional without new ceremony.
- **Generic group names over the reference's vocabulary.** `data`/`method` rather than the domain's `geometry`/`arm`, because the standard must cover the general "does approach X beat baseline Y under conditions Z" shape, not one study's nouns.
- **`metric` binds to the existing primary-metric gate.** Avoids inventing a parallel concept; the workflow already elicits the evaluation metric before any code.

## 9. Acceptance criteria

- A competent engineer can build all five artifacts from this spec without further design input.
- Every seam has an unambiguous treatment and contract: Seam 1 (verbatim wiring), Seam 2 (spine + enumerated invariants + optional/extension points), Seam 3 (role signatures + library-provided vs seam), Seam 4 (the `experiment/` key schema incl. `determinism` + the axis-split and axis-dependence rules + the run output contract), Seam 5 (the explicit lint and review check-lists). The prove layer (determinism gate) is specified as a generic helper, not a seam.
- The four-layer gate's check-targets are enumerated: what the lint detects, what the reviewer judges, what the determinism gate proves.
- The `experiment/` config schema is pinned as a data contract (its keys and their meaning).
- The promotion model is specified as a judgment trigger with a default signal, leaving quick PoCs untouched.

## 10. Validation strategy

- **Seam coverage:** for each of the five seams, a reader can point to the treatment, the contract, and (for Seams 1–2) the enforced invariant. No seam is left as "use judgment."
- **Enforcement completeness:** every Seam-5 mechanical rule maps to a lint check; every Seam-5 judgment rule maps to a reviewer responsibility; the determinism gate's contract semantics (`order_independent` / `single_worker` / `nondeterministic`, exact aggregate equality, escape hatch) are stated.
- **Heterogeneity preservation:** a worked thought-experiment of a non-PAUC investigation (different data, metric, analyses) slots into the role contract and `experiment/` schema without modifying the shell or the gate — confirming enforcement guards invariants, not shape.
- **Minimality:** the reference flow demonstrates exactly the two things prose cannot convey (the keyed data/training-axis split; ≥2 analysis branches composing off `train` artifacts) and nothing more.
