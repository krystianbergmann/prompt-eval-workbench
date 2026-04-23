# Prompt eval workbench

**Problem → solution portfolio piece:** a small end-to-end pattern for **observing** LLM apps in production-like conditions, **measuring** quality with repeatable suites, and **unifying** CI evals (Promptfoo) with observability (Langfuse)—so leaders and ICs share one narrative on quality.

---

## Executive summary

| | |
|---|---|
| **Problem** | LLM behavior is opaque; ad-hoc chat and one-off scripts do not scale for **regression control**, **trend visibility**, or **cross-team alignment**. |
| **Approach** | A **Streamlit** workbench for exploration and in-app benchmarks; **Promptfoo** for gated, versioned evals; **Langfuse** for traces, sessions, and scores—wired so batch results are not siloed from monitoring. |
| **Outcome** | One place to ask “did we break anything?” (CI) and “what happened in the wild?” (observability), with **named scores** suitable for dashboards and reviews. |

---

## What this repository contains

- **Interactive layer** — Solo chat, two-model dialogues (manual / automated), optional model comparison before standardizing on a provider.
- **Measurement layer** — Curated dataset under `data/`, simple rubric (`must_contain_any`), per-item and aggregate scores in Langfuse.
- **Automation layer** — Promptfoo config under `config/`, JSON results, sync of pass/fail and accuracy into Langfuse for portfolio- and CI-friendly runs.
- **Quality bar** — `pytest` for benchmark logic and Promptfoo JSON parsing (no live API required in tests).

**Architecture (one diagram):** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Mermaid system view (renders on GitHub).

For a **walkthrough deck** (problem space, architecture, observability, best practices), open `docs/presentation/index.html` in a browser.

---

## Repository layout

```text
├── app.py                      # Streamlit entrypoint (run from repo root)
├── prompt_eval_workbench/      # Application library
│   ├── benchmark.py            # Dataset load, grading, single-item generation
│   ├── benchmark_scores.py     # Langfuse scores for in-app benchmark runs
│   ├── chat_logic.py           # Shared formatting / model list
│   └── promptfoo_sync.py       # Promptfoo JSON → Langfuse scores (CLI module)
├── data/
│   └── benchmark_data.json     # Editable eval cases
├── config/
│   └── promptfooconfig.yaml    # Promptfoo suite
├── docs/
│   ├── ARCHITECTURE.md         # System diagram (Mermaid)
│   └── presentation/
│       └── index.html          # Static portfolio deck
├── tests/
├── requirements.txt
└── package.json                # Promptfoo npm scripts
```

---

## Quick start

**1. Python**

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_* and LANGFUSE_*
```

**2. Run the app**

```bash
streamlit run app.py
```

**3. Optional: Promptfoo + Langfuse sync** (requires Node for Promptfoo)

```bash
npm install
npm run test:promptfoo:langfuse
```

**4. Tests**

```bash
python3 -m pytest tests/ -q
```

---

## Design choices (for reviewers)

- **Separation of concerns** — UI and “lab” flows in Streamlit; **deterministic** suites in Promptfoo; **telemetry and scores** in Langfuse. The sync step exists so **CI and observability share a vocabulary**, not two competing reports.
- **Explicit score names** — `benchmark_*` vs `promptfoo_*` keeps session-level analysis unambiguous.
- **Small, auditable surface** — Favor readable Python and config over framework depth, so scope of change is obvious in review.

---

## Tech stack

Python 3.11+ · Streamlit · OpenAI API · Langfuse · Promptfoo · pytest · Node 18+ (dev, for Promptfoo CLI)

---

## License

Use and adapt for your portfolio as needed; ensure your own API keys and Langfuse project stay private.
