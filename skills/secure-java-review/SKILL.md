---
name: secure-java-review
description: Use this to review Java 21 / Spring Boot backend code (REST, Kafka) for correctness, maintainability, and security vulnerabilities, producing a prioritised review.
---

# Skill: secure-java-review

A reusable procedure for reviewing backend Java changes. The steps are stable; the
*knowledge* (version standards, security checklist) is swapped per team/stack.

## When to use
Reviewing a diff, file, or PR for a Java 21 / Spring Boot service that exposes REST APIs
and/or uses Kafka.

## Procedure
1. **Understand the change in context.** What is it trying to do? Which layer
   (controller, service, repository, messaging, config)?
2. **Correctness & concurrency.** Logic bugs, null handling, `Optional` misuse, resource
   leaks, thread-safety, and correct use of virtual threads (no pinning).
3. **API contract (if REST touched).** Status codes, validation, idempotency, versioning,
   error shape, pagination — against `rest-api-standards`.
4. **Messaging (if Kafka touched).** Keys/partitioning, idempotent consumers, error &
   retry/DLT handling, serialization, exactly-once vs at-least-once — against
   `kafka-guidelines`.
5. **Security pass.** Walk the `security-owasp-checklist`: injection, authn/authz, secrets,
   input validation, deserialization, SSRF, sensitive-data logging, dependency risks.
6. **Framework fit.** Idiomatic Spring Boot 4.1.x and Java 21 usage against
   `java21-standards` and `spring-boot-4.1.x-guidelines`.
7. **Tests.** Are the risky paths covered? Are new branches tested?
8. **Report by severity.** Blocker > High > Medium > Low/Nit, each with a concrete fix.

## Severity guide
- **Blocker:** security vuln, data loss, broken contract → must fix before merge.
- **High:** likely bug, resource leak, standards violation.
- **Medium:** maintainability, missing tests, unclear errors.
- **Low / Nit:** style, naming, minor cleanups.

## Output format
`Summary` → `Findings` (grouped by severity, each with Where / Why / Fix / Reference) →
`What's good` → `Merge verdict` (Approve / Approve with comments / Request changes).

## Anti-patterns to avoid
- Rewriting instead of proposing minimal fixes.
- Style nits drowning out real risks — lead with severity.
- Weakening security for simplicity.
