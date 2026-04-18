import json
import random
from pathlib import Path
from typing import Generator


def load(path: str | Path) -> list[str]:
    """Load model IDs from models.json → flat list of model_id strings."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [item["model_id"] for item in data["models"]]


def fetch(path: str | Path) -> dict:
    """Load models.json → dict keyed by index (legacy; prefer load())."""
    with open(path, "r") as fp:
        models = json.load(fp)["models"]
        return {
            item["index"]: {k: v for k, v in item.items() if k != "index"}
            for item in models
        }


def model_generator(pool: list[str], n: int = 3) -> Generator[list[str], None, None]:
    """Infinite generator: each draw is an independent random sample of n from pool.

    Each call to next() is a fresh random.sample — draws are independent, every
    model in the pool has equal probability on every draw.

    Args:
        pool: List of model_id strings. Must have len >= n.
        n:    Number of distinct models per draw (default 3).
    """
    if len(pool) < n:
        raise ValueError(f"Pool has {len(pool)} models but n={n} requested")
    while True:
        yield random.sample(pool, n)


def generate_models(models: dict | list, n: int = 3) -> Generator[list[str], None, None]:
    """One-shot draw (legacy). Prefer model_generator() for continuous sampling."""
    if isinstance(models, dict):
        pool = [v["model_id"] for v in models.values()]
    else:
        pool = list(models)
    yield random.sample(pool, n)


if __name__ == "__main__":
    _path = Path(__file__).parent.parent / "models.json"
    _pool = load(_path)
    print(f"Pool: {len(_pool)} models")
    _gen = model_generator(_pool)
    for _i in range(3):
        print(f"Draw {_i}: {next(_gen)}")
