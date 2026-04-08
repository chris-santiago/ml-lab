# Lessons Learned

## Python controls iteration, not prompts

**Rule:** Python code (loops, concurrent executors) must control iteration over cases/batches — never embed iteration logic inside a prompt.

**Why:** When iteration lives in a prompt, the model decides how many cases to process, when to stop, and how to batch. This is fragile, non-deterministic, and hard to debug. The user's example: "how many cases are there in total? what is our batch in this context? we should iterate through all known papers (or benchmark total cases). You can sequentially iterate and send a prompt for each, or batch into groups ≤5 and send concurrently. A prompt should not control iteration. A Python loop or concurrent executor should. For every stage."

**How to apply:** For any multi-case pipeline stage, the Python script wraps the LLM call in a `for` loop or `ThreadPoolExecutor` / `asyncio` gather. The prompt receives exactly one case at a time and returns output for that case. The script assembles results. Never ask the model to "process all N cases" in a single prompt.
