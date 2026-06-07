# Skills (ml-lab)

Skills are user-invocable slash commands. They run in the main session and dispatch subagents as needed.

## /ml-lab

Start a structured ML hypothesis investigation.

**Invocation:**

```shell
/ml-lab
```

Or describe an ML hypothesis in natural language — Claude Code routes to ml-lab automatically via its description.

**Parameters asked at start:**

| Parameter | Options | Default |
|-----------|---------|---------|
| `review_mode` | `debate`, `ensemble` | `debate` |
| `report_mode` | `full_report`, `conclusions_only` | `full_report` |

**Workflow:** 13-step structured investigation. See [Workflow Diagram](workflow.md) for the complete flowchart.

**Artifacts produced:**

| Step | Artifact |
|------|----------|
| Pre | `HYPOTHESIS.md` |
| 1 | Proof-of-concept script |
| 2 | `README.md` |
| 3 | `CRITIQUE.md` / `ENSEMBLE_REVIEW.md` |
| 4 | `DEFENSE.md` (debate only) |
| 7 | `CONCLUSIONS.md` |
| 8 | `REPORT.md` (full_report mode) |
| 9 | `REPORT_ADDENDUM.md` |
| 10 | `PEER_REVIEW_R1.md` |
| 11 | `TECHNICAL_REPORT.md` |
| 13 | Rewritten `README.md` |
| All | `INVESTIGATION_LOG.jsonl` |

---

## /intent-watch

Monitor an experiment directory for pre-registration drift.

**Invocation:**

```shell
# One-time check
/intent-watch <experiment_dir> <source_of_truth>

# Continuous monitoring (every 2 minutes)
/loop 2m /intent-watch <experiment_dir> HYPOTHESIS.md
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `experiment_dir` | Path to the experiment directory |
| `source_of_truth` | Path to the binding document (typically `HYPOTHESIS.md`) |

**Output:** Clean-pass line or structured conflict report with severity levels (HIGH, CRITICAL block the experiment).

**Used at:**

- **Gate 1 (mandatory)** — one clean pass required before Step 6
- **Step 6 (active loop)** — continuous monitoring during experiment scripting

---

## /deep-dive

Generate a comprehensive technical reference document.

**Invocation:**

```shell
/deep-dive [experiment_path]
```

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `experiment_path` | Path to the experiment directory | Current directory |

**Output:** `DEEP_DIVE.md` — covers data construction, model architecture, scoring mechanics, statistical methods, per-test detail, quality gates, aggregation, and key design decisions with sources cited.

**Works with or without a project journal.** Degrades gracefully when artifacts are missing.

---

## /pipeline-init

Promote an ml-lab investigation from an ad-hoc PoC to a config-driven Metaflow + Hydra pipeline.

**Invocation:** Orchestrator-invoked during the promotion phase (after Gate 1). This skill is not typically called directly by the user.

**When to promote:** The default signal is more than one analysis cell, or more than one distinct analysis or diagnostic. A PoC that computes a single number under a single condition is not a promotion candidate. The threshold is a recommendation, not a gate — the orchestrator may promote earlier when reproducibility matters from the start, or stay ad-hoc longer while the hypothesis is still unstable.

**What it scaffolds:**

| Seam | Source asset | Treatment |
|------|-------------|-----------|
| Shell wiring | `assets/shell_snippet.py` | Verbatim copy into the flow module top (PEP 723 header, `sys.path` shim, Hydra parser, lazy-metaflow guard). Do not modify. |
| DAG | `assets/reference_flow.py` | Annotated reference — adapt to the investigation's domain; not a fill-in template. |
| Component contract | `assets/COMPONENT_CONTRACT.md` | Four seam signatures to implement: `make_data`, `build_model`, `train_arm` (registry-dispatched, raises on unknown kind), `metric` (binds to the investigation's existing primary metric). |
| Config schema | `assets/conf/` scaffold + `SCHEMA.md` | `config.yaml`, `data/`, `method/`, `experiment/`, `training/` groups. Standard group names must not be renamed. |

**PoC migration — four component seams:**

- `make_data(data_spec, data_axes, seed)` — PoC data-generation logic; `data_axes` drives the dataset-keyed `foreach` grain.
- `build_model(model_spec)` — PoC model construction; standalone and composed by `train_arm`.
- `train_arm(method_spec, data, seed, train_cfg)` — dispatched on `method_spec["kind"]` via `TRAIN_REGISTRY`; raises on unknown kind (never silently defaults).
- `metric(scores, labels, **cfg)` — binds to the investigation's existing primary metric from `HYPOTHESIS.md`; no new metric may be introduced here.

**Determinism contract:** The flow declares `experiment.determinism` in the experiment YAML (`order_independent` | `single_worker` | `nondeterministic`). `nondeterministic` is the explicit escape hatch for flows that genuinely cannot be deterministic under parallelism — it must be a deliberate declaration, not a silent gap.

**Gate sequence (prevent → lint → review → prove):**

| Step | Tool | Blocking |
|------|------|---------|
| 1. Lint | `scripts/flow-lint.py` (exit 0 required) | Yes — five mechanical anti-patterns checked via `ast`; fix all findings before proceeding. |
| 2. Fidelity review | `pipeline-reviewer` agent | Yes — `FAIL` on any of five intent-fidelity invariants blocks promotion; `CONCERN` is non-blocking but must be resolved before production. |
| 3. Determinism gate | `scripts/determinism-check.py` | Yes — verifies the flow holds its declared `experiment.determinism` contract by diffing two runs' aggregates (skipped automatically when `nondeterministic`). |

**Key principle:** The promoted flow is a single source of truth for the final, debated methodology. It does not carry forward the throwaway PoC's numbers or assumptions. The Metaflow datastore supersedes loose `stats_*.json` files once the flow is running. `HYPOTHESIS.md` and `INVESTIGATION_LOG.jsonl` are preserved unchanged.
