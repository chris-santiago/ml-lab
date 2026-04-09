# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "rich>=13.0"]
# ///
"""
Temporary unit tests for smoke scoring logic.

Run with:
    uv run pipeline/test_scoring.py

Tests compute_smoke_scores() and recycle_action() without any LLM calls.
"""

import sys
from pathlib import Path

# Import pure functions from orchestrator (no API calls made at import time)
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
# Helpers to build minimal case/scorer dicts
# ---------------------------------------------------------------------------

def defense_wins_case(task_prompt: str = "A valid experiment design.") -> dict:
    return {
        "correct_verdict": "defense_wins",
        "must_find_issue_ids": [],
        "must_not_claim": [],
        "_pipeline": {"num_corruptions": 0},
        "task_prompt": task_prompt,
    }


def critique_case(
    num_corruptions: int = 1,
    must_find_ids: list | None = None,
    task_prompt: str = "A flawed experiment design.",
) -> dict:
    if must_find_ids is None:
        must_find_ids = [f"issue_{i:03d}" for i in range(1, num_corruptions + 1)]
    return {
        "correct_verdict": "critique",
        "must_find_issue_ids": must_find_ids,
        "must_not_claim": [],
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
# Test: FVC normalization (the critical regression)
# ---------------------------------------------------------------------------

section("FVC normalization — approve vs defense_wins")

# Sonnet correctly approves a sound design → FVC must be 1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve"),
    case=defense_wins_case(),
    task_prompt="A valid experiment design.",
)
check("approve + defense_wins correct_verdict → FVC=1.0", scores["FVC"], 1.0)
check("approve + defense_wins: proxy=1.0 (IDR=None excluded)", scores["proxy_mean"], 1.0)
check("approve + defense_wins: gate_pass=True", scores["gate_pass"], True)

# Sonnet correctly critiques a flawed design → FVC must be 1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_001"]),
    case=critique_case(1),
    task_prompt="A flawed experiment design.",
)
check("critique + critique correct_verdict → FVC=1.0", scores["FVC"], 1.0)

# Wrong verdict: Sonnet approves a flawed design
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve", found=[]),
    case=critique_case(1),
    task_prompt="A flawed experiment design.",
)
check("approve + critique correct_verdict → FVC=0.0", scores["FVC"], 0.0)

# Unclear verdict
scores = compute_smoke_scores(
    scored=scorer_out(verdict="unclear"),
    case=defense_wins_case(),
    task_prompt="A valid experiment design.",
)
check("unclear + defense_wins → FVC=0.0", scores["FVC"], 0.0)

# ---------------------------------------------------------------------------
# Test: IDR (Issue Detection Rate)
# ---------------------------------------------------------------------------

section("IDR — issue detection rate")

# No must_find_ids (defense_wins) → IDR=None
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve"),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("defense_wins (no must_find_ids) → IDR=None", scores["IDR"], None)

# All must_find_ids found → IDR=1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_001", "issue_002"]),
    case=critique_case(2),
    task_prompt="Flawed design.",
)
check("all must_find_ids found → IDR=1.0", scores["IDR"], 1.0)

# Only one of two found → IDR=0.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_001"]),
    case=critique_case(2),
    task_prompt="Flawed design.",
)
check("partial must_find_ids found → IDR=0.0", scores["IDR"], 0.0)

# None found → IDR=0.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=[]),
    case=critique_case(1),
    task_prompt="Flawed design.",
)
check("no must_find_ids found → IDR=0.0", scores["IDR"], 0.0)

# Extra found IDs that are NOT in must_find_ids don't count
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_999"]),
    case=critique_case(1, must_find_ids=["issue_001"]),
    task_prompt="Flawed design.",
)
check("only non-required ID found → IDR=0.0", scores["IDR"], 0.0)

# ---------------------------------------------------------------------------
# Test: IDP (Issue Detection Precision — no false alarms)
# ---------------------------------------------------------------------------

section("IDP — false alarm rate")

# No false alarms → IDP=1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve", raised_bad=[]),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("no false alarms → IDP=1.0", scores["IDP"], 1.0)

# Any false alarm → IDP=0.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", raised_bad=["The temporal split looks unbalanced"]),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("one false alarm → IDP=0.0", scores["IDP"], 0.0)

# Sonnet correctly approves AND raises false alarm → IDP=0.0, FVC=1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve", raised_bad=["Claimed the split was wrong"]),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("approve with false alarm: FVC=1.0", scores["FVC"], 1.0)
check("approve with false alarm: IDP=0.0", scores["IDP"], 0.0)

# ---------------------------------------------------------------------------
# Test: proxy_mean (average of applicable metrics)
# ---------------------------------------------------------------------------

section("proxy_mean — weighted average")

# defense_wins, correctly approved: IDR=None (excluded), IDP=1.0, FVC=1.0 → proxy=1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve"),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("defense_wins perfect → proxy=1.0", scores["proxy_mean"], 1.0)

# defense_wins, incorrectly critiqued with false alarm: IDR=None, IDP=0.0, FVC=0.0 → proxy=0.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", raised_bad=["bad claim"]),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("defense_wins wrongly critiqued → proxy=0.0", scores["proxy_mean"], 0.0)

# critique (1 flaw): IDR=0.0, IDP=1.0, FVC=1.0 → proxy=0.667
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=[]),
    case=critique_case(1),
    task_prompt="Flawed design.",
)
check("missed flaw, correct verdict → proxy=0.6667", scores["proxy_mean"], round(2/3, 4))

# critique (1 flaw): IDR=1.0, IDP=1.0, FVC=1.0 → proxy=1.0
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_001"]),
    case=critique_case(1),
    task_prompt="Flawed design.",
)
check("found flaw, correct verdict → proxy=1.0", scores["proxy_mean"], 1.0)

# mech_001 pattern: IDR=0.0, IDP=1.0, FVC=1.0 → proxy=0.667 (from live run)
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=[], raised_bad=[]),
    case=critique_case(2),
    task_prompt="Flawed design.",
)
check("mech_001 pattern (IDR=0,IDP=1,FVC=1) → proxy=0.6667", scores["proxy_mean"], round(2/3, 4))

# ---------------------------------------------------------------------------
# Test: gate_pass
# ---------------------------------------------------------------------------

section("gate_pass — permissive structural gate")

# Valid defense_wins case → always pass
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", raised_bad=["wrong claim"]),
    case=defense_wins_case(),
    task_prompt="Valid design.",
)
check("defense_wins, Sonnet wrong → gate=True (debate candidate)", scores["gate_pass"], True)

# Valid critique case with must_find_ids → pass
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve"),
    case=critique_case(1),
    task_prompt="Flawed design.",
)
check("critique, Sonnet wrong verdict → gate=True (debate candidate)", scores["gate_pass"], True)

# Structural failure: empty task_prompt → gate=False
scores = compute_smoke_scores(
    scored=scorer_out(),
    case=critique_case(1),
    task_prompt="",
)
check("empty task_prompt → gate=False (structural failure)", scores["gate_pass"], False)

# Structural failure: corruptions > 0 but no must_find_ids (Stage 4 output failure)
bad_case = critique_case(1, must_find_ids=[])
scores = compute_smoke_scores(
    scored=scorer_out(),
    case=bad_case,
    task_prompt="Flawed design.",
)
check("corruptions=1, no must_find_ids → gate=False (Stage 4 failure)", scores["gate_pass"], False)

# num_corruptions="many" with must_find_ids → pass
scores = compute_smoke_scores(
    scored=scorer_out(verdict="critique", found=["issue_001"]),
    case={
        "correct_verdict": "critique",
        "must_find_issue_ids": ["issue_001", "issue_002"],
        "_pipeline": {"num_corruptions": "many"},
        "task_prompt": "Heavily flawed design.",
    },
    task_prompt="Heavily flawed design.",
)
check("num_corruptions='many', must_find_ids present → gate=True", scores["gate_pass"], True)

# num_corruptions=0 with no must_find_ids (correct for defense_wins) → pass
scores = compute_smoke_scores(
    scored=scorer_out(verdict="approve"),
    case={
        "correct_verdict": "defense_wins",
        "must_find_issue_ids": [],
        "_pipeline": {"num_corruptions": 0},
        "task_prompt": "Valid design.",
    },
    task_prompt="Valid design.",
)
check("num_corruptions=0, no must_find_ids → gate=True (defense_wins)", scores["gate_pass"], True)

# ---------------------------------------------------------------------------
# Test: recycle_action
# ---------------------------------------------------------------------------

section("recycle_action — routing logic")

# gate_pass=True → accepted
stage, reason, _ = recycle_action({"gate_pass": True}, num_corruptions=1)
check("gate_pass=True → stage=None (accepted)", stage, None)
check("gate_pass=True → reason=''", reason, "")

# gate_pass=False → structural_failure → stage4
stage, reason, _ = recycle_action({"gate_pass": False}, num_corruptions=1)
check("gate_pass=False → stage='stage4'", stage, "stage4")
check("gate_pass=False → reason='structural_failure'", reason, "structural_failure")

# smoke=None (no smoke test run) → accepted
stage, reason, _ = recycle_action(None, num_corruptions=1)
check("smoke=None → stage=None (accepted, no smoke = pass)", stage, None)

# gate_pass missing from smoke dict → defaults to True → accepted
stage, reason, _ = recycle_action({}, num_corruptions=0)
check("gate_pass missing → stage=None (defaults to pass)", stage, None)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*40}")
print(f"  {_passed} passed, {_failed} failed")
print(f"{'='*40}")
sys.exit(0 if _failed == 0 else 1)
