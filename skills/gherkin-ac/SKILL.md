---
name: gherkin-ac
description: Use this when turning a user story into clear, testable acceptance criteria in Given/When/Then format.
---

# Skill: gherkin-ac

A reusable procedure for writing acceptance criteria. It is product-agnostic — the steps
never change; only the *knowledge* (glossary, Definition of Ready) changes per team.

## When to use
Any time a user story needs acceptance criteria before it can enter a sprint.

## Procedure
1. **Restate the goal.** Summarise the story's intent in one line so scope is explicit.
2. **Write in Given / When / Then.**
   - *Given* = the starting context/precondition.
   - *When* = the action or event.
   - *Then* = the observable, checkable outcome.
3. **Happy path first.** Write the primary success scenario before anything else.
4. **Then edge & error cases.** Empty states, invalid input, permissions, limits,
   timeouts, concurrency, and failure/rollback behaviour.
5. **Make each criterion testable.** Replace vague words ("fast", "easy", "secure") with
   measurable outcomes ("responds within 2s", "shows error message X", "stores only a
   tokenised card").
6. **Check Definition of Ready.** Confirm the story has a clear goal, criteria, and no
   open questions. List anything missing.

## Output format
- **Goal:** one line.
- **Acceptance Criteria:** numbered Given/When/Then list (happy path, then edge/error).
- **Readiness check:** meets DoR, or the gaps that remain.

## Anti-patterns to avoid
- Criteria that restate the story instead of specifying behaviour.
- Untestable adjectives.
- Gold-plating (criteria beyond the story's stated goal).
- Hidden decisions the Product Owner has not actually made.
