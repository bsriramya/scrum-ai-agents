# How to add a new agent

Any Scrum role can contribute. An agent is always: **an agent file + a prompt file + at
least one skill + the knowledge it needs.**

## Steps
1. **Pick a role folder for knowledge.** Reuse `knowledge/product-owner/` or
   `knowledge/developer/`, or create a new one (e.g. `knowledge/qa/`, `knowledge/scrum-master/`).
2. **Add knowledge files** — the reference facts your agent needs, as `.md` files.
3. **Add a skill** — the reusable how-to procedure: `skills/<skill-name>/SKILL.md`
   (lowercase-hyphenated name; frontmatter with `name` + `description`).
4. **Add the agent** — `.github/agents/<agent-name>.agent.md` with frontmatter:
   ```yaml
   ---
   name: my-agent
   description: Use this when ... (this is how Copilot decides to use it — be specific)
   ---
   ```
   In the body, reference the skill and the knowledge files by relative path.
5. **Add a prompt entry point** — `.github/prompts/<agent-name>.prompt.md` with
   `mode: agent`, so it can be invoked as `/<agent-name>`.
6. **Register it** — add a row to the catalog table in `README.md`.
7. **Open a Pull Request** (see CONTRIBUTING.md) and request review.

## Naming rules (portability)
- Agent/skill `name`: lowercase, hyphens only, no spaces, no reserved words.
- Keep `description` short and action-oriented ("Use this when...").

## Checklist before opening a PR
- [ ] `.agent.md` created with clear `description`
- [ ] `.prompt.md` created (`/name` works)
- [ ] Skill added under `skills/`
- [ ] Knowledge files added under `knowledge/<role>/`
- [ ] Agent references skill + knowledge by relative path
- [ ] README catalog table updated
