# Checkpoint & Resume Sessions

## Save session state

Before ending a session, compacting context, or switching tasks:

```shell
/checkpoint
```

This writes a `checkpoint` entry to the journal containing:

- `in_progress` — what you're currently working on
- `pending_decisions` — unresolved choices
- `recently_completed` — what you just finished
- `key_context` — important state that would be lost
- `git_state` — current branch and uncommitted changes
- `open_threads` — things to pick up later

## Resume in a new session

At the start of a new session:

```shell
/resume
```

This loads the most recent checkpoint into context. Claude picks up where you left off without you re-explaining the state.

## Automate with hooks

The ml-journal plugin registers two hooks automatically when it is installed (`plugins/ml-journal/hooks/hooks.json`). No settings changes are needed:

- **PreCompact** auto-writes a checkpoint before `/compact` runs
- **SessionStart** auto-injects the latest checkpoint at session start, in repos whose journal this machine trusts

Both hooks exit silently in repos without `.project-log/journal.jsonl`, so they only act once you have run `/log-init`.

Checkpoint text comes from the repo, so SessionStart only loads it from a journal this machine trusts. `/log-init` trusts a journal it creates and asks before trusting an existing one (a cloned repo, a new machine, or a repo set up before version 0.5). In an untrusted repo the hook shows a short notice instead, and `/resume` asks before showing the checkpoint. Run `/log-init` once in such a repo to trust it.

If your organization blocks hooks (`disableAllHooks`, or the managed `allowManagedHooksOnly`), the hooks don't run. Checkpoint and resume still work through the skills: run `/checkpoint` before `/compact` and `/resume` at session start.

!!! warning
    If you previously added ml-journal hooks to `.claude/settings.local.json` by hand, remove them. Plugin hooks run in addition to settings hooks, so keeping both writes duplicate checkpoints.

## Tips

- Checkpoint early and often — the cost is one journal entry
- The first session in a new repo has no checkpoint to resume; `/resume` will report nothing
- Hooks come with the plugin, so every developer who installs ml-journal gets them

## You have now...

Set up session persistence across context boundaries using `/checkpoint`, `/resume`, and the plugin's automation hooks.
