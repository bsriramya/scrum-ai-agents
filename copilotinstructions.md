# Copilot Workspace Instructions

## Compliance Memory Agent

This repo includes a stateful compliance agent that reviews every Java code
change against security and quality rules, remembers all past findings, and
trends them over time.

### How to run

Ask Copilot in agent mode:
> "Run the compliance agent"

Copilot will execute the following in the terminal:
```
python compliance_agent.py
```

### Prerequisites (first time only)

1. Copy `.env.example` to `.env` and add your API key.
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate   # Mac/Linux
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

### What the agent does

- **Phase 1** — Loads all past scan results from `.compliance-memory/runs/`
  and asks the LLM to summarise trends, recurring issues, and improvements.
- **Phase 2** — Runs a fresh compliance review on the latest git commit diff
  against the 9 rules in `.compliance-memory/compliance-rules.yaml`.
- Saves a timestamped JSON run file to `.compliance-memory/runs/`.

### Rules enforced

| Rule ID | Severity |
|---|---|
| SQL_INJECTION | HIGH |
| LOG_INJECTION | HIGH |
| HARDCODED_CREDENTIALS | HIGH |
| MISSING_AUTHENTICATION | HIGH |
| MISSING_TRANSACTIONAL | MEDIUM |
| MISSING_INPUT_VALIDATION | MEDIUM |
| EXCEPTION_EXPOSURE | MEDIUM |
| SENSITIVE_LOGGING | MEDIUM |
| ORACLE_CONNECTION_POOL | LOW |

### Switching models

Edit `LLM_MODEL` in your `.env` file — no code changes needed:

```
LLM_MODEL=claude-opus-4-5      # Anthropic (default)
LLM_MODEL=gpt-4o               # OpenAI
LLM_MODEL=azure/gpt-4o         # Azure / GitHub Copilot
```

### Memory location

```
.compliance-memory/
├── runs/            ← one JSON file per scan run
├── summary.md       ← rolling trend summary (auto-updated)
└── compliance-rules.yaml
```
