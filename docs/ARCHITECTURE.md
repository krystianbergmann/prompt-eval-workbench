# Architecture

This document is a **single end-to-end view** of the workbench: how the Streamlit app, the Python package, OpenAI, Langfuse, and the Promptfoo automation path connect. It matches the implementation under `app.py`, `prompt_eval_workbench/`, `data/`, and `config/`.

## System diagram

```mermaid
flowchart TB
  U[("User / operator")]

  subgraph app["Streamlit app"]
    A["app.py"]
  end

  subgraph pkg["Package: prompt_eval_workbench"]
    B["benchmark.py"]
    S["benchmark_scores.py"]
    C["chat_logic.py"]
    PF["promptfoo_sync.py"]
  end

  subgraph files["Config & data"]
    D[("data/benchmark_data.json")]
    Y[("config/promptfooconfig.yaml")]
    R[("promptfoo-results.json")]
  end

  subgraph external["External services"]
    OAI[("OpenAI API")]
    LF[("Langfuse")]
  end

  subgraph ci["CI / local automation"]
    PFC[("Promptfoo CLI\nnpm run test:promptfoo")]
  end

  U --> A
  D --> B
  A --> B
  A --> C
  A --> OAI
  B --> OAI
  A -.->|instrumented client + flush| LF
  B -->|grade + record| S
  S -->|create_score benchmark_*| LF

  Y --> PFC
  PFC --> OAI
  PFC -->|writes| R
  R --> PF
  PF -->|create_score promptfoo_*| LF

  style A fill:#e8f4fc,stroke:#0369a1
  style LF fill:#f3e8ff,stroke:#7c3aed
  style PFC fill:#ecfdf5,stroke:#059669
```

**Reading the diagram**

- **Solid lines** are primary data or control: HTTP to OpenAI, file reads, score uploads.
- **Dotted** from `app.py` to Langfuse indicates **tracing and generations** (via the Langfuse-wrapped client), not a separate file artifact.
- **Two score families** land in Langfuse: `benchmark_*` from the in-app benchmark (`benchmark_scores.py`), and `promptfoo_*` from `promptfoo_sync.py` after a Promptfoo run.

For a stakeholder-oriented narrative (including problem framing and best practices), see the static deck at [`presentation/index.html`](presentation/index.html).
