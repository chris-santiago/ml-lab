# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "rich>=13.0"]
# ///
"""
Temporary unit tests for smoke scoring logic.

Run with:
    uv run pipeline/test_scoring.py

Tests compute_smoke_scores() and recycle_action() without any LLM calls.

Scoring semantics:
  IDR  — fraction of must_find_ids found (None if no must_find_ids)
  IDP  — fraction of must_not_claim items NOT raised (None if no must_not_claim)
  FVC  — 1.0 if verdict correct, 0.0 otherwise (always applicable)
  proxy_mean — mean of whichever metrics are not None
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import compute_smoke_scores, recycle_action

# ---------------------------------------------------------------------------
# Minimal test harness
# ---------------------------------------------------------------------------

_passed = 0
_failed = 0


def check(label: str, actual, expected) -> None:
    global _passed, _failed
    if actual == expected:
        print(f"  PASS  {label}")
        _passed += 1
    else:
        print(f"  FAIL  {label}")
        print(f"        expected: {expected!r}")
        print(f"        actual:   {actual!r}")
        _failed += 1


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


# ---------------------------------------------------------------------------
# Case / scorer helpers
# ---------------------------------------------------------------------------

def mnc_items(n: int) -> list:
    """Build n must_not_claim dicts."""
    return [{"claim": f"claim_{i}", "why_wrong": "legitimate choice"} for i in range(n)]


def defense_wins_case(mnc_count: int = 3, task_prompt: str = "A valid design.") -> dict:
    return {
        "correct_verdict": "defense_wins",
        "must_find_issue_ids": [],
        "must_not_claim": mnc_items(mnc_count),
        "_pipeline": {"num_corruptions": 0},
        "task_prompt": task_prompt,
    }


def critique_case(
    num_corruptions: int = 1,
    must_find_ids: list | None = None,
    mnc_count: int = 0,
    task_prompt: str = "A flawed design.",
) -> dict:
    if must_find_ids is None:
        must_find_ids = [f"issue_{i:03d}" for i in range(1, num_corruptions + 1)]
    return {
        "correct_verdict": "critique",
        "must_find_issue_ids": must_find_ids,
        "must_not_claim": mnc_items(mnc_count),
        "_pipeline": {"num_corruptions": num_corruptions},
        "task_prompt": task_prompt,
    }


def scorer_out(
    verdict: str = "approve",
    found: list | None = None,
    raised_bad: list | None = None,
) -> dict:
    return {
        "verdict_given": verdict,
        "must_find_found": found or [],
        "must_not_claim_raised": raised_bad or [],
    }


# ---------------------------------------------------------------------------
# FVC normalization
# ---------------------------------------------------------------------------

section("FVC normalization — approve vs defense_wins")

scores = compute_smoke_scores(scorer_out("approve"), defense_wins_case(), "Valid design.")
check("approve + defense_wins → FVC=1.0", scores["FVC"], 1.0)

scores = compute_smoke_scores(scorer_out("critique", found=["issue_001"]), critique_case(1), "Flawed design.")
check("critique + critique correct_verdict → FVC=1.0", scores["FVC"], 1.0)

scores = compute_smoke_scores(scorer_out("approve"), critique_case(1), "Flawed design.")
check("approve + critique correct_verdict → FVC=0.0", scores["FVC"], 0.0)

scores = compute_smoke_scores(scorer_out("unclear"), defense_wins_case(), "Valid design.")
check("unclear verdict → FVC=0.0", scores["FVC"], 0.0)

# ---------------------------------------------------------------------------
# IDR — partial credit
# ---------------------------------------------------------------------------

section("IDR — partial credit (fraction of must_find_ids found)")

# No must_find_ids → IDR=None
scores = compute_smoke_scores(scorer_out("approve"), defense_wins_case(), "Valid design.")
check("0-corruption case → IDR=None", scores["IDR"], None)

# All found → IDR=1.0
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001", "issue_002"]),
    critique_case(2),
    "Flawed design.",
)
check("2/2 found → IDR=1.0", scores["IDR"], 1.0)

# 1 of 2 found → IDR=0.5 (partial credit, not 0.0)
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001"]),
    critique_case(2),
    "Flawed design.",
)
check("1/2 found → IDR=0.5", scores["IDR"], 0.5)

# 2 of 5 found → IDR=0.4
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001", "issue_003"]),
    critique_case(5),
    "Flawed design.",
)
check("2/5 found → IDR=0.4", scores["IDR"], 0.4)

# 0 found → IDR=0.0
scores = compute_smoke_scores(scorer_out("critique"), critique_case(1), "Flawed design.")
check("0/1 found → IDR=0.0", scores["IDR"], 0.0)

# Finding non-required IDs doesn't count
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_999"]),
    critique_case(1, must_find_ids=["issue_001"]),
    "Flawed design.",
)
check("only non-required ID found → IDR=0.0", scores["IDR"], 0.0)

# 1 of 1 found → IDR=1.0
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001"]),
    critique_case(1),
    "Flawed design.",
)
check("1/1 found → IDR=1.0", scores["IDR"], 1.0)

# ---------------------------------------------------------------------------
# IDP — partial credit
# ---------------------------------------------------------------------------

section("IDP — partial credit (fraction of must_not_claim NOT raised)")

# No must_not_claim → IDP=None (can't penalize for undefined false alarms)
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["some claim"]),
    critique_case(1, mnc_count=0),
    "Flawed design.",
)
check("no must_not_claim → IDP=None", scores["IDP"], None)

# 0 raised out of 3 → IDP=1.0
scores = compute_smoke_scores(scorer_out("approve"), defense_wins_case(mnc_count=3), "Valid design.")
check("0/3 raised → IDP=1.0", scores["IDP"], 1.0)

# 1 raised out of 3 → IDP=0.6667 (not 0.0)
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0"]),
    defense_wins_case(mnc_count=3),
    "Valid design.",
)
check("1/3 raised → IDP=0.6667", scores["IDP"], round(2/3, 4))

# 2 raised out of 3 → IDP=0.3333
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0", "claim_1"]),
    defense_wins_case(mnc_count=3),
    "Valid design.",
)
check("2/3 raised → IDP=0.3333", scores["IDP"], round(1/3, 4))

# All raised → IDP=0.0
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0", "claim_1", "claim_2"]),
    defense_wins_case(mnc_count=3),
    "Valid design.",
)
check("3/3 raised → IDP=0.0", scores["IDP"], 0.0)

# 5 false accusations on a sound design (all 5 must_not_claim raised)
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=[f"claim_{i}" for i in range(5)]),
    defense_wins_case(mnc_count=5),
    "Valid design.",
)
check("5/5 raised on sound design → IDP=0.0", scores["IDP"], 0.0)

# 1 of 5 raised → IDP=0.8 (much better than 5/5)
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0"]),
    defense_wins_case(mnc_count=5),
    "Valid design.",
)
check("1/5 raised → IDP=0.8", scores["IDP"], 0.8)

# IDP clamps at 0.0 (raised_bad can't exceed must_not_claim in practice, but guard)
scores = compute_smoke_scores(
    scorer_out(raised_bad=["x", "x", "x", "x"]),
    defense_wins_case(mnc_count=2),
    "Valid design.",
)
check("raised_bad > must_not_claim → IDP clamped to 0.0", scores["IDP"], 0.0)

# ---------------------------------------------------------------------------
# proxy_mean — None exclusion
# ---------------------------------------------------------------------------

section("proxy_mean — applicable metrics only (None excluded)")

# defense_wins, perfect: IDR=None, IDP=1.0, FVC=1.0 → proxy=(1+1)/2=1.0
scores = compute_smoke_scores(scorer_out("approve"), defense_wins_case(mnc_count=2), "Valid design.")
check("defense_wins perfect → proxy=1.0", scores["proxy_mean"], 1.0)
check("defense_wins perfect → IDR=None (excluded)", scores["IDR"], None)

# defense_wins, 1/3 MNC raised, wrong verdict: IDR=None, IDP=0.6667, FVC=0.0 → proxy=0.3333
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0"]),
    defense_wins_case(mnc_count=3),
    "Valid design.",
)
check(
    "defense_wins: 1/3 MNC raised, wrong verdict → proxy=(0.6667+0.0)/2=0.3333",
    scores["proxy_mean"],
    round((round(2/3, 4) + 0.0) / 2, 4),
)

# critique, 2/5 flaws found, no MNC defined, correct verdict:
# IDR=0.4, IDP=None, FVC=1.0 → proxy=(0.4+1.0)/2=0.7
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001", "issue_002"]),
    critique_case(5, mnc_count=0),
    "Flawed design.",
)
check("2/5 flaws found, no MNC, correct verdict → proxy=(0.4+1.0)/2=0.7", scores["proxy_mean"], 0.7)

# critique, 0/1 found, no MNC, correct verdict: IDR=0.0, IDP=None, FVC=1.0 → proxy=0.5
scores = compute_smoke_scores(
    scorer_out("critique"),
    critique_case(1, mnc_count=0),
    "Flawed design.",
)
check("0/1 found, correct verdict → proxy=(0.0+1.0)/2=0.5", scores["proxy_mean"], 0.5)

# critique, 1/2 found, 1/2 MNC raised, correct verdict:
# IDR=0.5, IDP=0.5, FVC=1.0 → proxy=(0.5+0.5+1.0)/3=0.6667
scores = compute_smoke_scores(
    scorer_out("critique", found=["issue_001"], raised_bad=["claim_0"]),
    critique_case(2, mnc_count=2),
    "Flawed design.",
)
check(
    "1/2 IDR, 1/2 IDP raised, correct verdict → proxy=0.6667",
    scores["proxy_mean"],
    round((0.5 + 0.5 + 1.0) / 3, 4),
)

# All None except FVC: IDR=None, IDP=None, FVC=1.0 → proxy=1.0
scores = compute_smoke_scores(
    scorer_out("approve"),
    {
        "correct_verdict": "defense_wins",
        "must_find_issue_ids": [],
        "must_not_claim": [],
        "_pipeline": {"num_corruptions": 0},
    },
    "Valid design.",
)
check("IDR=None, IDP=None → proxy=FVC alone", scores["proxy_mean"], 1.0)

# ---------------------------------------------------------------------------
# gate_pass — structural gate only (unchanged)
# ---------------------------------------------------------------------------

section("gate_pass — permissive structural gate")

# defense_wins → always pass (even with false alarms)
scores = compute_smoke_scores(
    scorer_out("critique", raised_bad=["claim_0", "claim_1", "claim_2"]),
    defense_wins_case(mnc_count=3),
    "Valid design.",
)
check("defense_wins, all MNC raised → gate=True (debate candidate)", scores["gate_pass"], True)

# critique with must_find_ids → pass
scores = compute_smoke_scores(scorer_out("approve"), critique_case(1), "Flawed design.")
check("critique, Sonnet wrong verdict → gate=True", scores["gate_pass"], True)

# Structural failure: empty task_prompt
scores = compute_smoke_scores(scorer_out(), critique_case(1), "")
check("empty task_prompt → gate=False", scores["gate_pass"], False)

# Structural failure: corruptions > 0 but no must_find_ids
scores = compute_smoke_scores(
    scorer_out(),
    critique_case(1, must_find_ids=[]),
    "Flawed design.",
)
check("corruptions=1, no must_find_ids → gate=False", scores["gate_pass"], False)

# num_corruptions=0, no must_find_ids → gate=True
scores = compute_smoke_scores(
    scorer_out("approve"),
    defense_wins_case(),
    "Valid design.",
)
check("num_corruptions=0, no must_find_ids → gate=True", scores["gate_pass"], True)

# ---------------------------------------------------------------------------
# recycle_action — routing logic (unchanged)
# ---------------------------------------------------------------------------

section("recycle_action — routing logic")

stage, reason, _ = recycle_action({"gate_pass": True}, num_corruptions=1)
check("gate_pass=True → accepted", stage, None)

stage, reason, _ = recycle_action({"gate_pass": False}, num_corruptions=1)
check("gate_pass=False → stage='stage4'", stage, "stage4")
check("gate_pass=False → structural_failure", reason, "structural_failure")

stage, reason, _ = recycle_action(None, num_corruptions=1)
check("smoke=None → accepted (no smoke = pass)", stage, None)

stage, reason, _ = recycle_action({}, num_corruptions=0)
check("gate_pass missing → accepted (defaults True)", stage, None)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*40}")
print(f"  {_passed} passed, {_failed} failed")
print(f"{'='*40}")
sys.exit(0 if _failed == 0 else 1)
