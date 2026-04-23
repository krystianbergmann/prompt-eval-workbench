"""Tests for Promptfoo → Langfuse JSON parsing (no Langfuse API calls)."""

import json
from pathlib import Path

from sync_promptfoo_to_langfuse import parse_promptfoo_results, row_item_key, row_passed


def test_parse_promptfoo_results_shape(tmp_path: Path):
    payload = {
        "evalId": "eval-x",
        "results": {
            "results": [
                {
                    "gradingResult": {"pass": True},
                    "testCase": {
                        "description": "Capital of France",
                        "vars": {"question": "..."},
                    },
                    "testIdx": 0,
                }
            ]
        },
    }
    p = tmp_path / "r.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    eid, rows = parse_promptfoo_results(p)
    assert eid == "eval-x"
    assert len(rows) == 1


def test_row_passed_grading_result():
    assert row_passed({"gradingResult": {"pass": True}, "success": False}) is True
    assert row_passed({"gradingResult": {"pass": False}}) is False
    assert row_passed({"success": True}) is True


def test_row_item_key():
    row = {"testCase": {"description": "Hello World"}}
    assert row_item_key(row, 0) == "Hello_World"
