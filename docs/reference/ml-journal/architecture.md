# Architecture

ml-journal is a four-layer system with no background daemons and no external dependencies beyond `python3` and `git`.

## Layer diagram

```
judgment layer     →  Claude skills (extract, classify, construct args)
agent layer        →  Subagents (isolated context ingestion for heavy synthesis)
mechanical layer   →  Python scripts (validate, serialize, write)
storage            →  .project-log/journal.jsonl (per-repo, append-only)
```

## Judgment layer

Claude Code skills (`/log-entry`, `/checkpoint`, `/log-commit`, etc.) handle the parts that require reasoning: extracting the right fields from conversation context, classifying entry types, constructing arguments for the mechanical layer.

## Agent layer

The `report-drafter` agent is dispatched by `/research-report` for heavy synthesis that benefits from isolated context. It reads the full journal, git history, and supplementary docs to produce a 9-section draft. The agent never writes files directly — it returns a draft to the skill for confirmation.

## Mechanical layer

Two stdlib-only Python scripts handle validation and serialization:

- **`journal_log.py`** — validates fields, constructs the envelope (`id`, `timestamp`, `type`, `project`, `session_id`), appends to `journal.jsonl`
- **`journal_query.py`** — read operations: status, list, filter, search

The scripts live in the installed skills (`skills/log-init/scripts/`), never in the repo, and can be invoked directly from the command line (see [Scripts](../scripts.md)).

## Storage

`journal.jsonl` is a plain JSONL file — one JSON object per line, append-only. Each entry has a unique ID, timestamp, type, and session ID. The file is committed to git alongside the code it documents.

## Data flow

```mermaid
flowchart LR
    A[Conversation context] -->|skill extracts fields| B["/log-entry"]
    B -->|validates + serializes| C["journal_log.py"]
    C -->|appends| D["journal.jsonl"]
    D -->|reads| E["journal_query.py"]
    D -->|reads| F["/research-report → report-drafter"]
```

## Chain workflows

Entry types chain naturally during a session:

```mermaid
flowchart LR
    A[Bug identified] -->|auto-propose| B["issue"]
    B --> C[Fix verified]
    C -->|auto-propose| D["resolution"]
    D --> E[Root cause understood]
    E -->|auto-propose| F["lesson"]
```

```mermaid
flowchart LR
    A[Hypothesis formed] -->|manual| B["hypothesis"]
    B --> C[Experiment run]
    C -->|auto-propose| D["experiment"]
    D --> E{outcome}
    E -->|unexpected| F["discovery"]
    E -->|direction confirmed| G["decision"]
```

## Synthesis ladder

```mermaid
flowchart TB
    J[journal.jsonl] --> S["/log-summarize<br/>prose by type"]
    S -->|reused as input| N["/research-note<br/>session-scoped note"]
    J -->|end of phase| R["/research-report<br/>dispatches report-drafter"]
    R --> RP[RESEARCH_REPORT.md]
```
