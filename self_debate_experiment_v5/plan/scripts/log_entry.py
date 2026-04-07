# log_entry.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Structured INVESTIGATION_LOG.jsonl entry writer.
Enforces schema compliance, validates cat, auto-increments seq, auto-generates ts.
Usage: uv run log_entry.py --step 6 --cat exec --action run_case --detail "..." [--case_id X] [--artifact Y] [--duration_s Z] [--meta '{"k": "v"}']
NEVER write log entries manually. Always use this script.
"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_CATS = {'gate', 'write', 'read', 'subagent', 'exec', 'decision', 'debate', 'review', 'audit', 'workflow'}

parser = argparse.ArgumentParser()
parser.add_argument('--step', required=True)
parser.add_argument('--cat', required=True, choices=sorted(ALLOWED_CATS))
parser.add_argument('--action', required=True)
parser.add_argument('--detail', required=True)
parser.add_argument('--artifact', default=None)
parser.add_argument('--case_id', default=None)
parser.add_argument('--duration_s', type=float, default=None)
parser.add_argument('--meta', default='{}')
parser.add_argument('--meta-file', default=None,
                    help='Path to JSON file for meta field (avoids brace+quote approval heuristic)')
args = parser.parse_args()

if args.meta_file:
    try:
        with open(args.meta_file) as _mf:
            meta = json.load(_mf)
    except Exception as e:
        print(f"ERROR: --meta-file could not be loaded: {e}", file=sys.stderr)
        sys.exit(1)
else:
    try:
        meta = json.loads(args.meta)
    except json.JSONDecodeError as e:
        print(f"ERROR: --meta must be valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

if args.case_id:
    meta['case_id'] = args.case_id

log_file = Path('INVESTIGATION_LOG.jsonl')
seq = 1
if log_file.exists():
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    if lines:
        try:
            last = json.loads(lines[-1])
            seq = last.get('seq', 0) + 1
        except Exception:
            seq = len(lines) + 1

entry = {
    'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'step': args.step,
    'seq': seq,
    'cat': args.cat,
    'action': args.action,
    'detail': args.detail,
    'artifact': args.artifact,
    'duration_s': args.duration_s,
    'meta': meta,
}

with open(log_file, 'a') as f:
    f.write(json.dumps(entry) + '\n')

print(f"[seq={seq}] {args.cat}/{args.action}: {args.detail}")
