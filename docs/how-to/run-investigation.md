# Run an ML Investigation

## Start the investigation

Invoke the skill:

```shell
/ml-lab
```

Or describe your hypothesis in natural language — Claude Code routes to ml-lab automatically.

## Provide your hypothesis

ml-lab will ask you to sharpen your hypothesis into a falsifiable claim. You need:

1. **The claim** — what you believe is true
2. **The metric** — how you'll measure it
3. **The pass criteria** — what outcome would falsify the claim

You'll also choose:

- **Review mode** — `debate` (default, adversarial) or `ensemble` (3× independent critics)
- **Report mode** — `full_report` or `conclusions_only`

## Wait for the PoC

ml-lab builds a minimal proof-of-concept to confirm the measurement works before investing in review. This is typically a few lines of code and a handful of API calls.

Review the PoC and confirm it measures what you intend.

## Review the critique

In debate mode, you'll see:

1. `CRITIQUE.md` — initial critic findings with severity levels (FATAL, MATERIAL, MINOR)
2. `DEFENSE.md` — structured rebuttals (CONCEDE, REBUT-*, DEFER, EXONERATE)
3. Stage B rounds — challenge/response loop until verdicts converge

In ensemble mode, you'll see `ENSEMBLE_REVIEW.md` with tier-weighted findings (3/3, 2/3, 1/3 support).

## Approve the experiment plan

Gate 1 requires your approval. Review:

- All pre-flight items are CLOSED
- The experiment design matches your intent
- Cost estimates are acceptable

## Optional: promote to a Metaflow flow

After Gate 1 approval, a multi-cell investigation may be promoted onto a config-driven Metaflow+Hydra pipeline before Step 6 runs. This is a judgment call, not a requirement — the default signal is more than one cell or more than one distinct analysis. Quick single-cell PoCs skip this entirely and proceed to Step 6 unchanged.

When you promote, Step 6 runs as the Metaflow flow instead of inline. The promotion gate is: flow-lint → pipeline-reviewer → determinism check (`prevent → lint → review → prove`).

Run `/pipeline-init` to start the promotion. See [Promote an Investigation to a Metaflow Flow](promote-to-flow.md) for the full procedure.

## Monitor the experiment

During Step 6, `/intent-watch` runs to catch pre-registration drift. If a HIGH or CRITICAL conflict is flagged, resolve it before continuing.

## Review conclusions

ml-lab synthesizes `CONCLUSIONS.md` with the primary result, figures, and a verdict against your pre-specified pass criteria.

If findings are surprising enough to falsify a review assumption, ml-lab proposes a macro-iteration — reopening the review cycle with results in hand. Up to 3 macro-iteration cycles are allowed.

## Optional: peer review and final report

After conclusions, ml-lab offers:

- **Step 10** — Peer review loop (`research-reviewer` + `research-reviewer-lite`, up to 3 rounds)
- **Step 11** — Final `TECHNICAL_REPORT.md` in results mode

Both require your confirmation to start.

## You have now...

Completed a full ml-lab investigation from hypothesis to conclusions, with adversarial review, pre-registered experiments, and optional peer review.
