# Kafka guidelines

Apply to all producers and consumers. The Code Review Agent checks messaging changes here.

## Producers
- Choose a **partition key** deliberately — it drives ordering and balance. Document why.
- Set `acks=all` for durability on important topics; enable idempotent producer
  (`enable.idempotence=true`) to avoid duplicates on retry.
- Handle send failures (callbacks/futures); never fire-and-forget critical events.
- Keep messages small; put large payloads behind a reference, not inline.

## Consumers
- Design consumers to be **idempotent** — assume at-least-once delivery and possible
  redelivery; dedupe by a business key or event id.
- Manage offsets deliberately; prefer committing **after** successful processing.
- Handle poison messages with **retry + dead-letter topic (DLT)**; never block the
  partition forever on one bad record.
- Keep processing off the poll thread if long-running; respect `max.poll.interval.ms`.

## Schema & serialization
- Use a schema (Avro/Protobuf/JSON Schema) with a registry; evolve schemas
  **backward-compatibly**.
- Never deserialize untrusted payloads into arbitrary types (see security checklist).

## Delivery semantics
- Be explicit about at-least-once vs exactly-once; document the choice and its cost.
- For exactly-once, use transactions (`transactional.id`) consistently across the flow.

## Error handling & observability
- Log with correlation/trace ids; never log full payloads containing PII.
- Emit metrics for lag, retries, and DLT volume; alert on growing consumer lag.

## Review flags
- Non-idempotent consumers assuming exactly-once.
- No DLT / infinite retry on poison messages.
- Missing/poor partition key; unbounded message size.
- Offsets committed before processing; long work on the poll thread.
- Incompatible schema change.
