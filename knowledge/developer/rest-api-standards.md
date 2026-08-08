# REST API standards

Apply to every HTTP endpoint. The Code Review Agent checks changes against these.

## Resources & methods
- Nouns for resources, plural (`/orders`, `/orders/{id}`). No verbs in paths.
- Correct method semantics: `GET` (safe), `POST` (create), `PUT` (full replace),
  `PATCH` (partial), `DELETE`.
- `GET` and `DELETE` must not have side effects beyond their contract; `PUT`/`DELETE`
  should be **idempotent**.

## Status codes
- `200` OK, `201` Created (+ `Location` header), `204` No Content.
- `400` validation error, `401` unauthenticated, `403` unauthorized, `404` not found,
  `409` conflict, `422` unprocessable, `429` rate-limited.
- `500` only for genuine server faults — never mask client errors as 500.

## Requests & validation
- Validate all input with `jakarta.validation`; reject unknown/oversized payloads.
- Support **idempotency keys** for non-idempotent creates where retries are possible.
- Paginate collections (`page`/`size` or cursor); never return unbounded lists.

## Error response shape (consistent)
```json
{
  "timestamp": "2026-01-01T12:00:00Z",
  "status": 400,
  "error": "Bad Request",
  "code": "VALIDATION_FAILED",
  "message": "Human-readable summary",
  "details": [{ "field": "email", "issue": "must be a valid email" }],
  "traceId": "..."
}
```
- Centralise via `@RestControllerAdvice`. Never leak stack traces or internal messages.

## Versioning & compatibility
- Version the API (`/v1/...` or media-type versioning). Do not make breaking changes to a
  released version.

## Security (see security-owasp-checklist.md)
- Authn/authz on every non-public endpoint. Enforce authorization at the resource level.
- Rate-limit public endpoints. Set sensible timeouts.

## Review flags
- Wrong/999-style status codes; 500 for validation errors.
- Missing input validation or pagination.
- Entities (not DTOs) returned; stack traces in responses.
- Breaking change to a released version.
