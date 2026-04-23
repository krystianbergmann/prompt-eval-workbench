"""Tests for benchmark.py (no API calls)."""

import json

from prompt_eval_workbench.benchmark import DEFAULT_DATA_PATH, grade_answer, load_benchmark, pick_items


def test_load_benchmark_default_path():
    spec = load_benchmark(DEFAULT_DATA_PATH)
    assert spec.name
    assert len(spec.items) >= 1


def test_grade_answer_pass():
    item = {
        "id": "x",
        "question": "q",
        "must_contain_any": ["Paris"],
    }
    assert grade_answer("The capital is Paris.", item) is True


def test_grade_answer_fail_missing():
    item = {"id": "x", "question": "q", "must_contain_any": ["Paris"]}
    assert grade_answer("London is nice.", item) is False


def test_grade_answer_respects_must_not_contain():
    item = {
        "id": "x",
        "must_contain_any": ["yes"],
        "must_not_contain": ["no"],
    }
    assert grade_answer("yes absolutely", item) is True
    assert grade_answer("yes and no", item) is False


def test_grade_answer_empty_needles_fails():
    assert grade_answer("anything", {"must_contain_any": []}) is False


def test_benchmark_json_is_valid():
    with open(DEFAULT_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    assert "items" in data
    assert len(data["items"]) >= 5
    for it in data["items"]:
        assert "question" in it
        assert "must_contain_any" in it and it["must_contain_any"]


def test_pick_items_first_n():
    items = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert pick_items(items, max_count=2, shuffle=False) == [{"id": 1}, {"id": 2}]


def test_pick_items_shuffle_reproducible():
    items = [{"id": i} for i in range(10)]
    a = pick_items(items, max_count=5, shuffle=True, seed=123)
    b = pick_items(items, max_count=5, shuffle=True, seed=123)
    assert a == b
    assert len(a) == 5
