#!/bin/bash
# sync-plugin-cache.sh
# PostToolUse hook: syncs plugin source to Claude Code cache after any edit.
# Fires on Edit or Write tool calls; no-ops for unrelated files.

REPO_ROOT="/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab"

# Read tool input from stdin and extract file_path
FILE_PATH=$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
")

case "$FILE_PATH" in
  *plugins/ml-journal/*)
    rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-journal/" \
      "$HOME/.claude/plugins/cache/ml-debate-lab/ml-journal/0.1.0/"
    ;;
  *plugins/ml-lab/*)
    rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-lab/" \
      "$HOME/.claude/plugins/cache/ml-debate-lab/ml-lab/1.5.0/"
    ;;
esac
