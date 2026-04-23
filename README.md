# Prompt eval workbench

**Streamlit chat, Langfuse observability, and repeatable LLM benchmarks** — a small app that combines interactive model testing, structured offline evaluation (Promptfoo), and scores in Langfuse so quality and regressions live in one place.

**Stack:** Streamlit · OpenAI · Langfuse · Promptfoo · pytest

For the full narrative (slides on problem space, diagrams, score semantics, and pipeline practices), open **[docs/presentation/index.html](docs/presentation/index.html)** in a browser. This README mirrors that deck in shorter form and adds setup and layout.

---

## Building blocks

**Promptfoo** is an open-source evaluation framework: prompts, test cases, and assertions in config; batch runs against your provider; machine-readable results for CI, PRs, and regression checks. It fits **offline / pipeline** work — same inputs every run so you can diff behavior over time.

**Langfuse** is an LLM engineering platform for observability and evaluation: traces, generations, sessions, and scores in a shared UI or API. It answers **how the model is used in practice**, with **scores and dashboards** so product and engineering align on the same quality picture.

Together they are **complementary, not redundant**: Promptfoo gates changes and keeps benchmarks steady; Langfuse watches usage and how quality moves over time.

---

## Problem space

| What is hard? | What this project optimizes for |
|----------------|----------------------------------|
| **Black-box LLMs** — behavior shifts with prompts, models, and temperature. | **Observability** — sessions, tags, and flushing traces to Langfuse during chat and benchmarks. |
| **No single metric** — you need traces for debugging and aggregate scores for trends. | **Comparable runs** — benchmark JSON, Promptfoo config, and shared grading hooks. |
| **Manual chat ≠ CI** — exploratory UI must pair with repeatable tests and exportable results. | **Actionable dashboards** — explicit score names in Langfuse (`benchmark_*`, `promptfoo_*`). |

---

## Why wire Promptfoo and Langfuse?

Promptfoo answers **“did the tests pass?”** in CI; Langfuse answers **“what happened, and how does quality trend?”** for live and batched work. Wiring them avoids two parallel stories about the same product.

- **Same vocabulary** — offline eval scores sit next to session-scoped app and benchmark metrics.
- **Comparable over time** — Promptfoo runs become first-class Langfuse scores so pipeline regressions show up where teams already look.
- **Less context switching** — no hand-off between “the eval tool” and “the observability tool” when triaging a drop in pass rate.

**Why keep both?** Promptfoo: regression testing, CI signal, controlled benchmarks. Langfuse: production-style evaluation, traces and sessions, trend tracking, light scoring in one place for dashboards.

---

## Why use it / why this design?

**Operators** — one loop (chat, in-app benchmark, Promptfoo); faster debugging via sessions, tags, and scores; regressions visible as `benchmark_*` and `promptfoo_*` in Langfuse; two-model mode for side-by-side checks before standardizing a model.

**Implementers** — small, inspectable surface (Streamlit + a few Python modules); CI-friendly evals (Promptfoo → JSON → short sync script → Langfuse); portable stack (OpenAI + Langfuse + env-based config); pytest around benchmark logic and sync for safe extension.

---

## Observability (what lands in Langfuse)

| Point | What is captured | How it appears |
|--------|-------------------|----------------|
| **Generations** | OpenAI chat completions (solo, duel, benchmark) via the Langfuse-wrapped client. | Traces and generations; `flush()` after key UI actions. |
| **Session scope** | Browser session, duel (`…-duel`), benchmark (`…-benchmark`), or Promptfoo eval (`promptfoo-…` / custom id). | Filter runs in Langfuse **Sessions** without cross-talk. |
| **Tags & routes** | Tag `streamlit-chat` plus route: `solo`, `duel-manual`, `duel-auto`, `benchmark`. | Slice traces by interaction type. |
| **Context metadata** | Duel speaker label; benchmark item id; Promptfoo rows carry `eval_id` and test keys in score metadata. | Link scores and traces to the exact turn or test case. |
| **Scores** | `benchmark_item_pass`, `benchmark_accuracy`; after sync, `promptfoo_item_pass`, `promptfoo_accuracy`. | Langfuse **Scores** — filter by name and session. |

---

## Solution outline

Two paths converge on Langfuse: **live app instrumentation** (Streamlit → OpenAI → traces) and **offline eval → JSON → score sync** (`promptfoo-results.json` → `prompt_eval_workbench.promptfoo_sync`).

**Diagram (renders on GitHub):** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

**Data flow (short):** `data/benchmark_data.json` and `.env` feed the app; `config/promptfooconfig.yaml` drives Promptfoo; the CLI writes `promptfoo-results.json`; the sync module posts `promptfoo_*` scores. Benchmark scores are written from the app path. Solid lines are requests/files; tracing sits alongside the same OpenAI calls (see architecture doc).

### Reading Promptfoo scores in Langfuse

- **`promptfoo_item_pass`** — numeric per test row (typically 0/1); use to see **which cases failed**.
- **`promptfoo_accuracy`** — 0.0–1.0 for the full run (passed ÷ total); **headline** for one eval when filtered to one session.
- **Session** — set via env (`LANGFUSE_PROMPTFOO_SESSION_ID`), CLI, or default `promptfoo-{evalId}` so **one Promptfoo run ≈ one session slice**. Fix **session and time filters** before comparing runs. Streamlit paths send live generations; Promptfoo in CI is usually **scores-first** unless you instrument those calls too.

---

## Repository layout

```text
├── app.py                         # Streamlit entrypoint (run from repo root)
├── prompt_eval_workbench/
│   ├── benchmark.py               # Dataset, grading, single-item generation
│   ├── benchmark_scores.py        # Langfuse scores for in-app benchmark
│   ├── chat_logic.py              # Shared formatting / model list
│   └── promptfoo_sync.py          # Promptfoo JSON → Langfuse scores (CLI)
├── data/benchmark_data.json       # Editable eval cases
├── config/promptfooconfig.yaml    # Promptfoo suite
├── docs/
│   ├── ARCHITECTURE.md            # System diagram (Mermaid)
│   └── presentation/index.html    # Full walkthrough deck
├── tests/
├── requirements.txt
├── pyproject.toml                 # Package metadata + deps
└── package.json                   # Promptfoo npm scripts
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

**3. Optional: Promptfoo + Langfuse sync** (Node 18+)

```bash
npm install
npm run test:promptfoo:langfuse
```

**4. Tests**

```bash
python3 -m pytest tests/ -q
```

### Commands (from repo root)

| | |
|--|--|
| App | `streamlit run app.py` |
| Promptfoo only | `npm run test:promptfoo` |
| Push Promptfoo scores to Langfuse | `npm run sync:langfuse` |
| Eval + sync | `npm run test:promptfoo:langfuse` |
| Python tests | `python3 -m pytest tests/` |

---

## Technical stack

| Layer | Choice |
|-------|--------|
| UI | Streamlit — solo chat, manual/auto two-model duels, benchmark tab |
| LLM | OpenAI Python SDK; `langfuse.openai` for instrumentation |
| Observability | Langfuse `get_client()`, `propagate_attributes`, `flush()` |
| Benchmark | `data/benchmark_data.json`, `must_contain_any` grading |
| CLI eval | Promptfoo + `config/promptfooconfig.yaml` → `npm run test:promptfoo` |
| Scores sync | `prompt_eval_workbench/promptfoo_sync.py` reads JSON, `create_score` |
| Tests | pytest — `tests/test_benchmark.py`, `test_chat_logic.py`, `test_sync_promptfoo.py` |

Requires **Python 3.11+** and **Node 18+** (for Promptfoo CLI).

---

## Pipeline practices (from the deck)

**Do:** align evals with real tasks; change one thing at a time when comparing runs; unify interactive traces and batch scores in one observability story; treat credentials and data like production; use aggregates for trends and drill into failures for root cause.

**Avoid:** a single headline metric without context; automation that never reaches the same dashboards as live traffic; rubrics that reward the wrong behavior; silent model or prompt changes without a baseline; evals that only gate releases without learning *why* behavior changed.

---

## License

Use and adapt for your portfolio as needed; keep your own API keys and Langfuse project private.
