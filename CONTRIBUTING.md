# Contributing

This repo is owned by the whole Scrum team. Product Owners, Scrum Masters, Developers,
QA, and BAs are all encouraged to add agents, skills, and knowledge for their role.

## What you can contribute
- **Agents** (`.github/agents/*.agent.md`) — a named persona for a recurring task.
- **Skills** (`skills/<name>/SKILL.md`) — a reusable how-to procedure.
- **Knowledge** (`knowledge/<role>/*.md`) — team standards, glossaries, checklists.

## Workflow
1. Create a branch: `feat/<role>-<agent-name>` (e.g. `feat/qa-test-case-generator`).
2. Follow `docs/how-to-add-a-new-agent.md`.
3. Keep changes small and focused; one agent (or one knowledge update) per PR.
4. Update the catalog table in `README.md`.
5. Open a Pull Request. Tag the relevant role owner as reviewer.

## Review expectations
- **Skills** are reviewed for clarity and reusability (would it work on another product?).
- **Knowledge** is reviewed for accuracy — it is treated as a source of truth, so it must
  be correct and current. Cite internal sources where possible.
- **Agents** are reviewed for a precise `description` (drives correct invocation) and for
  correctly referencing their skill + knowledge.

## Keeping knowledge current
Knowledge files are only as good as they are accurate. If a standard changes (a new
Definition of Ready, an updated framework version), open a PR to update the file — do not
let agents run on stale facts.

## Ownership (suggested)
| Area | Owner |
|------|-------|
| `knowledge/product-owner/` | Product Owner |
| `knowledge/developer/` | Dev lead / tech lead |
| `knowledge/qa/` (future) | QA lead |
| `knowledge/scrum-master/` (future) | Scrum Master |
| Repo structure & standards | Whoever maintains the repo |
