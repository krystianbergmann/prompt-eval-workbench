"""Langfuse scores for Streamlit benchmark runs (session-scoped)."""

import hashlib

from langfuse import get_client


def _item_score_id(session_id: str, item_id: str, run_index: int) -> str:
    raw = f"{session_id}|{item_id}|{run_index}".encode()
    return "bm_pass_" + hashlib.sha256(raw).hexdigest()[:32]


def record_benchmark_item_pass(
    session_id: str,
    *,
    item_id: str,
    passed: bool,
    run_index: int,
) -> None:
    """Numeric 0/1 per benchmark row; appears on Scores dashboard filtered by session."""
    get_client().create_score(
        name="benchmark_item_pass",
        value=1.0 if passed else 0.0,
        data_type="NUMERIC",
        session_id=session_id,
        metadata={"benchmark_item_id": item_id},
        score_id=_item_score_id(session_id, item_id, run_index),
    )


def record_benchmark_accuracy(session_id: str, *, passed: int, total: int) -> None:
    """Aggregate pass rate for this benchmark run (0.0–1.0)."""
    if total <= 0:
        return
    get_client().create_score(
        name="benchmark_accuracy",
        value=float(passed / total),
        data_type="NUMERIC",
        session_id=session_id,
        comment=f"{passed}/{total} items passed",
        score_id="bm_acc_" + hashlib.sha256(f"{session_id}|acc".encode()).hexdigest()[:32],
    )
