# Scrum AI Agents

A shared, team-owned catalog of **AI agents** that any role on our Scrum team can use
inside **GitHub Copilot** and **Microsoft Copilot**. Each agent is built from three
reusable parts:

| Part | What it is | Where it lives |
|------|-----------|----------------|
| **Agent** | A named persona Copilot runs (the "who + what") | `.github/agents/*.agent.md` |
| **Skill** | A reusable *how-to* procedure the agent follows | `skills/<name>/SKILL.md` |
| **Knowledge** | Reference *facts* the agent draws on (our standards, glossary) | `knowledge/<role>/*.md` |

> **The idea:** a **prompt** is your one-off ask. A **skill** is the repeatable
> procedure. **Knowledge** is our team-specific reference material. An agent bundles a
> skill + the right knowledge behind a name you can call.

---

## Agent catalog

| Agent | Role | Invoke as | Skill used | Knowledge used |
|-------|------|-----------|------------|----------------|
| **Acceptance Criteria Writer** | Product Owner | `/acceptance-criteria-writer` | `gherkin-ac` | `definition-of-ready`, `domain-glossary` |
| **Code Review Agent** | Developer | `/code-review` | `secure-java-review` | `java21-standards`, `spring-boot-4.1.x-guidelines`, `rest-api-standards`, `kafka-guidelines`, `security-owasp-checklist` |

More agents welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Quick start (2 minutes)

1. **Clone this repo** and open it in **VS Code** (with the GitHub Copilot extension) or
   run **GitHub Copilot CLI** inside the repo folder.
2. Open **Copilot Chat**.
3. Pick an agent (see [docs/how-to-run-an-agent.md](docs/how-to-run-an-agent.md)):
   - **VS Code:** choose the agent from the chat **mode/agent picker**, or type the
     matching prompt command, e.g. `/acceptance-criteria-writer`.
   - **Copilot CLI:** run `copilot`, then `/agents` to list and select one.
4. Give it your input (a user story, a code diff, etc.) and go.

Because Copilot reads everything under `.github/` automatically, no install step is
needed beyond having the repo open.

---

## Repository structure

```
scrum-ai-agents/
├── README.md                     # this file
├── CONTRIBUTING.md               # how any role adds an agent / skill / knowledge
├── AGENTS.md                     # index Copilot CLI & the coding agent read
├── .github/
│   ├── copilot-instructions.md   # repo-wide baseline, applied to every request
│   ├── agents/                   # THE AGENTS (invocable personas)
│   │   ├── acceptance-criteria-writer.agent.md
│   │   └── code-review-agent.agent.md
│   ├── prompts/                  # slash-command entry points (/name)
│   │   ├── acceptance-criteria-writer.prompt.md
│   │   └── code-review.prompt.md
│   └── instructions/             # path-specific rules (auto-applied by file type)
│       └── java-backend.instructions.md
├── skills/                       # reusable HOW-TO procedures
│   ├── gherkin-ac/SKILL.md
│   └── secure-java-review/SKILL.md
├── knowledge/                    # reference FACTS, organised by role
│   ├── product-owner/
│   │   ├── definition-of-ready.md
│   │   └── domain-glossary.md
│   └── developer/
│       ├── java21-standards.md
│       ├── spring-boot-4.1.x-guidelines.md
│       ├── rest-api-standards.md
│       ├── kafka-guidelines.md
│       └── security-owasp-checklist.md
└── docs/
    ├── how-to-run-an-agent.md
    └── how-to-add-a-new-agent.md
```

## Why this split matters

Move an agent to a different product and its **skill stays identical** (the procedure is
universal) while its **knowledge is swapped out** (different glossary, different
standards). Keeping the two apart is what makes this repo reusable and easy to extend.
