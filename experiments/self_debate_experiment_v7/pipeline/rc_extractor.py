# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28",
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
RC Extractor — v7 Pipeline Phase 1

Four sequential stages:
  RC-1: Fetch OpenReview API (RC 2020–2023) + ReScience C (GitHub API)
        → rc_candidates/reports_fetched.json
  RC-2: Flaw extraction + task_prompt construction (GPT-5.4 via OpenRouter)
        → rc_candidates/flaws_extracted.json
  RC-3: must_not_claim extraction (GPT-5.4 via OpenRouter)
        → rc_candidates/must_not_claim.json
  RC-4: Filtering + contamination gate
        → rc_candidates/rc_cases_raw.json

Contamination prevention (PM1 recurrence risk):
  task_prompt must come from the original paper's methodology description, NOT
  from the reproducer's critique. RC-2 explicitly separates the two. RC-4 applies
  a keyword gate to reject any task_prompt containing reproducer-language patterns.

Usage:
    uv run pipeline/rc_extractor.py --stage rc1        # fetch only (no LLM calls)
    uv run pipeline/rc_extractor.py --stage rc2        # extract flaws (GPT-5.4)
    uv run pipeline/rc_extractor.py --stage rc3        # extract must_not_claim (GPT-5.4)
    uv run pipeline/rc_extractor.py --stage rc4        # filter + contamination gate
    uv run pipeline/rc_extractor.py --all              # run all stages sequentially
    uv run pipeline/rc_extractor.py --all --dry-run    # simulate (no API calls)
    uv run pipeline/rc_extractor.py --stage rc1 --discover-venues  # probe OpenReview for valid venues
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from openai import OpenAI
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PIPELINE_DIR = Path(__file__).parent
RUN_DIR = PIPELINE_DIR / "run"
RC_CANDIDATES_DIR = RUN_DIR / "rc_candidates"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENREVIEW_BASE_URL = "https://api2.openreview.net"
GITHUB_API_BASE = "https://api.github.com"
API_TIMEOUT = 180.0
RESCIENCE_REPO = "ReScience/MLRC"   # ML Reproducibility Challenge accepted papers
RESCIENCE_BRANCH = "main"

# ---------------------------------------------------------------------------
# OpenReview venue candidates
# The exact invitation strings vary by year. We try multiple patterns per year
# and log actual yield so the user can see which venues returned data.
# ---------------------------------------------------------------------------

OPENREVIEW_VENUE_PATTERNS: list[dict] = [
    # Year 2023
    {"year": 2023, "invitation": "ML_Reproducibility_Challenge/2023/Paper*/Submission"},
    {"year": 2023, "invitation": "ML_Reproducibility_Challenge.2023/Paper*/Submission"},
    {"year": 2023, "invitation": "ML_Reproducibility_Challenge/2023/-/Submission"},
    # Year 2022
    {"year": 2022, "invitation": "ML_Reproducibility_Challenge/2022/Paper*/Submission"},
    {"year": 2022, "invitation": "ML_Reproducibility_Challenge.2022/Paper*/Submission"},
    {"year": 2022, "invitation": "ML_Reproducibility_Challenge/2022/-/Submission"},
    # Year 2021
    {"year": 2021, "invitation": "ML_Reproducibility_Challenge/2021/Paper*/Submission"},
    {"year": 2021, "invitation": "ML_Reproducibility_Challenge.2021/Paper*/Submission"},
    {"year": 2021, "invitation": "ML_Reproducibility_Challenge/2021/-/Submission"},
    # Year 2020
    {"year": 2020, "invitation": "ML_Reproducibility_Challenge/2020/Paper*/Submission"},
    {"year": 2020, "invitation": "ML_Reproducibility_Challenge.2020/Paper*/Submission"},
    {"year": 2020, "invitation": "ML_Reproducibility_Challenge/2020/-/Submission"},
]

# Contamination prevention: reject task_prompt containing any of these phrases
CONTAMINATION_KEYWORDS = [
    "we found that",
    "failed to reproduce",
    "the reported results",
    "our reproduction",
    "could not replicate",
    "we were unable to",
    "reproduction failed",
    "reproducer found",
    "reproducibility report",
    "could not be reproduced",
]

# Exclusion criteria from DATA_ACQUISITION.md
EXCLUSION_REASONS = {
    "no_root_cause": "Results didn't match with no documented root cause",
    "environment_only": "Environment or compute failures only",
    "vague_description": "Flaw description too vague (< 2 sentences equivalent)",
    "implementation_only": "Purely implementation bug in released code",
    "no_task_prompt": "Could not construct contamination-clean task_prompt",
    "contamination_gate": "task_prompt contains reproducer-language keywords",
    "extraction_failed": "GPT-4o extraction produced no usable flaw records",
}

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------

DEFAULT_MODELS = {
    "rc2": "openai/gpt-5.4",
    "rc3": "openai/gpt-5.4",
}

# ---------------------------------------------------------------------------
# API helpers (shared with orchestrator.py pattern)
# ---------------------------------------------------------------------------


def get_llm_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]ERROR: OPENROUTER_API_KEY not set[/red]", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=API_TIMEOUT)


def extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


def call_llm(prompt: str, model: str, client: OpenAI | None, dry_run: bool = False) -> str:
    if dry_run:
        preview = prompt[:120].replace("\n", " ")
        console.print(f"    [DRY RUN] {model} ← {len(prompt)}ch: {preview}...")
        return '{"dry_run": true}'
    assert client is not None, "OpenAI client required when not in dry_run mode"
    for attempt, delay in enumerate([0, 1, 2, 4]):
        if delay:
            time.sleep(delay)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            if attempt == 3:
                raise
            console.print(f"    [yellow]API error ({model}), retrying: {exc}[/yellow]")
    return ""


def call_llm_json(
    prompt: str, model: str, client: OpenAI | None, dry_run: bool = False
) -> dict | list:
    raw = call_llm(prompt, model, client, dry_run)
    if dry_run:
        return {"dry_run": True}
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError:
        retry_prompt = prompt + "\n\nIMPORTANT: Return valid JSON only. No markdown. No code fences."
        raw2 = call_llm(retry_prompt, model, client, dry_run)
        try:
            return json.loads(extract_json(raw2))
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON parse failed after retry ({model}):\n{raw2[:400]}"
            ) from e


# ---------------------------------------------------------------------------
# RC-1: Fetch — OpenReview API
# ---------------------------------------------------------------------------


_openreview_token: str = ""


def _get_openreview_token() -> str:
    """Obtain a guest token from OpenReview v2 API (cached per process)."""
    global _openreview_token
    if _openreview_token:
        return _openreview_token
    try:
        resp = requests.post(
            f"{OPENREVIEW_BASE_URL}/token",
            json={"user": "", "password": ""},
            timeout=15,
        )
        if resp.status_code == 200:
            _openreview_token = resp.json().get("token", "")
            if _openreview_token:
                console.print("[RC-1] Obtained OpenReview guest token")
                return _openreview_token
    except requests.RequestException as exc:
        console.print(f"  [yellow]Could not obtain OpenReview token: {exc}[/yellow]")
    return ""


def _openreview_get(endpoint: str, params: dict) -> dict:
    """Single OpenReview API call with retry on transient errors."""
    url = f"{OPENREVIEW_BASE_URL}/{endpoint}"
    token = _get_openreview_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    for attempt, delay in enumerate([0, 1, 3]):
        if delay:
            time.sleep(delay)
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return {"notes": [], "count": 0}
            if resp.status_code == 429:
                time.sleep(5)
                continue
            resp.raise_for_status()
        except requests.RequestException as exc:
            if attempt == 2:
                console.print(f"  [red]OpenReview request failed: {exc}[/red]")
                return {"notes": [], "count": 0}
    return {"notes": [], "count": 0}


def _extract_note_text(note: dict) -> str:
    """Pull report text from OpenReview note content fields."""
    content = note.get("content", {})
    pieces = []
    # Newer API versions wrap values in {value: ...}
    def unwrap(val):
        if isinstance(val, dict) and "value" in val:
            return val["value"]
        return val or ""

    for field in ["title", "abstract", "paper_summary", "summary", "main_claims",
                  "findings", "reproducibility", "overall_comment", "comment",
                  "claims_replication", "experimental_design", "methodology"]:
        val = unwrap(content.get(field, ""))
        if val and isinstance(val, str) and len(val.strip()) > 20:
            pieces.append(f"[{field.upper()}]\n{val.strip()}")
    return "\n\n".join(pieces)


def fetch_openreview_venue(pattern: dict, max_per_venue: int = 200) -> list[dict]:
    """
    Fetch submissions for one venue pattern.
    Returns list of report dicts — may be empty if venue not found.
    """
    invitation = pattern["invitation"]
    year = pattern["year"]
    reports = []
    offset = 0
    limit = 100

    while True:
        data = _openreview_get("notes", {
            "invitation": invitation,
            "limit": limit,
            "offset": offset,
            "details": "replyCount",
        })
        notes = data.get("notes", [])
        if not notes:
            break

        for note in notes:
            content = note.get("content", {})
            def unwrap(val):
                if isinstance(val, dict) and "value" in val:
                    return val["value"]
                return val or ""

            title = unwrap(content.get("title", "")) or unwrap(content.get("paper_title", ""))
            if not title:
                continue

            report_text = _extract_note_text(note)
            if not report_text:
                continue

            reports.append({
                "report_id": f"rc_or_{year}_{note['id'][:12]}",
                "source": "openreview",
                "year": year,
                "title": title,
                "report_text": report_text,
                "original_paper_abstract": unwrap(content.get("abstract", "")),
                "report_url": f"https://openreview.net/forum?id={note['id']}",
                "submission_id": note["id"],
                "venue_invitation": invitation,
            })

        offset += len(notes)
        if len(notes) < limit or offset >= max_per_venue:
            break

    return reports


def discover_openreview_venues() -> list[str]:
    """
    Query OpenReview for venue groups matching 'Reproducibility'.
    Used for --discover-venues flag to find correct invitation strings.
    """
    console.print("[RC-1] Discovering OpenReview venues matching 'Reproducibility'...")
    data = _openreview_get("groups", {
        "regex": ".*[Rr]eproducib.*",
        "limit": 50,
    })
    groups = data.get("groups", [])
    ids = [g.get("id", "") for g in groups if g.get("id")]
    for gid in ids:
        console.print(f"  Found venue group: {gid}")
    return ids


# ---------------------------------------------------------------------------
# RC-1: Fetch — ReScience C via GitHub API
# ---------------------------------------------------------------------------


def _github_get(endpoint: str) -> dict | list:
    """Single GitHub API call."""
    url = f"{GITHUB_API_BASE}/{endpoint}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    for attempt, delay in enumerate([0, 2, 5]):
        if delay:
            time.sleep(delay)
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                console.print("  [yellow]GitHub rate limit hit — waiting 60s...[/yellow]")
                time.sleep(60)
                continue
            resp.raise_for_status()
        except requests.RequestException as exc:
            if attempt == 2:
                console.print(f"  [yellow]GitHub request failed: {exc}[/yellow]")
                return []
    return []


def _fetch_github_file_content(download_url: str) -> str:
    """Fetch raw file content from a GitHub download URL."""
    try:
        resp = requests.get(download_url, timeout=30)
        if resp.status_code == 200:
            return resp.text
    except requests.RequestException:
        pass
    return ""


def fetch_rescience_c(max_articles: int = 100, concurrency: int = 8) -> list[dict]:
    """
    Fetch article metadata from ReScience/MLRC GitHub repo via the GitHub API.
    Each paper directory contains metadata.yaml (structured metadata) and
    content.tex (full LaTeX report text). No article.md files exist in this repo.

    Uses concurrent HTTP fetching (two requests per paper: metadata + content).
    """
    console.print("[RC-1] Fetching MLRC articles via GitHub API...")

    # Find all metadata.yaml files — one per paper directory
    tree_data = _github_get(f"repos/{RESCIENCE_REPO}/git/trees/{RESCIENCE_BRANCH}?recursive=1")
    if not tree_data or not isinstance(tree_data, dict):
        console.print("  [yellow]Could not fetch MLRC repo tree — skipping[/yellow]")
        return []

    tree = tree_data.get("tree", [])
    metadata_files = [
        f for f in tree
        if isinstance(f, dict)
        and f.get("path", "").endswith("metadata.yaml")
        and f.get("type") == "blob"
    ][:max_articles]

    console.print(f"  Found {len(metadata_files)} metadata.yaml files in {RESCIENCE_REPO}")

    raw_base = f"https://raw.githubusercontent.com/{RESCIENCE_REPO}/{RESCIENCE_BRANCH}"

    def fetch_one(item: dict) -> dict | None:
        """Fetch metadata + report content for a single paper. Returns None to skip."""
        meta_path = item.get("path", "")
        parts = meta_path.split("/")
        paper_dir = "/".join(parts[:-1])  # e.g. "2022/albanis2021on/journal"
        article_id = paper_dir.replace("/", "_")[:40]
        report_id = f"rc_rescience_{article_id}"

        # Fetch metadata.yaml for structured fields (title, year, keywords)
        meta_text = _fetch_github_file_content(f"{raw_base}/{meta_path}")
        if not meta_text:
            return None

        title = ""
        year_val = None
        title_match = re.search(r'^title:\s*"?(.+?)"?\s*$', meta_text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip().strip('"\'[]')
        year_match = re.search(r'^year:\s*(\d{4})', meta_text, re.MULTILINE)
        if year_match:
            year_val = int(year_match.group(1))
        if not year_val and len(parts) >= 2:
            try:
                year_val = int(parts[0])
            except ValueError:
                pass
        if not title:
            title = f"MLRC {paper_dir}"

        # Fetch report body (LaTeX; GPT-4o handles it well).
        # Structure: {year}/{slug}/journal/metadata.yaml (entry point found by tree)
        #            {year}/{slug}/journal/content.tex   (stub: \input{../openreview/content.tex})
        #            {year}/{slug}/openreview/content.tex (actual full report — 20–40 KB)
        # Try openreview/content.tex first (real content), then fall back to meta_text.
        paper_root = "/".join(parts[:-2])  # strip "journal" + "metadata.yaml"
        content_text = _fetch_github_file_content(f"{raw_base}/{paper_root}/openreview/content.tex")
        if not content_text or len(content_text.strip()) < 100:
            content_text = None  # don't use the stub
        report_text = (content_text or meta_text)[:8000]  # cap at 8k chars for LLM

        if len(report_text.strip()) < 100:
            return None

        return {
            "report_id": report_id,
            "source": "rescience",
            "year": year_val,
            "title": title,
            "report_text": report_text,
            "original_paper_abstract": meta_text[:2000],  # yaml metadata as abstract proxy
            "report_url": f"https://github.com/{RESCIENCE_REPO}/blob/{RESCIENCE_BRANCH}/{paper_dir}",
            "submission_id": article_id,
            "venue_invitation": "rescience_mlrc",
        }

    results: list[dict | None] = [None] * len(metadata_files)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("RC-1 MLRC fetch", total=len(metadata_files))
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_idx = {
                executor.submit(fetch_one, item): idx
                for idx, item in enumerate(metadata_files)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    console.print(f"  [yellow]RC-1 fetch error (idx {idx}): {exc}[/yellow]")
                    results[idx] = None
                progress.advance(task_id)

    reports = [r for r in results if r is not None]
    console.print(f"  [green]✓ MLRC: {len(reports)} reports fetched[/green]")
    return reports


# ---------------------------------------------------------------------------
# RC-1: Main fetch stage
# ---------------------------------------------------------------------------

RC2_EXTRACTION_PROMPT = """\
You are extracting structured benchmark case data from an ML reproducibility report.

Your task has two parts:
1. TASK PROMPT: Extract a clean methodology description from what the ORIGINAL PAPER claimed
   to do — not what the reproducer found. This becomes the debate prompt that agents see.
2. FLAW RECORDS: Extract structured records of every methodology flaw the REPRODUCER documented.

CRITICAL (contamination prevention):
- The task_prompt must describe what the ORIGINAL PAPER claimed, not the reproducer's findings.
- A debate agent reading task_prompt should see only the paper's methodology — no hints about
  what the reproducer found.
- task_prompt should read like an experimental design description, not a review or critique.

REPORT TEXT:
{report_text}

PAPER TITLE: {title}

ORIGINAL ABSTRACT (if available): {abstract}

For each methodology flaw the reproducer documented:
- flaw_type: one of [data_leakage, evaluation_mismatch, baseline_broken, distribution_shift,
  metric_mismatch, hyperparameter_tuning, scope_overclaim, statistical_flaw, other]
- description: one paragraph, specific enough that an independent reviewer could check whether
  a critique raised this concern (do NOT include "the reproducer found..." language)
- severity: "minor" | "major" | "critical" (based on reproducer's framing)
- reproducible: true if the flaw was confirmed to affect results, false if only suspected
- ground_truth_type: "critique" (flaw confirmed), "defense" (design confirmed sound),
  or "mixed" (paper mostly sound but one choice is contestable/overstated)

Return JSON only — no markdown, no code fences:
{{
  "task_prompt": "2-4 paragraph description of the paper's claimed methodology (NO critique text)",
  "ground_truth_type": "critique | defense | mixed",
  "mixed_rationale": "If mixed: one sentence explaining what is contestable. Otherwise null.",
  "flaw_records": [
    {{
      "issue_id": "to_be_filled",
      "flaw_type": "...",
      "description": "...",
      "severity": "minor | major | critical",
      "reproducible": true,
      "source": "reproducer_documented"
    }}
  ],
  "extraction_confidence": "high | medium | low",
  "extraction_notes": "Any caveats about the extraction quality"
}}

If no specific methodology flaw is documented (environment failures, missing code, etc.),
return flaw_records = [] and ground_truth_type = "defense" if the paper is confirmed sound,
or ground_truth_type = "none" if the report is unusable.
"""

RC3_MUST_NOT_CLAIM_PROMPT = """\
You are identifying sound design choices in an ML paper that a pattern-matching reviewer
might wrongly criticize.

TASK PROMPT (the paper's claimed methodology):
{task_prompt}

PAPER TITLE: {title}

FLAW RECORDS ALREADY FOUND (do NOT include these in must_not_claim):
{flaw_records_json}

Your job: identify 2-4 sound design choices in the task_prompt that:
1. Look unusual at first glance but are justified for this domain/hypothesis
2. Differ from a common default but have a domain-specific rationale
3. A reviewer without deep domain context might flag as "risky" or "incorrect"

Do NOT include the documented flaws above — they are real problems.
Do NOT include obvious defaults that any reasonable reviewer would accept.

Return JSON only — no markdown, no code fences:
{{
  "must_not_claim": ["claim_001", "claim_002"],
  "must_not_claim_details": [
    {{
      "claim_id": "claim_001",
      "claim": "One-sentence description of the incorrect concern a reviewer might raise",
      "why_wrong": "Why this concern does not apply — the design choice is correct or justified"
    }}
  ]
}}

If no such choices exist, return must_not_claim = [] and must_not_claim_details = [].
"""


def run_rc1(config: dict) -> list[dict]:
    """
    RC-1: Fetch reports from OpenReview API and ReScience C.
    No LLM calls — pure HTTP fetching.
    """
    console.rule("[bold blue]RC-1: Fetch[/bold blue]")
    reports: list[dict] = []

    if config.get("discover_venues"):
        discover_openreview_venues()
        console.print("\nRun again without --discover-venues to proceed with fetch.")
        return []

    if config.get("dry_run"):
        console.print("[RC-1] DRY RUN — generating 5 synthetic report stubs")
        dry_reports = []
        for i in range(5):
            dry_reports.append({
                "report_id": f"rc_or_2022_dry{i:04d}",
                "source": "openreview",
                "year": 2022,
                "title": f"Dry Run Paper {i}: FastText Feature Learning",
                "report_text": "Paper claims to use standard train/val/test split with no data augmentation.",
                "original_paper_abstract": "We propose a method for feature learning using FastText embeddings.",
                "report_url": f"https://openreview.net/forum?id=dry{i}",
                "submission_id": f"dry{i}",
                "venue_invitation": "ML_Reproducibility_Challenge/2022",
            })
        out = RC_CANDIDATES_DIR / "reports_fetched.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dry_reports, indent=2), encoding="utf-8")
        console.print(f"[RC-1] DRY RUN: wrote {len(dry_reports)} stubs → {out}")
        return dry_reports

    # OpenReview: try each venue pattern, deduplicate by submission_id
    seen_ids: set[str] = set()
    or_count_by_year: dict[int, int] = {}

    console.print(f"[RC-1] Trying {len(OPENREVIEW_VENUE_PATTERNS)} OpenReview venue patterns...")
    for pattern in OPENREVIEW_VENUE_PATTERNS:
        venue_reports = fetch_openreview_venue(pattern, max_per_venue=config.get("max_per_venue", 200))
        new = [r for r in venue_reports if r["submission_id"] not in seen_ids]
        for r in new:
            seen_ids.add(r["submission_id"])
        if new:
            year = pattern["year"]
            or_count_by_year[year] = or_count_by_year.get(year, 0) + len(new)
            console.print(
                f"  [green]✓[/green] {pattern['invitation']}: {len(new)} new reports"
            )
            reports.extend(new)
        else:
            console.print(
                f"  [dim]{pattern['invitation']}: 0 results (venue may not exist)[/dim]"
            )

    console.print(f"\n[RC-1] OpenReview total: {sum(or_count_by_year.values())} reports")
    for yr, cnt in sorted(or_count_by_year.items()):
        console.print(f"  {yr}: {cnt}")

    # ReScience C
    rescience_reports = fetch_rescience_c(
        max_articles=config.get("max_rescience", 80),
        concurrency=config.get("concurrency", 100),
    )
    reports.extend(rescience_reports)

    out = RC_CANDIDATES_DIR / "reports_fetched.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")

    console.print(f"\n[RC-1] Total: {len(reports)} reports → {out}")
    console.print("       Run --stage rc2 to proceed with flaw extraction.")
    return reports


# ---------------------------------------------------------------------------
# RC-2: Flaw extraction
# ---------------------------------------------------------------------------


def run_rc2(config: dict, client: OpenAI | None) -> list[dict]:
    """
    RC-2: For each fetched report, use GPT-4o to extract structured flaw records
    and a clean task_prompt (contamination-free).
    """
    console.rule("[bold blue]RC-2: Flaw Extraction[/bold blue]")

    fetched_path = RC_CANDIDATES_DIR / "reports_fetched.json"
    if not fetched_path.exists():
        console.print(f"[red]ERROR: {fetched_path} not found — run --stage rc1 first[/red]")
        sys.exit(1)

    reports: list[dict] = json.loads(fetched_path.read_text(encoding="utf-8"))
    console.print(f"[RC-2] Processing {len(reports)} reports with {config['models']['rc2']}...")

    extracted: list[dict] = []
    model = config["models"]["rc2"]
    dry_run = config.get("dry_run", False)

    def extract_one(report: dict) -> dict:
        report_id = report["report_id"]
        report_text = report.get("report_text", "")
        title = report.get("title", "")
        abstract = report.get("original_paper_abstract", "")

        if dry_run:
            return {
                "report_id": report_id,
                "source": report["source"],
                "year": report.get("year"),
                "title": title,
                "task_prompt": f"[DRY RUN] Methodology description for: {title}",
                "ground_truth_type": "critique",
                "mixed_rationale": None,
                "flaw_records": [
                    {
                        "issue_id": f"{report_id}_flaw_001",
                        "flaw_type": "evaluation_mismatch",
                        "description": "[DRY RUN] Synthetic flaw description.",
                        "severity": "major",
                        "reproducible": True,
                        "source": "reproducer_documented",
                    }
                ],
                "extraction_confidence": "high",
                "extraction_notes": "dry_run",
                "report_url": report.get("report_url", ""),
                "submission_id": report.get("submission_id", ""),
            }

        prompt = RC2_EXTRACTION_PROMPT.format(
            report_text=report_text[:6000],
            title=title,
            abstract=abstract[:1000] if abstract else "(not available)",
        )
        try:
            result = call_llm_json(prompt, model, client, dry_run=False)
        except (ValueError, Exception) as exc:
            console.print(f"  [red]✗ RC-2 {report_id}: {exc}[/red]")
            return {
                "report_id": report_id,
                "title": title,
                "error": str(exc),
                "status": "failed",
                "report_url": report.get("report_url", ""),
            }

        if not isinstance(result, dict):
            return {
                "report_id": report_id,
                "title": title,
                "error": "non-dict response",
                "status": "failed",
                "report_url": report.get("report_url", ""),
            }

        # Assign stable issue_ids to flaw records
        flaw_records = result.get("flaw_records", [])
        for idx, flaw in enumerate(flaw_records):
            flaw["issue_id"] = f"{report_id}_flaw_{idx+1:03d}"

        return {
            "report_id": report_id,
            "source": report["source"],
            "year": report.get("year"),
            "title": title,
            "task_prompt": result.get("task_prompt", ""),
            "ground_truth_type": result.get("ground_truth_type", "critique"),
            "mixed_rationale": result.get("mixed_rationale"),
            "flaw_records": flaw_records,
            "extraction_confidence": result.get("extraction_confidence", "medium"),
            "extraction_notes": result.get("extraction_notes", ""),
            "report_url": report.get("report_url", ""),
            "submission_id": report.get("submission_id", ""),
        }

    concurrency = config.get("concurrency", 100)
    results: list[dict | None] = [None] * len(reports)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("RC-2 extraction", total=len(reports))
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_idx = {
                executor.submit(extract_one, report): idx
                for idx, report in enumerate(reports)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    results[idx] = {
                        "report_id": reports[idx]["report_id"],
                        "error": str(exc),
                        "status": "failed",
                    }
                progress.advance(task_id)

    extracted = [r for r in results if r is not None]
    n_ok = sum(1 for r in extracted if "error" not in r)
    n_failed = len(extracted) - n_ok

    out = RC_CANDIDATES_DIR / "flaws_extracted.json"
    out.write_text(json.dumps(extracted, indent=2), encoding="utf-8")
    console.print(
        f"\n[RC-2] {n_ok}/{len(extracted)} succeeded ({n_failed} failed) → {out}"
    )
    return extracted


# ---------------------------------------------------------------------------
# RC-3: must_not_claim extraction
# ---------------------------------------------------------------------------


def run_rc3(config: dict, client: OpenAI | None) -> list[dict]:
    """
    RC-3: For each RC-2 output with a valid task_prompt, run a separate GPT-4o
    pass to extract must_not_claim items (sound design choices to not wrongly criticize).
    """
    console.rule("[bold blue]RC-3: must_not_claim Extraction[/bold blue]")

    extracted_path = RC_CANDIDATES_DIR / "flaws_extracted.json"
    if not extracted_path.exists():
        console.print(f"[red]ERROR: {extracted_path} not found — run --stage rc2 first[/red]")
        sys.exit(1)

    extracted: list[dict] = json.loads(extracted_path.read_text(encoding="utf-8"))
    usable = [
        r for r in extracted
        if not r.get("error")
        and r.get("task_prompt")
        and r.get("ground_truth_type") not in ("none", None)
    ]
    console.print(
        f"[RC-3] Processing {len(usable)}/{len(extracted)} usable records "
        f"with {config['models']['rc3']}..."
    )

    model = config["models"]["rc3"]
    dry_run = config.get("dry_run", False)
    augmented: list[dict] = []

    def augment_one(record: dict) -> dict:
        report_id = record["report_id"]
        task_prompt = record.get("task_prompt", "")
        title = record.get("title", "")
        flaw_records = record.get("flaw_records", [])

        if dry_run:
            record["must_not_claim"] = ["claim_001"]
            record["must_not_claim_details"] = [
                {
                    "claim_id": "claim_001",
                    "claim": "[DRY RUN] Incorrect concern about train/test split.",
                    "why_wrong": "The split is appropriate for the domain.",
                }
            ]
            return record

        prompt = RC3_MUST_NOT_CLAIM_PROMPT.format(
            task_prompt=task_prompt[:4000],
            title=title,
            flaw_records_json=json.dumps(
                [{"id": f["issue_id"], "desc": f["description"][:200]}
                 for f in flaw_records[:10]],
                indent=2,
            ),
        )
        try:
            result = call_llm_json(prompt, model, client, dry_run=False)
            if isinstance(result, dict):
                record["must_not_claim"] = result.get("must_not_claim", [])
                record["must_not_claim_details"] = result.get("must_not_claim_details", [])
            else:
                record["must_not_claim"] = []
                record["must_not_claim_details"] = []
        except (ValueError, Exception) as exc:
            console.print(f"  [yellow]RC-3 {report_id}: {exc} (setting empty must_not_claim)[/yellow]")
            record["must_not_claim"] = []
            record["must_not_claim_details"] = []

        return record

    concurrency = config.get("concurrency", 100)
    results: list[dict | None] = [None] * len(usable)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("RC-3 must_not_claim", total=len(usable))
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_idx = {
                executor.submit(augment_one, record): idx
                for idx, record in enumerate(usable)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    console.print(f"  [yellow]RC-3 future failed: {exc}[/yellow]")
                    results[idx] = {**usable[idx], "must_not_claim": [], "must_not_claim_details": []}
                progress.advance(task_id)

    augmented = [r for r in results if r is not None]

    out = RC_CANDIDATES_DIR / "must_not_claim.json"
    out.write_text(json.dumps(augmented, indent=2), encoding="utf-8")
    console.print(f"\n[RC-3] {len(augmented)} records with must_not_claim → {out}")
    return augmented


# ---------------------------------------------------------------------------
# RC-4: Filtering + contamination gate
# ---------------------------------------------------------------------------


def check_contamination(task_prompt: str) -> tuple[bool, str | None]:
    """
    Returns (is_clean, keyword_hit).
    Fails if any CONTAMINATION_KEYWORDS appear in the task_prompt (case-insensitive).
    """
    lower = task_prompt.lower()
    for kw in CONTAMINATION_KEYWORDS:
        if kw.lower() in lower:
            return False, kw
    return True, None


def run_rc4(config: dict) -> list[dict]:
    """
    RC-4: Apply exclusion criteria and contamination gate.
    Outputs rc_cases_raw.json — the final RC case candidate pool.
    """
    console.rule("[bold blue]RC-4: Filter + Contamination Gate[/bold blue]")

    source_path = RC_CANDIDATES_DIR / "must_not_claim.json"
    if not source_path.exists():
        # Try falling back to rc2 output if rc3 was skipped
        source_path = RC_CANDIDATES_DIR / "flaws_extracted.json"
        if not source_path.exists():
            console.print(f"[red]ERROR: No RC-2 or RC-3 output found — run earlier stages first[/red]")
            sys.exit(1)
        console.print(f"  [yellow]RC-3 output not found — using RC-2 output (no must_not_claim)[/yellow]")

    records: list[dict] = json.loads(source_path.read_text(encoding="utf-8"))
    console.print(f"[RC-4] Filtering {len(records)} records...")

    passed: list[dict] = []
    rejected: dict[str, list[str]] = {k: [] for k in EXCLUSION_REASONS}
    rejected["contamination_gate"] = []

    for record in records:
        report_id = record.get("report_id", "?")
        task_prompt = record.get("task_prompt", "")
        flaw_records = record.get("flaw_records", [])
        ground_truth_type = record.get("ground_truth_type", "critique")
        extraction_confidence = record.get("extraction_confidence", "medium")

        # Skip failed extractions
        if record.get("error") or record.get("status") == "failed":
            rejected["extraction_failed"].append(report_id)
            continue

        # Reject unusable ground_truth_type
        if ground_truth_type in ("none", None):
            rejected["extraction_failed"].append(report_id)
            continue

        # Require task_prompt
        if not task_prompt or len(task_prompt.strip()) < 100:
            rejected["no_task_prompt"].append(report_id)
            continue

        # Contamination gate — primary PM1 prevention
        is_clean, kw = check_contamination(task_prompt)
        if not is_clean:
            rejected["contamination_gate"].append(f"{report_id} (keyword: '{kw}')")
            continue

        # Critique cases: require at least one documented flaw
        if ground_truth_type == "critique" and not flaw_records:
            rejected["extraction_failed"].append(report_id)
            continue

        # Require at least one flaw with adequate description (> 50 chars)
        if ground_truth_type == "critique":
            adequate_flaws = [
                f for f in flaw_records
                if len(f.get("description", "")) > 50
            ]
            if not adequate_flaws:
                rejected["vague_description"].append(report_id)
                continue

        # Reject low-confidence extractions for critique cases (keep for defense/mixed)
        if ground_truth_type == "critique" and extraction_confidence == "low":
            rejected["vague_description"].append(report_id)
            continue

        # Assemble the final RC case record
        rc_case = _assemble_rc_case(record)
        passed.append(rc_case)

    # Yield summary
    console.print(f"\n[RC-4] Results:")
    console.print(f"  Passed:  {len(passed)}")
    for reason, ids in rejected.items():
        if ids:
            console.print(f"  Rejected ({reason}): {len(ids)}")

    n_critique = sum(1 for c in passed if c["ground_truth_type"] == "critique")
    n_defense  = sum(1 for c in passed if c["ground_truth_type"] == "defense")
    n_mixed    = sum(1 for c in passed if c["ground_truth_type"] == "mixed")
    console.print(f"\n  By type: critique={n_critique}  defense={n_defense}  mixed={n_mixed}")

    # Decision gate (PLAN.md Design Decision §1)
    console.print("\n[RC-4] Yield gate evaluation:")
    if n_critique >= 60 and n_mixed >= 20:
        console.print("  → [green]GATE PASS: Use RC exclusively (regular >= 60 AND mixed >= 20)[/green]")
    elif n_critique >= 60 and n_mixed < 20:
        console.print(
            f"  → [yellow]PARTIAL: regular >= 60 but mixed < 20 (got {n_mixed}). "
            "Supplement mixed with synthetic pipeline.[/yellow]"
        )
    elif n_critique < 60:
        console.print(
            f"  → [yellow]LOW YIELD: regular < 60 (got {n_critique}). "
            "Supplement regular cases with synthetic (lower proxy threshold).[/yellow]"
        )
    if len(passed) < 30:
        console.print(
            "  → [red]CRITICAL: RC total < 30. Full synthetic fallback required.[/red]"
        )

    # Apply target-count cap if specified (sort by confidence, then truncate)
    target_count = config.get("target_count")
    if target_count and len(passed) > target_count:
        confidence_rank = {"high": 0, "medium": 1, "low": 2}
        passed.sort(key=lambda c: confidence_rank.get(c.get("extraction_confidence", "medium"), 1))
        console.print(f"  [dim]Target count cap: {len(passed)} → {target_count}[/dim]")
        passed = passed[:target_count]

    out = RC_CANDIDATES_DIR / "rc_cases_raw.json"
    out.write_text(json.dumps(passed, indent=2), encoding="utf-8")
    rejected_log = RC_CANDIDATES_DIR / "rc_cases_rejected.json"
    rejected_log.write_text(
        json.dumps({k: v for k, v in rejected.items() if v}, indent=2),
        encoding="utf-8",
    )

    console.print(f"\n[RC-4] Usable cases → {out}")
    console.print(f"       Rejection log → {rejected_log}")
    return passed


def _assemble_rc_case(record: dict) -> dict:
    """
    Assemble the final RC case dict (pre-normalization format).
    This is the input Schema to normalize_cases.py.
    """
    flaw_records = record.get("flaw_records", [])
    must_find_issue_ids = [f["issue_id"] for f in flaw_records]
    must_not_claim = record.get("must_not_claim", [])
    must_not_claim_details = record.get("must_not_claim_details", [])

    ground_truth_type = record.get("ground_truth_type", "critique")
    # Map ground_truth_type to correct_position expected by Schema B
    correct_position_map = {
        "critique": "critique",
        "defense": "defense",
        "mixed": "mixed",
    }
    correct_position = correct_position_map.get(ground_truth_type, "critique")

    # ideal_debate_resolution type
    ideal_type_map = {
        "critique": "critique_wins",
        "defense": "defense_wins",
        "mixed": "mixed",
    }
    ideal_type = ideal_type_map.get(ground_truth_type, "critique_wins")

    # acceptable_resolutions — flat string array (PLAN.md Schema B constraint)
    acceptable_resolutions_map = {
        "critique": ["critique_wins"],
        "defense": ["defense_wins"],
        "mixed": ["empirical_test_agreed"],
    }
    acceptable_resolutions = acceptable_resolutions_map.get(ground_truth_type, ["critique_wins"])

    return {
        "report_id": record["report_id"],
        "source": record.get("source", "openreview"),
        "year": record.get("year"),
        "title": record.get("title", ""),
        "task_prompt": record.get("task_prompt", ""),
        "ground_truth_type": ground_truth_type,
        "correct_position": correct_position,
        "ideal_debate_resolution_type": ideal_type,
        "acceptable_resolutions": acceptable_resolutions,
        "flaw_records": flaw_records,
        "must_find_issue_ids": must_find_issue_ids,
        "must_not_claim": must_not_claim,
        "must_not_claim_details": must_not_claim_details,
        "mixed_rationale": record.get("mixed_rationale"),
        "extraction_confidence": record.get("extraction_confidence", "medium"),
        "report_url": record.get("report_url", ""),
        "_rc_metadata": {
            "submission_id": record.get("submission_id", ""),
            "n_flaws": len(flaw_records),
            "source": record.get("source", "openreview"),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="RC Extractor — v7 Pipeline Phase 1"
    )
    parser.add_argument(
        "--stage",
        choices=["rc1", "rc2", "rc3", "rc4"],
        help="Run a single stage",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all stages sequentially",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate all stages without API calls",
    )
    parser.add_argument(
        "--discover-venues",
        action="store_true",
        help="Probe OpenReview API to discover available RC venue IDs",
    )
    parser.add_argument(
        "--model-rc2",
        default=DEFAULT_MODELS["rc2"],
        help=f"Model for RC-2 flaw extraction (default: {DEFAULT_MODELS['rc2']})",
    )
    parser.add_argument(
        "--model-rc3",
        default=DEFAULT_MODELS["rc3"],
        help=f"Model for RC-3 must_not_claim (default: {DEFAULT_MODELS['rc3']})",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Concurrent workers for RC-1 HTTP fetch and RC-2/RC-3 LLM calls (default: 100)",
    )
    parser.add_argument(
        "--max-rescience",
        type=int,
        default=80,
        help="Max ReScience C articles to fetch (default: 80)",
    )
    parser.add_argument(
        "--max-per-venue",
        type=int,
        default=200,
        help="Max reports to fetch per OpenReview venue pattern (default: 200)",
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=None,
        help="Cap final RC-4 output to this many cases (by extraction_confidence then source)",
    )
    args = parser.parse_args()

    if not args.stage and not args.all and not args.discover_venues:
        parser.print_help()
        sys.exit(1)

    config = {
        "dry_run": args.dry_run,
        "discover_venues": args.discover_venues,
        "models": {
            "rc2": args.model_rc2,
            "rc3": args.model_rc3,
        },
        "concurrency": args.concurrency,
        "max_rescience": args.max_rescience,
        "max_per_venue": args.max_per_venue,
        "target_count": args.target_count,
    }

    RC_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    if args.discover_venues:
        discover_openreview_venues()
        return

    if args.stage == "rc1" or args.all:
        run_rc1(config)

    if args.stage == "rc2" or args.all:
        client = get_llm_client() if not args.dry_run else None
        run_rc2(config, client)

    if args.stage == "rc3" or args.all:
        client = get_llm_client() if not args.dry_run else None
        run_rc3(config, client)

    if args.stage == "rc4" or args.all:
        run_rc4(config)


if __name__ == "__main__":
    main()
