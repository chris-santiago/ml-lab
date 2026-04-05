# claude-ml-lab — Plugin Distribution Plan

**Plugin name:** `claude-ml-lab`
**Marketplace name:** `ml-debate-lab`
**Scope:** ml-lab trio (ml-lab, ml-critic, ml-defender) — `research-reviewer` and `research-reviewer-lite` live in `agents/` but are excluded from v1; candidate for a separate plugin or v2 expansion
**Distribution:** Claude Code native plugin system via `marketplace.json` hosted in this GitHub repo

---

## How it works

Claude Code has a built-in plugin system. A **marketplace** is a git repo containing a `.claude-plugin/marketplace.json` catalog. Users add your marketplace once, then install individual plugins from it. Claude Code handles all file management natively — no custom install scripts needed.

This repo is both the plugin source and the marketplace.

---

## What users get after install

```
~/.claude/agents/
  ml-lab.md
  ml-critic.md
  ml-defender.md

~/.claude/agent-memory/ml-lab/
  MEMORY.md   (created by ml-lab on first investigation run)
```

Claude Code picks up the agents automatically. Users invoke the workflow by describing an ML hypothesis — Claude Code routes to `ml-lab` via the description field.

---

## Repository layout (new files only)

```
ml-debate-lab/
├── agents/
│   ├── ml-lab.md
│   ├── ml-critic.md
│   ├── ml-defender.md
│   ├── research-reviewer.md     (out of v1 scope)
│   ├── research-reviewer-lite.md (out of v1 scope)
│   └── ...
└── .claude-plugin/
    ├── plugin.json              (plugin manifest)
    └── marketplace.json         (marketplace catalog)
```

No `plugin/` directory. No Node.js. No npm publish step. The repo itself is the distribution artifact.

---

## Step 1 — `.claude-plugin/plugin.json`

The plugin manifest declares what gets installed.

```json
{
  "name": "claude-ml-lab",
  "description": "Structured 10-step ML hypothesis investigation for Claude Code — critic, defender, orchestrator, and peer review.",
  "version": "1.1.0",
  "license": "MIT",
  "agents": [
    "./agents/ml-lab.md",
    "./agents/ml-critic.md",
    "./agents/ml-defender.md"
  ]
}
```

The `agents` paths are relative to the plugin root (the repo root, which is also where `.claude-plugin/` lives). Claude Code copies these files to `~/.claude/agents/` on install.

---

## Step 2 — `.claude-plugin/marketplace.json`

The marketplace catalog lists the plugin and where to find it. Since the plugin lives in the same repo as the marketplace, `source` is `"./"`.

```json
{
  "name": "ml-debate-lab",
  "owner": {
    "name": "chris-santiago"
  },
  "metadata": {
    "description": "ML hypothesis investigation agents for Claude Code"
  },
  "plugins": [
    {
      "name": "claude-ml-lab",
      "source": "./",
      "description": "Structured 10-step ML hypothesis investigation — critic, defender, orchestrator, and peer review.",
      "version": "1.1.0",
      "license": "MIT",
      "keywords": ["ml", "hypothesis-testing", "agents", "research"]
    }
  ]
}
```

---

## Step 3 — User install

```shell
# In Claude Code:
/plugin marketplace add chris-santiago/ml-debate-lab
/plugin install claude-ml-lab@ml-debate-lab
```

Or from the CLI:

```bash
claude plugin marketplace add chris-santiago/ml-debate-lab
claude plugin install claude-ml-lab@ml-debate-lab
```

---

## Step 4 — Uninstall

```shell
/plugin uninstall claude-ml-lab@ml-debate-lab
```

Agent memory at `~/.claude/agent-memory/ml-lab/` is NOT removed. Delete it manually to clear investigation history.

---

## Step 5 — Version management

When agent files change:

1. Update the relevant `.md` file(s) in `agents/` (source of truth)
2. Bump version in `.claude-plugin/plugin.json` (semver: patch for prompt tweaks, minor for new modes or new steps, major for protocol changes — e.g., Step 10 addition = 1.0.0 → 1.1.0)
3. Push to GitHub

Users update by running:

```shell
/plugin marketplace update ml-debate-lab
/plugin install claude-ml-lab@ml-debate-lab
```

No publish step. No npm. The git push is the release.

---

## A note on npm

npm is supported as a plugin *source type* within a marketplace entry (alongside `github`, `url`, `git-subdir`). It is NOT a replacement for the marketplace mechanism — the user-facing install is always `/plugin install`, regardless of the underlying source. Publishing to npm could be useful for private registries or enterprise deployments, but adds no benefit for a public GitHub-hosted plugin. The git-based approach here is simpler and gets automatic update propagation via `/plugin marketplace update`.

---

## Pre-publish checklist

- [ ] `.claude-plugin/plugin.json` created with correct paths and version
- [ ] `.claude-plugin/marketplace.json` created with correct plugin entry
- [ ] `claude plugin validate .` run from repo root — no errors
- [ ] Add marketplace locally and install to test: `/plugin marketplace add ./` then `/plugin install claude-ml-lab@ml-debate-lab`
- [ ] Verify all three agent files appear in `~/.claude/agents/` after install
- [ ] Verify Claude Code picks up ml-lab (describe an ML hypothesis)
- [ ] Push to GitHub
- [ ] Test from a clean machine: `/plugin marketplace add chris-santiago/ml-debate-lab` then `/plugin install claude-ml-lab@ml-debate-lab`
- [ ] Update `agents/README.md` with the plugin install as the primary path

---

## What does NOT change

- Agent file contents — all three `.md` files are used as-is
- Memory system spec inside `ml-lab.md` — kept fully embedded; ml-lab creates `~/.claude/agent-memory/ml-lab/MEMORY.md` on first investigation run
- Subagent dispatch design — ml-critic and ml-defender remain internal; only ml-lab is user-facing
- Experiment artifacts, reports, and analysis — not referenced by plugin.json, not installed
