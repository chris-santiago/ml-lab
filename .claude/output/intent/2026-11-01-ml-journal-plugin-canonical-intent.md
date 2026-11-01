# Intent: ml-journal plugin is canonical

Frozen 2026-11-01. Changes only by explicit user decision.

> "this (plugins/ml-journal) is the CANONICAL version. everything else should flow from this. the ml-lab repo should use the plugin. everything comes from plugin."
> "what i want: the best designed, robust fixes"
> "i use ml-journal in multiple repos at work ... the broader use is more important"

## Acceptance statements

1. Every ml-journal skill and hook runs the plugin's own `journal_log.py` / `journal_query.py`; none runs a script from the repo's `.project-log/`.
2. A fresh `/log-init` in any repo creates `.project-log/journal.jsonl` and no scripts.
3. `/log-init` in a repo set up the old way removes the copied `.project-log/*.py` and rewrites `CLAUDE.md` lines that call them, leaving `journal.jsonl` intact.
4. The ml-lab repo itself is upgraded the same way and works purely through the plugin; the field validation that existed only in ml-lab's copy (commit 782506d) is in the plugin.
5. A symlinked `.project-log/` or `journal.jsonl` is refused by the plugin scripts, whichever skill or hook calls them.
6. A test fails if any skill, hook, or `CLAUDE.md` template references `.project-log/*.py` again.
