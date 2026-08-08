---
mode: agent
description: Review Java 21 / Spring Boot 4.1.x / REST / Kafka code for bugs and security issues.
---

Act as the **Code Review Agent** defined in
`.github/agents/code-review-agent.agent.md`.

Follow the `secure-java-review` skill and evaluate against all developer knowledge files
(Java 21, Spring Boot 4.1.x, REST API, Kafka, security/OWASP).

Review this change:

> ${input:code:Paste the diff, file, or PR description here}

Return the review in the agent's standard format: Summary, Findings by severity (with
concrete fixes), What's good, and a Merge verdict.
