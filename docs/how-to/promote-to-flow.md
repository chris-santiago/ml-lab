# Promote an Investigation to a Metaflow Flow

`/pipeline-init` promotes a PoC-stage investigation into a config-driven, reproducible Metaflow + Hydra pipeline. This page walks through the full sequence: when to promote, what the scaffold looks like, how to fill the four component seams, and how to pass the blocking gate.

## Decide whether to promote

The default signal is **more than one analysis cell, or more than one distinct analysis or diagnostic.** A PoC that computes a single number under a single condition is not a promotion candidate. Promote when the PoC iterates over multiple data conditions, trains multiple methods, or branches into two or more diagnostics.

This threshold is a recommendation, not a rule. Promote earlier when reproducibility matters from the start; stay ad-hoc longer when the hypothesis is still unstable. Quick one-number PoCs are explicitly excluded: the overhead of a pipeline serves no purpose when there is nothing yet to orchestrate.

## Invoke `/pipeline-init`

```shell
/pipeline-init
```

The skill creates a `flow/` directory under your investigation root (if it does not exist) and stamps the bundle into place:

- `flow/<investigation>_flow.py` — a flow module pre-wired with the invariant shell (PEP 723 header, `sys.path` shim, Hydra parser, lazy-metaflow guard)
- `flow/conf/` — a `config.yaml` plus four config-group directories: `data/`, `method/`, `experiment/`, and `training/`

The scaffolded flow is your starting point, not a filled-in template. The reference flow (`assets/reference_flow.py`) shows the annotated DAG shape; adapt it to your investigation's domain.

## Fill the four seams

The PoC's logic maps to four module-level functions. Implement each as a plain function in the flow module — no Metaflow import required — so they are unit-testable via a bare `import`.

### `make_data(data_spec, data_axes, seed) -> Dataset`

Move the PoC's data-generation logic here. `data_axes` is the data-affecting subset of the current config cell and overrides `data_spec` values. This is what makes the dataset-keyed `foreach` correct: the dataset is generated once per `(data_axes + seed)` combination, not once per full configuration cell.

### `build_model(model_spec) -> nn.Module`

Move the PoC's model construction here. Keep it standalone; `train_arm` composes it.

### `train_arm(method_spec, data, seed, train_cfg) -> TrainResult`

Dispatched on `method_spec["kind"]` via `TRAIN_REGISTRY`. Every method kind used in the investigation must appear in the registry. An unknown kind must raise — never silently default a new method.

Classify each registered kind as either **axis-agnostic** (the trained model does not depend on the training-axis value; trains once, evaluated at every value) or **axis-dependent** (the loss bakes in the axis value; retrains per value). Register both classifications in `is_axis_agnostic_method(kind)`, which must also raise on an unknown kind.

### `metric(scores, labels, **cfg) -> float`

Binds to the investigation's existing primary evaluation metric — the one already in `HYPOTHESIS.md` and computed in the PoC. Do not introduce a new metric here. The `cfg` kwargs carry training-axis values when the metric is parameterized by them (for example, `k` from `eval_k`).

## Declare the experiment config

Edit `flow/conf/experiment/<name>.yaml`. Every experiment YAML pins these keys:

| key | meaning |
|---|---|
| `name` | tags every record; `an_*` branches filter on it |
| `axes` | cartesian-product axes; one cell key per axis |
| `data_axes` | subset of `axes` keys that change the generated dataset |
| `methods` | method config-group names compared in each cell |
| `method_overrides` | per-method override map applied before sweep expansion |
| `split_convention` | `sequential` or `independent` |
| `diagnostics` | named diagnostics computed by `an_*` branches from train artifacts |
| `requests_model` | store the trained `nn.Module` in each record |
| `requests_scores` | store raw scores and labels in each record |
| `determinism` | reproducibility contract (see below) |

### Data-axis vs training-axis split

List in `data_axes` every axis that changes the generated dataset (for example, `separation`). Axes that affect only training or evaluation (for example, `eval_k`) are training axes. The `foreach` grain is `(data_axes + seed)`: each dataset is generated once, and all methods that share that data train in-process on the shared tensors.

### Training config authority

`training/` is authoritative for shared knobs (`epochs`, `lr`, `batch`, `hidden`). A `method/` YAML carries only method-specific params (`margin`, `temp`, `warmup_frac`, sweep axes) and must omit those shared keys. A method that hard-sets them would block a per-experiment training override.

## Declare the determinism contract

Add one line to your experiment YAML:

```yaml
determinism: order_independent   # or: single_worker | nondeterministic
```

- **`order_independent`** (default) — aggregated outputs are identical across worker counts.
- **`single_worker`** — the flow is pinned to `--max-workers 1` because a dependency is nondeterministic under parallelism (for example, gensim). Determinism is claimed only at one worker.
- **`nondeterministic`** — explicit escape hatch: no reproducibility claim; the determinism gate is skipped. Use this rather than silently shipping a flow whose numbers move between runs.

The flow stores the declared value as a run artifact so any reader of a finished run knows the contract.

## Pass the gate

Three steps, in order. Each must pass before promotion is complete. This is the **prevent → lint → review → prove** sequence.

### Step 1 — Lint (blocking)

Resolve the plugin install path from the plugin registry (the same portable resolution used for `derive_verdict.py` — read `installPath` for `ml-lab` from `installed_plugins.json`), then run:

```shell
uv run "$PLUGIN_DIR/skills/pipeline-init/scripts/flow-lint.py" flow/<name>_flow.py
```

The linter checks five mechanical anti-patterns via stdlib `ast` only (no project deps, no flow import):

- `merge-artifacts-module` — `merge_artifacts()` missing `include=`/`exclude=`
- `cwd-relative-config` — `Config(default=...)` not anchored to `__file__`
- `per-config-foreach` — `foreach` grain is per-method/config rather than per-dataset
- `bare-project-import` — first-party import with no preceding `sys.path.insert` shim
- `module-global-experiment-const` — module-level numeric constant read inside a `@step`/`@card` body

Must exit 0. Fix every finding before proceeding.

### Step 2 — Fidelity review (blocking)

Dispatch the `pipeline-reviewer` agent with the promoted flow source and the investigation's source-of-truth documents (`HYPOTHESIS.md`, the original PoC script, `CONCLUSIONS.md` if it exists). The reviewer checks five intent-fidelity invariants: split convention, per-epoch reshuffle symmetry, axes-match-source, same-name/different-quantity metrics, and sweep-override inflation.

A `FAIL` on any check is blocking. Address all `FAIL` findings and re-dispatch until none remain.

### Step 3 — Run the flow, then verify the determinism contract (blocking)

Run the flow, then verify it holds the contract it declared:

```shell
# For order_independent: run at two different worker counts, then:
uv run "$PLUGIN_DIR/skills/pipeline-init/scripts/determinism-check.py" <run_a> <run_b>

# For single_worker: run twice at --max-workers 1, then diff.
# For nondeterministic: the check is N/A and self-skips.
```

This gate validates the flow against itself, not against the PoC. A `nondeterministic` declaration is a deliberate, recorded choice — not a silent gap.

Only after all three steps exit cleanly is promotion complete.

## What the flow is — and is not

The promoted flow is the single source of truth for the final methodology. It does not reproduce the throwaway PoC. The PoC was a debate seed; the critic/defender cycle exists to redirect its assumptions, not preserve them. Bad assumptions, abandoned directions, and superseded numbers belong in `INVESTIGATION_LOG.jsonl` (the investigation journal), not in the flow.

`HYPOTHESIS.md` stays unchanged. It is the canonical claim the investigation is testing.

## You have now...

Promoted a PoC-stage investigation to a config-driven Metaflow flow with verified seams, a declared determinism contract, and a passing lint/review/prove gate.
