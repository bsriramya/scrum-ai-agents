# Copilot Workspace Instructions

This repo has two stateful AI agents. Both remember every past run and reason
over history before scanning today's code. Trigger them from Copilot Agent chat.

---

## 1 — Security Vulnerability Agent

Scans every git commit for OWASP Top 10 vulnerabilities. Maintains a persistent
registry (V-001, V-002 …) and links new findings to past ones — showing systemic
patterns across commits and files.

### Trigger phrases (Copilot Agent chat)
```
Run the security vulnerability agent
Scan for security vulnerabilities
Check this commit for security issues
```

### What Copilot will run
```bash
python security_agent.py
```

### Memory location
```
.security-memory/
├── registry.json        ← persistent V-ID registry (all vulnerabilities ever found)
├── runs/                ← one JSON per scan
├── summary.md           ← rolling attack surface summary
└── security-rules.yaml  ← 15 OWASP-mapped rules
```

### Rules covered
| Rule ID | OWASP | Severity |
|---|---|---|
| BROKEN_ACCESS_CONTROL | A01:2021 | CRITICAL |
| PATH_TRAVERSAL | A01:2021 | HIGH |
| SENSITIVE_DATA_EXPOSURE | A02:2021 | HIGH |
| HARDCODED_SECRETS | A02:2021 | CRITICAL |
| WEAK_CRYPTOGRAPHY | A02:2021 | HIGH |
| SQL_INJECTION | A03:2021 | CRITICAL |
| LOG_INJECTION | A03:2021 | HIGH |
| COMMAND_INJECTION | A03:2021 | CRITICAL |
| MISSING_RATE_LIMITING | A04:2021 | MEDIUM |
| SECURITY_MISCONFIGURATION | A05:2021 | HIGH |
| XML_EXTERNAL_ENTITY | A05:2021 | HIGH |
| INSECURE_DESERIALIZATION | A08:2021 | HIGH |
| SSRF | A10:2021 | HIGH |

---

## 2 — Compliance Agent

Reviews every git commit against Spring Boot + Oracle coding standards.
Tracks findings over time and reports trends.

### Trigger phrases (Copilot Agent chat)
```
Run the compliance agent
Check my code for compliance issues
Run compliance review
```

### What Copilot will run
```bash
python compliance_agent.py
```

### Memory location
```
.compliance-memory/
├── runs/                    ← one JSON per scan
├── summary.md               ← rolling trend summary
└── compliance-rules.yaml    ← 9 compliance rules
```

---

## First-time setup (both agents)

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
pip install -r requirements.txt
cp .env.example .env           # then fill in your API key
```

## Switching models

Edit `LLM_MODEL` in `.env`:
```
LLM_MODEL=claude-opus-4-5      # Anthropic Claude (default)
LLM_MODEL=claude-sonnet-4-5    # Faster Claude
LLM_MODEL=gpt-4o               # OpenAI
LLM_MODEL=azure/gpt-4o         # Azure / GitHub Copilot
```
