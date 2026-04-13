> **FROZEN — Source of Truth.** This document records verbatim peer reviewer feedback on the v6 working paper. Do not edit, paraphrase, or update. All v7 design decisions that respond to this feedback cite it by filename and quote.

**Primary concernsP**

**Scale.** n=120 total, n=80 regular cases is small for a main-paper claim at ACL. The RC subgroup (n=25) being explicitly underpowered compounds this. Reviewers will flag it immediately.

**Single domain, single vendor.** ML methodology review is a niche task. All agents are Claude. The convergent/divergent framework is pitched as a general reconciliation of the debate literature, but it's post-hoc and tested on one domain with one model family. Reviewers will note this gap between claim scope and evidence scope.

**The central framework is explicitly post-hoc.** You're appropriately honest about this, but it undermines the contribution. A post-hoc interpretive framework consistent with the data is a hypothesis, not a finding. At ACL, this typically gets downgraded from contribution to "future work motivation."

**The most interesting finding isn't compute-matched.** The debate advantage on convergent judgment (FVCmixed = 0.3667) comes from multiround at ~5× compute — not from isolated debate at 3×. The debate-vs-ensemble mixed comparison is formally inconclusive (CI spans zero, n=40). So the paper's thesis — "task type determines whether debate helps" — rests on a matched-compute result for the divergent case and an unmatched, underpowered result for the convergent case.

**Defense case failure deserves more.** 0/60 correct verdicts across four conditions is striking and underanalyzed. The Saunders et al. generator-discriminator framing is mentioned briefly, but this finding has implications for prompt design and generalizability that the paper doesn't pursue.

**ETD is a broken metric.** ETD = 1.0 for 100% of debate outputs — you note this, but a metric that produces no signal shouldn't be in the scoring battery without a replacement.

**Smaller issues**

The abstract is dense with specific numbers on first read (∆ = +0.1114, FC ∆ = +0.0287, CI [+0.0154, +0.0434]). ACL reviewers skim abstracts hard — lead with the conceptual claim, then the numbers.

The reflexive AI assistance disclosure — "a reflexive disclosure is warranted: the principal AI tool used for writing assistance is also the subject of the experimental study" — is intellectually honest and I'd keep it, but it's unusual enough that a reviewer might flag it as distracting.

The benchmark isn't positioned as a reusable community resource with its own contribution slot. If the 120 cases are being released, that's worth foregrounding more explicitly.

-------

**MUST DO**

- Scale benchmark to ≥160 regular cases
Add ~80 cases (ideally 40+ synthetic critique/defense). n=80 is the most likely desk-reject risk for Findings. Target n≥160 for the primary comparison.

- Design and run compute-matched multiround variant
Cap multiround at exactly 3× budget (e.g. 2 rounds max, fixed). This makes the convergent judgment comparison clean — currently multiround at ~5× vs. ensemble at 3× is not apples-to-apples

- Scale mixed cases to ≥80 (from 40)
The debate-vs-ensemble mixed comparison is inconclusive at n=40. Doubling it may push the CI off zero and make the convergent/divergent framework formally testable rather than post-hoc.

- Replace or fix ETD metric
ETD = 1.0 for 100% of debate outputs — a metric with no variance is not a metric. Either add the sub-element rubric (specificity, falsifiability, orthogonality) or drop ETD and describe it as a known ceiling in limitations.

- Reframe convergent/divergent as prospective prediction, not just post-hoc
State explicit falsifiable predictions in §5.1 — "ensemble IDR should exceed debate IDR on code bug-finding; multiround should exceed ensemble on accept/reject judgment." This upgrades the framework's status for reviewers.

- Deeper analysis of defense case failure
0/60 correct verdicts across 4 conditions is striking and currently underused. Add at least one diagnostic: does the critic prompt even include a "no issues found" output path? This finding alone could anchor a short analysis section.

- Run TOST equivalence test for H1a
You correctly note that non-significance ≠ equivalence. A TOST with a stated equivalence bound (e.g. FC ∆ < 0.02) converts "not sig" into a formal claim about debate adding no meaningful value over baseline.

- Rewrite abstract — concept before numbers
Currently leads with five specific deltas in the first three lines. Reviewers skim. Lead with the claim ("independent ensembles outperform adversarial debate at matched compute; task type moderates this"), then numbers.

- Add IDR as co-primary metric throughout
§5.2 makes the case that IDR is the metric that matters for detection tasks and FC composites dilute it. Apply this consistently: report IDR prominently in abstract, intro, and conclusion, not just as a row in Table 2.

- Move reflexive AI disclosure to footnote
The AI assistance statement in §AI is substantively good but placement as a standalone section before References looks unusual. A footnote on the title page is standard for ACL-style venues.

- Foreground benchmark as a releasable artifact
The 120-case benchmark with planted ground-truth is a concrete contribution independent of the experiment. Mention release in intro, not just the reproducibility section — reviewers weight released resources positively at Findings.
