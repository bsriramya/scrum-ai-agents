---
mode: agent
description: Write testable Given/When/Then acceptance criteria for a user story.
---

Act as the **Acceptance Criteria Writer** agent defined in
`.github/agents/acceptance-criteria-writer.agent.md`.

Follow the `gherkin-ac` skill and use the Product Owner knowledge files
(Definition of Ready, domain glossary).

My user story:

> ${input:story:Paste the user story here (As a <role>, I want <goal> so that <benefit>)}

Produce: (1) a one-line goal restatement, (2) numbered Given/When/Then acceptance
criteria covering the happy path then edge/error cases, (3) a Definition-of-Ready check.
