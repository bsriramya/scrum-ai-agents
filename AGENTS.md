# Agents index

This file helps Copilot CLI and the coding agent understand the repo. Human-readable
catalog and details live in `README.md`.

## Available agents
- **acceptance-criteria-writer** (`.github/agents/acceptance-criteria-writer.agent.md`)
  — Product Owner: turns user stories into testable Given/When/Then acceptance criteria.
- **code-review-agent** (`.github/agents/code-review-agent.agent.md`)
  — Developer: reviews Java 21 / Spring Boot 4.1.x / REST / Kafka code for bugs and
  security vulnerabilities.

## Conventions
- Agents: `.github/agents/*.agent.md`
- Prompt entry points: `.github/prompts/*.prompt.md` (invoke as `/name`)
- Reusable skills: `skills/<name>/SKILL.md`
- Reference knowledge: `knowledge/<role>/*.md`

To add an agent, see `docs/how-to-add-a-new-agent.md`.
