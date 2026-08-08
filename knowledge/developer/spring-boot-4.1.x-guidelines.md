# Spring Boot 4.1.x guidelines

Target framework: **Spring Boot 4.1.x** (Spring Framework 6+/7 line), Java 21 baseline.

> Version note: verify exact API availability against the Spring Boot 4.1.x reference for
> your build; the guidance below is durable across the 4.x line.

## Application structure
- **Constructor injection** everywhere; avoid `@Autowired` on fields.
- Keep controllers thin: validation + delegation. Business logic lives in services.
- Use `@ConfigurationProperties` (typed, records-friendly) over scattered `@Value`.
- Externalise config; never hardcode URLs, credentials, or environment-specific values.

## Web layer
- Prefer constructor-based `RestClient`/`WebClient` beans over `RestTemplate` for new code.
- Return proper `ResponseEntity` status codes; centralise error handling with
  `@RestControllerAdvice` + a consistent error body (see `rest-api-standards.md`).
- Validate request bodies with `jakarta.validation` (`@Valid`, `@NotNull`, `@Size`, ...).

## Data & transactions
- Keep `@Transactional` on the service layer, not controllers; make read paths
  `readOnly = true`.
- Do not leak entities across the API boundary — map to DTO records.

## Observability & config
- Expose health/metrics via Actuator; **restrict actuator endpoints** and never expose
  `env`/`heapdump` publicly.
- Use structured logging; never log secrets or full PII payloads.

## Testing
- Slice tests (`@WebMvcTest`, `@DataJpaTest`) for fast feedback; `@SpringBootTest` only
  when full context is needed. Use Testcontainers for Kafka/DB integration tests.

## Review flags
- Field injection, fat controllers, business logic in controllers.
- `@Transactional` on controllers, or missing on multi-write services.
- Entities serialized directly to clients.
- Unrestricted actuator endpoints.
