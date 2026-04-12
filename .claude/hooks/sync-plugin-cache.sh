#!/bin/bash
# sync-plugin-cache.sh
# PostToolUse hook: syncs plugin source to Claude Code cache after any edit.
# Also warns on version mismatches across plugin.json and marketplace.json.
# Fires on Edit or Write tool calls; no-ops for unrelated files.

REPO_ROOT="/Users/chrissantiago/Dropbox/GitHub/ml-lab"
PLUGINS_JSON="$HOME/.claude/plugins/installed_plugins.json"

# Read tool input from stdin and extract file_path.
# Note: python3 - << 'HEREDOC' makes the heredoc python's stdin, so the piped
# JSON never reaches sys.stdin. Read all of stdin into a shell variable first,
# then pass it to python3 via -c to avoid the stdin conflict.
HOOK_INPUT=$(cat)
FILE_PATH=$(echo "$HOOK_INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
")

# Resolve installPath from Claude Code's plugin registry.
# Tries both @ml-lab and @ml-debate-lab key variants to survive marketplace renames.
get_install_path() {
    python3 - << PYEOF
import json, sys
plugin_name = '$1'
try:
    with open('$PLUGINS_JSON') as f:
        d = json.load(f)
    plugins = d.get('plugins', {})
    # Try exact key first, then strip marketplace suffix and try known variants
    for key in [plugin_name, plugin_name.split('@')[0] + '@ml-lab',
                plugin_name.split('@')[0] + '@ml-debate-lab']:
        entries = plugins.get(key, [])
        if entries:
            print(entries[0].get('installPath', ''))
            raise SystemExit(0)
    print('')
except SystemExit:
    raise
except Exception:
    print('')
PYEOF
}

# Warn if plugin.json and marketplace.json versions are out of sync
check_versions() {
    python3 - << PYEOF
import json

market_path = '$REPO_ROOT/.claude-plugin/marketplace.json'
plugins = [
    ('ml-lab',     '$REPO_ROOT/plugins/ml-lab/.claude-plugin/plugin.json'),
    ('ml-journal', '$REPO_ROOT/plugins/ml-journal/.claude-plugin/plugin.json'),
]

try:
    with open(market_path) as f:
        market = json.load(f)
    market_versions = {p['name']: p['version'] for p in market.get('plugins', [])}
except Exception as e:
    print(f'WARNING: Could not read marketplace.json: {e}')
    raise SystemExit(0)

mismatches = []
for name, path in plugins:
    try:
        with open(path) as f:
            pv = json.load(f).get('version', '?')
        mv = market_versions.get(name, '?')
        if pv != mv:
            mismatches.append(f'  {name}: plugin.json={pv}  marketplace.json={mv}')
    except Exception as e:
        mismatches.append(f'  {name}: could not read plugin.json ({e})')

if mismatches:
    print('VERSION MISMATCH — update marketplace.json to match plugin.json (or vice versa):')
    for m in mismatches:
        print(m)
PYEOF
}

# Sync cache — registry-tracked path + known bare cache path (both may be active)
case "$FILE_PATH" in
  *plugins/ml-journal/*)
    DEST=$(get_install_path "ml-journal@ml-lab")
    [ -n "$DEST" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-journal/" "$DEST/"
    BARE="$HOME/.claude/plugins/cache/ml-journal"
    [ -d "$BARE" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-journal/" "$BARE/"
    ;;
  *plugins/ml-lab/*)
    DEST=$(get_install_path "ml-lab@ml-lab")
    [ -n "$DEST" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-lab/" "$DEST/"
    BARE="$HOME/.claude/plugins/cache/ml-lab"
    [ -d "$BARE" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-lab/" "$BARE/"
    ;;
esac

# Version check — only when a version-bearing file is touched
case "$FILE_PATH" in
  *plugins/*/.claude-plugin/plugin.json|*.claude-plugin/marketplace.json)
    check_versions
    ;;
esac
