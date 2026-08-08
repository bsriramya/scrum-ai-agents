# Copilot instructions — Scrum AI Agents repo

This repository is a catalog of role-based AI agents for our Scrum team. When helping in
this repo, follow these baseline rules regardless of which agent is active.

## General behaviour
- Be concise and practical. Prefer checklists and concrete examples over prose.
- When a task matches one of our agents, follow that agent's definition in
  `.github/agents/*.agent.md`, the skill it references under `skills/`, and the knowledge
  files it names under `knowledge/`.
- Never invent our internal standards. If a knowledge file exists, use it as the source
  of truth; if information is missing, say so and ask.

## Repo conventions
- **Agents** live in `.github/agents/<name>.agent.md` (the invocable persona).
- **Skills** are reusable how-to procedures in `skills/<name>/SKILL.md`.
- **Knowledge** is reference material in `knowledge/<role>/<topic>.md`.
- A prompt entry point for each agent lives in `.github/prompts/<name>.prompt.md` so it
  can be invoked as `/<name>` in Copilot Chat.

## When asked to add a new agent
Follow `docs/how-to-add-a-new-agent.md`. Every new agent needs: an `.agent.md`, a
`.prompt.md`, at least one skill, and the knowledge files it depends on, plus a row added
to the catalog table in `README.md`.
