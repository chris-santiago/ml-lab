#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
# ]
# ///
"""
Phase 5.5 — Collect all 90 baseline and ensemble responses.
Calls claude-haiku-4-5 (3 baseline + 3 ensemble) for each of 15 cases.
Saves raw responses to phase_5_5_raw_responses.json.
"""
import json, os, time, threading
from openai import OpenAI
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CASES_FILE = Path(__file__).parent / "benchmark_cases_verified.json"
OUTPUT_FILE = Path(__file__).parent / "phase_5_5_raw_responses.json"
ENV_FILE = REPO_ROOT / "UV.env"

# Load API key
api_key = None
for line in ENV_FILE.read_text().strip().splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        api_key = line.split("=", 1)[1].strip()
        break

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in UV.env")

client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# Load cases and select
with open(CASES_FILE) as f:
    all_cases = json.load(f)

medium_cases = [c for c in all_cases if c["difficulty"] == "medium"][:5]
hard_cases = [c for c in all_cases if c["difficulty"] == "hard"][:10]
selected_cases = medium_cases + hard_cases

print(f"Selected {len(selected_cases)} cases: {len(medium_cases)} medium + {len(hard_cases)} hard")

def call_model(case_id: str, task_prompt: str, run_idx: int, condition: str) -> dict:
    """Single model call - returns {case_id, condition, run_idx, response, error}"""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="anthropic/claude-haiku-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": task_prompt}]
            )
            content = resp.choices[0].message.content
            return {
                "case_id": case_id,
                "condition": condition,
                "run_idx": run_idx,
                "response": content,
                "error": None
            }
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {case_id} {condition} run {run_idx}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return {
        "case_id": case_id,
        "condition": condition,
        "run_idx": run_idx,
        "response": None,
        "error": "max retries exceeded"
    }

# Collect all responses with rate limiting
results = []
total_calls = len(selected_cases) * 6  # 3 baseline + 3 ensemble per case
call_count = 0

SEMAPHORE = threading.Semaphore(5)  # max 5 concurrent

def collect_one(case, run_idx, condition):
    global call_count
    with SEMAPHORE:
        result = call_model(case["case_id"], case["task_prompt"], run_idx, condition)
        call_count += 1
        print(f"  [{call_count}/{total_calls}] {case['case_id']} {condition} run {run_idx+1} — {'OK' if result['response'] else 'ERROR'}")
        return result

import concurrent.futures

tasks = []
for case in selected_cases:
    for run_idx in range(3):
        tasks.append((case, run_idx, "baseline"))
        tasks.append((case, run_idx, "ensemble"))

print(f"\nRunning {len(tasks)} calls with semaphore(5)...")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(collect_one, case, run_idx, condition)
               for case, run_idx, condition in tasks]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

# Save raw results
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved {len(results)} results to {OUTPUT_FILE}")
errors = [r for r in results if r["error"]]
print(f"Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"  {e['case_id']} {e['condition']} run {e['run_idx']}: {e['error']}")
