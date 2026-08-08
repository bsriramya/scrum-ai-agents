---
applyTo: "**/*.java"
description: Baseline standards auto-applied to all Java files in this repo's target codebase.
---

# Java backend instructions (auto-applied to *.java)

When writing or reviewing Java in this codebase, assume **Java 21** and
**Spring Boot 4.1.x**, and apply our standards:

- Prefer **constructor injection**; never field injection.
- Use **records** for immutable DTOs; use **sealed types** and **pattern matching** where
  they clarify intent.
- Consider **virtual threads** for blocking I/O-bound work; do not pin them by
  synchronizing over blocking calls.
- Validate all external input; never trust request bodies, headers, or Kafka payloads.
- Never log secrets, tokens, or full payloads containing PII.

For full detail see the knowledge files under `knowledge/developer/`. For a full review,
invoke the **code-review** agent.
