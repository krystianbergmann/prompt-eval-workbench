#!/usr/bin/env python3
"""
Option A: After `npm run test:promptfoo`, push scores from `promptfoo-results.json` to Langfuse.

Usage:
  python sync_promptfoo_to_langfuse.py
  python sync_promptfoo_to_langfuse.py --json path/to/results.json
  LANGFUSE_PROMPTFOO_SESSION_ID=my-ci-run python sync_promptfoo_to_langfuse.py

Requires: .env with LANGFUSE_* and OPENAI was used by promptfoo already; Langfuse keys for ingestion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client  # noqa: E402

DEFAULT_JSON = Path(__file__).resolve().parent / "promptfoo-results.json"


def _slug(s: str, max_len: int = 80) -> str:
    out = re.sub(r"[^a-zA-Z0-9_-]+", "_", s.strip())[:max_len]
    return out or "test"


def _item_score_id(session_id: str, stable_key: str) -> str:
    raw = f"{session_id}|{stable_key}|promptfoo".encode()
    return "pf_pass_" + hashlib.sha256(raw).hexdigest()[:32]


def _acc_score_id(session_id: str) -> str:
    return "pf_acc_" + hashlib.sha256(f"{session_id}|accuracy".encode()).hexdigest()[:32]


def parse_promptfoo_results(path: Path) -> tuple[str, list[dict]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    eval_id = str(data.get("evalId", "unknown"))
    inner = data.get("results") or {}
    rows = inner.get("results")
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected JSON shape in {path}: missing results.results array")
    return eval_id, rows


def row_passed(row: dict) -> bool:
    gr = row.get("gradingResult") or {}
    if "pass" in gr:
        return bool(gr["pass"])
    return bool(row.get("success"))


def row_item_key(row: dict, index: int) -> str:
    tc = row.get("testCase") or {}
    desc = tc.get("description") or ""
    if desc:
        return _slug(desc)
    return f"test_{row.get('testIdx', index)}"


def sync_to_langfuse(
    path: Path,
    *,
    session_id: str,
) -> tuple[int, int]:
    eval_id, rows = parse_promptfoo_results(path)
    lf = get_client()
    passed = 0
    for i, row in enumerate(rows):
        ok = row_passed(row)
        if ok:
            passed += 1
        key = row_item_key(row, i)
        tc = row.get("testCase") or {}
        desc = tc.get("description") or ""
        metadata = {
            "source": "promptfoo",
            "eval_id": eval_id,
            "promptfoo_test_key": key,
            "test_idx": row.get("testIdx", i),
        }
        if desc:
            metadata["promptfoo_test_description"] = desc

        lf.create_score(
            name="promptfoo_item_pass",
            value=1.0 if ok else 0.0,
            data_type="NUMERIC",
            session_id=session_id,
            metadata=metadata,
            score_id=_item_score_id(session_id, f"{key}_{i}"),
            comment=f"Promptfoo eval {eval_id}",
        )

    n = len(rows)
    if n > 0:
        lf.create_score(
            name="promptfoo_accuracy",
            value=float(passed / n),
            data_type="NUMERIC",
            session_id=session_id,
            comment=f"{passed}/{n} Promptfoo tests passed (eval {eval_id})",
            score_id=_acc_score_id(session_id),
            metadata={"source": "promptfoo", "eval_id": eval_id},
        )
    lf.flush()
    return passed, n


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync Promptfoo JSON results to Langfuse scores.")
    ap.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON,
        help=f"Path to promptfoo-results.json (default: {DEFAULT_JSON})",
    )
    ap.add_argument(
        "--session-id",
        default=os.environ.get("LANGFUSE_PROMPTFOO_SESSION_ID"),
        help="Langfuse session id for these scores (default: env LANGFUSE_PROMPTFOO_SESSION_ID or derived from evalId)",
    )
    args = ap.parse_args()
    path: Path = args.json

    if not path.is_file():
        print(f"Missing file: {path}. Run: npm run test:promptfoo", file=sys.stderr)
        return 1

    eval_id, rows = parse_promptfoo_results(path)
    session_id = args.session_id
    if not session_id:
        safe_eval = re.sub(r"[^a-zA-Z0-9._-]", "-", eval_id)[:120]
        session_id = f"promptfoo-{safe_eval}"

    p, n = sync_to_langfuse(path, session_id=session_id)
    print(f"Langfuse session_id: {session_id}")
    print(f"Uploaded scores for {n} tests ({p} passed). Names: promptfoo_item_pass, promptfoo_accuracy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
