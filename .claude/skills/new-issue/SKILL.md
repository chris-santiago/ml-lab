---
name: new-issue
description: Scaffold a new numbered post-mortem issue for ml-debate-lab and append it to POST_MORTEM.md. Invokes the issue-drafter agent to draft, then confirms before writing.
---

Create a new post-mortem issue entry for this project.

## Step 1 — Gather Context

Ask the user (or infer from context) for:

1. **What went wrong** — a plain-language description of the problem. If the user already provided one as an argument to this skill, use it directly without asking.
2. **Which experiment** — default to v3 (`self_debate_experiment_v3/POST_MORTEM.md`) unless the user specifies otherwise.
3. **Scope** — Active (affects current results) or Future fix. If unclear, ask.
4. **Severity** — Critical / High / Moderate / Minor. If unclear, infer from the description and ask the user to confirm.

If all four are clear from context, skip asking and proceed.

## Step 2 — Dispatch issue-drafter

Invoke the `issue-drafter` agent with:
- The issue description
- The experiment version and POST_MORTEM.md path
- Scope and severity (or the instruction to infer them)

Wait for the agent to return a draft.

## Step 3 — Present the Draft

Show the complete draft to the user. Include the assigned issue number prominently.

Ask: "Does this look right? I'll append it to POST_MORTEM.md when you confirm."

Do not write anything to POST_MORTEM.md until the user explicitly confirms.

## Step 4 — Append and Commit

Once confirmed:

1. Append the issue text to the end of the appropriate POST_MORTEM.md, preceded by `\n---\n`.
2. Run `/artifact-sync` to update all dependent artifacts.
3. Stage and commit with message: `Add Issue N: [title]`

   Use `uv run` for any Python scripts invoked during artifact sync.
