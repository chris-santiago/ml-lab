# HANDOFF — ml-lab Metaflow-Pipeline Integration

**For:** an agent picking up this build in the `ml-lab` repo (`/Users/chrissantiago/Dropbox/GitHub/ml-lab`).
**Status:** design + plan complete and approved; **no code written yet**. Your job is to build the five artifacts.

---

## Mission (one paragraph)

Extract a reusable Metaflow-pipeline standard into the ml-lab plugin so any investigation that outgrows a single-cell PoC is *promoted* onto a config-driven Metaflow flow that **cannot drift** from verified toolchain wiring and reproduction-fidelity rules. The standard is genericized from a validated reference build (the PAUCAtBudgetLoss flow, which lives in a *different* repo). The governing principle: **strictness only in the small invariant core where prose-only demonstrably fails; generosity everywhere the investigation legitimately varies.**

## Read these first (in order)

1. **Spec** — `.claude/output/specs/2026-06-07-ml-lab-metaflow-integration-design.md`. §6 (the five seam contracts) is load-bearing; read it twice.
2. **Plan** — `.claude/output/plans/2026-06-07-ml-lab-metaflow-integration-plan.md`. Files table, constraints, 5 tasks, acceptance.
3. **Reference lessons** (other repo, same machine) — `/Users/chrissantiago/Dropbox/GitHub/imbalanced-losses/.claude/output/2026-06-06-ml-lab-pipeline-lessons-learned.md`. The hard-won traps. If you can't read across repos, the load-bearing items are embedded below.

## How to execute

Use **chris-code:subagent-driven-development**. Staged by file footprint:

- **Stage 1** (parallel, disjoint files): Task 1 authoring bundle (shell / reference flow / contract / `conf/` + schema) ‖ Task 3 `pipeline-reviewer` agent.
- **Stage 2**: Task 2 `flow-lint.py` + `tests/test_flow_lint.py` (needs Task 1's reference flow as the positive control).
- **Stage 3**: Task 4 `pipeline-init` SKILL.md (wraps the bundle + lint).
- **Stage 4**: Task 5 edit `skills/ml-lab/SKILL.md` (references the skill + agent).

Coder agents: `pytorch-coder` for the reference flow (it's torch + Metaflow), `python-coder` for the lint/tests, plain authoring for the markdown skill/agent/contract docs.

## Non-negotiable constraints (these are the ones an eager agent breaks)

- **Branch before any work; do NOT commit without explicit user approval.** This repo's `main` is protected by the user's convention.
- **The reference flow is NOT runnable and NOT CI'd.** Syntactically real, heavily annotated, module-importable via the lazy-metaflow guard, one `# verified against metaflow 2.19.x` comment. **Do NOT** add a runnable toy investigation, a smoke test, or any rot-prevention machinery — these were explicitly considered and dropped (the agent never executes the reference; the reproduction gate catches API drift downstream).
- **No monolithic fill-in `flow_template.py`.** Only the ~30-line shell snippet is verbatim-copy. Everything domain-specific is contract + example.
- **Generic names:** `data/` and `method/` config groups — NOT the reference's `geometry/`/`arm/`.
- **uv-native**, PEP 723 inline deps; `flow-lint.py` follows the `log_entry.py` PEP-723 pattern.
- **Match plugin conventions:** agent frontmatter `name/description/model/color` (see `plugins/ml-lab/agents/ml-critic.md`); skills are `SKILL.md` with `name/description` frontmatter (see `skills/deep-dive/SKILL.md`).
- **Enforcement guards invariants + reproduction, never a DAG shape.** A legitimately different-shaped flow that honors the Seam-2 invariants must lint/review clean.

## Load-bearing facts the reference flow MUST encode (from the lessons doc)

**Seam 1 — shell wiring (verbatim, prose fails here):**
- `sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "src"))` — script mode (`uv run flow.py`) does NOT install the repo package; a bare `from <project> import …` raises `ModuleNotFoundError` at run time *even though unit tests pass* (tests run in project mode). Anchor to `__file__`.
- `Config(default=…)` must be an **absolute, `__file__`-anchored** path (CWD-relative breaks from repo root).
- Hydra↔Metaflow: a `Config(parser=hydra_parser)` that `GlobalHydra.instance().clear()` → `initialize_config_dir` → `compose` → `OmegaConf.to_container(resolve=True)`. CLI override form: `--config-value cfg "hydra_overrides: [experiment=X]"` (two positional args, before `run`).
- Keep `FlowSpec` + all metaflow/`@card` imports inside a `try: from metaflow import …` guard so the module imports without metaflow.

**Seam 2 — DAG invariants:**
- train→analyze separation (diagnostics consume `train` artifacts, never inside `train`).
- **Dataset-keyed `foreach`**: split axes into data-axes (change the data) vs training-axes; key the fan-out on `(geometry + data_axes + seed)`; generate data once per branch; axis-agnostic methods train once and are evaluated at all training-axis values, axis-dependent methods retrain per value; **raise on unknown `method.kind`**.
- A `join` after a model-carrying branch reads `inputs[0]` — never `merge_artifacts` over an `nn.Module` (equality comparison raises).
- `aggregate` owns bootstrap + paired lifts.

**Seam 5 — fidelity traps the lint/reviewer target:** module-global experiment constants; per-config `foreach`; model in `merge_artifacts`; CWD-relative `Config`; bare project import (→ lint). Split convention (sequential vs independent), per-epoch reshuffle symmetry across methods, axes-match-source, same-name/different-quantity metrics, sweep-override inflation (→ reviewer).

## Definition of done

Plan §6 acceptance: lint tests pass (every mechanical rule flagged on its fixture; reference flow clean), `py_compile` succeeds on shell + reference, every seam maps to an artifact, the `experiment/` schema is pinned, and the workflow edit shows promotion as a judgment trigger with the lint/review gate blocking before reproduction.
