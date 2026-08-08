# How to run an agent

All agents live in `.github/agents/*.agent.md` and each has a matching slash-command in
`.github/prompts/*.prompt.md`. Copilot discovers everything under `.github/` automatically
when the repo is open — there is nothing to install.

---

## Option A — VS Code (GitHub Copilot)
1. Open this repo folder in VS Code with the **GitHub Copilot** extension signed in.
2. Open **Copilot Chat** (Ctrl/Cmd + Alt/Ctrl + I).
3. **Either** pick the agent from the chat **agent/mode picker** at the top of the chat
   panel, **or** type its slash command, e.g.:
   - `/acceptance-criteria-writer`
   - `/code-review`
4. Provide your input when prompted (a user story, or a code diff/PR).

## Option B — GitHub Copilot CLI
1. Install the Copilot CLI and run `copilot` **inside the repo folder**.
2. List discovered agents: `/agents`
3. Select the agent you want, then give it your input.
   (Repo agents in `.github/agents/` are picked up automatically at session start.)

## Option C — Copilot coding agent (assign an Issue)
The cloud coding agent also reads `.github/agents/` and `.github/copilot-instructions.md`.
Reference the agent by name in the issue (e.g. "Use the code-review agent to review this
PR") and it will apply that persona.

## Option D — Microsoft / Copilot Chat in the browser (manual fallback)
The browser Copilot does not auto-read this repo. To use an agent there:
1. Open the agent file (e.g. `.github/agents/code-review-agent.agent.md`) and the skill +
   knowledge files it references.
2. Paste their contents into the chat as context, then paste your story or code.
This is the portable fallback — the same definitions work anywhere you can paste context.

---

## Worked examples

**Acceptance Criteria Writer**
```
/acceptance-criteria-writer
As a returning customer, I want to save my payment details so that checkout is faster.
```

**Code Review Agent**
```
/code-review
<paste your Java diff or PR description here>
```
