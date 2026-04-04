# claude-ml-lab — npm Plugin Plan

**Package name:** `claude-ml-lab`
**Scope:** ml-lab trio only (ml-lab, ml-critic, ml-defender)
**Design:** self-contained agent files, memory system kept as-is

---

## What this produces

After `npx claude-ml-lab install`, users have:

```
~/.claude/agents/
  ml-lab.md
  ml-critic.md
  ml-defender.md

~/.claude/agent-memory/ml-lab/
  MEMORY.md   (empty index, created on first install)
```

Claude Code picks up the agents automatically. Users invoke the workflow by describing an ML hypothesis — Claude Code routes to `ml-lab` via the description field.

---

## Repository layout (new files only)

All plugin-related files live under `plugin/`. Experiment work stays under `agents/`, `self_debate_experiment_v2/`, etc. — untouched.

```
ml-debate-lab/
├── agents/
│   ├── ml-lab.md          (no changes)
│   ├── ml-critic.md       (no changes)
│   ├── ml-defender.md     (no changes)
│   ├── README.md          (add npx install as primary path)
│   └── PLUGIN_PLAN.md     (this file)
└── plugin/
    ├── package.json        (npm package metadata)
    ├── README.md           (user-facing install + usage docs)
    └── bin/
        └── claude-ml-lab.js  (CLI entry point)
```

The `plugin/` directory is the npm package root — `npm publish` is run from there. The agent `.md` files are referenced from `../agents/` at install time and copied into the published package via the `files` field in `package.json`.

No agent file content changes. All three files are already sanitized and ready.

---

## Step 1 — `plugin/package.json`

```json
{
  "name": "claude-ml-lab",
  "version": "1.0.0",
  "description": "ML hypothesis investigation agents for Claude Code — critic, defender, and orchestrator.",
  "keywords": ["claude", "claude-code", "ml", "agents", "hypothesis-testing"],
  "license": "MIT",
  "bin": {
    "claude-ml-lab": "./bin/claude-ml-lab.js"
  },
  "files": [
    "agents/ml-lab.md",
    "agents/ml-critic.md",
    "agents/ml-defender.md",
    "bin/claude-ml-lab.js",
    "README.md"
  ],
  "engines": {
    "node": ">=18"
  }
}
```

`files` whitelist is critical — it keeps experiment data, reports, and analysis out of the published package. Paths are relative to `plugin/`, so `agents/` here means `plugin/agents/` (the copied agent files, not the source in the repo root).

---

## Step 2 — `plugin/bin/claude-ml-lab.js`

Single-file Node.js CLI. No dependencies. Supports two commands: `install` and `uninstall`.

When installed via npm/npx, the package root is `plugin/`. The agent files are copied into `plugin/agents/` at publish time (see Step 3), so `SOURCE_DIR` resolves to `plugin/agents/` at runtime.

```javascript
#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const os = require("os");

const AGENTS = ["ml-lab.md", "ml-critic.md", "ml-defender.md"];
const AGENTS_DIR = path.join(os.homedir(), ".claude", "agents");
const MEMORY_DIR = path.join(os.homedir(), ".claude", "agent-memory", "ml-lab");
const SOURCE_DIR = path.join(__dirname, "..", "agents"); // plugin/agents/

const MEMORY_INDEX = `# ml-lab Agent Memory\n\n<!-- Populated by ml-lab as investigations run -->\n`;

function install() {
  // Create ~/.claude/agents/ if needed
  fs.mkdirSync(AGENTS_DIR, { recursive: true });

  // Copy agent files
  for (const file of AGENTS) {
    const src = path.join(SOURCE_DIR, file);
    const dest = path.join(AGENTS_DIR, file);
    fs.copyFileSync(src, dest);
    console.log(`  ✓ installed ${file}`);
  }

  // Create memory directory and empty index if not present
  fs.mkdirSync(MEMORY_DIR, { recursive: true });
  const memIndex = path.join(MEMORY_DIR, "MEMORY.md");
  if (!fs.existsSync(memIndex)) {
    fs.writeFileSync(memIndex, MEMORY_INDEX);
    console.log(`  ✓ created agent memory at ${MEMORY_DIR}`);
  } else {
    console.log(`  · agent memory already exists — skipping`);
  }

  console.log("\nclaude-ml-lab installed.");
  console.log("Describe an ML hypothesis to Claude Code to start an investigation.\n");
}

function uninstall() {
  let removed = 0;
  for (const file of AGENTS) {
    const dest = path.join(AGENTS_DIR, file);
    if (fs.existsSync(dest)) {
      fs.rmSync(dest);
      console.log(`  ✓ removed ${file}`);
      removed++;
    }
  }
  if (removed === 0) {
    console.log("  · no agents found — nothing to remove");
  }
  console.log("\nAgent memory at ~/.claude/agent-memory/ml-lab/ was NOT removed.");
  console.log("Delete it manually if you want to clear investigation history.\n");
}

const cmd = process.argv[2];
if (cmd === "install") {
  install();
} else if (cmd === "uninstall") {
  uninstall();
} else {
  console.log("Usage:");
  console.log("  npx claude-ml-lab install     Install agents to ~/.claude/agents/");
  console.log("  npx claude-ml-lab uninstall   Remove agents from ~/.claude/agents/");
}
```

---

## Step 3 — Update `agents/README.md`

Add the npm install as the primary path. Current manual `cp` stays as fallback.

**New opening section:**

```markdown
## Install

```bash
npx claude-ml-lab install
```

This copies the three agent files to `~/.claude/agents/` and creates
`~/.claude/agent-memory/ml-lab/` for persistent investigation memory.

To remove:

```bash
npx claude-ml-lab uninstall
```

**Alternative — manual install:**

```bash
cp agents/ml-lab.md ~/.claude/agents/
cp agents/ml-critic.md ~/.claude/agents/
cp agents/ml-defender.md ~/.claude/agents/
```
```

---

## Step 3 — Copy agent files into `plugin/agents/`

The npm package is published from `plugin/`. The agent source files live in `agents/` (repo root). Before publishing, copy them into `plugin/agents/` so the `files` whitelist can bundle them.

```bash
mkdir -p plugin/agents
cp agents/ml-lab.md plugin/agents/
cp agents/ml-critic.md plugin/agents/
cp agents/ml-defender.md plugin/agents/
```

Add `plugin/agents/` to `.gitignore` — these are copies, not the source of truth.

```
# .gitignore addition
plugin/agents/
```

On future agent updates: re-copy and re-publish with a bumped version.

---

## Step 4 — Publish to npm

Prerequisites: npm account created at npmjs.com, logged in locally via `npm login`.

```bash
# Copy agent files into the package (see Step 3)
mkdir -p plugin/agents
cp agents/ml-lab.md agents/ml-critic.md agents/ml-defender.md plugin/agents/

# Publish from the plugin directory
cd plugin
npm login                    # one-time, prompts for credentials
npm publish --access public  # publishes claude-ml-lab@1.0.0
```

After publish, users install with:

```bash
npx claude-ml-lab install
```

Or as a persistent global CLI:

```bash
npm install -g claude-ml-lab
claude-ml-lab install
```

---

## Step 5 — Version management

When agent files change (prompt updates, new modes, bug fixes):

1. Update the relevant `.md` file(s) in `agents/` (the source of truth)
2. Re-copy into `plugin/agents/`
3. Bump version in `plugin/package.json` (semver: patch for prompt tweaks, minor for new modes, major for protocol changes)
4. `cd plugin && npm publish`

Users update by re-running `npx claude-ml-lab install` — it overwrites the agent files in `~/.claude/agents/` with the latest version. Memory is never touched on updates.

---

## Pre-publish checklist

- [ ] npm account created at npmjs.com
- [ ] `npm login` run locally (from `plugin/` directory)
- [ ] Verify `claude-ml-lab` is available on npm (check npmjs.com/package/claude-ml-lab)
- [ ] Agent files copied into `plugin/agents/`
- [ ] `plugin/agents/` added to `.gitignore`
- [ ] `node plugin/bin/claude-ml-lab.js install` tested locally end-to-end
- [ ] `node plugin/bin/claude-ml-lab.js uninstall` tested
- [ ] `npx claude-ml-lab install` tested from a clean directory (simulates how users will run it)
- [ ] Verify agents appear in Claude Code after install (restart Claude Code if needed)
- [ ] `cd plugin && npm publish --dry-run` — inspect file list matches `files` whitelist

---

## What does NOT change

- Agent file contents — all three `.md` files are published as-is
- Memory system spec inside `ml-lab.md` — kept fully embedded
- Subagent dispatch design — ml-critic and ml-defender remain internal; only ml-lab is user-facing
- Experiment artifacts, reports, and analysis — excluded by `files` whitelist
