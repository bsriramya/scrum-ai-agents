# Security checklist (OWASP-aligned)

The security pass of every code review. Any confirmed item here is a **Blocker**.

## Injection
- [ ] SQL/JPQL uses **parameterised queries** — no string-concatenated queries.
- [ ] No OS command construction from user input; avoid `Runtime.exec` with untrusted data.
- [ ] Output is encoded for its sink (HTML/URL/JSON) to prevent injection/XSS downstream.

## Authentication & authorization
- [ ] Every non-public endpoint enforces authentication.
- [ ] Authorization checked at the **resource** level (no IDOR — a user cannot access
      another user's object by changing an id).
- [ ] No security decisions made on the client side alone.

## Secrets & sensitive data
- [ ] No hardcoded secrets, keys, or passwords; loaded from config/secret manager.
- [ ] Secrets, tokens, and full PII payloads are **never logged**.
- [ ] Sensitive data (e.g., card data) is tokenised; comply with PCI — never store raw PANs.
- [ ] TLS enforced for data in transit; sensitive data encrypted at rest where required.

## Input validation & deserialization
- [ ] All external input (HTTP, Kafka, files) is validated and size-limited.
- [ ] **No unsafe deserialization** of untrusted data into arbitrary types.
- [ ] File uploads validated by type/size; stored outside the web root.

## SSRF & outbound calls
- [ ] URLs from user input are validated/allow-listed before server-side requests (SSRF).
- [ ] Outbound calls have timeouts and do not follow untrusted redirects blindly.

## Error handling & exposure
- [ ] Errors do not leak stack traces, SQL, or internal details to clients.
- [ ] Actuator/admin/debug endpoints are restricted and not publicly exposed.

## Dependencies & config
- [ ] No known-vulnerable dependencies introduced (check advisories); pin versions.
- [ ] Security headers set (CSP, HSTS, X-Content-Type-Options) where applicable.
- [ ] CORS is restrictive, not `*` on authenticated endpoints.

## Kafka-specific
- [ ] Consumers do not deserialize untrusted payloads into polymorphic/arbitrary types.
- [ ] Message contents with PII are handled per data-protection rules.

> If any box cannot be confirmed from the code, call it out as a risk rather than
> assuming it is handled elsewhere.
