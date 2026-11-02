# Setting Up ml-journal

This tutorial walks you through initializing ml-journal in a repository, logging your first entry, and using checkpoints to survive context compaction. By the end, you'll have a working audit trail.

## Prerequisites

- ml-journal plugin installed (see [Installation](installation.md))
- A git repository (ml-journal stores its log alongside your code)

## Initialize the journal

In your repo, run:

```shell
/log-init
```

This creates:

```
.project-log/
└── journal.jsonl       # append-only log (starts with a verification entry)
```

The repo holds data only. The scripts that read and write the journal run from the installed ml-journal skills, never from the repo.

Verify it worked:

```shell
/log-status
```

You should see something like:

```
Last checkpoint: none
Entries: 1 (verification)
Unresolved issues: 0
```

## Log your first entry

Start working on something, then when you make a decision:

```shell
/log-entry
```

ml-journal infers the entry type from the conversation context. If you just discussed a design choice, it proposes a `decision` entry. If you found a bug, it proposes an `issue`. You review a draft before it's written.

Example output:

```
Proposed entry (decision):
  description: Use Kruskal-Wallis instead of ANOVA for preamble comparison
  rationale: Score distributions are non-normal; KW is the rank-based equivalent
  alternatives: ANOVA with log transform, bootstrap confidence intervals

Write this entry? [y/n]
```

## Checkpoint before context loss

When you're about to hit a context boundary (long session, about to `/compact`, ending for the day):

```shell
/checkpoint
```

This snapshots your current state:

- What you're working on (`in_progress`)
- Pending decisions
- Recently completed items
- Open threads
- Git state (branch, uncommitted changes)

## Resume in a new session

Next time you open the repo:

```shell
/resume
```

This loads the last checkpoint into context, so Claude knows where you left off without you re-explaining.

## Commit with an audit trail

Instead of bare `git commit`:

```shell
/log-commit
```

This stages your changes, creates a commit, and writes a `git` journal entry with a `diff_summary` — a prose description of *why* the commit exists, written while the context is fresh.

## You have now...

- Initialized `.project-log/journal.jsonl`
- Logged a decision entry with `/log-entry`
- Saved session state with `/checkpoint`
- Learned the `/resume` and `/log-commit` workflow

For the full set of journal skills and entry types, see the [ml-journal skills reference](../reference/ml-journal/skills.md) and [entry types reference](../reference/ml-journal/entry-types.md).
