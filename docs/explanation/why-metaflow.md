# Why a Metaflow Pipeline

Most ml-lab investigations never need a pipeline. A hypothesis that only has to produce a single number lives happily in a single-cell proof-of-concept: one script, one command, one result. The promotion to a config-driven Metaflow flow is reserved for the investigations that outgrow that — the ones that accumulate several methods, multiple analyses, and two or three rounds of debate-driven revision before the methodology settles. This page explains *why* that promotion exists, what it is meant to fix, and the principles that decide what the pipeline does and does not carry.

## The problem it solves: script sprawl and the lost conclusion

A serious investigation rarely converges on the first try. The critic finds a flaw, the methodology changes, a new analysis is added, a baseline is corrected. Each cycle tends to spawn another ad-hoc experiment script, and each of those scripts re-implements the same core pieces — data generation, training, the metric, the bootstrap — with signatures that drift apart over time. The reference build that motivated this standard consolidated **eight** such scripts, every one of which had its own copy of `make_data`, `train_*`, `coverage`, and `bootstrap_ci`, no two of them quite agreeing.

The cost of that drift is not just duplication. It is that the experiment folder fills with stale, superseded, and sometimes outright *wrong* artifacts — loose `stats_*.json` and `results_*.jsonl` files left over from abandoned approaches. By the end, a human reviewer trying to answer the simple question "what did this investigation actually conclude?" has to excavate the directory and reason about which files are current and which are debris. The final answer is in there somewhere, mixed in with everything that was tried and discarded along the way.

A promoted flow exists to collapse all of that into a **single source of truth**: one config-driven pipeline that holds only the final, debated methodology. The Metaflow datastore supersedes the loose result files, the component logic lives in exactly one place, and the conclusions are read from a pinned output surface rather than reconstructed from a pile of scripts. The sprawl never accumulates because there is one flow, not a growing pile of cycles.

## Reproducibility as a declared, verifiable contract

A pipeline that produces a different answer depending on how many workers happened to be free is not reproducible, no matter how clean its code looks. So the flow does not merely *aspire* to determinism — it **declares** a reproducibility contract and the prove layer verifies the flow honors it.

The contract is one of three values:

- `order_independent` — the aggregate is identical regardless of how the fan-out is scheduled. This is verified by running the flow at two different worker counts and diffing the aggregated outputs for exact equality. Order-independence is a real, checkable property, not a hope. In the reference build the two runs were bit-identical.
- `single_worker` — the flow is pinned to `--max-workers 1` because a dependency is nondeterministic under parallelism (gensim, encountered in the ATO investigation, is the canonical case: deterministic at one worker, not across workers). Determinism is claimed and verified only at a single worker; cross-worker invariance is deliberately not asserted.
- `nondeterministic` — an honest escape hatch for an experiment that cannot guarantee reproducible aggregates at all. Forcing a false determinism claim onto such work would only invalidate it. The declaration is explicit and recorded as a run artifact; the gate self-skips rather than pretending.

The key move is that determinism is **config-controlled and verified**, not asserted in prose. The flow echoes its declared contract as a run artifact, and the prove layer diffs two real runs against that declaration. Crucially, the check validates the flow *against itself* — it proves the pipeline's numbers are execution-invariant as declared. It does not reproduce the proof-of-concept's numbers, for reasons developed below.

## Consistency: one contract instead of drifting re-implementations

The deeper fix for script sprawl is a single **component contract**. Instead of every cycle re-writing the same four functions, the flow defines them once at fixed seams:

```
make_data(data_spec, data_axes, seed)         -> Dataset
build_model(model_spec)                        -> nn.Module
train_arm(method_spec, data, seed, train_cfg)  -> TrainResult(model, scores, val_score)
metric(scores, labels, **cfg)                  -> float
```

These signatures do not drift because there is only one of each. The metric, in particular, is not a new concept invented for the pipeline — it binds to the investigation's existing primary evaluation metric, the one elicited before any code is written. The pipeline gives that metric a single code home rather than scattering it.

Consistency also comes from a less obvious mechanism: the **data-axis / training-axis split**. Most experimental axes change only the *training* (a budget, a capacity, a weight-decay sweep), not the *data*. The flow tags each axis as data-affecting or training-affecting, keys the `foreach` fan-out on the data axes plus seed, and generates the dataset **once** per branch. Every method that shares that dataset trains in-process against it.

This is simultaneously a performance win and a fidelity guarantee. An axis-agnostic method — a plain baseline that does not depend on the training axis — trains **exactly once** and is evaluated across all axis values, which is precisely what the original ad-hoc scripts did. An axis-dependent method retrains per value. The classification is read from the method's declared kind, and an unknown kind **raises** rather than silently defaulting, because a silent default here would quietly change the numbers. Re-generating data per training value, or retraining a baseline that should have trained once, both produce plausible-but-wrong aggregates; the split prevents both by construction.

One more consistency rule: **config is authoritative, not module globals.** Geometry, training, and method parameters are sourced from the Hydra config groups (`data/`, `method/`, `experiment/`, `training/`), never from module-level constants like `_EP = 15`. Functions take parameters; their defaults are mere library fallbacks. The `training/` group is authoritative over any method-specific `epochs`/`lr`/`batch`, so a method config carries only what is genuinely method-specific and cannot block a per-experiment training override. When the config is the single source of an experiment's behavior, two people reading the same config see the same experiment.

## Accuracy: the traps that silently break results

The hardest-won lessons are about failures that do not announce themselves. They pass the obvious checks, produce a number that looks reasonable, and are wrong. The standard bakes defenses against them in directly, split between a mechanical lint and a judgment reviewer.

**Toolchain traps** — mechanical, caught by the deterministic lint:

- *Script-mode import failure.* `uv run flow.py run` is PEP 723 *script* mode and does not install the local repo package, so a bare project-package import raises at run time — while the contract tests, which run in project mode, import it fine and pass. The flow is broken but the tests are green. The fix is a `__file__`-anchored `sys.path` insert, encoded in the invariant shell.
- *CWD-relative `Config` default.* A relative config default path fails the moment you run from a different directory. The default must be absolute and `__file__`-anchored.
- *Per-config `foreach` overhead.* Each Metaflow task is a subprocess that re-imports torch and does datastore I/O — a fixed two-to-four-second overhead that can *double* the wall-clock of a short training. Making every config its own `foreach` branch (thousands of branches in the reference grid) is the anti-pattern; the dataset-keyed fan-out is the fix.
- *`nn.Module` in `merge_artifacts`.* A model-carrying artifact breaks the merge at a join, because equality comparison on a module raises. A join after a model-carrying branch reads `inputs[0]` explicitly instead.

**Fidelity traps** — judgment, caught by the reviewer reading intent:

- *Split convention.* Drawing train and test from one sequential RNG stream is a *different* data-generating process than independent seed-offset splits, and the two shift the numbers. Which one the source used is a fact about intent, not a pattern in the code.
- *Reshuffle symmetry.* If one method reshuffles per epoch and another uses a fixed order, that asymmetry is a silent training-fidelity divergence — a likely source of confidence intervals that fail to overlap when they should.
- *Axes matching the source.* An experiment that fixed one cue in the source but is given three in config silently dilutes every aggregate by mixing regimes. It looks like a bug; it is a config mismatch only a reader checking against the source script can catch.
- *Same name, different quantity.* Two metrics can share a label and mean different things — fraction-of-decoys-in-the-band versus fraction-of-the-band-that-is-decoys. Reusing one helper for both produces a number that is precise and wrong.
- *Sweep-override inflation.* Applying a validation-selected sweep where the source used a single fixed config inflates the baseline, because best-of-N is never worse than one. The reviewer checks that an experiment's sweep matches the source's.

The reference build's review gates caught every one of these *before* the slow validation phase. That is the whole point: these are not bugs you find by staring at output, because the output looks fine.

## The enforcement model: prevent, lint, review, prove

None of the above is advice you are trusted to remember. The standard is **wired**, the same way ml-lab already mandates adversarial critique rather than suggesting it. Enforcement is four layers:

1. **Prevent** — the promotion scaffolds the invariant shell and component seams, so the load-bearing wiring (the `sys.path` insert, the Hydra↔Metaflow `Config` parser, the lazy-metaflow import guard) is copied verbatim and cannot be re-derived wrong.
2. **Lint** — a deterministic, static check for the mechanical traps: module-global constants, per-config `foreach` grain, an `nn.Module` reaching `merge_artifacts`, a CWD-relative `Config` default, a script-mode project import.
3. **Review** — a judgment agent reads the flow against the investigation's source of truth and reasons about the fidelity traps the lint cannot pattern-match.
4. **Prove** — the determinism gate diffs two runs against the declared contract.

The lint and the review run as a **blocking gate** on every promoted flow, before it is run, and the flow does not execute until both pass or the user explicitly overrides a finding. This follows the project's standing division of labor: deterministic logic is a script, judgment is an agent prompt — the very same boundary that already separates ml-lab's deterministic verdict function from its critic and defender agents. Enforcement guards the *invariants and the declared determinism*, never a specific DAG shape; a legitimately different flow shape passes as long as it honors the invariants, lints clean, reviews clean, and holds its contract.

## What the pipeline is not: it does not carry the PoC forward

This is the central design correction, and it is a principle, not a feature.

It is tempting to treat the proof-of-concept as the thing the pipeline must reproduce — to add a gate that checks the flow's numbers against the PoC's, the way the original reference build validated against an independently produced prior table. In a fresh ml-lab promotion that instinct is exactly backwards, for three reasons.

First, the PoC is **throwaway debate fodder**. It is the artifact the critic/defender phase exists to interrogate and overturn. Anchoring a gate to it would enshrine precisely the pre-debate assumptions the debate is meant to redirect.

Second, it anchors fidelity to the **least rigorous artifact** in the investigation. The PoC is the one number written before any critique. Reproducing it faithfully would mean reproducing whatever was wrong with it.

Third, it is **circular**. Promotion migrates the PoC's data, training, and metric logic *into the flow's component seams* — the flow and the PoC share code. A gate comparing them would have shared code reproducing its own bug and calling the agreement a pass.

So the flow holds **only final, validated methodology**, and nothing else. The audit trail of abandoned assumptions — what was tried, why it was wrong, what the debate overturned — belongs to the investigation journal, which is built to own exactly that history. The determinism gate validates the flow against *itself*, never against the PoC. And the experiment's findings are certified by the existing ml-lab machinery — verdicts, baselines, bootstrap CIs, debate, peer review — not by any reproduce-the-PoC check, because that machinery is what the whole tool is for.

The result is a clean separation: the journal remembers everything the investigation discarded; the pipeline carries only what survived.
