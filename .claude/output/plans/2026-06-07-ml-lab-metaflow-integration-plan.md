# ml-lab Metaflow-Pipeline Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use chris-code:subagent-driven-development (recommended) or chris-code:executing-plans to implement this plan task-by-task.

## 1. Objective

Build the five ml-lab artifacts that promote multi-cell investigations onto a config-driven Metaflow flow which cannot drift from the verified wiring and fidelity rules. The flow is a single source of truth (final validated methodology only); its reproducibility is a declared determinism contract, never a reproduce-the-PoC check.

## 2. Spec references

- `.claude/output/specs/2026-06-07-ml-lab-metaflow-integration-design.md` §4 System behavior, §5 Architecture
- `…-design.md` §6 Canonical interfaces — the five seam contracts (load-bearing)
- `…-design.md` §7 Invariants, §8 Key decisions, §9 Acceptance
- Reference lessons: `imbalanced-losses/.claude/output/2026-06-06-ml-lab-pipeline-lessons-learned.md`

## 3. Files

| Action | Path | Reason |
|--------|------|--------|
| Create | `plugins/ml-lab/skills/pipeline-init/assets/shell_snippet.py` | Seam 1 verbatim wiring (§6) |
| Create | `plugins/ml-lab/skills/pipeline-init/assets/reference_flow.py` | annotated non-runnable reference (Seam 2/3) |
| Create | `plugins/ml-lab/skills/pipeline-init/assets/COMPONENT_CONTRACT.md` | Seam 3 role signatures + Seam 5 rules |
| Create | `plugins/ml-lab/skills/pipeline-init/assets/conf/` | Seam 4 scaffold (`config.yaml` + `data/ method/ experiment/ training/`) |
| Create | `plugins/ml-lab/skills/pipeline-init/assets/conf/SCHEMA.md` | `experiment/` key schema (incl. `determinism`) + run output contract (§6 Seam 4) |
| Create | `plugins/ml-lab/skills/pipeline-init/scripts/flow-lint.py` | deterministic Seam-5 mechanical lint |
| Create | `plugins/ml-lab/skills/pipeline-init/scripts/determinism-check.py` | prove layer: diff two runs' aggregates vs declared determinism contract |
| Create | `plugins/ml-lab/skills/pipeline-init/SKILL.md` | promotion skill: scaffolding + authoring guidance |
| Create | `plugins/ml-lab/agents/pipeline-reviewer.md` | judgment-gate agent (Seam-5 judgment rules) |
| Test | `plugins/ml-lab/tests/test_flow_lint.py` | lint flags each anti-pattern; passes the reference |
| Test | `plugins/ml-lab/tests/test_determinism_check.py` | pure-function aggregate-diff unit tests |
| Modify | `plugins/ml-lab/skills/ml-lab/SKILL.md` | insert promotion step + wire lint/review/determinism gate |

## 4. Constraints

- **Generic names** — `data/`/`method/` config groups, not the reference's `geometry/`/`arm/`.
- **Strictness only in the invariant core.** Only the shell snippet is verbatim-copy. Everything domain-specific is contract + example. **Do not** create a monolithic fill-in `flow_template.py`.
- **Reference flow is NOT runnable and NOT CI'd.** Syntactically real, heavily annotated, module-importable via the lazy-metaflow guard, carries one `# verified against metaflow 2.19.x` stamp. **Do not** add a runnable toy investigation, smoke test, or any rot-prevention machinery.
- **Enforcement guards invariants + declared determinism, never a specific DAG shape.** Lint/review must pass a legitimately different-shaped flow that honors the §6 Seam-2 invariants.
- **No reproduce-the-PoC gate.** The PoC is throwaway; the flow is a single source of truth of final methodology only. The prove layer verifies a declared determinism contract, not PoC reproduction.
- **uv-native** — PEP 723 inline deps; `flow-lint.py` follows the `log_entry.py` PEP-723 pattern.
- **Match plugin conventions** — agent frontmatter `name/description/model/color` (see `agents/ml-critic.md`); skill is `SKILL.md` with `name/description` frontmatter.
- **Promotion is judgment-triggered** — the SKILL.md edit adds the ">1 cell OR >1 analysis" signal as a recommendation in prose, not a hard rule.
- The lint/review gate is **blocking before the flow is run**, mirroring how Step 3 mandates `ml-critic`; the determinism gate is the prove layer after the run.

## 5. Tasks

### Task 1: Authoring-asset bundle (shell, reference flow, contract, conf scaffold + schema)
One coherent unit — the reference flow must embed the shell, satisfy the contract, and consume the conf schema.
- [ ] `shell_snippet.py`: Seam-1 wiring per spec §6 (PEP 723 header, `__file__`-anchored repo-src `sys.path` insert, `hydra_parser`+`Config` wiring, lazy-metaflow import guard, version stamp).
- [ ] `reference_flow.py`: canonical DAG spine (§6 Seam 2) on a genericized toy domain ("feature X separates two classes"). Must demonstrate exactly: (a) the data-axis/training-axis split with `foreach` keyed on `(data_axes + seed)`; (b) ≥2 analysis branches composing off `train` artifacts. Embeds the shell; annotated, non-runnable. Encodes the Seam-2 invariants (train→analyze separation; `join` reads `inputs[0]`, never `merge_artifacts` over `nn.Module`; `aggregate` owns bootstrap + paired lifts).
- [ ] `COMPONENT_CONTRACT.md`: the four role signatures (§6 Seam 3), library-provided vs seam, `metric`↔primary-metric binding, and the Seam-5 fidelity rules (mechanical + judgment lists).
- [ ] `conf/`: `config.yaml` defaults list + `data/ method/ experiment/ training/` group exemplars matching the reference flow; `SCHEMA.md` pins the `experiment/` keys (`name, axes, data_axes, methods, method_overrides, split_convention, diagnostics, requests_model, requests_scores, determinism`) and the axis-split + axis-dependence (`raise on unknown kind`) + `training`-authoritative merge rules + the **run output contract** (`lift_results`/`aggregate_results`/`an_<name>.an_result`/`determinism` shapes, generic `method`/`<primary_metric>` field names) as the SSOT read-surface + the **determinism contract** semantics. The reference flow echoes `experiment.determinism` as a run artifact.
- [ ] Verify: `python -m py_compile` on `shell_snippet.py` + `reference_flow.py`.

### Task 2: flow-lint.py + tests
- [ ] PEP-723 script (no project deps) that statically (AST, not grep) detects the §6 Seam-5 **mechanical** anti-patterns: module-global experiment constants, per-config `foreach` grain, `nn.Module` reaching `merge_artifacts`, CWD-relative `Config` default, bare project-package import under script mode. Reports file:line + rule id; nonzero exit on any finding.
- [ ] **Fuzzy-rule narrowing** (these two false-positive easily and would break the "different-shaped clean flow lints clean" invariant): define *bare project import* as `from <top_pkg> import …` whose `<top_pkg>` is the repo's own package AND no module-scope `sys.path.insert` precedes it; define *module-global experiment constant* narrowly (e.g. an uppercase module-level assignment read inside a `@step`, not any constant). Each rule pinned as a concrete AST predicate in COMPONENT_CONTRACT.md.
- [ ] `tests/test_flow_lint.py`: one deliberately-broken fixture per rule (must flag) + the reference flow as positive control (must pass clean) + a **clean-but-structurally-different fixture** (different DAG shape honoring Seam-2 invariants) that must also pass clean.
- [ ] `scripts/determinism-check.py` (prove layer): a PEP-723 (`metaflow>=2.19` only) helper with a PURE, importable `compare_aggregates(lift_a, agg_a, lift_b, agg_b)` (order-insensitive over canonicalized cells, exact-equality on numeric fields) + Metaflow run-fetch + contract gating that reads `run.data.determinism` (`nondeterministic` self-skips — the escape hatch). No `TARGETS`, no PoC anchor.
- [ ] `tests/test_determinism_check.py`: pure-function unit tests (identical→clean; field diff→reported; missing cell→reported; reordered-but-equal→clean; list-valued cell axis canonicalizes).
- [ ] Verify: `uv run pytest plugins/ml-lab/tests/test_flow_lint.py plugins/ml-lab/tests/test_determinism_check.py -v`.

### Task 3: pipeline-reviewer agent
- [ ] `agents/pipeline-reviewer.md` with conventional frontmatter (`model: sonnet`). Reviews a promoted flow against the Seam-5 **judgment** rules (split convention, reshuffle symmetry, axes-match-source, same-name/different-quantity metrics, sweep-override inflation). Reads the flow + investigation source-of-truth; does **not** run the flow. Emits structured findings; explicitly scoped to invariants/fidelity, NOT DAG shape.
- [ ] Verify: frontmatter parses; responsibilities map 1:1 to spec §6 Seam-5 judgment list.

### Task 4: pipeline-init skill
- [ ] `skills/pipeline-init/SKILL.md`: scaffolds the bundle into the investigation dir, migrates PoC `make_data`/`train`/`metric` into the seams, **declares the `experiment.determinism` contract** (no PoC-reproduction seeding — the flow is SSOT of final methodology only), preserves `HYPOTHESIS.md` + `INVESTIGATION_LOG.jsonl`, points the datastore at Metaflow (drops loose `stats_*.json`; bad assumptions live in the journal). Carries the authoring guidance: when to promote, canonical DAG as default-not-mandate, the seam-treatment table, the lint→review→determinism gate. References `flow-lint.py` + `determinism-check.py` + the bundle.
- [ ] Verify: SKILL.md frontmatter parses; references resolve to Task 1–2 paths.

### Task 5: Wire the orchestrator workflow
- [ ] Modify `skills/ml-lab/SKILL.md`: insert a **named promotion phase between Gate 1 (Experiment Plan, ~line 449) and Step 6 (Design and Run, ~line 497)** — do **NOT** renumber Steps 6–13 (cross-refs in macro-iteration, the corrections table ~864–874, and mode gates are dense). The phase carries the judgment trigger + default signal, the lint + `pipeline-reviewer` gate as blocking *before* the flow is run, and a distinct **prove sub-phase** (the determinism contract check, not PoC reproduction) after the run. Quick single-cell PoCs untouched.
- [ ] Verify: the four enforcement layers (§8, prevent→lint→review→prove) appear as workflow steps; Steps 6–13 numbering and all cross-refs stay byte-consistent (the promotion phase is named, not numbered).

## 6. Acceptance checks

- `uv run pytest plugins/ml-lab/tests/test_flow_lint.py plugins/ml-lab/tests/test_determinism_check.py -v` — all pass (every mechanical rule flagged on its fixture; reference flow clean; the clean-but-different-shaped fixture also clean; determinism aggregate-diff unit tests pass).
- `python -m py_compile` on `shell_snippet.py`, `reference_flow.py`, and `determinism-check.py` — succeed.
- Every spec §6 seam (1–5) maps to a built artifact with an unambiguous contract; the prove layer (determinism gate) maps to `determinism-check.py`; every §6 Seam-5 rule maps to either a lint check (Task 2) or a reviewer responsibility (Task 3).
- The `experiment/` schema (incl. `determinism`) **and** the run output contract are pinned in `conf/SCHEMA.md`; `determinism-check.py` reads the pinned aggregate shape.
- ml-lab/SKILL.md shows promotion as a judgment trigger, the lint/review gate as blocking before the run, and the determinism contract as the prove layer; quick PoC path unchanged; no reproduce-the-PoC gate anywhere.
- Heterogeneity check (spec §10): the role contract + `experiment/` schema accommodate a non-PAUC investigation without touching the shell or the gate.

## 7. Open questions

- None blocking. The genericization is proven only when Task 1's reference flow is authored against the toy domain; a wrong seam surfaces there first.
