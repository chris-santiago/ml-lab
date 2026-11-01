# Query the Journal

## Using the skill

For a quick overview:

```shell
/log-status
```

To list entries by type:

```shell
/log-list decision --since 7d
```

## Using the CLI directly

The query script lives only in the installed plugin; repos hold journal data, not code. Set `Q` to the plugin's copy, using the `installPath` for `ml-journal` in `~/.claude/plugins/installed_plugins.json`, then run it from anywhere inside the repo:

```bash
Q="<installPath>/skills/log-init/scripts/journal_query.py"

# Journal health overview
python3 "$Q" --status

# List all decisions from the last week
python3 "$Q" --list decision --since 7d

# List unresolved issues
python3 "$Q" --unresolved-issues

# List resolved issues with linked resolutions
python3 "$Q" --resolved-issues

# Show the 10 most recent entries
python3 "$Q" --recent 10

# Show recent entries within a time window
python3 "$Q" --recent 5 --since 7d

# Look up a specific entry by ID prefix
python3 "$Q" --entry abc123

# Show the latest checkpoint
python3 "$Q" --latest-checkpoint
```

## Filtering by type

The `--list` flag accepts any entry type:

```bash
--list decision      # design choices with rationale
--list issue         # bugs and inconsistencies
--list resolution    # verified fixes
--list discovery     # unexpected findings
--list experiment    # verdicts (confirmed/refuted/inconclusive)
--list lesson        # root cause explanations
--list hypothesis    # testable claims
--list summary       # phase completion summaries
--list post_mortem   # failure analyses
```

## Synthesis

For prose summaries rather than raw entries:

```shell
# Prose synthesis of a specific entry type
/log-summarize decision

# Session or day-scoped formatted note
/research-note

# Full project retrospective (dispatches report-drafter agent)
/research-report
```

## You have now...

Learned to query the journal by type, time, and status using both skills and the CLI script.
