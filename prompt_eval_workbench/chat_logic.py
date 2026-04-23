"""Pure helpers shared by the Streamlit app (testable without importing streamlit)."""

MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]


def format_transcript(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        label = "Model A" if row["speaker"] == "A" else "Model B"
        lines.append(f"{label}: {row['content']}")
    return "\n".join(lines)
