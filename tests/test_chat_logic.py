"""Tests for pure helpers used by app.py."""

from prompt_eval_workbench.chat_logic import MODELS, format_transcript


def test_format_transcript_empty():
    assert format_transcript([]) == ""


def test_format_transcript_one_line_each_speaker():
    rows = [
        {"speaker": "A", "content": "Hello."},
        {"speaker": "B", "content": "Hi there."},
    ]
    assert format_transcript(rows) == "Model A: Hello.\nModel B: Hi there."


def test_models_list_nonempty():
    assert isinstance(MODELS, list)
    assert len(MODELS) >= 1
    assert all(isinstance(m, str) for m in MODELS)
