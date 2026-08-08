# Java 21 standards

Target runtime: **Java 21 (LTS)**. Review and write code to use its features where they
improve clarity, safety, or performance.

## Language features to prefer
- **Records** for immutable data carriers (DTOs, value objects). No boilerplate getters.
- **Sealed classes/interfaces** to model closed hierarchies; pair with pattern matching.
- **Pattern matching** for `switch` and `instanceof` — replace long if/else chains.
- **Text blocks** for multi-line strings (SQL, JSON, templates).
- **Sequenced collections** (`getFirst()`, `getLast()`, `reversed()`) where ordering matters.

## Virtual threads (Project Loom)
- Prefer **virtual threads** for blocking, I/O-bound tasks (HTTP calls, DB, Kafka) to get
  high concurrency cheaply.
- **Avoid pinning:** do not hold a `synchronized` block across a blocking call — use
  `ReentrantLock` instead so the carrier thread is not pinned.
- Do not pool virtual threads; create one per task (`Executors.newVirtualThreadPerTaskExecutor()`).
- Keep thread-locals small; heavy thread-local use scales poorly with millions of threads.

## General
- **Constructor injection only**; fields `private final`.
- Return `Optional<T>` for "maybe absent" results; never return `null` collections — return empty.
- Use `var` for local types only when the right-hand side makes the type obvious.
- Prefer immutability; avoid shared mutable state.
- Handle `InterruptedException` correctly (restore the interrupt flag).

## Review flags
- `synchronized` around blocking I/O (virtual-thread pinning).
- Field injection (`@Autowired` on fields).
- Mutable static state.
- Swallowed exceptions or `catch (Exception e) {}`.
