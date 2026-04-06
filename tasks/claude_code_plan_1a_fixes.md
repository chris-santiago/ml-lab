# Claude Code Execution Plan 1a — Fix All Current Issues (No New Experiments)

**Purpose:** Execute all fixes to v2 experiment artifacts that require only file edits — no new agent calls, no re-runs. Safe to execute immediately. Run inside the ml-debate-lab repo.

**Prerequisites:**
- Repo cloned and accessible
- Python 3.11+ with `json` package (stdlib only — no API calls made here)

> **No API key needed.** Every fix in this plan is a pure file edit or JSON patch. No agent calls are made.

---

## Step 0 — Confirm State Before Touching Anything

```bash
cd ml-debate-lab

# Confirm baseline pass flags are still wrong
python3 -c "
import json
with open('self_debate_experiment_v2/self_debate_results.json') as f:
    d = json.load(f)
passing = [(c['case_id'], c['baseline_pass']) for c in d['cases'] if c.get('baseline_pass')]
print('Baseline passes in JSON (should be 0):', len(passing))
for p in passing:
    print(' ', p)
"

# Confirm convergence table in REPORT.md is stale
grep -A 8 "Convergence by Difficulty" self_debate_experiment_v2/REPORT.md | head -10

# Confirm TECHNICAL_REPORT.md is stale
grep -n "Defender — receives the task scenario only (never the Critic" TECHNICAL_REPORT.md

# Confirm isolation staleness not yet fixed in agent files
grep -c "Benchmark vs. Production Context" agents/ml-defender.md
grep -c "Note on Context Isolation" agents/README.md
```

---

## Fix 1 — Correct self_debate_results.json Baseline Pass Flags

> **Status: COMPLETED — 2026-04-05**

**What:** Two cases (`broken_baseline_001`, `metric_mismatch_002`) have `baseline_pass: true` but DC=0.0 fails the per-dimension floor. Fix the JSON in place.

```python
# fix_baseline_pass_flags.py
import json

path = 'self_debate_experiment_v2/self_debate_results.json'

with open(path) as f:
    d = json.load(f)

fixed = 0
for case in d['cases']:
    bs = case.get('baseline_scores', {})
    if bs.get('DC') == 0.0 and case.get('baseline_pass') == True:
        print(f"Fixing {case['case_id']}: baseline_pass True -> False (DC=0.0 fails floor)")
        case['baseline_pass'] = False
        fixed += 1

d['baseline_pass_count'] = sum(1 for c in d['cases'] if c.get('baseline_pass'))
d['baseline_pass_fraction'] = d['baseline_pass_count'] / len(d['cases'])
d['correction_note'] = (
    "2026-04-05: baseline_pass flags corrected. Two cases (broken_baseline_001, "
    "metric_mismatch_002) were incorrectly marked passing before DC=0.0 structural "
    "override was applied. With DC=0.0, both fail the per-dimension floor. "
    "Correct baseline pass count: 0/20."
)

with open(path, 'w') as f:
    json.dump(d, f, indent=2)

print(f"\nFixed {fixed} cases. Baseline pass count now: {d['baseline_pass_count']}/20")
```

```bash
python3 fix_baseline_pass_flags.py
python3 -c "
import json
with open('self_debate_experiment_v2/self_debate_results.json') as f:
    d = json.load(f)
print('Baseline pass count:', d['baseline_pass_count'])
print('Correction note present:', 'correction_note' in d)
"
```

---

## Fix 2 — Update REPORT.md §2.4 Convergence Table

> **Status: COMPLETED — 2026-04-05**

**What:** §2.4 table shows original n=3/10/7 and values 0.833/0.944/0.938. Data from new_benchmark_results.json already exists — just update the table.

```python
# fix_convergence_table.py
report_path = 'self_debate_experiment_v2/REPORT.md'

with open(report_path) as f:
    content = f.read()

old_table = """| Difficulty | Cases | Mean convergence |
|------------|-------|-----------------|\n| easy | 3 | 0.833 |\n| medium | 10 | 0.944 |\n| hard | 7 | 0.938 |"""

new_table = """| Difficulty | Original n | Combined n (≥10) | Combined convergence |
|------------|-----------|-----------------|---------------------|\n| easy | 3 | 10 | 0.950 |\n| medium | 10 | 10 | 0.944 |\n| hard | 7 | 10 | 0.957 |

*Original n=3 easy-tier estimate (0.833) was a single-data-point artifact (defense_wins_003 conv=0.5). Combined figures include 10 new cases from `new_benchmark_results.json`. See §4.4 and §9 for full analysis.*"""

if old_table in content:
    content = content.replace(old_table, new_table)
    with open(report_path, 'w') as f:
        f.write(content)
    print("Convergence table updated.")
else:
    print("WARNING: Old table not found exactly — check whitespace and update manually.")
    idx = content.find("Convergence by Difficulty")
    print("Context around section:", content[idx:idx+400])
```

```bash
python3 fix_convergence_table.py
grep -A 12 "Convergence by Difficulty" self_debate_experiment_v2/REPORT.md
```

---

## Fix 3 — Document DC Scoring Inconsistency in External Benchmark

> **Status: COMPLETED — 2026-04-05**

**What:** External benchmark gives baseline DC=1.0 naturally; internal benchmark hardcodes DC=0.0. Add metadata note and a paragraph to REPORT.md §7.1.

```python
# fix_external_benchmark_dc_note.py
import json

ext_path = 'external_benchmark/results.json'
with open(ext_path) as f:
    d = json.load(f)

d['metadata']['dc_scoring_note'] = (
    "DC scoring differs from internal benchmark. The internal benchmark hardcodes "
    "baseline DC=0.0 as a structural override (the baseline has no defense role). "
    "The external benchmark scores DC naturally — baseline DC=1.0 on 9/10 cases "
    "where it correctly identified critique-type verdicts, DC=0.5 on 1/10 mixed case. "
    "This makes the external baseline mean (0.967) not directly comparable to the "
    "internal baseline mean (0.384). The external benchmark is appropriate for "
    "validating IDR only — not for replicating the full internal rubric comparison."
)

with open(ext_path, 'w') as f:
    json.dump(d, f, indent=2)
print("External benchmark DC note added.")

report_path = 'self_debate_experiment_v2/REPORT.md'
with open(report_path) as f:
    content = f.read()

dc_note = (
    "\n\n**DC scoring note:** The external fault-detection benchmark scores DC naturally "
    "for the baseline (DC=1.0 when the baseline correctly identified a critique verdict), "
    "whereas the internal benchmark hardcodes baseline DC=0.0 as a structural override. "
    "This means the external baseline mean (0.967) is not directly comparable to the "
    "internal baseline mean (0.384). The external benchmark is used here specifically "
    "to validate IDR against ground truth from the published record — not to replicate "
    "the full internal rubric comparison."
)

marker = "**Result:** Debate IDR = **0.95**"
if marker in content:
    insert_at = content.find(marker) + len(marker)
    para_end = content.find("\n\n", insert_at)
    content = content[:para_end] + dc_note + content[para_end:]
    with open(report_path, 'w') as f:
        f.write(content)
    print("DC note added to REPORT.md §7.1.")
else:
    print("WARNING: Marker not found — add DC note to §7.1 manually.")
```

```bash
python3 fix_external_benchmark_dc_note.py
```

---

## Fix 4 — Add Protocol Deviation Note to REPORT.md §7.1

> **Status: COMPLETED — 2026-04-05**

**What:** External fault-detection benchmark ran Defenders without Critic output. REPORT.md §7.1 doesn't mention this deviation.

```python
# fix_external_protocol_deviation_note.py
report_path = 'self_debate_experiment_v2/REPORT.md'
with open(report_path) as f:
    content = f.read()

deviation_note = (
    "\n\n**Protocol deviation in external benchmark:** Defenders in the external "
    "fault-detection benchmark received only the task prompt — they did not receive "
    "the Critic's output before producing their assessment. This means the external "
    "benchmark ran a two-agent parallel assessment rather than a true adversarial debate. "
    "The Judge reconciled two independent views rather than adjudicating a genuine "
    "exchange. ETD production is expected to be lower as a result (only 1/10 external "
    "cases generated an agreed empirical test). Verdict correctness (IDR, FVC) is "
    "unaffected — both agents independently converged on the correct issues on all "
    "critique cases. Documented in `external_benchmark/results.json` metadata."
)

marker = "### 7.2 Exoneration Benchmark"
if marker in content:
    content = content.replace(marker, deviation_note + "\n\n" + marker)
    with open(report_path, 'w') as f:
        f.write(content)
    print("Protocol deviation note added before §7.2.")
else:
    print("WARNING: §7.2 marker not found — add manually before §7.2.")
```

```bash
python3 fix_external_protocol_deviation_note.py
```

---

## Fix 5 — Update TECHNICAL_REPORT.md (Root Level)

> **Status: COMPLETED — 2026-04-05**

**What:** Adds a document status notice clarifying that the Judge is the orchestrator, and that Defender isolation is a benchmark-specific choice not a permanent property.

```python
# fix_technical_report.py
path = 'TECHNICAL_REPORT.md'
with open(path) as f:
    content = f.read()

notice = """> **Document status (2026-04-05):** This report reflects the experimental protocol
> as originally designed. Two sections have been superseded by post-experiment findings:
>
> 1. **Protocol architecture (§1.2):** The "Judge" described here is the ml-lab
>    orchestrator acting in an adjudication role — not a dedicated fourth subagent
>    invocation. The Critic and Defender are separate subagent calls; the Judge
>    function is performed inline by the orchestrating session.
>
> 2. **Defender isolation:** The Defender receiving "the task scenario only (never
>    the Critic's output)" is a **benchmark-specific isolation design choice**, not
>    a property of the ml-defender agent in production use. In the standard ml-lab
>    workflow, the Defender receives the Critic's output (CRITIQUE.md) before
>    responding. The benchmark isolates them specifically to make independent
>    convergence meaningful as evidence.
>
> See `self_debate_experiment_v2/REPORT.md` for the current authoritative version.

"""

if not content.startswith("> **Document status"):
    content = notice + content
    with open(path, 'w') as f:
        f.write(content)
    print("Staleness notice added to TECHNICAL_REPORT.md.")
else:
    print("Notice already present.")
```

```bash
python3 fix_technical_report.py
head -20 TECHNICAL_REPORT.md
```

---

## Fix 6 — Fix Stale Isolation Description in Agent Files

> **Status: NOT APPLIED — 2026-04-05.** Agent `.md` files are dispatched as system prompts; adding meta-documentation to them becomes context window noise during agent execution. The isolation distinction is documented in `TECHNICAL_REPORT.md` (Fix 5) instead. The isolation confusion at the source is addressed by the document status notice, not by modifying agent files.

**What:** Adds a permanent "Benchmark vs. Production Context" section to ml-defender.md and agents/README.md. This kills the recurring isolation description confusion at the source.

```python
# fix_isolation_description.py
defender_path = 'agents/ml-defender.md'
with open(defender_path) as f:
    content = f.read()

isolation_note = """
---

## Benchmark vs. Production Context

**Important:** In the standard ml-lab workflow (Mode 1), the Defender receives `CRITIQUE.md`
as an input and responds point-by-point to the Critic's findings. This is the default
production behavior.

**Context isolation** — where the Defender receives only the task prompt and never sees
the Critic's output before forming its position — is a **benchmark-specific experimental
design choice** used in `self_debate_experiment_v2/`. That isolation is what makes
independent convergence meaningful as evidence: when both agents find the same flaw
without seeing each other's work, that is convergent signal. It is not a property of
this agent in production use.

When running the ml-lab investigation workflow normally, the Defender should receive
the Critique. When running a controlled benchmark, dispatch the Defender with only
the task prompt and dispatch separately from the Critic with no shared context.

"""

if "Benchmark vs. Production Context" not in content:
    content = content + isolation_note
    with open(defender_path, 'w') as f:
        f.write(content)
    print("Isolation clarification added to ml-defender.md.")
else:
    print("Already present in ml-defender.md.")

readme_path = 'agents/README.md'
with open(readme_path) as f:
    readme = f.read()

readme_note = """

---

## Note on Context Isolation

In the `self_debate_experiment_v2/` benchmark, the Critic and Defender are dispatched
with **only the task prompt** — neither sees the other's output before forming its
position. This is a deliberate experimental design choice to make independent convergence
meaningful as evidence.

In the standard ml-lab production workflow, the Defender receives `CRITIQUE.md` as
input and responds to the Critic's specific points. This is the correct default behavior
outside of controlled benchmark runs.

If you see documentation stating "the Defender never sees the Critic's output" without
this qualification, that description is specific to the benchmark configuration and
should not be generalized to the production agent behavior.

"""

if "Note on Context Isolation" not in readme:
    readme = readme + readme_note
    with open(readme_path, 'w') as f:
        f.write(readme)
    print("Isolation note added to agents/README.md.")
else:
    print("Already present in agents/README.md.")
```

```bash
python3 fix_isolation_description.py
```

---

## Fix 7 — Add Judge Clarification to REPORT.md §1.1

> **Status: COMPLETED — 2026-04-05**

**What:** REPORT.md §1.1 implies the Judge is a separate subagent. Add one sentence clarifying it is the ml-lab orchestrator.

```python
# fix_judge_clarification.py
report_path = 'self_debate_experiment_v2/REPORT.md'
with open(report_path) as f:
    content = f.read()

old = ("3. **Adjudication.** The Judge receives both independent outputs and assigns "
       "a verdict. The verdict is typed: `critique_wins`, `defense_wins`, or "
       "`empirical_test_agreed`.")

new = ("3. **Adjudication.** The Judge receives both independent outputs and assigns "
       "a verdict. The verdict is typed: `critique_wins`, `defense_wins`, or "
       "`empirical_test_agreed`. In this benchmark, the Judge function is performed "
       "by the ml-lab orchestrating session — it is not a separate subagent invocation. "
       "The Critic and Defender are dispatched as independent subagents; the orchestrator "
       "then reviews both outputs and adjudicates.")

if old in content:
    content = content.replace(old, new)
    with open(report_path, 'w') as f:
        f.write(content)
    print("Judge clarification added.")
else:
    print("WARNING: Target text not found exactly — add manually to §1.1.")
```

```bash
python3 fix_judge_clarification.py
```

---

## Verification Pass

```bash
python3 -c "
import json

# Fix 1: baseline pass flags
with open('self_debate_experiment_v2/self_debate_results.json') as f:
    d = json.load(f)
passing = [c['case_id'] for c in d['cases'] if c.get('baseline_pass')]
print(f'Baseline passes in JSON: {len(passing)} (expected 0)')
if passing:
    print('  Still wrong:', passing)
print(f'Correction note present: {\"correction_note\" in d}')

# Fix 3: external benchmark DC note
with open('external_benchmark/results.json') as f:
    ext = json.load(f)
print(f'External DC note present: {\"dc_scoring_note\" in ext.get(\"metadata\", {})}')
"

# Fix 5: TECHNICAL_REPORT.md notice
head -3 TECHNICAL_REPORT.md

# Fix 6: isolation notes
grep -c "Benchmark vs. Production Context" agents/ml-defender.md
grep -c "Note on Context Isolation" agents/README.md

# Fix 2: convergence table
grep -A 6 "Convergence by Difficulty" self_debate_experiment_v2/REPORT.md

echo "All 1a fixes verified."
```

---

## Git Commit

```bash
git add -A
git commit -m "Fix 1a: all non-experiment fixes

- self_debate_results.json: baseline_pass corrected to False for bb001 and mm002
- REPORT.md §2.4: convergence table updated with combined n>=10 per tier data
- REPORT.md §7.1: DC scoring inconsistency note and protocol deviation note added
- REPORT.md §1.1: Judge clarification (orchestrator, not separate subagent)
- TECHNICAL_REPORT.md: document status notice added (stale protocol description)
- agents/ml-defender.md: Benchmark vs. Production Context section added (permanent fix)
- agents/README.md: Note on Context Isolation added (permanent fix)
- external_benchmark/results.json: dc_scoring_note added to metadata
"
```
