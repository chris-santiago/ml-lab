# Explanation

Understanding the design decisions, trade-offs, and evolution behind ml-lab. These pages answer *why*, not *how*.

| Topic | What it covers |
|-------|---------------|
| [Why a Metaflow Pipeline](why-metaflow.md) | Why investigations that outgrow a single-cell PoC are promoted onto a config-driven flow: reproducibility, consistency, accuracy, and why the pipeline never carries the PoC forward |
| [Project Origin](origin.md) | How a FastText experiment recursed into its own evaluation infrastructure |
| [The Experiment Arc](experiment-arc.md) | Why eight experiment versions exist and what each one taught |
| [Debate Protocol](debate-protocol.md) | Why adversarial critique works, how the verdict function enforces convergence, and when ensemble mode is better |
| [Evaluation Methodology](evaluation.md) | Pre-registration, metrics, scoring, cross-vendor evaluation, and statistical methods |
| [Post-Mortems & Lessons](post-mortems.md) | What broke across v3-v5 and what the fixes revealed about LLM evaluation |
