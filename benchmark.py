"""Simple substring benchmark for LLM outputs. Dataset: benchmark_data.json"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "benchmark_data.json"


@dataclass(frozen=True)
class BenchmarkSpec:
    name: str
    version: int
    description: str
    items: list[dict[str, Any]]


def load_benchmark(path: Path | None = None) -> BenchmarkSpec:
    p = path or DEFAULT_DATA_PATH
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("items", [])
    if not items:
        raise ValueError(f"No items in benchmark file: {p}")
    return BenchmarkSpec(
        name=str(raw.get("name", "unnamed")),
        version=int(raw.get("version", 0)),
        description=str(raw.get("description", "")),
        items=items,
    )


def pick_items(
    items: list[dict[str, Any]],
    *,
    max_count: int,
    shuffle: bool = False,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Return up to max_count items: first N in file order, or a random subset if shuffle=True."""
    if max_count <= 0:
        return []
    pool = list(items)
    k = min(max_count, len(pool))
    if shuffle:
        rng = random.Random(seed)
        return rng.sample(pool, k=k)
    return pool[:k]


def grade_answer(model_text: str, item: dict[str, Any]) -> bool:
    """Pass if output contains any must_contain_any (case-insensitive) and none of must_not_contain."""
    t = model_text.lower()
    needles = item.get("must_contain_any", [])
    if not needles:
        return False
    if not any(str(n).lower() in t for n in needles):
        return False
    forbidden = item.get("must_not_contain", [])
    return not any(str(b).lower() in t for b in forbidden)


def run_item_answer(
    client,
    *,
    model: str,
    system: str,
    question: str,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    return (response.choices[0].message.content or "").strip()
