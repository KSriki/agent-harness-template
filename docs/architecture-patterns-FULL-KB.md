# Software Architecture Patterns — Knowledge Base

> A living reference for designing software systems — when to reach for which pattern, how it's actually used in production, and which real-world systems anchor each one.
> Sibling document to `agentic-frameworks-knowledge-base.md`. That doc is the agent-stack reference; this one is the substrate underneath it. When designing an agent system you're also designing a software system, and most failure modes in the former are failure modes in the latter.

---

## 0. How to read this doc

Organized by **category**, not alphabetically. Each pattern has the same five things:

1. **Shape** — one-line structural description of what the pattern looks like
2. **When to use / when not to** — the picking criteria
3. **Real-world examples** — named systems that anchor the pattern
4. **Watch out for** — the failure mode that bites you in production
5. **Cross-refs** — where it connects to the agentic doc or to other patterns here

Source index is at the bottom (§12). The 14 patterns from Red Hat's reference list are all here; extensions are flagged inline where they're additions to that list. Deep-dive sections use letter suffixes to keep numbering stable: **§0.8** (Paradigm Choice: OO/FP/Hybrid), **§1A** (Domain-Driven Design + Hexagonal in depth), **§1B** (Testability & Test Architecture), **§2A** (Hosting & Scaling), **§5A** (Security Architecture & Access Control). **§11A** is a quick-reference catalog of GoF design patterns.

---

## 0.5 The Five Pillars (the axes every architectural decision trades against)

Architecture is not a tower of patterns. It's a set of tradeoffs along these axes. When two architects disagree, they're almost always weighting these differently — not picking different facts. Naming the pillar makes the disagreement productive.

| Pillar | The question | Failure mode if you ignore it |
|---|---|---|
| **Reliability / Availability** | Will the system keep working when a dependency, a node, or a network partition fails? | Cascading failures, user-facing outages, SLA breaches |
| **Scalability** | Does the system get cheaper-per-request as load grows? Does it have a knee where it stops scaling? | Hot shards, queue backups, capacity panic |
| **Maintainability / Evolvability** | How fast can a new engineer make a safe change? How easy is it to delete code? | Velocity collapse, rewrite pressure, knowledge silos |
| **Performance** | Are latency, throughput, and resource use acceptable at target load? | P99 latency explosions, throttling, cost spikes |
| **Cost** | Does the architecture's run cost track the business value it produces? | Cloud bill that scares the CFO |

No pattern wins on all five. Microservices wins on evolvability and scalability, loses on cost and complexity. Modular monolith wins on cost and maintainability, loses on independent scaling. Event sourcing wins on auditability and reliability, loses on operational simplicity. Always say which pillar you're optimizing for.

### Two pillars that hide inside the others
- **Observability.** Not on the list because it's an *enabler* for the others — you can't keep reliability without it. Always design for it from day one. Same point as Pillar 2 in the agentic doc: the audit surface and the control surface are the same thing.
- **Security.** Same — it's not an axis you trade against the others, it's a cross-cutting constraint. If you have to choose between "secure" and "scalable," you've made a mistake earlier in the design.

---

## 0.6 The Three Levels of Pattern Abstraction (vocabulary worth getting right)

"Pattern" gets used sloppily. When engineers argue, half the time they're talking past each other because they mean different *levels* of pattern. Wikipedia and the *Fundamentals of Software Architecture* (O'Reilly, 2020) make the distinction explicit. Worth internalizing.

| Level | Scope | What it organizes | Examples | Where in this doc |
|---|---|---|---|---|
| **Architecture style** | System-wide | Overall shape of the system; component types and how they connect | Layered, Microservices, Event-Driven, Client-Server, Pipe-and-Filter, Space-Based | Most of §1, §2, §4 |
| **Architecture pattern** | Component / cross-component | A reusable solution to a recurring system-level problem | Circuit Breaker, Saga, CQRS, Event Sourcing, Strangler Fig, Sharding | §3, §5, §6, §7 |
| **Design pattern** (GoF and friends) | Class / object | A reusable solution at the code-organization level | Singleton, Observer, Strategy, Factory, Adapter, Decorator | §11A reference |

The boundary between style and pattern is fuzzy. "Microservices" is usually called a style; "Saga" inside microservices is a pattern. "Layered" is a style; "Anti-Corruption Layer" inside layered is a pattern. Don't fight the fuzziness — what matters is that all three levels exist and serve different jobs.

**Why this matters in practice:**
- Confusing levels leads to bad arguments. "We should use the Adapter pattern!" — at which level? GoF Adapter (an OO wrapper around a class) is a different thing from Ports & Adapters (an architectural style for a whole service). Same word, different things.
- Confusing levels leads to bad design. Reaching for the Singleton design pattern when you need an architectural decision about who owns a piece of state. Reaching for microservices (a style) when you needed a CQRS (a pattern) inside a monolith.
- Confusing levels leads to over-engineering. Most "we used 23 GoF patterns!" stories end with a codebase nobody can read. Most "we adopted microservices!" stories end with a distributed monolith. The fix is picking the level your problem actually lives at, then picking the smallest thing at that level that works.

The rest of this doc focuses on architecture styles and architecture patterns — they're where most production design decisions live. §11A has a brief reference to GoF design patterns for completeness, since you'll encounter them in code reviews and reading.

---

## 0.7 The Ladder of Architectural Complexity (don't default to distributed)

Same discipline as §0.7 in the agentic doc: reach for the simplest thing that works, climb only when you can name the failure mode at the rung below.

| Rung | Architecture | Sweet spot | Failure mode that pushes you up |
|---|---|---|---|
| 0 | **Single script / single process** | Personal tools, prototypes, batch jobs | Multiple users; need uptime; deployment pain |
| 1 | **Monolith** (one codebase, one deploy) | Most startups, most internal tools, most products under ~50 engineers | Build/test/deploy time blocks the team; conflicting release cadences |
| 2 | **Modular Monolith** (one deploy, internal module boundaries) | Same scale as monolith, but with discipline. The default many architects forget exists. | Genuine need for independent scaling or independent deploys of specific modules |
| 3 | **Service-Oriented (a few services)** | When 2-5 components have genuinely different scaling/availability/team-ownership profiles | Need for finer-grained independence; team growth past ~5 service-owners |
| 4 | **Microservices** | Many teams, many deploy cadences, real polyglot needs, real scaling heterogeneity | (End of the ladder for most companies. The complexity tax compounds.) |
| 5 | **Serverless / FaaS** | Spiky workloads, no-ops mandates, glue between services | Long-running work; tight latency budgets; cold starts; observability gaps |

**The discipline:** at every rung you're either solving the problem or naming the specific reason this rung doesn't suffice. "Microservices because Netflix" is not a reason. "Microservices because two teams need independent deploys on incompatible cadences" *is* a reason.

The cost of climbing isn't linear. Each step up roughly doubles operational complexity — more services, more networks, more failure modes, more observability surface, more deployment surface, more security boundaries. **Modular monolith is the rung most teams should pick and skip past.** It buys you most of the evolvability of microservices at a fraction of the cost; you can extract a service later when you genuinely need it. (This is the same shape as "agent only when workflow won't work" in §4.5.1 of the agentic doc.)

### Two things people miss about the ladder
- **The bottom rungs aren't shameful.** Plenty of $10M+ ARR businesses run on Rung 1. Stack Overflow famously ran on a few large servers for a decade. The rung is a function of constraints, not status.
- **You can't skip rungs cheaply.** Going from monolith straight to microservices without passing through modular-monolith means you're learning service-boundary discipline at the same time as distributed-system operations. That's where the famous "we did microservices and regretted it" stories come from.

---

## 0.8 Paradigm Choice: OO, FP, and Hybrid

Below the ladder of §0.7 sits a more primitive question: **what programming paradigm is the code organized around?** Most production systems aren't pure — they pick a primary paradigm and borrow from the others. But the primary choice colors every pattern decision downstream. Worth naming explicitly because two engineers can be using the same vocabulary (DI, repository, adapter) and meaning very different things if one thinks in OO and the other in FP.

### 0.8.1 The three flavors

| Paradigm | Core unit | Key idea | Famous languages |
|---|---|---|---|
| **Object-Oriented (OO)** | Object (encapsulated state + methods) | Hide state behind methods that enforce invariants; compose objects via inheritance and composition | Java, C#, Ruby, Smalltalk, classic Python |
| **Functional (FP)** | Pure function (input → output, no side effects) | Immutable data, function composition, side effects pushed to the edges | Haskell, OCaml, Elixir, Clojure, F# |
| **Hybrid / Multi-paradigm** | Both, deliberately | OO for structure & subsystems, FP for transformations & data pipelines | Scala, Kotlin, Rust, modern TypeScript, modern Python, modern Java (post-8) |

Almost every modern language is hybrid — Java has streams and lambdas, C# has LINQ and records, Python has comprehensions and `functools`, JavaScript has had FP capabilities since ES6. **Pure-OO and pure-FP are now niche.** The interesting question isn't "OO or FP," it's *which problems you solve in which paradigm within the same codebase*.

### 0.8.2 What FP buys you, named

If you've only ever done OO, here are the wins FP brings — most of which you can adopt selectively without going pure:

- **Immutability by default.** Data doesn't change; new data is derived. Removes a whole category of bugs (the "who mutated this and when?" debugging session). Modern languages support this via records (Java/C#/Python `frozen=True`), `readonly` arrays, persistent collections (Immer, Immutable.js, Clojure's vector).
- **Pure functions.** Same input → same output, no side effects. Trivially testable (see §1B), trivially cacheable (memoization), trivially parallelizable (no shared state). The mental model is "this code only depends on what's passed in."
- **Composition over inheritance.** Build complex behavior by composing small functions, not by inheriting from base classes. Less coupling, more reusable. Even strongly OO codebases now prefer composition; this is the FP idea that fully crossed over.
- **Sum types / algebraic data types** (ADTs). Either-this-or-that types with the compiler enforcing exhaustive handling. `Result<T, E>` (success or error), `Option<T>` (some or none), `Either<L, R>`. Makes illegal states unrepresentable at compile time (echoing §1A.7). Rust's `enum`, Kotlin's sealed classes, TypeScript's union types, Scala's sealed traits.
- **Pattern matching.** Destructure data by shape rather than via getters. Works hand-in-hand with sum types. Rust's `match`, Kotlin's `when`, modern Python's `match`, Scala's `match`, F#'s `match`.

### 0.8.3 What OO buys you, named

- **Encapsulation around lifecycle.** Objects can have construction/destruction protocols, validate themselves on creation, and protect invariants over time. Aggregates in DDD (§1A) are deeply OO — an `Order` is *a thing that exists and has rules*, not a sequence of transformations on a record.
- **Identity through change.** A `User` object is the same user across many state changes. FP-purist approaches struggle with identity (everything's just a value); OO handles it natively.
- **Polymorphism / dynamic dispatch.** A `PaymentProcessor` interface with five implementations selected at runtime. FP does this too (via type classes, traits, higher-order functions), but the OO mental model is the most familiar to most engineers.
- **Familiar to almost everyone.** Whatever else you say about it, OO is the default mental model 70%+ of working engineers have. The hiring market reflects this.

### 0.8.4 The pattern that ties it together: Functional Core, Imperative Shell

Coined by Gary Bernhardt around 2012 (his "Boundaries" talk), this is the single most useful idea for hybrid-paradigm design:

- **Functional core.** Business logic written as pure functions over immutable data. No I/O, no databases, no time, no randomness. Trivial to test in isolation.
- **Imperative shell.** A thin outer layer that does I/O — reads from DBs, writes to APIs, handles HTTP, generates IDs, calls `now()`. The shell calls the core, then writes the results out.

The two layers map almost perfectly onto Hexagonal Architecture (§1A.2): the functional core is the Domain Layer; the imperative shell is the Application + Infrastructure layers. Most of the testability wins from §1B follow directly from this split. Most of the FP-in-OO-codebases hybrid approaches converge on this shape whether they name it or not.

### 0.8.5 Real-world examples

- **Functional DDD** — Scott Wlaschin's *Domain Modeling Made Functional* (in F#) rebuilds DDD with sum types and pure functions instead of classes and aggregates. Same results, different vocabulary. Worth reading even if you stay in OO; it sharpens the OO version.
- **Elixir / Erlang at WhatsApp, Discord, Pinterest** — concurrency-heavy backends where FP + the actor model (immutability per process, message passing) outperforms shared-memory OO at scale. WhatsApp famously ran on Erlang with a tiny engineering team.
- **React (and the front-end shift to FP)** — React's "UI as a function of state" is mainstream FP applied to UI. Redux extends this with pure reducers. The front-end community absorbed FP ideas faster than the back-end community did.
- **Modern data engineering** — Spark, Beam, Flink are fundamentally FP shapes (immutable RDDs/datasets, pure transformations). dbt's SQL-as-code pipelines are FP-in-disguise. The whole data stack leans FP.
- **Rust adoption in systems programming** — Rust isn't pure FP, but ownership + traits + ADTs are FP-flavored ideas applied to systems code. Cloudflare, Discord, AWS Firecracker, much of npm's tooling have moved to Rust partly for these reasons.

### 0.8.6 The pragmatic advice

Don't pick a paradigm; pick a *style policy*:
- **Default to immutability.** Use `final`/`readonly`/`const` liberally. Mutate when you have a reason, not by default.
- **Prefer pure functions for transformations.** Anywhere you're mapping data shapes, computing derived values, applying business rules — write a pure function. Save OO classes for things with lifecycle.
- **Push side effects to the edges.** I/O, time, randomness, network calls all live in a thin shell that wraps the pure core.
- **Use sum types where the language supports them.** `Result<T, E>` over throwing for expected errors. Union types over `string \| null \| undefined` for optional/variant data.
- **Use OO for aggregates and lifecycle.** Things that have identity, exist over time, and have invariants. The classic DDD Entity is genuinely OO.

The rule of thumb: in a typical hybrid codebase, ~70% of the code is data transformations that should be FP-style; ~30% is lifecycle/identity stuff that should be OO. Getting the split right is the design skill.

### 0.8.7 Cross-refs
- **§1A.7 (Make illegal states unrepresentable)** — the FP discipline that pays the biggest dividends in OO codebases too
- **§1B.4 (Functional core / imperative shell)** — the testability payoff of this paradigm choice
- **§3.2 (Event Sourcing)** — fundamentally FP: state as a fold over events
- **§11A** — the design-pattern catalog is OO-flavored; in FP languages many of those patterns disappear (Norvig's observation)

---

## 0.9 The Determinism–Autonomy Spectrum (who authors the control flow)

The ladder of §0.7 asks *how distributed* a system is. This section asks a different and increasingly important question: **who authors the control flow — you, in source code, or a model, at runtime?** It belongs in a software-architecture doc, not just an AI one, because the question is older than LLMs (a rules engine vs. a hand-coded `if` is the same axis) and because the answer determines what you can test, debug, and trust — the core architectural properties this whole doc is about.

The terms **microservice**, **LLM integration**, **RAG**, and **agent** get used interchangeably and shouldn't be. They answer different questions, and conflating them leads to over-building (shipping an "agent" where a function would do) and mis-debugging (hunting the bug in the wrong layer).

### 0.9.1 The spectrum

```
 DETERMINISM ──────────────────────────────────────────────────► AUTONOMY
     │              │                 │               │              │
 Microservice   LLM-in-a-         Workflow         Agent       Multi-agent
 (no model)     pipeline          (LLM picks       (LLM drives  (agents
                (fixed flow,       from branches    the loop,    coordinate
                 one LLM call      YOU defined)     chooses      other
                 fills one slot)                    tools,       agents)
                                                    decides done)
     └──────────── YOU hold the pen ───────────┤├──── MODEL holds the pen ───┘
                                                ▲
                                         THE AGENT LINE
```

The horizontal axis is **who authors the sequence of decisions about what happens next.** On the left, you do — the branches are `if`/`for`/`switch`, written by you, legible in source. On the right, the model does — it chooses which tool to call, in what order, whether to retry, when it's done, at runtime, in its outputs.

The single most important feature is **the agent line**, between *Workflow* and *Agent*. Everything left of it is a deterministic system with a model bolted in. Everything right of it is a system where the model *constructs the path*. Most confusion comes from putting the line too far left — calling something an "agent" the moment an LLM appears at all.

### 0.9.2 The four-plus positions

| Position | Who authors control flow | What it is |
|---|---|---|
| **Microservice (no model)** | You, entirely | Same input → same path, every time. The entire pre-LLM world, still the right answer whenever the decision reduces to rules, comparisons, or a query. Exact, fast, free, reproducible, testable. |
| **LLM-in-a-pipeline** | You; model fills one slot | "Classify this," "extract these fields," "summarize this." The model is a smart function call; your code decides what happens next. |
| **Workflow** | You define the branches; model picks one | "Route to billing, technical, or complaints, then run the handler." The model chose, but from a menu you wrote into handlers you built. You can still draw the full flowchart in advance. |
| **Agent** | The model, at runtime | You gave it tools and a goal; *it* decides the sequence, depth, and stopping point. You can't draw the flowchart in advance because the model builds it per input. |
| **Multi-agent** | Multiple models, each authoring its own | Single-agent autonomy multiplied across coordinating roles. Top of the cost/complexity curve. |

### 0.9.3 Three orthogonal axes, not one line

"Agent," "LLM integration," and "RAG" are not three points on one line — they answer three *separate* questions that co-occur:

| Term | Question it answers | The axis it's on |
|---|---|---|
| **LLM integration** | Is there a model in the loop at all? | Have you left pure software? |
| **RAG** | Where does the model get facts it wasn't trained on? | The knowledge / read-path axis |
| **AI agent** | Does the model author the control flow? | The autonomy axis (the spectrum above) |

Because they're different axes, they **stack** rather than compete: LLM-alone, LLM+RAG with no autonomy, agent with no RAG, or all three. The term most often misfiled is **RAG** — people line it up as a sibling of "agent," as if a system is "either RAG or an agent." It's neither-nor: RAG is on the knowledge axis, agent-vs-microservice on the control-flow axis. Asking "is it RAG or an agent?" is like asking "is the car red or is it fast?"

### 0.9.4 The test that resolves it

> **Can you draw the complete flowchart before the model runs?**
> - **Yes** → microservice or workflow. A deterministic skeleton; the model fills slots or picks pre-drawn branches.
> - **No, because the model decides the sequence, depth, and stopping point at runtime** → agent.

The common error is thinking *"the model made a choice"* is the test. It isn't — a regex "decides" whether a string matches; a `switch` "decides" which case runs. The real threshold: **did the model author the space of choices, or merely select from a space you authored?** Model picks 1-of-N handlers you defined → workflow (left). Model given tools and a goal, deciding what to do and when to stop → agent (right). All involve "choosing"; only the last authors the option space.

**Tools and protocols (even MCP) don't move the line.** Exposing tools is about *how capabilities are made available*, not *who sequences them*. The same tools sit on either side: your code calls tool A then tool B on a branch you wrote (workflow), or the model loops over the available tools deciding which to call next until it judges itself done (agent). The tool layer is plumbing; the question is whether a human-authored control flow wraps the calls or the model *is* the loop.

### 0.9.5 Why crossing the line costs more (the architectural payload)

This is why the line matters to *this* doc specifically: crossing it changes what you owe the system. The loop mechanics (poll, call, retry, emit telemetry) are identical on both sides — your existing instincts cover those. What the agent line *adds* is everything that follows from one element of the loop being non-deterministic and self-directing:

| Left of the line | What the agent line adds |
|---|---|
| Unit-test every branch (§1B) | Can't test a path the model invents → you need evaluation harnesses and trajectory replay |
| Logic readable in source | Logic lives in model outputs → observability must capture the *decision path*, not just I/O |
| Actions are exactly what you coded | Model may take an expensive/irreversible action because it "decided to" → approval gates and guardrails (§5A.10) |
| Same input → same path, same cost | Same input → variable path, variable cost → cost and latency become distributions, not constants |

None are optional once you're right of the line; they're the price of admission. Which is the real argument for keeping as much of a system as possible on the **left** — not purism, but that the left side is cheaper, faster, and far easier to trust. Echoes the §0.7 discipline exactly: *don't default to the expensive rung.*

### 0.9.6 Putting a model where rules belong is a downgrade

Taking logic that *could* be deterministic and moving it into a prompt isn't more "agentic" — if the rule is exact (a threshold, a count, a match), handing it to a model makes a deterministic decision **probabilistic**. You trade something exact, instant, free, reproducible, and testable for something approximate, slower, metered, and non-reproducible, and you add failure modes to do a job a comparison did perfectly. "We put the rules in the prompt" feels like building an agent and is really building a *less reliable microservice*. The model earns its place when the input genuinely can't be reduced to rules (subtext, intent, open-ended language, messy unstructured data), not when it's standing in for an `if` you didn't feel like writing.

### 0.9.7 Cross-refs
- **§0.7 (Ladder of complexity)** — same "don't default to the expensive rung" discipline, applied to distribution instead of autonomy
- **§1B (Testability)** — what you lose the moment the model authors a path you can't enumerate
- **§5A.10 (Agentic security overlay)** — the guardrails the right side of the line requires
- **§9.5 (Agentic reference architecture)** — a worked system that crosses the line deliberately
- **Agentic doc §4.0** — the same spectrum from the AI-engineering side, with framework specifics

---

## 1. Foundational Structural Patterns

These describe *how code is organized inside a single deployable*. They compose with everything below — a microservice can be internally hexagonal; a modular monolith can be internally layered.

### 1.1 Layered (n-tier)
**Shape:** Code organized in horizontal layers (presentation → business logic → data access → database), each layer only calling the layer directly below it.

**When to use:** Default for traditional enterprise applications, especially CRUD-shaped systems. Easy to teach, easy to staff for, easy to onboard junior engineers. Works extremely well for systems where the dominant operation is "form in, database out."

**When not to use:** Systems with complex domain logic that doesn't map onto CRUD. Layers tend to leak — the business logic ends up scattered across the controller layer and the data access layer, and nobody can find the actual rules.

**Real-world examples:**
- Most enterprise Java applications (Spring Boot's default opinions are layered)
- Most Django and Rails applications (MVC is a flavor of layered; see §1.3)
- Most pre-2015 .NET enterprise applications

**Watch out for:**
- **Anemic domain model** — when the "business logic" layer becomes just methods that move data between DTOs and the DB. The real logic ends up in controllers or in stored procedures.
- **Skip-the-layer temptation** — when a UI directly hits the data layer "just for this one query." Once you allow it once, the boundaries are gone.

### 1.2 Client-Server
**Shape:** Two-party communication — a *client* that requests a service and a *server* that provides it. The grandparent pattern of almost everything else here.

**When to use:** Any time you have a clear asymmetry between consumer (many, ephemeral) and provider (few, persistent). This is the implicit shape of the web, of databases, of APIs in general.

**When not to use:** Genuinely peer-to-peer systems (file-sharing networks, blockchain consensus, mesh networking) where every node is both client and server. Also overkill framing for in-process function calls.

**Real-world examples:**
- The Web itself — browser (client) ↔ HTTP server
- Email — mail client ↔ IMAP/SMTP server
- Banking — ATM/app (client) ↔ core banking system (server)
- Every REST API ever

**Watch out for:**
- **Server as single point of failure** — the asymmetry is also a fragility. Mitigated by clustering, load balancing, replication.
- **Chatty clients** — many small round-trips, each with network overhead. Push to fewer richer calls.

### 1.3 Model-View-Controller (MVC)
**Shape:** Three components — the **Model** owns data and core logic; the **View** renders to the user; the **Controller** receives input and mediates between Model and View.

**When to use:** Web applications and desktop applications with interactive UIs. The dominant pattern for server-rendered web frameworks.

**When not to use:** APIs without UI — you don't need a View layer. Single-page applications often invert the pattern (MVVM, Flux/Redux, or component-based shapes like React) because the client owns rendering state.

**Real-world examples:**
- Ruby on Rails (the framework that popularized the pattern in web)
- Django (its own variant — "MTV": Model, Template, View, where Django's "View" is really MVC's Controller)
- Spring MVC
- ASP.NET MVC

**Watch out for:**
- **Fat controllers** — business logic creeping into the controller because the model is anemic. The cure is a richer domain model (or going hexagonal — see §1.4).
- **MVC for APIs** — using MVC framing for a pure REST API means you have empty "View" code generating JSON. At that point it's just Controller + Model, and you should say so.

### 1.4 Hexagonal / Ports and Adapters (extension beyond Red Hat 14)
**Shape:** Domain logic in the center, surrounded by **ports** (interfaces describing what the domain needs/offers) and **adapters** (implementations of those ports for specific technologies — REST, gRPC, Postgres, Kafka, S3). Also known as "Onion Architecture" or "Clean Architecture" in some variants.

**When to use:** Systems where the domain logic is the durable asset and the I/O technologies are likely to change. Especially valuable when you have multiple delivery channels (web, mobile API, CLI, background jobs) hitting the same business logic.

**When not to use:** Simple CRUD systems where the abstraction overhead exceeds the savings. Hexagonal pays dividends when domain logic is rich; for a thin shim over a database, it's ceremony.

**Real-world examples:**
- Most modern DDD (Domain-Driven Design) implementations
- The reference architectures Netflix and Uber publish for their newer services
- Most Spring Boot + DDD projects in the wild

**Watch out for:**
- **Over-abstraction** — introducing ports for things that will never have a second adapter. The test: if you can't name two plausible adapters, don't make a port.
- **Hexagonal-flavored layered** — teams adopt the vocabulary but keep the layered structure underneath. Easy to spot: if "the domain" still imports Spring or Django annotations, it's not really in the center.

**Cross-ref:** This is the same instinct as the **inference gateway pattern** in §2.9 of the interview prep — depend on an abstract port (an LLM interface) rather than a concrete adapter (the Bedrock SDK). When you want to swap Bedrock for Ollama you change adapters, not domain logic.

### 1.5 Controller-Responder
**Shape:** Two-component division — the **Controller** receives work, distributes it, and owns the canonical state; the **Responder** holds a replicated read copy and serves results without affecting the source of truth.

**When to use:** Read-heavy workloads where you can tolerate replication lag. Reporting systems, analytics dashboards, search indexes built from a primary store.

**When not to use:** Read-after-write requirements where the client expects to immediately see what they just wrote — replication lag will burn you. Also overkill for low-traffic systems.

**Real-world examples:**
- Primary/replica Postgres or MySQL setups (where read traffic goes to replicas)
- Search infrastructure — primary DB writes, Elasticsearch replicas read
- Many CQRS implementations (see §3.1) — the read model is a Responder

**Watch out for:**
- **Replication lag** — the Responder is always slightly behind. Clients that expect strong consistency will see ghosts.
- **Failover complexity** — if the Controller fails, promoting a Responder cleanly is nontrivial. Tools like Patroni, Vitess, or managed RDS handle most of this but not all.

---

## 1A. Domain-Driven Design + Hexagonal Architecture — The Practitioner Stack

This is the deepest, most opinionated section in the doc. It exists because **DDD, Hexagonal Architecture, Clean Architecture, Onion Architecture, SOLID, and Secure by Design all point in the same direction** — they're convergent answers to the same question: *how do you keep complex business logic from rotting into spaghetti?* Treat them as one stack with overlapping vocabulary, not as competing alternatives.

When to read this section: when you're building a system with **rich domain logic** (financial calculations, regulated workflows, complex state machines, anything where "the business rules" are themselves the product). When to skip it: simple CRUD glue work. The ceremony in this section is overkill for most apps — but for the apps it fits, nothing else holds up nearly as well at scale.

### 1A.1 The convergent stack
Six things that look like different methodologies but are really the same disciplines from different angles:

| Methodology | What it emphasizes | What it adds |
|---|---|---|
| **Domain-Driven Design (DDD)** — Eric Evans, 2003 | Modeling the business domain explicitly; ubiquitous language between code and domain experts | The vocabulary of Entities, Aggregates, Value Objects, Bounded Contexts |
| **Hexagonal Architecture / Ports & Adapters** — Alistair Cockburn, 2005 | Domain at the center, technology at the edges, swappable adapters | The Ports/Adapters split — interfaces (ports) toward infrastructure, implementations (adapters) at the edge |
| **Onion Architecture** — Jeffrey Palermo, 2008 | Dependency direction: outer layers depend on inner; never reverse | The visual onion model and explicit dependency rule |
| **Clean Architecture** — Robert C. Martin (Uncle Bob), 2012 | Same as Onion with sharper rules: entities → use cases → interface adapters → frameworks | The "Use Case" as a first-class concept |
| **Secure by Design** — Bergh Johnsson et al., 2019 | Security as a structural property; invariants, illegal-states-unrepresentable | Domain Primitives, Always-Valid Domain Model, Guarding vs Validating |
| **SOLID** — Robert C. Martin, ~2000 | Object-level design principles | Substrate principles all the above sit on |

**The unifying principle:** business logic is the durable asset. Technology choices (databases, frameworks, message brokers, web servers) change. The domain model should outlive them. Therefore: domain code must not depend on infrastructure code; infrastructure depends on domain through interfaces.

### 1A.2 The dependency direction rule

The diagram everyone draws looks like this:

```
            ┌─────────────────────────────────────┐
            │  INFRASTRUCTURE (outermost)         │
            │  DB drivers, HTTP, message brokers, │
            │  external APIs, frameworks          │
            │  ┌─────────────────────────────┐    │
            │  │  INTERFACE ADAPTERS         │    │
            │  │  Controllers, DTOs,         │    │
            │  │  Presenters, Resolvers      │    │
            │  │  ┌───────────────────────┐  │    │
            │  │  │  APPLICATION LAYER    │  │    │
            │  │  │  Use Cases, Commands, │  │    │
            │  │  │  Queries, Ports       │  │    │
            │  │  │  ┌─────────────────┐  │  │    │
            │  │  │  │  DOMAIN LAYER   │  │  │    │
            │  │  │  │  Entities,      │  │  │    │
            │  │  │  │  Aggregates,    │  │  │    │
            │  │  │  │  Value Objects, │  │  │    │
            │  │  │  │  Domain Events  │  │  │    │
            │  │  │  └─────────────────┘  │  │    │
            │  │  └───────────────────────┘  │    │
            │  └─────────────────────────────┘    │
            └─────────────────────────────────────┘

       Dependencies point INWARD only.
       Domain never imports application.
       Application never imports infrastructure.
       Infrastructure implements interfaces defined inward.
```

**The rule is one sentence:** outer layers depend on inner layers; inner layers never depend on outer layers. The Domain Layer at the center has no imports from anything outside it — no frameworks, no ORMs, no logging libraries. It's pure business logic. This is enforceable mechanically (see §1A.8).

### 1A.3 Domain Layer building blocks

This is where the business rules live. Five core building blocks:

**Entities** — objects with identity that persists through state changes.
- Have an ID that defines them; equality is by ID, not by field values
- Contain business logic and protect their own invariants
- Should never be in an invalid state (validate in constructor; throw or return error on first violation — "Fail Fast")
- Avoid public setters; mutate state through methods that enforce rules
- Example: a `User`, `Order`, `Invoice`, `Booking`

The common anti-pattern is the **anemic domain model** — entities that are just bags of public fields with getters and setters, and all the business logic in "service" classes. This is the layered/CRUD shape with DDD vocabulary pasted on top. It's worse than not doing DDD at all because it costs you ceremony without delivering the encapsulation benefit.

**Aggregates** — clusters of related entities and value objects treated as a single consistency unit. An **Aggregate Root** is the entity that serves as the only entry point to the cluster; outside code can only reach the inner objects through the root.
- Aggregate boundaries define **transaction boundaries** — any change to anything inside the aggregate must keep the whole aggregate consistent within one DB transaction
- Aggregates reference *other* aggregates by ID only, never by direct object reference
- Don't make aggregates too large — large aggregates create contention and slow writes
- Examples: an `Order` aggregate root containing `OrderLine` entities and `Money` value objects

**Value Objects** — immutable objects with no identity, equal by structural value.
- Used for things like `Email`, `Money`, `Address`, `DateRange`, `PhoneNumber`
- Encapsulate validation and behavior for their value
- Cheap to pass around, copy, and reason about
- This is where the **primitive obsession** fix lives — instead of `string email`, use an `Email` value object that validates on construction

**Domain Services** — operations that don't belong to a single entity (cross-entity logic).
- Stateless; operate on domain types only
- Example: a `TransferService` that moves money between two `Account` entities — the logic doesn't belong to either account
- Used sparingly; most logic belongs on entities or aggregates

**Domain Events** — first-class objects representing something that happened in the domain.
- "OrderPlaced", "UserRegistered", "PaymentRefunded" — past tense, factual, immutable
- Published by aggregates when state changes
- Consumed in-process by event handlers in the same bounded context
- Decouple cross-aggregate logic: instead of `Order` calling `Inventory` directly, `Order` raises `OrderPlaced` and an `InventoryEventHandler` reacts
- Distinct from **Integration Events** (next section)

### 1A.4 The Domain Events vs Integration Events distinction

This catches everyone the first time and is worth getting right:

| | Domain Event | Integration Event |
|---|---|---|
| Scope | In-process, single bounded context | Out-of-process, between services or systems |
| Transport | In-memory event dispatcher | Kafka, RabbitMQ, SNS/SQS |
| Consistency | Same DB transaction as the originating change | Eventually consistent; needs Outbox pattern (§3.7) |
| Schema | Internal to the bounded context; can change freely | External contract; needs schema versioning |
| Example | `UserCreated` consumed by `WalletEventHandler` in the same service | `UserRegistered` published to Kafka, consumed by Notifications service |

**The rule:** convert Domain Events into Integration Events at the bounded-context boundary, not before. The internal events are richer and freer to evolve; the external events are a public contract.

### 1A.5 Application Layer building blocks

Sitting between the Domain Layer (which knows nothing about the outside world) and the Interface Adapters (which speak HTTP/CLI/gRPC):

**Application Services / Use Cases** — orchestrate a single business operation end to end.
- One service per use case (`CreateUserService`, `PlaceOrderService`, `RefundPaymentService`)
- Loads aggregates through ports, calls methods on them, persists results back, emits events
- Contains **no domain logic itself** — it's the choreographer, not the dancer
- Each one corresponds to a single intent the user (or another system) can express

**Commands and Queries** (CQS — Command-Query Separation, distinct from but related to CQRS in §3.1):
- **Commands** = state-changing intents. Return either nothing or just an identifier. No business data.
- **Queries** = read-only intents. Return data. Never mutate state.
- Commands and Queries are *DTOs themselves* — they're the typed input to a use case
- Routed through a Command Bus / Query Bus to their handlers; decouples invoker from handler

This is "small-c CQS" — separating reads from writes at the *method* level. "Large-C CQRS" (§3.1) extends this to the *storage* level (separate read and write models). They compose naturally.

**Ports** — interfaces the application defines toward infrastructure.
- Domain or application code declares "I need to save a User somewhere" via a `UserRepository` interface
- Infrastructure layer provides the implementation (Postgres adapter, MongoDB adapter, in-memory adapter for tests)
- This is the actual Hexagonal "ports" — the inward-facing interfaces
- Crucially: the port is defined by the *application's needs*, not by mimicking the database's API

### 1A.6 Infrastructure & Interface Adapter layers

The outer rings of the diagram. Where the technology lives.

**Adapters** (infrastructure-side implementations of ports):
- `PostgresUserRepository implements UserRepository`
- `SesEmailService implements EmailService`
- `KafkaEventPublisher implements DomainEventPublisher`
- These are the only places that know about specific technologies

**Repositories** (a specific kind of adapter):
- Centralize entity persistence and retrieval
- Map between Domain Models (rich, behavior-bearing) and Persistence Models (DB-shaped, flat, optimized for the storage technology)
- Receive a domain entity, save it; or query and return domain entities, not DB rows
- **Domain Models ≠ Persistence Models.** This is non-negotiable in DDD. The shape that's best for the database is rarely the shape that's best for the business logic. The repository is the translator.

**Controllers / Interface Adapters** (driving adapters, the input side):
- HTTP controllers, CLI commands, message handlers, gRPC handlers
- Translate external requests into Commands or Queries
- Translate use case results into responses (HTTP JSON, CLI output, message replies)
- Multiple controllers can drive the same use case — one HTTP, one CLI, one async-message — without the use case knowing about transport

**DTOs (Data Transfer Objects):**
- **Request DTOs** = contract for what callers send. Validated at this boundary.
- **Response DTOs** = contract for what callers receive. Whitelists exposed fields (don't leak entity internals).
- Distinct from Commands/Queries — DTOs are the wire format; Commands/Queries are the internal call format. There's mapping between them at the controller boundary.

### 1A.7 The disciplines that make this work

A pattern catalog without discipline is just decoration. These are the operational habits that turn DDD ceremony into actual benefit.

**Ubiquitous Language.** Code and domain experts use the same words for the same things. If accountants call it a "Journal Entry," the class is `JournalEntry`, not `Transaction` or `Record`. Naming drift between domain and code is the early warning that the model is decaying.

**Make illegal states unrepresentable.** Two layers:
- *Compile-time:* use the type system. If contact info requires either an email or a phone (or both), use a union type, not two optional fields. The IDE catches missing cases before the program runs. This is the "typestate pattern" in formal terms.
- *Runtime:* validate in constructors, throw on first violation. A `Money` value object can't exist with a negative amount; an `Order` aggregate can't exist with zero line items.

The combination is powerful: most invalid states are impossible at compile time; the rest fail loud at construction time. The downstream code never has to defensively check.

**Always-Valid Domain Model.** Once an aggregate is constructed, every method must leave it valid. If you can't enforce this, the domain model is leaking — somewhere external code is mutating internals. Find that path and close it.

**Guarding vs Validating** (the discipline that separates the two):
- **Validating** = boundary filtering. External input is sanity-checked at the edge (Request DTO decorators, controller-level validators). If invalid, return 400 to the caller with a useful error.
- **Guarding** = internal failsafe. Inside the domain, we assume the input is valid (it passed validation), but we double-check invariants anyway. If a guard fails, it's a *bug*, not a user error — throw an exception, fail fast, page someone.

Mixing these up creates two symmetric problems: bug-as-user-error (system 500s when user sent bad data) and user-error-as-bug (system silently accepts bad data and corrupts state). Keep them separate.

**Primitive Obsession.** Most production codebases pass `string` for email, `number` for money, `string` for user ID, etc. Each of these has invariants the type doesn't express. The fix: wrap primitives in Value Objects (`Email`, `Money`, `UserId`) that enforce their own rules on construction. Now any function that takes an `Email` is guaranteed to receive a valid email. Tradeoff: more boilerplate; in TypeScript especially, this can be over-engineering. Apply selectively to the primitives that have nontrivial rules.

**Domain Errors: return, don't throw.** Expected business-rule violations ("seat already booked", "insufficient funds", "user already exists") are not exceptional — they're normal program flow. Returning a typed `Result<Success, Error>` (a la Rust, Haskell's `Either`, or libraries like `oxide.ts`, `@badrap/result`) makes errors part of the function signature. The caller sees what can go wrong. Throw only for *truly* exceptional situations (DB down, out of memory, bugs). This is one of the highest-impact discipline shifts when a team adopts DDD.

### 1A.8 Module organization: vertical slices over horizontal layers

The classic layered file structure groups files by *type*:
```
src/
  controllers/
    UserController.ts
    OrderController.ts
  services/
    UserService.ts
    OrderService.ts
  repositories/
    UserRepository.ts
    OrderRepository.ts
```
This looks tidy but every change touches three folders. Worse, it invites cross-module coupling — once `UserService` imports from `OrderService`, you have a hairball.

**Vertical Slicing** groups files by *feature*:
```
src/
  modules/
    user/
      commands/
        create-user/
          create-user.command.ts
          create-user.controller.ts
          create-user.service.ts
          create-user.dto.ts
      queries/
        find-users/
          find-users.query.ts
          find-users.handler.ts
      domain/
        user.entity.ts
        user.repository.port.ts
      infrastructure/
        user.repository.ts
    order/
      ...
```

This is the **Common Closure Principle** in action: things that change together live together. Adding a new feature means adding one slice, not editing five layers. Modules become independently understandable; each one is "a mini application" inside the codebase.

**Module rules** (from the Sairyss repo, mostly verbatim because they're right):
- Each module is named after a domain concept, not a technical type
- Module internals are private; cross-module access goes through a public facade or via events
- Direct imports between modules (`import X from '../OtherModule'`) are forbidden — that's tight coupling
- If two modules need to talk, they do it through events, commands, or a small explicit shared layer
- **Keep modules small enough to rewrite.** If you couldn't redo a module in under a week, it's too big — break it down further

This pattern works at every scale. In a modular monolith, the modules are folders. In microservices, the modules become services (and the in-process commands become network calls). The mental model is the same; the deployment shape changes.

### 1A.9 Enforcing the architecture mechanically

Architecture rules that depend on code review will rot. Architecture rules enforced by tooling don't.

**Dependency cruisers** verify the dependency direction rule:
- `dependency-cruiser` (JS/TS)
- `ArchUnit` (Java)
- `archlint`, `archtest` (other ecosystems)

Example rule (`dependency-cruiser`):
```javascript
{
  name: 'no-domain-deps-on-infra',
  comment: 'Domain layer cannot depend on infrastructure or controllers',
  severity: 'error',
  from: { path: 'src/.*/domain/' },
  to:   { path: 'src/.*/(infrastructure|controllers)/' },
}
```
Run it in CI. The build fails when someone accidentally imports the ORM in the domain layer. That's the only durable way to keep the architecture honest.

**Other enforcement tools:**
- **Module boundary rules** in ESLint (`eslint-plugin-boundaries`), Sorbet (Ruby), Modulith (Spring), explicit `__init__.py` exports (Python)
- **API contract tests** at module boundaries — Pact, schema validation, snapshot tests
- **Dependency graphs** generated automatically and reviewed in PRs — when the graph changes, the team sees it

### 1A.10 Real-world examples

This isn't a hypothetical architecture. It's deployed in serious production at scale.

- **Many financial-services backends** — banking ledgers, trading systems, insurance policy engines. The domain has irreducible business rules and the cost of getting them wrong is real money. DDD pays for itself.
- **Healthcare and life-sciences workflows** — clinical decision support, lab order management. Regulatory pressure plus domain complexity makes the discipline mandatory.
- **The reference implementations:**
  - `Sairyss/domain-driven-hexagon` — the TypeScript/NestJS reference (§12, source 11). Worth reading end to end.
  - Microsoft's eShopOnContainers — the C# reference DDD + microservices project, widely used as a teaching artifact
  - Vaughn Vernon's "Implementing Domain-Driven Design" sample code (Java)
  - Khalil Stemmler's `solid-typescript-starter` and his enterprisecraftsmanship.com worked examples
- **Inside well-known products** — most large product engineering orgs have at least one or two services built this way, usually around domain complexity hotspots (billing, identity, compliance). It rarely makes it into public engineering blogs because it's foundational rather than novel.

### 1A.11 When this stack is overkill

The honest counter-position. DDD + Hexagonal is *not* the right answer for:
- **Simple CRUD applications** where the business logic is "save form, retrieve form." MVC (§1.3) is correct here. Adding aggregates and value objects just creates ceremony with no encapsulation payoff.
- **Glue services** whose entire job is to call other services in a sequence. Workflow tools (Step Functions, Temporal) or simple scripts beat domain models for this.
- **Early-stage products** where the domain is still being discovered. Premature DDD locks in a model before you know the right model. Start simple; refactor toward DDD when you can name the domain complexity you're protecting against.
- **Small teams (<5 engineers)** where everyone has the whole codebase in their head. The encapsulation tax exceeds the encapsulation benefit.

The rule: DDD + Hexagonal is for **services with rich domain logic that will live for years and be maintained by rotating engineers.** That's a real category, but it's not every service.

### 1A.12 Cross-refs
- **§1.3 (MVC)** is the simpler alternative for CRUD-shaped apps.
- **§1.4 (Hexagonal intro)** is the lightweight summary; this section is the deep treatment.
- **§3.1 (CQRS)** extends the CQS discipline from §1A.5 to the storage layer.
- **§3.2 (Event Sourcing)** pairs naturally with DDD — domain events become both the in-process mechanism and the durable record.
- **§3.7 (Outbox Pattern)** is how Domain Events become Integration Events reliably.
- **§6.2 (Anti-Corruption Layer)** is how this stack integrates with hostile legacy systems.
- **Agentic doc §2.9 (Inference Gateway pattern)** is Ports & Adapters applied to LLM providers — same instinct, narrower scope.

---

## 1B. Testability & Test Architecture

**Testability is an architectural property, not a tooling concern.** When engineers say "I had to refactor my classes to make them testable," the refactor isn't fighting the tests — the tests are *surfacing pre-existing design problems*. Hard-to-test code is almost always over-coupled, poorly bounded, or hiding side effects. Easy-to-test code is also easy to change, easy to reason about, and easy to compose. The two properties are the same property.

This section names the patterns that make code testable and the anti-patterns that destroy testability, plus the test architecture itself (pyramid vs trophy, doubles taxonomy, contract testing). It's intentionally near §1 and §1A because testability is a *structural* concern — by the time you're picking a test framework, the architecture decisions have already been made.

### 1B.1 The test pyramid (and its modern competition)

The classical model from Mike Cohn, ~2009:
```
              /\
             /E2E\         <- few, slow, brittle, high-confidence
            /------\
           / Integ. \      <- some, medium-speed, medium-confidence
          /----------\
         /   Unit     \    <- many, fast, focused
        /--------------\
```

**The pyramid argument:** unit tests dominate by count because they're fast and stable; integration tests verify the wiring; E2E tests catch the highest-level regressions but are too slow to run on every commit. Run the pyramid bottom-up — fast feedback first, slow feedback last.

**The Testing Trophy** (Kent C. Dodds, ~2018) — the modern challenger:
```
              /----\
             /  E2E \       <- few
            /--------\
           / Integ.   \     <- MORE than unit (the inversion)
          /------------\
         /   Unit       \
        /----------------\
         Static analysis    <- TypeScript, ESLint, etc. as the foundation
```

**The trophy argument:** in modern codebases, especially front-end, integration tests are higher-value than unit tests because they exercise real wiring. Unit tests against heavily-mocked code prove the mocks work, not that the system works. Static analysis (TS, ESLint, dependency-cruiser from §1A.8) catches a class of bugs that used to need unit tests.

**The honest read:** neither shape is universally right. The pyramid is right for backend services with clear unit boundaries and expensive integration setup. The trophy is right for UI code and well-tooled backends where integration tests are cheap. Pick the shape that matches *your* feedback-loop economics.

### 1B.2 Test doubles — get the vocabulary right

Martin Fowler's taxonomy is the standard. Five distinct things, often called "mocks" sloppily:

| Double | What it is | When to use |
|---|---|---|
| **Dummy** | A placeholder passed but never used (filling a parameter slot) | When a method signature demands an argument the test path doesn't exercise |
| **Stub** | Returns canned answers; doesn't verify how it's called | When the system-under-test needs *data* back from a collaborator but you don't care how |
| **Fake** | A working alternative with shortcuts (in-memory DB, in-memory queue) | When you want real behavior without real I/O. Often the highest-leverage double |
| **Mock** | Pre-programmed with expectations about how it'll be called; test fails if expectations aren't met | When the test is verifying *interaction* (did we call the email service?) rather than *state* |
| **Spy** | Records how it was called for later inspection; doesn't fail proactively | When the test wants to assert calls after the fact rather than declare them upfront |

**The rule:** use the simplest double that works. Dummies and stubs are cheap; mocks couple the test to implementation. Fakes are often the best choice — an in-memory `FakeUserRepository` that satisfies the same interface as the real one is usually more useful than three layers of mocks.

The famous warning, attributed to many: **don't mock what you don't own.** Mocking a library you don't control means your tests verify your *understanding* of that library, not its actual behavior. When the library updates, your tests still pass and production breaks. Wrap third-party libraries in your own adapter (Hexagonal!) and mock the adapter.

### 1B.3 The patterns that make code testable

These are the same patterns the rest of the doc recommends for other reasons. Testability is a beneficiary, not the goal.

**Dependency Injection (DI)** — pass collaborators in; don't construct them inside. If `OrderService.placeOrder()` does `new PostgresOrderRepository()` inside, you cannot test it without a Postgres database. If it accepts an `OrderRepository` interface in its constructor, you swap in a fake. This is the foundation. (See §11A.1.)

**Ports & Adapters (Hexagonal)** — formalizes DI at the architectural scale. The Domain Layer depends on `Port` interfaces; in production you wire real adapters; in tests you wire fake adapters. Same code, different wiring. (See §1A.2.)

**Pure functions for transformations** — a function that takes inputs and returns outputs (no I/O, no mutation, no time-dependence) is trivially testable. No setup, no mocking, no order-of-test problems. The FP discipline from §0.8 pays its biggest dividend here.

**Functional Core, Imperative Shell** (§0.8.4) — the pure core gets unit tests with no mocks at all; the thin imperative shell gets a small number of integration tests. The hardest parts of the system become the easiest to test.

**Make illegal states unrepresentable** (§1A.7) — when invalid inputs can't be constructed, you don't need tests for them. The type system carries the proof. This is why teams adopting sum types and value objects often *shrink* their test suites while increasing coverage.

**Humble Object** (Fowler, in *PoEAA*) — when a piece of code is intrinsically hard to test (a UI framework callback, a database trigger), extract the testable logic into a separate object and leave the untestable shell as thin as possible. The "humble" part stays untested; everything else gets tested.

### 1B.4 The anti-patterns that destroy testability

If you find yourself refactoring to test, look for these:

| Anti-pattern | Why it kills testability | The fix |
|---|---|---|
| **Singletons / global state** | Tests share state through the back door; order matters; concurrent tests interfere | Make singletons explicit dependencies passed in (DI) |
| **Static methods doing real work** | Can't substitute, can't mock without bytecode tricks | Make them instance methods on an injectable service |
| **`new()` inside methods** | Caller has no way to substitute the constructed object | Inject a factory or the object itself |
| **Direct calls to `DateTime.now()` / `Random` / `UUID.generate()`** | Tests can't make these deterministic | Inject a `Clock` / `RandomSource` / `IdGenerator` |
| **Tight coupling to frameworks** | Can't unit-test domain logic without standing up the framework | Hexagonal — domain doesn't import framework code |
| **Long chains of internal state mutations** | Tests have to walk through N intermediate states to reach the one being verified | Break into pure functions with explicit input/output |
| **Big methods doing many things** | Tests have to set up everything to test one thing | Extract until each thing is its own function |
| **Module loading does work** (e.g. ORM auto-connects on import) | Test runs can't avoid the side effect | Lazy initialization; explicit setup functions |

**The diagnostic:** if writing a test for a function requires extensive setup, mocking, or arrangement of global state, the function has a design problem. The test is *telling* you something. Refactor toward DI, pure functions, and explicit dependencies — and the test will write itself.

This is the seam concept from Michael Feathers's *Working Effectively with Legacy Code*: a **seam** is a place where you can change behavior without modifying the code itself. Seamless code is untestable; seam-rich code is testable. Adding seams (interfaces, injection points, factory methods) is what "refactor for testability" actually means.

### 1B.5 TDD as a design pressure, not a test discipline

Test-Driven Development (Kent Beck) is widely misunderstood as "write tests first." Its actual value is **using tests as a design probe**. If a test is hard to write, the design is wrong; back up and reshape. The tests are scaffolding for the design, not deliverables.

The TDD cycle:
1. **Red** — write a failing test that describes the next small piece of behavior
2. **Green** — write the smallest code that makes the test pass
3. **Refactor** — clean up the code (and the test) while staying green

You don't have to follow TDD literally to benefit from this discipline. The valuable habit is: **when you find a piece of code hard to test, treat that as a design signal, not a testing problem.** Even teams that don't TDD usually adopt this principle once they've felt the pain a few times.

### 1B.6 Beyond unit tests — the layered test architecture

A mature test architecture has more than two or three tiers. The layers, in order of breadth:

| Layer | What it tests | Real-world tools |
|---|---|---|
| **Static analysis** | Type errors, lint violations, dependency-direction violations | TypeScript, mypy, ESLint, dependency-cruiser, ArchUnit |
| **Unit tests** | Single function/class in isolation | Jest, pytest, JUnit, NUnit, RSpec |
| **Property-based tests** | A function's behavior across generated inputs (not a fixed example) | QuickCheck (Haskell), Hypothesis (Python), fast-check (JS), ScalaCheck |
| **Component / module tests** | A whole module against its interface | Same frameworks as unit tests, scoped wider |
| **Integration tests** | Multiple modules wired together against real (or near-real) dependencies | Testcontainers (real DBs in Docker), in-memory DBs for fast feedback |
| **Contract tests** | A service's interface matches its consumer's expectations | Pact, Spring Cloud Contract, OpenAPI schema validation |
| **End-to-end tests** | The whole system, browser-to-database | Playwright, Cypress, Selenium, Detox (mobile) |
| **Behavioral / acceptance tests** | Whole-system tests written in domain language | Cucumber, SpecFlow, jest-cucumber. Often paired with BDD |
| **Smoke tests** | Did the deploy work? Most critical paths only | Cheap subset of E2E run post-deploy |
| **Synthetic monitoring** | Production correctness, continuously | Datadog Synthetics, Pingdom, custom |
| **Chaos engineering** | Resilience under realistic failures | Chaos Monkey, Litmus, Gremlin — Netflix originated this discipline |
| **Mutation testing** | Are your tests actually catching bugs? Flip a `+` to a `-` and see if tests fail | Stryker (JS/TS), PIT (Java), Mutmut (Python) |

**Not every project needs every layer.** A small CRUD app probably has unit + integration + a handful of E2E. A bank settles for nothing less than contract tests + property tests + chaos. Match the test architecture to the cost of a bug.

### 1B.7 Contract testing — the underused win for microservices

A common microservices failure mode: Service A and Service B both have green tests, but they can't actually talk to each other because they disagree about the contract. Integration tests in A's repo mock B's behavior; integration tests in B's repo mock A's. Neither catches the drift.

**Contract testing** (Pact is the standard tool) makes the contract a first-class artifact:
1. Consumer (A) writes tests against B with a generated contract file
2. Contract is uploaded to a broker
3. Provider (B) verifies it can satisfy the contract as part of its own CI
4. Either side's CI fails when the contract drifts

**Real-world adopters:** atlassian, IBM, the British government (gov.uk), thousands of mid-size microservices shops. If you have microservices and you're not contract-testing, you're flying blind on integration drift.

### 1B.8 Property-based testing — the underused win for domain logic

Example-based tests verify behavior on the inputs you thought to write. Property-based tests verify behavior on inputs the framework *generates* — hundreds or thousands of them per property, including edge cases you'd never think to write.

```python
# Example-based (one input)
def test_reverse_known():
    assert reverse([1,2,3]) == [3,2,1]

# Property-based (Hypothesis)
@given(lists(integers()))
def test_reverse_is_involutive(xs):
    assert reverse(reverse(xs)) == xs
```

Properties express invariants — *what's true regardless of input*. Round-tripping (encode then decode), idempotence (apply twice = apply once), commutativity, monotonicity. Property tests are how QuickCheck originally found bugs in well-tested production code at Erlang shops.

**Real-world adopters:** the AWS SDK team uses property testing extensively; Volvo runs property tests on safety-critical automotive code; most well-engineered Erlang/Elixir shops use it.

### 1B.9 Real-world examples and references

- **The Test Pyramid** — Mike Cohn, *Succeeding with Agile* (2009); the canonical reference
- **The Testing Trophy** — Kent C. Dodds, [kentcdodds.com](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- **Test doubles taxonomy** — Martin Fowler, ["Mocks Aren't Stubs"](https://martinfowler.com/articles/mocksArentStubs.html)
- **Functional Core, Imperative Shell** — Gary Bernhardt, ["Boundaries"](https://www.destroyallsoftware.com/talks/boundaries) talk
- **Working Effectively with Legacy Code** — Michael Feathers — the canonical reference for seams and refactoring untested code
- **Growing Object-Oriented Software, Guided by Tests** (Freeman & Pryce) — the canonical book on TDD applied at design level
- **xUnit Test Patterns** (Meszaros) — the encyclopedic reference for test design
- **Chaos Monkey** (Netflix, 2011) — the resilience-testing approach that birthed chaos engineering as a discipline
- **The Sairyss/domain-driven-hexagon repo** (§12, source 11) — has a worked BDD example with Cucumber/Gherkin

### 1B.10 Cross-refs
- **§0.8 (Paradigm Choice)** — FP makes testing dramatically easier; the functional core / imperative shell pattern is the main payoff
- **§1A (DDD + Hexagonal)** — ports and adapters exist partly to make testing tractable
- **§2.1 (Microservices)** — contract testing is the missing piece most microservices stacks need
- **§4.4 (BFF)** — BFFs are particularly testable because they're thin coordinators over already-tested services
- **§8 (Deployment patterns)** — canary, shadow, parallel run are forms of *production testing*; tests don't stop at the CI boundary
- **Agentic doc §6.5 (Evaluation)** — eval harnesses for LLM systems are the testing-architecture problem for non-deterministic outputs; same architectural principles apply

---

## 2. Service Decomposition Patterns

These describe *how a system is split across deployables*. The rungs of the §0.7 ladder live here.

### 2.1 Microservices
**Shape:** A system composed of small, independently deployable services, each owning a bounded slice of business capability, communicating over the network (HTTP, gRPC, messaging).

**When to use:** Organizations with many teams that need independent deploy cadences; workloads with genuinely heterogeneous scaling (one service is read-heavy at 100k QPS, another is write-heavy at 100 QPS); polyglot teams that need different stacks for different services.

**When not to use:** Small teams. Single-team microservices is a famous anti-pattern — you get all the distributed-systems pain and none of the organizational benefits. Under ~30 engineers, modular monolith almost always wins.

**Real-world examples:**
- Netflix — the canonical microservices story; published their stack as the "Netflix OSS" ecosystem (Eureka, Hystrix, Ribbon, Zuul)
- Uber — famously moved from monolith to microservices and then partway back ("DOMA" — Domain-Oriented Microservices Architecture)
- Amazon — Bezos's "two-pizza teams" mandate from 2002 was the founding microservices story
- Spotify — "squad model" published widely; engineers debate how much of it is real vs marketing

**Watch out for:**
- **Distributed monolith** — services that have to be deployed together. The worst of both worlds. Symptom: every release touches three services.
- **Shared databases** — two services writing to one schema is microservices in name only. The schema is the coupling.
- **Synchronous chains** — service A calls B calls C calls D synchronously. Any latency or failure cascades through all four. Mitigate with async patterns (§4) or smarter aggregation.
- **Operational complexity** — you need service discovery, distributed tracing, distributed logging, rolling deploys, schema versioning, contract testing, secret management, network policies. That's a platform team.

**Cross-ref:** The Agent Mesh architecture in §2.6 of the interview prep is microservices applied to agent specialists. Same tradeoffs.

### 2.2 Modular Monolith (extension)
**Shape:** Single deployable, but internally organized into modules with explicit interfaces and dependency direction enforced (often via package boundaries, build rules, or architectural fitness functions).

**When to use:** Almost every team smaller than ~30 engineers. Most teams larger. It is the rung most teams should choose and don't.

**When not to use:** When you have proven, named, current pressure for independent deploys or scaling on a specific module. ("Future flexibility" is not a current pressure.)

**Real-world examples:**
- Shopify — famously moved *toward* modular monolith, not away from it. Their Ruby monolith is partitioned via "components" with strict boundary enforcement.
- Stack Overflow — ran a beautifully simple monolith for years at remarkable scale
- Most successful YC-stage startups before they outgrow it
- DHH/Basecamp's "Majestic Monolith" essays

**Watch out for:**
- **Boundary erosion** — without enforcement, "modular" decays into "spaghetti" in 18 months. Use tooling: ArchUnit for JVM, Modulith for Spring, Sorbet/RBI in Ruby, ESLint boundary rules in TS. The boundary has to be machine-checked or it will rot.
- **Shared mutable state** — global singletons, shared caches, shared DB schemas across modules. All the symptoms of a real coupling problem dressed up as convenience.

**Cross-ref:** Same logic as Anthropic's "start with a single LLM call, add complexity only when measurement shows it's needed" (§4.5.1 in the agentic doc). The structural advice is identical: start undivided, divide only when you can name the pressure.

### 2.3 Serverless / FaaS (extension)
**Shape:** Functions deployed individually, scaled and billed per-invocation, with no long-running process. AWS Lambda, GCP Cloud Functions, Azure Functions, Cloudflare Workers.

**When to use:** Spiky workloads where capacity planning is hard; glue code between cloud services; event-driven pipelines; teams that want to minimize ops. Cost wins when traffic is bursty; cost loses when traffic is steady and high.

**When not to use:** Long-running work (over Lambda's 15-min cap); tight tail-latency requirements (cold starts); workloads requiring local state; workloads where you'd burn money on warm baseline.

**Real-world examples:**
- The Coca-Cola Freestyle vending machines famously run on Lambda
- Most "alert handler" / "data pipeline glue" code at AWS-shop companies
- iRobot's IoT backend on Lambda + IoT Core
- Cloudflare Workers powering edge logic across many SaaS products

**Watch out for:**
- **Cold starts** — first invocation after idle can take seconds. Mitigated with provisioned concurrency, but that erodes the cost win.
- **Distributed-tracing nightmares** — many tiny functions = many tiny spans. Without good tooling (X-Ray, OpenTelemetry) you can't find anything.
- **Bill surprises** — Lambda is cheap until it isn't. A retry loop or a misconfigured event source can run up four-figure bills overnight. Always set concurrency limits and budget alerts.

---

## 2A. Where Your Code Runs: Hosting, Scaling, and Load Distribution

Patterns from §1–§2 describe *what* you build. This section is the layer underneath: *where it physically runs* and *how it grows*. Often the architecture decision and the hosting decision are made together; pretending they're independent is one reason migration projects underrun.

### 2A.1 Scaling vocabulary
Two axes everyone needs to be fluent in:

- **Vertical scaling (scale up)** — same server, more resources (more RAM, more CPU, faster disk). Bounded by the largest box you can buy. Simple; no application changes required.
- **Horizontal scaling (scale out)** — more servers running the same workload, traffic distributed across them. Effectively unbounded; requires the workload to be stateless or to coordinate state externally.

The discipline: **scale up before you scale out.** A modern box can do astonishing work — 64 cores, 1TB RAM, NVMe SSDs. Many systems that "needed microservices for scale" actually needed a bigger VM and a database read replica. Horizontal scaling is real complexity; don't pay for it until vertical hits a ceiling.

### 2A.2 Load balancers
The piece of infrastructure that makes horizontal scaling possible. Sits in front of N identical servers, distributes incoming requests across them, removes failed instances from rotation.

- **Layer 4 vs Layer 7.** L4 (TCP) is fast and dumb; L7 (HTTP) understands the protocol and can route by URL, header, cookie. AWS NLB is L4, ALB is L7. Most app traffic wants L7.
- **Distribution algorithms.** Round-robin, least-connections, IP-hash (sticky sessions), latency-based. Each has gotchas at scale.
- **Health checks.** The LB needs to know which instances are healthy. Liveness vs readiness probes — liveness = "is this process alive?", readiness = "is this process ready to take traffic?" Treat them as separate.
- **Reverse proxy.** Load balancers are a special case of reverse proxies. nginx, HAProxy, Envoy, Traefik all do this; cloud LBs (ALB, NLB, GCP LB, Azure LB) are managed flavors.

**Real-world examples:** Every internet-facing service over ~1k QPS has a load balancer. Stack Overflow had ~9 web servers behind HAProxy for years — a famously minimal horizontal-scale setup at large traffic.

### 2A.3 Database scaling
Databases need their own scaling story because they hold state. Stateless app servers are easy; stateful databases are not.

- **Read replicas (source-replica)** — primary takes writes, replicates to N read-only replicas. Read traffic spreads across replicas. **Replication lag** is the price (§1.5, Controller-Responder).
- **Sharding** — partition data across DB instances by key. Each instance owns a slice. Hard to do right; near-impossible to undo. See §3.4.
- **Read-through caching** — Redis or Memcached in front of the DB absorbs read traffic. Easier than read replicas for many workloads. See §7.2.
- **Connection pooling** — databases have hard connection limits. PgBouncer (Postgres), ProxySQL (MySQL) multiplex many app connections onto fewer DB connections. Often the actual bottleneck.

### 2A.4 Where infrastructure physically lives
Four broad options, each with a hosting culture and a cost profile.

| Model | What you own | Sweet spot | Failure mode |
|---|---|---|---|
| **On-premise** | All of it — datacenter, hardware, ops | High-security / classified environments; very stable predictable workloads where capex beats opex; data sovereignty mandates | Massive capex; staffing for hardware ops; slow to scale; hard to scale *down* |
| **Traditional hosting providers** (Hostinger, Hetzner, OVH, dedicated boxes) | Just the software | Cost-sensitive workloads with steady predictable traffic; teams that want hardware control without owning hardware | Less automation; manual scaling; fewer managed-service options |
| **Cloud (traditional)** — VMs (EC2, GCE, Azure VMs) | Software + OS config | Workloads with moderate variability; teams porting from on-prem; need for specific OS/network control | You pay for what you provision, not what you use — over-provisioning waste is real |
| **Cloud (managed / PaaS)** — managed DBs, container services, App Engine, Cloud Run, Fargate, ECS | Software only; provider runs everything else | The default for most new workloads; lets a small team operate large infra | Less control; vendor-specific abstractions; cost can balloon without discipline |
| **Cloud (serverless)** — Lambda, Cloud Functions, Cloudflare Workers (§2.3) | Just the function code | Spiky / event-driven workloads; glue between services; minimal ops mandates | Cold starts; runtime limits; observability is harder |

**The strategic point:** these aren't a hierarchy. They're tools for different shapes of work. A single company often runs all four — classified data on-prem, steady transactional services on managed cloud (Kubernetes / ECS), spiky event handlers on serverless, dev infrastructure on traditional VMs.

### 2A.5 Elastic vs reserved capacity
Inside cloud, the per-workload decision is whether to:
- **Reserve** capacity for 1-3 years (cheaper, but only if you actually use it). AWS Reserved Instances, Savings Plans, GCP Committed Use Discounts.
- **Pay on-demand** for elastic capacity that scales with load. More expensive per unit; flexible.
- **Use spot / preemptible** instances for fault-tolerant batch work. Cheapest, but the provider can reclaim them with minutes of notice.

Steady-state production traffic usually justifies reservation; bursty or experimental workloads stay on-demand; batch/training workloads love spot. Most mature cloud bills are a mix.

### 2A.6 Cross-refs
- **§2.1 (Microservices)** — splitting into services and scaling them independently usually means horizontal scaling at the service granularity
- **§3.4 (Sharding)** — horizontal scaling for databases
- **§5.2 (Throttling)** — rate-limit when scaling out isn't keeping up
- **§7.5 (AWS Bedrock / SageMaker)** in the agentic doc — managed-cloud pattern applied to AI workloads
- **Agentic doc §5.3 (cost monitoring at Synertex)** — operational reality of cloud cost discipline

---

## 3. Data Management Patterns

The hard problems in distributed systems live here. Communication patterns (§4) are usually easier than data patterns — moving messages is well-understood; coordinating durable state across services is not.

### 3.1 Command Query Responsibility Segregation (CQRS)
**Shape:** Split the model that handles **commands** (writes) from the model that handles **queries** (reads). They can use different storage, different schemas, even different databases.

**When to use:** Read-write asymmetry — when reads vastly outnumber writes, when queries need different shapes than the write model supports (e.g., the canonical model is normalized but the dashboard wants denormalized rollups), when audit/historical reads benefit from a different store than transactional writes.

**When not to use:** Symmetric workloads, simple CRUD, low traffic. CQRS adds a whole second storage system and a synchronization mechanism between them. Don't pay that cost speculatively.

**Real-world examples:**
- Microsoft's eShopOnContainers reference architecture (their canonical microservices teaching project)
- Most order-management systems at scale — write through transactional DB, read through denormalized search indexes
- Banking statement views — writes hit the ledger, reads come from a precomputed view

**Watch out for:**
- **Eventual consistency** — the read side is always slightly behind the write side. The user who just placed an order may not see it in their order history for a few hundred milliseconds. Design for it.
- **Complexity tax** — you now have two models to evolve, two stores to keep in sync, two surfaces to test. Often paired with Event Sourcing (§3.2) to get the sync mechanism for free.

### 3.2 Event Sourcing
**Shape:** The system's state is derived from a log of immutable events, not stored directly. Every change is appended to an event log; current state is computed by replaying events. The log is the source of truth; everything else is a projection.

**When to use:** Domains where the *history* is as important as the *current state* — financial ledgers, audit-regulated systems, anywhere "how did we get here?" is a real question. Also valuable when you want to derive multiple views from one source of truth (pairs naturally with CQRS).

**When not to use:** Domains where only the current state matters and you don't care about history. The event-replay machinery is real cost; don't pay it if you won't use it.

**Real-world examples:**
- **Git itself** — the canonical event-sourced system. The objects directory is the event log; the working tree is the projection.
- Bank ledgers — accounts are computed by summing the transaction log, not stored as a balance
- Kafka-backed systems where the Kafka topic *is* the source of truth and databases are downstream projections
- Most insurance claims systems (you need to be able to reconstruct claim state at any point in time)

**Watch out for:**
- **Schema evolution** — the event log is forever. When you change event shapes, old events still need to be replayable. Versioning and upcasters are mandatory; this is the operational cost most teams underestimate.
- **Snapshotting** — replaying a million events to compute current state is slow. Periodic snapshots are needed at scale, which adds complexity.
- **GDPR / right-to-be-forgotten** — "immutable event log" and "user has the right to have their data deleted" do not get along. Solutions exist (crypto-shredding, tombstone events) but they're not free.

### 3.3 Saga
**Shape:** A multi-step distributed transaction modeled as a sequence of local transactions with explicit **compensating actions** to undo each step if a later step fails. Two flavors: **choreography** (each service publishes events, others react) and **orchestration** (a central coordinator drives the steps).

**When to use:** Cross-service transactions where you can't use a database transaction. Travel booking (flight → hotel → car, each is a separate system). Order fulfillment (reserve inventory → charge payment → ship). Anywhere "if any step fails, partially undo the earlier steps" is the requirement.

**When not to use:** When you can keep it in one DB transaction, do. ACID is easier than sagas, every time. Also avoid sagas for transactions with too many steps (>5-7) — the compensation logic combinatorially explodes.

**Real-world examples:**
- Travel reservations — Expedia, Booking.com (the textbook example, and the actual real example)
- Uber's payment flows — pickup, ride, calculate fare, charge, payout to driver
- E-commerce order processing at any company that has split inventory, payment, fulfillment, and notification into separate services

**Watch out for:**
- **Non-reversible side effects** — what's the compensation for "we sent the email"? You can't unsend it. Sagas are easier when every step is logically reversible; design for reversibility from the start.
- **Choreography spaghetti** — without orchestration, "what's the current state of order #4423?" is unanswerable. You have to assemble it from events across many services. Most teams that start with choreography eventually wish they had picked orchestration.
- **Orchestrator becomes a god-object** — if you go with orchestration, the orchestrator can accumulate every business rule. Discipline matters.

**Cross-ref:** Step Functions (in §6.8 of the interview prep) is AWS-native saga orchestration. Temporal is the OSS standard. Don't roll your own — use a workflow engine.

### 3.4 Sharding
**Shape:** Split data across multiple database instances by a partition key (user_id, tenant_id, geographic region). Queries route to the relevant shard based on the key.

**When to use:** When a single database can't hold the working set, can't keep up with write throughput, or can't meet a regulatory locality requirement. Hard scale problems, not "we might grow."

**When not to use:** Before you have to. Sharding is irreversible in practice — un-sharding is a project on the scale of the original sharding effort. Read replicas, vertical scaling, and caching often solve the same problem more cheaply.

**Real-world examples:**
- **Discord on Cassandra** (their well-known engineering blog post about reading and writing trillions of messages)
- **YouTube on Vitess** — sharded MySQL at planet scale; eventually open-sourced as Vitess and now widely used
- **Slack** — sharded by team_id, which is why some operations can't easily span teams
- **Notion** — sharded their Postgres in a famous engineering writeup when they hit the limits of vertical scaling

**Watch out for:**
- **Shard key choice** — picking the wrong key is the most painful sharding mistake. Pick a key that's high-cardinality, evenly distributed, and aligned with your most common queries. You will not get to change it without massive rework.
- **Cross-shard queries** — anything that has to span shards (analytics, search, joins) becomes hard. You typically need a separate denormalized store (see Controller-Responder, §1.5) for cross-shard reads.
- **Hot shards** — even with good keys, traffic can skew. Celebrity users, viral content, batched operations. Plan for splittable shards from day one.

### 3.5 Database-per-Service (extension)
**Shape:** In a microservices architecture, each service owns its database exclusively. No other service reads or writes that database — they go through the owning service's API.

**When to use:** Mandatory for real microservices. If two services share a schema, they're a distributed monolith pretending otherwise (see §2.1).

**When not to use:** In a modular monolith — one DB, multiple modules is fine and good. The discipline of "module A doesn't reach into module B's tables" is enforced by code review and tooling, not network boundaries.

**Real-world examples:**
- This is foundational to every credible microservices story (Netflix, Uber, Amazon, Spotify)
- The cleanest example: Amazon's services don't share databases — period. It's a hard rule from the 2002 memo.

**Watch out for:**
- **Cross-service joins are now your problem** — you can't `JOIN orders ON customers` if those are different services. You have three choices: API composition (gather from both, join in memory), CQRS read models, or data replication. All are more expensive than a SQL join.
- **Distributed transactions** — see Saga (§3.3). You no longer have multi-table ACID; you have multi-service eventual consistency.

### 3.6 Materialized View (extension)
**Shape:** A precomputed, queryable representation of data that would otherwise require expensive joins or aggregations. Refreshed on write, on schedule, or on demand.

**When to use:** Read patterns that are predictable, repeated, and expensive to compute on demand. Dashboards. Search-result rankings. Leaderboards. Recommendation feeds.

**Real-world examples:**
- Postgres materialized views (the explicit feature)
- Twitter's home timeline — a famously denormalized precomputed view per user, written-on-tweet rather than computed-on-read
- Most analytics dashboards backed by daily/hourly aggregation jobs

**Watch out for:** Staleness budgets — how out of date can it be? Refresh strategy is the design choice that determines everything else.

### 3.7 Outbox Pattern (extension)
**Shape:** When a service needs to update its database *and* publish an event, write both in one local transaction — the event goes into an "outbox" table in the same DB. A separate process polls the outbox and publishes to the message bus, then marks it sent.

**When to use:** Any time a service writes to its DB and emits an event. Without this, you have a dual-write problem — DB succeeds, message fails (or vice versa), and your system is now inconsistent.

**Real-world examples:**
- Debezium (CDC tool) implements the pattern — reads the WAL and emits events
- Most modern event-driven microservices that take consistency seriously
- A standard recipe in the eventuate.io and Chris Richardson "Microservices Patterns" book

**Watch out for:** "At-least-once" delivery — downstream consumers must be idempotent. The publish step can be retried; consumers must handle duplicate events.

---

## 4. Communication Patterns

### 4.1 Publish-Subscribe (Pub-Sub)
**Shape:** Publishers emit messages to a *topic* without knowing who consumes them. Subscribers register interest in topics and receive matching messages. Decoupled in time, space, and synchronization.

**When to use:** Fan-out scenarios where one event has many interested consumers. Notification systems. Event-driven architectures. Cross-service decoupling where the publisher shouldn't know its consumers.

**When not to use:** Request-reply scenarios where you need a synchronous answer. Pub-sub is fire-and-forget by nature; bolting reply semantics on top is awkward.

**Real-world examples:**
- **Kafka at LinkedIn** — Kafka was built at LinkedIn specifically for their pub-sub needs at scale; now the standard event streaming platform across the industry
- **AWS SNS** — managed pub-sub, fan-out to SQS queues, Lambda, email, SMS
- **Google Cloud Pub/Sub** — analogous service on GCP
- Slack's real-time message delivery uses pub-sub internally
- Redis pub-sub for in-memory low-latency scenarios

**Watch out for:**
- **Testing is hard** — async by nature, hard to assert "this happened because of that." Investing in contract tests and good observability pays back fast.
- **Delivery guarantees** — at-most-once, at-least-once, exactly-once. Read the fine print of your broker. "Exactly-once" usually has asterisks.
- **Ordering** — pub-sub doesn't guarantee order by default. Kafka does within a partition; SNS doesn't.

**Cross-ref:** SNS vs SQS distinction from §5.2 of the interview prep — SNS for fan-out (many consumers want every message), SQS for work distribution (one consumer per message).

### 4.2 Request-Reply (extension)
**Shape:** The bread-and-butter synchronous communication pattern. Client sends a request, blocks (or awaits) a reply, processes it. HTTP, gRPC, traditional RPC.

**When to use:** When you need an answer to proceed. Most CRUD. Most queries. Most user-facing interactions.

**When not to use:** When the operation is fire-and-forget (use pub-sub or a queue). When the operation is long-running (return a job ID, poll or callback). When latency budgets force you to parallelize.

**Real-world examples:** Every REST API. Every gRPC service. Every database query.

**Watch out for:**
- **Synchronous chains** — A → B → C → D, where each waits for the next. Latency adds up; any failure cascades. Break with async patterns or aggregator services.
- **Timeout configuration** — every request-reply call needs a timeout. Default infinite timeouts are how outages turn into hangs that take down upstream callers.

### 4.3 Event Sourcing as Communication (extension)
**Shape:** Different angle on §3.2 — when events are not just internal state but the way services communicate. Service A publishes events; Service B subscribes to those events as its way of learning about Service A's state changes.

**When to use:** When services need to share state changes without coupling on synchronous APIs. When you want the option to add new consumers without changing the producer.

**Real-world examples:** Most "event-driven microservices" architectures. LinkedIn's data infrastructure is famously event-driven end-to-end.

**Watch out for:** Schema evolution across producer and consumer versions. Use schema registries (Confluent Schema Registry, AWS Glue Schema Registry) and explicit compatibility rules.

### 4.4 API Gateway (extension)
**Shape:** A single entry point that fronts many internal services. Handles routing, auth, rate limiting, request/response transformation, logging.

**When to use:** Any external-facing microservices architecture. Almost always — gives you a central place to enforce cross-cutting concerns.

**Real-world examples:**
- Netflix Zuul (their famous gateway, since superseded by Spring Cloud Gateway in many shops)
- Kong, Tyk, AWS API Gateway, Apigee, Azure API Management
- Cloudflare's edge as a gateway for many SaaS products

**Watch out for:** Gateway as bottleneck. The thing that fronts everything also fails for everything. Plan for HA.

### 4.5 Backend-for-Frontend (BFF) (extension)
**Shape:** Per-client-type aggregation layer. The mobile app has its own BFF; the web app has its own; each tailored to that client's needs. The BFFs talk to the same underlying microservices.

**When to use:** Multiple client types with different data needs. Avoiding the "lowest-common-denominator API" problem where every client gets everything.

**Real-world examples:**
- SoundCloud (popularized the pattern, and the term)
- Netflix uses BFFs heavily across device types
- Most large-scale apps with native mobile + web have BFFs whether they call them that or not

---

## 5. Reliability & Resilience Patterns

These are the patterns that turn "the happy path works" into "the system survives." Every production system has all of them at some level — explicitly or hidden in framework defaults.

### 5.1 Circuit Breaker
**Shape:** Wraps a call to a dependency. Tracks failures over a window. After a failure threshold, **opens** — short-circuits subsequent calls without trying, returning a failure or fallback immediately. After a cool-off period, goes **half-open** — lets a trickle of calls through to test. If they succeed, closes; if not, stays open.

**When to use:** Calls to any unreliable dependency — third-party APIs, slow databases, external services with worse SLAs than yours. Anywhere a slow failure could cascade up and exhaust your own thread/connection pool.

**Real-world examples:**
- **Netflix Hystrix** — the canonical implementation (now in maintenance; Netflix moved to adaptive concurrency limits)
- **Resilience4j** — modern JVM standard, the successor to Hystrix
- **Polly** for .NET
- **Istio / Envoy** — built-in circuit breakers at the service mesh layer
- Most production-grade HTTP clients include circuit-breaker hooks

**Watch out for:**
- **Tuning sensitivity** — too sensitive and you trip on transient blips; too forgiving and you cascade failures anyway. Tuning is empirical.
- **What to do when open?** — returning an error is fine; degraded behavior is better; cached or default responses are often best. Design the fallback.
- **Per-instance vs global** — should the breaker be per-process or shared? Per-process is simpler; global is more accurate. Service mesh gets you global without coupling logic.

**Cross-ref:** Mentioned in §6.2 of the interview prep as the standard pattern for Bedrock throttling resilience. Same shape, different dependency.

### 5.2 Throttling / Rate Limiting
**Shape:** Cap the rate at which requests are accepted by a service. Excess requests are queued, delayed, or rejected. Distinct from circuit breaker — throttling protects you from being *overloaded*, circuit breaker protects you from *cascading downstream failures*.

**When to use:** Public APIs (always); abuse-prone endpoints (login, signup); cost-bounded systems (LLM calls, expensive queries); fair-use across tenants.

**Real-world examples:**
- AWS API Gateway with usage plans
- Stripe's API rate limits (well-publicized, well-engineered — 25 read/100 write per second by default)
- GitHub's API (5000/hour authenticated, 60/hour unauthenticated)
- Cloudflare's edge rate limiting
- Most public APIs you've ever heard of

**Watch out for:**
- **Per-what?** — Per-IP? Per-user? Per-API-key? Per-tenant? Per-endpoint? Often multiple, layered. Cite the unit explicitly.
- **Token bucket vs leaky bucket vs fixed window** — different mathematical shapes, different burst behaviors. Token bucket is the most common for APIs.
- **Signaling** — return 429 with `Retry-After`. Don't just drop. Clients need to know.

**Cross-ref:** Cost-control story in §5.3 of the interview prep — AWS Budgets + alarms is throttling-shaped: cap the spend, alert at thresholds. Same control-theory shape, different unit.

### 5.3 Bulkhead (extension)
**Shape:** Isolate resources (thread pools, connection pools, semaphores) per dependency or per tenant so that one dependency's exhaustion can't drag down the rest of the system. Named after ship compartments — flood one, the others stay dry.

**When to use:** Multi-tenant systems; systems with multiple downstream dependencies of varying reliability; anywhere "one slow thing took down everything" is a story you want to prevent.

**Real-world examples:**
- Hystrix and Resilience4j both implement bulkheads explicitly
- Most thread-pool-per-downstream patterns in production JVM services
- Kubernetes resource limits are a coarse bulkhead at the pod level
- Database connection pools per tenant in multi-tenant SaaS

**Watch out for:**
- **Over-partitioning** — too many tiny pools, each under-utilized. Tune by traffic, not by anxiety.
- **Misses shared resources** — bulkheads protect against thread/connection exhaustion. They don't protect against CPU starvation or memory pressure. Layer with other limits.

### 5.4 Retry with Exponential Backoff (extension)
**Shape:** On a retryable failure, wait, then try again. Wait time grows exponentially (with jitter to avoid thundering herd) up to a cap. After N attempts, give up.

**When to use:** Transient failures — network blips, brief throttling, leader elections. Anywhere "the same call would probably succeed if we tried again in a moment."

**When not to use:**
- 4xx errors (client error, not transient) — retrying won't help, just delays the inevitable
- Non-idempotent operations without dedup keys — retrying a payment twice is worse than failing once
- Hot dependencies — piling retries on a struggling service makes it worse, not better (the "retry storm")

**Real-world examples:**
- AWS SDKs do this by default for transport errors
- Polly (.NET), Resilience4j (JVM), Tenacity (Python), backoff (Node)
- Most queue-based systems with dead-letter queues for "tried N times, giving up"

**Watch out for:**
- **Retry storms** — N upstream callers each retry K times when downstream chokes; downstream sees N*K traffic instead of N. Cap retries low; combine with circuit breakers.
- **Jitter is mandatory** — without it, all clients retry at the same offset and the next attempt also fails as a herd.

### 5.5 Timeout (extension — too important to omit)
**Shape:** Every outbound call has a maximum wait time. If exceeded, the call fails (not hangs).

**When to use:** Always. Every call. No exceptions. Default-infinite timeouts are how outages turn into hangs that take down upstream callers.

**Watch out for:** Timeouts must be tighter than upstream's. If service A times out at 30s and calls service B which times out at 60s, A gives up while B is still working — wasted load. Always: A's timeout to B < A's own timeout from its caller.

### 5.6 Fallback / Degraded Mode (extension)
**Shape:** When a dependency is unavailable, the system continues to serve a degraded but useful response — cached data, default values, simplified UI, "this feature is temporarily unavailable" — rather than a full error.

**Real-world examples:**
- Netflix famously falls back to a curated default list when its personalization service is unavailable
- Amazon product pages stay up even when the recommendations service is down — the page just doesn't have recommendations
- Most well-engineered apps degrade rather than fail

---

## 5A. Security Architecture & Access Control

Security is everywhere in this doc — already cross-referenced in §1A.7 (illegal states), §5 (defensive patterns), and §1B (testability supports auditability). This section pulls the dedicated security architecture together because it's a *category of pattern decisions*, not a checklist. Getting these wrong fails differently from getting performance or scalability wrong — instead of a slow site, you have an incident, a breach, and a CISO with a phone in her hand.

The framing this section uses: security architecture splits into three sub-problems, often confused because they all start with "A":
- **Authentication (AuthN)** — *who are you?* Proving identity.
- **Authorization (AuthZ)** — *what are you allowed to do?* Granting or denying access given identity.
- **Audit** — *what did you do?* Recording actions for later inspection. Often the only path to detecting that something went wrong.

These are independent layers. Bad AuthN with good AuthZ doesn't save you. Good AuthN with bad AuthZ doesn't save you. Both with no audit means a successful breach is invisible. Most production failures happen because one of the three was treated as an afterthought.

### 5A.1 Authentication patterns

Mostly a question of: who holds session state, and what's the credential the client carries between requests?

| Pattern | Where state lives | When to use | Watch out for |
|---|---|---|---|
| **Session-based** (server-side session, cookie holds session ID) | Server (in DB / Redis / sticky memory) | Traditional web apps, browser clients, anywhere logout-everywhere needs to be instant | Session-store availability is a hard dependency; horizontal scaling needs shared session store or sticky LBs |
| **Token-based** (JWT, stateless, claims signed in the token) | Client (token carries the claims) | APIs, mobile clients, microservice-to-microservice | Revocation is hard (tokens are valid until expiry); never put secrets in claims; rotate signing keys |
| **OAuth 2.0 + OIDC** | Identity provider (Google, Okta, Auth0, Cognito, custom) | Any time you delegate identity to another system; SSO across many apps | Implementation complexity; many flows (auth code, PKCE, client credentials, device flow) — pick the right one |
| **API keys** | Client-held long-lived secret; server-side lookup | Service-to-service in non-user contexts; webhook receivers; CLI tools | Long-lived = high blast radius if leaked; rotate; scope tightly; never embed in client-side JS |
| **mTLS (mutual TLS)** | Both client and server present X.509 certs | Service-to-service in zero-trust networks; high-security internal APIs | Cert lifecycle management is real work; SPIFFE/SPIRE are the modern approach |
| **Passkeys / WebAuthn** | Client-held device-bound key + server-held public key | New web/mobile apps wanting passwordless from day one | Recovery flow (lost device) is the design challenge; ecosystem still maturing in 2025-26 |
| **MFA / 2FA** (layered on the above) | Codes/devices in addition to primary credential | Always for production. TOTP, push notifications, hardware keys (YubiKey), passkeys | SMS is no longer considered MFA-grade by NIST; phishing resistance matters more than possession |

**The strategic split:** for *user-facing* auth, modern default is OIDC + passkeys-or-MFA (delegate to a provider, never roll your own password hashing). For *service-to-service*, modern default is mTLS or short-lived OAuth tokens via a workload identity system. The "we wrote our own auth" stack is a famous category of post-incident war story.

### 5A.2 Sessions, tokens, and the recurring confusion

A subtle distinction worth getting right: **sessions and tokens are not opposites.** They're complementary primitives that can compose.

- **A session** is the *concept* — "this user is currently logged in, here's what we know about them."
- **A session ID** is a *handle* — a server-side lookup key. Used in cookie-based session auth.
- **A token** is a *bearer credential* — the holder is treated as authenticated. JWTs are the common form.
- A token *can* identify a session. A session *can* be represented as a token. They're not the same axis.

The actual axis is **stateful vs stateless authentication:**
- **Stateful** = server keeps the session record; client sends an opaque ID; server looks up state every request.
- **Stateless** = server signs claims into a token; client sends the token; server verifies the signature without lookup.

Tradeoffs are real:

| Property | Stateful | Stateless |
|---|---|---|
| Scaling | Needs shared session store | No shared state needed |
| Revocation | Trivial (delete the session) | Hard (must wait for expiry or maintain a revocation list) |
| Payload size | Tiny (just an ID) | Larger (claims travel with every request) |
| Trust boundary | Server is the source of truth | Anyone with the signing key can mint valid tokens |
| Refresh strategy | Refresh session TTL on activity | Short-lived access token + long-lived refresh token (the canonical pattern) |

**The pragmatic default**: short-lived JWTs (15 min) for access + long-lived refresh tokens stored server-side (with revocation capability). Gets you most of stateless's scaling benefits without losing revocation entirely. This is what most well-designed APIs in 2025 use.

### 5A.3 Authorization models — the StrongDM lineup, extended

This is where the §5A meat lives, because authorization is where most architectural decisions accumulate. Six named models, each with different sweet spots. Most production systems combine two or three.

| Model | Decision rule | Real-world example | When to use |
|---|---|---|---|
| **DAC** — Discretionary Access Control | Owner of the resource decides who can access it | Google Docs sharing model — you own a doc, you decide who can edit; Unix file permissions | Collaboration tools, document systems, social platforms where users own their content |
| **MAC** — Mandatory Access Control | System enforces labels; users *cannot* override | Classification systems (Secret/Top Secret); SELinux; FedRAMP-High deployments | Military, intelligence, classified work, any environment where users-can't-be-trusted is the design assumption |
| **RBAC** — Role-Based Access Control | Permissions attach to roles; users get roles | "Admin can edit users; Editor can publish posts; Reader can only view" — most enterprise SaaS | Most internal tools and B2B SaaS; when the number of distinct permission patterns is manageable |
| **ABAC** — Attribute-Based Access Control | Decision evaluates attributes of subject, resource, environment at runtime | "Allow if user.department == doc.department AND time.hour BETWEEN 9 AND 17 AND user.location == 'US'" | Fine-grained context-aware policies; HIPAA-style PHI access; compliance-heavy domains |
| **PBAC** — Policy-Based Access Control | Policies expressed in a dedicated language, evaluated centrally | Open Policy Agent (OPA) with Rego; AWS IAM JSON policies; Cedar (AWS's newer policy language) | When policies need to be auditable, versionable, and reviewed by non-engineers (compliance, security) |
| **ReBAC** — Relationship-Based Access Control | Decision walks a graph of relationships | Google Drive's "users connected to docs via folders and groups"; Google's Zanzibar paper (2019) | Social graphs, hierarchical sharing, anywhere "X has access because they're connected through Y to Z" is the natural model |
| **ACL** — Access Control List (a *mechanism*, not really a model) | Explicit list of (subject, resource, permission) tuples | Unix file permissions; AWS S3 bucket ACLs; network firewall rules | Building block under DAC; useful for fine-grained network and file-level controls |

**The honest combinatorics** — almost every real production system is a hybrid:
- **RBAC + ABAC** is the most common combo. RBAC handles the coarse permissions ("admins can edit users"); ABAC handles the fine-grained context ("only during business hours, only for users in their region"). This is what StrongDM, Auth0, and most modern access platforms now combine.
- **RBAC + ReBAC** for collaboration tools: roles inside organizations (RBAC) + per-document sharing graphs (ReBAC).
- **MAC + RBAC** for regulated environments: classification labels are MAC; functional permissions inside that label are RBAC.

**ReBAC is the rising star.** Google's Zanzibar paper (2019) catalyzed a wave of open-source ReBAC engines — OpenFGA (CNCF, originated at Okta/Auth0), SpiceDB (Authzed), Permify, Ory Keto. Worth knowing about because for graph-shaped authorization problems (social, collaboration, hierarchical), ReBAC is dramatically simpler than expressing the same logic in RBAC+ABAC. If your authorization questions feel like "is this user related to this resource through some path?", look at ReBAC before extending an RBAC system to breaking point.

### 5A.4 Policy engines — externalizing authorization

A separate question from "which model": **where is authorization evaluated?** Two architectural choices:

- **Inline** — authorization checks live inside each service. Familiar, easy to reason about per-service, but consistency across services drifts and policy reviews are scattered.
- **Externalized** — services ask a central authorization engine for each decision. The classic "PEP/PDP" model from XACML (Policy Enforcement Point at the service, Policy Decision Point at the engine).

**Open Policy Agent (OPA)** — the dominant externalized engine. Policies in Rego, evaluated as a sidecar or library, used by Netflix, Goldman Sachs, Pinterest, Atlassian, and across Kubernetes for admission control. Single source of truth for policy across an org.

**AWS Cedar** — Amazon's newer policy language, designed specifically for application-level authorization. Cleaner syntax than Rego; cleaner formal semantics. Powers AWS Verified Permissions.

**Casbin** — open-source, multi-language, supports RBAC/ABAC/RBAC-with-domains/ReBAC. Lighter-weight than OPA for in-process embedding.

**The strategic choice**: externalize policy when (a) you have many services that need consistent authorization, (b) compliance demands a reviewable policy artifact, or (c) policies change faster than service deployments. Otherwise inline checks are fine.

### 5A.5 Zero Trust as the modern security stance

The traditional model — *perimeter security*, where inside-the-network is trusted and outside is hostile — broke in the cloud-and-remote-work era. Zero Trust is the replacement frame, with three principles:

1. **Never trust, always verify.** Every request gets authenticated and authorized, regardless of where it came from. There is no "inside."
2. **Least privilege.** Identities get exactly the access they need, for as short a time as possible. JIT (Just-in-Time) elevation is the norm.
3. **Assume breach.** Design as if an attacker is already inside. Limit blast radius; require continuous re-verification; log everything.

In architecture terms, Zero Trust translates to: mTLS between services, identity attached to every request, fine-grained authorization at every hop, observability for forensics, network segmentation as defense-in-depth not as the primary control.

**Real-world adoptions:** Google's BeyondCorp (the canonical paper); CISA's Zero Trust Maturity Model (US federal mandate); most large tech companies are some-fraction-implemented.

### 5A.6 Defense in depth — layered, not nested

The principle: no single control should be the only thing between an attacker and the asset. If the WAF fails, the auth still catches it. If the auth fails, the authorization still catches it. If the authorization fails, the audit log catches it post-hoc.

Typical layers from outside in:
1. **Edge** — DDoS protection, WAF, bot detection (Cloudflare, AWS Shield, Akamai)
2. **Network** — VPC, security groups, private subnets, no direct internet egress from sensitive workloads
3. **Transport** — TLS everywhere, mTLS for service-to-service
4. **AuthN** — every request identified, MFA-protected for human users
5. **AuthZ** — every action checked against policy
6. **Application** — input validation, output encoding, parameterized queries (SQL injection defense), CSRF protection, CSP headers
7. **Data** — encryption at rest, field-level encryption for PII, tokenization for ultra-sensitive (credit cards)
8. **Audit** — comprehensive logging, immutable log store, alerting on anomalies
9. **Operational** — secrets management, key rotation, vulnerability scanning, dependency auditing

**The discipline:** every layer is independently sufficient to mitigate *some* class of attack. The combination handles the realistic threat surface. Skipping any layer because "the others would catch it" is how breaches happen.

### 5A.7 Data protection patterns

Three orthogonal techniques that compose:

- **Encryption at rest** — data on disk is encrypted. Cloud-native (S3 SSE, RDS encryption, KMS-backed). Cheap; should be default-on everywhere. Doesn't protect against a compromised app that has decrypted access.
- **Encryption in transit** — TLS for all network traffic. Default for external; should be default for internal too.
- **Field-level encryption** — sensitive fields (SSN, health records) encrypted with separate keys, decrypted only at the exact point of use. Protects against an app-level compromise that can read the DB but not the per-field keys.
- **Tokenization** — replace sensitive values with non-sensitive tokens; original lives in a separate vault. Used for PCI/credit cards. Reduces compliance scope (services that handle only tokens are out of PCI scope).
- **Key management** — KMS (AWS KMS, GCP KMS, Azure Key Vault, HashiCorp Vault). Keys never leave the KMS; you call the KMS to encrypt/decrypt. Rotation, audit, access control on the keys themselves.

### 5A.8 Secrets management

Secrets are not configuration. They are not environment variables. They are not git-ignored files. They are credentials whose disclosure is a security incident, and they need their own lifecycle.

**The pattern:**
- Secrets stored in a dedicated service (Vault, AWS Secrets Manager / Parameter Store, GCP Secret Manager, Azure Key Vault, sealed-secrets for Kubernetes)
- Fetched at runtime, not baked into images
- Rotated on schedule and on incident
- Access audited (every fetch logged)
- Workloads authenticate via short-lived credentials (IAM roles, workload identity, SPIFFE)
- Never logged, never committed, never in client-side code

**The famous failures**: AWS keys committed to public GitHub (still happens weekly); secrets in environment variables visible in error pages; long-lived API keys that get exfiltrated and not rotated for years. Every one of these has a generic fix in a secrets-management product.

### 5A.9 Compliance frames worth knowing

Most security architecture decisions in regulated environments are downstream of one of these frameworks. You don't need to memorize them, but knowing what they care about helps you anticipate review questions.

| Framework | Scope | What it cares about |
|---|---|---|
| **SOC 2 (Type I and II)** | Operational practices for service providers | Access controls, audit logs, change management, incident response. Most B2B SaaS needs this |
| **HIPAA** | US healthcare data | PHI protection, BAA contracts, access controls scoped to "minimum necessary," breach notification |
| **PCI DSS 4.0** | Credit-card data | Network segmentation around CHD, encryption, tokenization, vulnerability management. Tokenization can dramatically reduce scope |
| **GDPR / CCPA** | EU and California consumer data | Lawful basis, consent, right to deletion, breach notification, data portability |
| **ISO 27001** | Information security management | Risk assessment process, security controls catalog (Annex A), continuous improvement |
| **FedRAMP** | US federal cloud workloads | NIST 800-53 controls; categorized as Low/Moderate/High based on impact |
| **NIST 800-53** | US federal information systems | The big catalog underlying FedRAMP and many others |
| **NYDFS Part 500** | NY-regulated financial institutions | CISO governance, MFA, encryption, incident reporting |

**The architectural takeaway**: pick the right primitives early. Tokenization, audit logging, encryption, secrets management, RBAC/ABAC — these aren't decoration; they're the structural moves that make compliance audits survivable rather than rebuilds.

### 5A.10 The agentic-system security overlay (cross-ref)

Most of this section applies directly to agent systems. A few additions that matter for AI workloads specifically:

- **Prompt injection** — adversarial input in retrieved content tries to hijack the model's instructions. Mitigations: treat retrieved content as untrusted, sanitize, use a separate critic agent, never let untrusted content reach the system prompt. (Agentic doc §8.2)
- **Tool-call sandboxing** — agents that execute code or call tools need sandboxing equivalent to executing user-provided code. Lambda, Firecracker, gVisor, E2B. (Agentic doc §6.7)
- **Memory poisoning** — adversarial turns write false facts to persistent memory. Mitigations: HITL on writes, provenance tagging, versioned writes. (Agentic doc §5)
- **Data exfiltration via tool calls** — an agent with access to sensitive data and an outbound tool can leak. Allowlist egress; classify tool-call outputs.
- **Model artifacts as classified material** — if fine-tuned on classified data, the weights may inherit that classification. (Interview prep §9.3)

These are all instances of the same security patterns applied to a new substrate. The agentic doc §9 ("Cleared / Restricted Environment Specifics") covers them in more depth.

### 5A.11 Real-world references and tools

- **OWASP Top 10** — the canonical list of application-security vulnerabilities. Updated periodically. If you've never read it, read it.
- **CIS Benchmarks** — concrete hardening guides per platform (Linux, Kubernetes, AWS). Best free starting point for "what does secure config look like."
- **NIST SP 800-63** — digital identity guidelines, including the part where SMS is no longer MFA-grade.
- **Google's BeyondCorp papers** — the canonical Zero Trust treatment.
- **Sairyss's *Secure by Design* references** in §1A — security as a structural property; ties §5A back to §1A.7.
- **Auth providers worth knowing:** Auth0, Okta, AWS Cognito, Clerk, WorkOS (B2B-focused), Stytch, Supabase Auth, Firebase Auth, Keycloak (OSS), Ory (OSS suite).
- **Policy / authorization engines:** OPA, AWS Cedar, Casbin, OpenFGA, SpiceDB, Permify, Ory Keto.
- **Secrets management:** HashiCorp Vault, AWS Secrets Manager + Parameter Store, GCP Secret Manager, Azure Key Vault, Doppler, 1Password Secrets Automation.

### 5A.12 Cross-refs
- **§1A.7 (illegal states, guarding vs validating)** — security as a structural property; input filtering at the boundary, invariant enforcement inside
- **§1B.6 (audit / observability tests)** — security and audit share infrastructure
- **§5 (Reliability patterns)** — circuit breaker, rate limiting, throttling are also security primitives (DDoS mitigation, abuse prevention)
- **§9 (Reference Architectures)** — every reference architecture has implicit security layering; make it explicit
- **Agentic doc §9 (Cleared environment specifics)** — security architecture applied to AI workloads in regulated settings

---

## 6. Evolution & Migration Patterns

How do you change a system that's already running with users on it? The patterns that distinguish "we shipped a rewrite" from "we shipped a rewrite without an outage."

### 6.1 Strangler Fig
**Shape:** Place a façade (proxy, gateway, router) in front of the old system. Build new functionality behind the façade as new services. Gradually migrate old functionality piece by piece. The old system "strangles" away as more traffic routes to the new one. Named after Martin Fowler's analogy to strangler fig trees.

**When to use:** Any migration of a running, customer-facing system. The alternative ("big bang rewrite") has a very long Wikipedia article titled "List of rewrites that ruined companies." Strangler fig is almost always safer.

**Real-world examples:**
- **eBay** — famously migrated from a Perl monolith to Java services using strangler fig over many years
- **Amazon's transition from monolith to services** (2002-onward) was a multi-year strangler-shaped migration
- **The Guardian** newspaper — well-documented strangler migration of their content platform
- Most "we moved off the legacy mainframe" stories that didn't end in disaster

**Watch out for:**
- **Permanent half-state** — the façade is supposed to be temporary. Often it isn't. Plan the deprecation milestones from the start; otherwise the legacy lives forever behind the proxy.
- **Façade as new monolith** — the façade itself can accumulate logic and become the new center of gravity. Keep it dumb.
- **Routing complexity** — which feature is on which side? Logging, observability, and clear ownership matter even more during migration than after.

### 6.2 Anti-Corruption Layer (extension)
**Shape:** When integrating with a legacy or external system whose model is hostile to yours, build a translation layer that converts between the two. The new system never speaks the old system's vocabulary directly.

**When to use:** Integrations with legacy systems, third-party SaaS, or any external system whose data model would corrupt yours if let in raw.

**Real-world examples:**
- DDD-style adapters that translate between legacy mainframe formats and modern microservices
- Many CRM integrations sit behind an ACL because Salesforce's data model rarely matches the internal one

**Watch out for:** ACL becomes a god-object. Same risk as strangler façades — without discipline, all the cross-system logic accumulates there.

### 6.3 Branch by Abstraction (extension)
**Shape:** Want to replace a component? Introduce an abstraction in front of it. Migrate callers to the abstraction. Build the new implementation behind the abstraction. Flip the switch. Remove the old. Different from strangler — that's at the system level; branch-by-abstraction is at the code level.

**When to use:** In-codebase refactors that are too big to do in one PR. Replacing an ORM, a logging library, a serialization layer.

**Real-world examples:** Pervasive technique in long-lived codebases. Trunk-based development workflows depend on it.

### 6.4 Parallel Run (extension)
**Shape:** Run the old system and the new system side by side on real traffic. Compare outputs. Don't cut over until you trust the new one. Then route reads to the new system; eventually retire the old.

**When to use:** High-stakes migrations where being wrong is unacceptable — pricing engines, ledger systems, fraud detection, anywhere "the new system gave a different answer" is a story your company will not survive.

**Real-world examples:**
- GitHub's Scientist library — purpose-built for parallel-run / shadow-traffic experiments
- Most payment-system migrations
- Migration patterns in any heavily-regulated domain (banking, healthcare, insurance)

**Cross-ref:** Same shape as **shadow-mode evaluation** in §6.5.4 of the agentic doc — log new-system output against the old system's results without surfacing to users, score post-hoc. Same pattern, different domain.

---

## 7. Optimization Patterns

The patterns whose job is "make it faster" or "make it cheaper" without changing what the system does.

### 7.1 Static Content Hosting / CDN
**Shape:** Separate static content (HTML, CSS, JS, images, videos, MP3s, downloads) from dynamic content. Serve static from a CDN — geographically distributed edge nodes that cache and deliver close to the user. Dynamic content stays on origin servers.

**When to use:** Almost every web-facing application. Static-content hosting is basically free correctness-wise and the wins are large.

**Real-world examples:**
- Cloudflare, Fastly, AWS CloudFront, Akamai — every CDN you've heard of
- Every Netflix video stream goes through their proprietary CDN (Open Connect)
- Every Spotify track, every YouTube video, every Wikipedia image

**Watch out for:**
- **Cache invalidation** — the hardest problem. When static content changes, how do edges know? Use cache-busting URLs (hash in filename); avoid relying on TTLs for "fresh content."
- **CORS / security headers** — easy to misconfigure when serving from a different domain. Test.
- **Cost on cache misses** — origin egress fees if cache miss rate is high. Misconfigured cache headers can multiply origin traffic.

### 7.2 Cache-Aside (Lazy Loading) (extension)
**Shape:** Application reads from cache; on miss, reads from DB and writes to cache; subsequent reads hit cache. The cache is "aside" the main data flow.

**When to use:** Read-heavy workloads with cacheable data. Default cache pattern most teams use.

**Real-world examples:** Redis / Memcached as session stores, query caches, computed-value caches in front of expensive DB operations. Used at virtually every large-scale web property.

**Watch out for:**
- **Cache stampede** — popular key expires, N concurrent requests all miss and stampede to the DB. Mitigate with locks, probabilistic early refresh, or stale-while-revalidate.
- **Stale data** — invalidation is hard. Either accept eventual consistency or wire writes to also invalidate the cache (write-through, see below).

### 7.3 Write-Through / Write-Behind Cache (extension)
**Shape:**
- **Write-through:** writes go to cache and DB synchronously
- **Write-behind:** writes go to cache immediately, DB is updated asynchronously

**When to use:** Write-through for consistency-critical reads. Write-behind for write-heavy workloads where eventual consistency is acceptable.

**Watch out for:** Write-behind loses data if the cache dies before flushing. Use only when that data loss is tolerable.

### 7.4 Read Replicas (extension)
**Shape:** Replicate the primary database to one or more read-only secondaries. Route read queries to replicas; writes to the primary. Same pattern as Controller-Responder (§1.5), narrower to databases.

**Real-world examples:** Standard pattern in Postgres, MySQL, MongoDB, every managed DB service. AWS RDS Multi-AZ is read-replica-shaped.

**Watch out for:** Replication lag — replicas trail the primary. Read-your-own-writes scenarios will see ghosts.

---

## 8. Deployment & Release Patterns

Worth its own short section. These are how patterns from §1–§7 actually reach production.

### 8.1 Blue-Green Deployment
**Shape:** Two production environments (Blue and Green), one live. Deploy to the inactive one, test, switch the router to point at it, retire the other. Instant rollback by switching back.

**Real-world examples:** Standard pattern in AWS (with Elastic Beanstalk, ECS, CodeDeploy support); GCP (with Cloud Run revisions); Kubernetes (with traffic-split controllers).

**Watch out for:** Database migrations that aren't backward-compatible — both Blue and Green need to coexist with the schema. Forward/backward-compatible migrations are mandatory.

### 8.2 Canary Deployment
**Shape:** Deploy the new version to a small percentage of traffic (1%, 5%, 10%). Monitor. If healthy, roll forward; if not, roll back.

**Real-world examples:** Google's standard deployment pattern; Netflix's Spinnaker has first-class canary support; most large-scale services do some form of this.

**Watch out for:** Need good observability to detect regressions in a small sample. Need metrics that are sensitive enough at low traffic but not so sensitive they false-positive.

### 8.3 Feature Flags
**Shape:** Wrap new functionality in a runtime flag. Deploy code with the feature off. Turn it on for some users via a control plane. Decouples deploy from release.

**Real-world examples:**
- LaunchDarkly, Split.io, Statsig — the SaaS players
- Open-source: Unleash, GrowthBook
- Every large engineering org has either bought one of these or built one

**Watch out for:**
- **Flag debt** — flags that should have been removed are still in the code. Process matters: every flag has an owner and an expiration date.
- **Combinatorial test surface** — N flags = 2^N possible configurations. Most aren't actually tested. Be honest about it.

### 8.4 Shadow / Mirror Traffic
**Shape:** Route real production traffic to both the old and new systems. Only the old system's response goes to the user. The new system's output is logged and compared. Same idea as Parallel Run (§6.4) but at the request layer rather than the service layer.

**Real-world examples:** Common at scale — Envoy, Istio, and most service meshes support shadow traffic natively. GitHub's Scientist mentioned earlier.

---

## 9. Putting it together — Reference Architectures

A few combinations of the above that recur often enough to be worth naming.

### 9.1 Classic SaaS Web App (Rung 1-2)
```
Browser → CDN (static) → API Gateway → Modular Monolith → Postgres (primary)
                                          │                    │
                                          └────→ Redis cache   └→ Read replicas
```
Patterns: Static Content Hosting, API Gateway, Modular Monolith, Cache-Aside, Read Replicas, Layered or MVC inside the monolith.

Real example: Most YC-stage startups. Stack Overflow at its scale. Basecamp. Shopify (at a much larger scale, but structurally the same shape).

### 9.2 Mature Microservices Platform (Rung 4)
```
                  ┌→ Auth Service ─→ Postgres-A
Browser/Mobile     ├→ Catalog Service → Postgres-B
 │                 ├→ Order Service ──→ Postgres-C ──→ Kafka (events)
 ▼                 ├→ Payment Service → Postgres-D ◄────┘
[CDN] → [API GW] → ├→ Search Service → Elasticsearch (replica from B+C)
                   └→ Notification Service ─→ SES/SNS
```
Patterns: Microservices, Database-per-Service, API Gateway, BFF, Pub-Sub (Kafka), CQRS (Search as read model), Saga (Order → Payment), Circuit Breaker between services, Service Mesh for cross-cutting concerns.

Real example: A simplified version of what most large e-commerce platforms run.

### 9.3 Event-Sourced Ledger System
```
Commands → Command Handler → Validate → Append to Event Store (immutable)
                                              │
                                              ├→ Projection: Balance View
                                              ├→ Projection: Transaction History
                                              └→ Projection: Audit Log
```
Patterns: Event Sourcing, CQRS, Pub-Sub, Materialized View, Outbox.

Real example: Bank ledgers, accounting systems, anything where the history matters as much as the current state. Git is structurally this shape.

### 9.4 Migration Architecture (in flight)
```
                    ┌─ NEW SERVICE (handles routes /api/v2/*)
Browser → Façade ───┤
                    └─ LEGACY MONOLITH (handles everything else)
                          │
                          └→ ACL → Old Mainframe DB
```
Patterns: Strangler Fig, Anti-Corruption Layer, Feature Flags (to control which routes go where), Parallel Run for risky cutover steps.

Real example: eBay's Perl-to-Java migration. Most "we moved off the mainframe" stories.

### 9.5 Agentic System (cross-ref to agentic doc)
The reference architecture in §8 of the agentic-frameworks doc maps onto patterns here:
- **Orchestrator** = stateful Layered or Hexagonal service
- **Agent-to-agent (A2A)** = Pub-Sub or Request-Reply between services
- **MCP tool layer** = Anti-Corruption Layer + API Gateway
- **Storage layer** = some mix of CQRS, Read Replicas, Materialized Views
- **HITL queues** = Saga with manual approval steps (Step Functions / Temporal)
- **Evaluation harness** = Shadow Traffic / Parallel Run

The agentic system isn't a new species of architecture — it's the same patterns with LLM nodes in places where logic nodes used to be.

---

## 10. Anti-Patterns to Avoid

The other side of the coin. These are the shapes that look fine in a diagram and bite you in production.

| Anti-pattern | What it is | Why it bites |
|---|---|---|
| **Distributed Monolith** | Microservices that must be deployed together; share a DB or hidden coupling | All the costs of distributed systems, none of the independence benefits |
| **God Service** | One service in a microservices architecture that knows everything | Replaces the monolith problem at a smaller scale; deployment bottleneck |
| **Shared Database** | Two services writing to the same schema | The schema is the coupling; you don't have services, you have facades on a monolith |
| **Synchronous Chains** | A → B → C → D, all blocking | Tail latency multiplies; cascading failures; capacity coupling |
| **Untimed Calls** | Network call without an explicit timeout | An outage in a downstream becomes a hang in upstream |
| **Premature Sharding** | Sharding before you need to | Irreversible; shard key mistakes are forever; you could have just bought a bigger box |
| **Optimistic Locking Everywhere** | Eventual consistency in places where ACID was fine | Subtle data corruption bugs; user confusion |
| **Microservices Before Modular Monolith** | Splitting services before learning where the boundaries are | The boundaries you pick will be wrong, and re-splitting services is expensive |
| **Pub-Sub for Replies** | Using async messaging for synchronous request-reply | Awkward, hard to debug, no natural timeout semantics |
| **Cache-as-Truth** | Treating the cache as the source of truth | Cache outage = data loss; cache stampedes; consistency bugs |
| **Flag Soup** | Hundreds of feature flags, no expiration discipline | Combinatorial test surface; nobody knows what's on for whom |
| **The 100% Test Coverage Lie** | Mistaking line coverage for confidence | The lines you don't cover are the ones that bite; coverage isn't testing |

**The common thread:** every anti-pattern in this list is a pattern from §1-§8 applied without naming the pillar (§0.5) it was supposed to optimize for. "We're using microservices" doesn't tell you what the system is optimized for; "we needed independent deploys per team" does.

---

## 11. Picking Patterns — A Practical Workflow

When you sit down to design a system, walk this in order. Don't skip steps.

1. **Name the pillar(s) you're optimizing for** (§0.5). Reliability? Maintainability? Cost? At least one will win, and you'll trade against it later.
2. **Pick a rung on the complexity ladder** (§0.7) and a primary paradigm (§0.8). Start as low as you can on the ladder; default to hybrid OO + FP with immutability where it doesn't cost you. The reason to go higher is *current named pressure*, not future flexibility.
3. **Pick a foundational structural pattern** (§1). Layered for CRUD. MVC for server-rendered web. **Hexagonal + DDD (§1A)** for rich domain logic that will be maintained long-term. Make sure the structure supports **testability** (§1B) from day one — refactoring for testability later is more expensive than designing for it upfront.
4. **Decide your data shape** (§3). Mostly transactional? ACID DB. Read-heavy and asymmetric? CQRS. History matters? Event Sourcing. Multi-tenant at scale? Maybe sharding, but probably read replicas first.
5. **Decide your communication shape** (§4). Synchronous request-reply by default; async pub-sub or events where decoupling is the goal.
6. **Layer in reliability and security patterns** (§5 + §5A). Every external call: timeout, retry with backoff, circuit breaker. Multi-tenant or multi-downstream: bulkhead. Pick auth model (RBAC/ABAC/PBAC/ReBAC) before the second feature ships; retrofitting authorization is painful. Don't wait for an outage or an incident to add either.
7. **Plan for evolution** (§6). How will you change this system in 18 months? If the answer is "rewrite," that's a smell — strangler-fig your way out.
8. **Plan deployment and hosting** (§8 + §2A). Blue-green or canary. Feature flags for risky changes. Shadow traffic for high-stakes. Pick the hosting model (on-prem / managed cloud / serverless) that fits the workload, not the trend.
9. **Plan observability before launch, not after.** Same point as the agentic doc — the observability surface is the control surface.

The two questions worth asking before any design decision:
- **What's the simplest thing that could possibly work?**
- **What's the failure mode I'm explicitly designing against?**

If you can't answer the second, you're not designing — you're decorating.

---

## 11A. Design Patterns Reference (GoF and Beyond)

Per §0.6, **design patterns** are the class/object-level patterns from the Gang of Four book and its descendants. They show up in code review, in coding interviews, and inside the architectural patterns above. They're not what you design a *system* with — they're what you write *classes* with. Included here as a reference catalog so the doc covers all three levels of abstraction.

Source: Gang of Four ("Design Patterns: Elements of Reusable Object-Oriented Software," Gamma/Helm/Johnson/Vlissides, 1994) plus Wikipedia's compiled list. The full GoF book is still worth owning; this table is the lookup card.

### 11A.1 Creational patterns — how objects are made

| Pattern | One-line intent | When you reach for it |
|---|---|---|
| **Singleton** | One instance, globally accessible | Shared config, connection pools, loggers. Famously overused; usually a smell |
| **Factory Method** | Defer object creation to a subclass / factory function | When the type to create depends on runtime conditions |
| **Abstract Factory** | Family of related objects created together | When products come in compatible families (e.g., Windows controls vs macOS controls) |
| **Builder** | Step-by-step construction of complex objects | When constructors have too many parameters; immutable objects with optional fields |
| **Prototype** | Create new objects by cloning an existing one | When construction is expensive and instances are similar |
| **Dependency Injection** | Pass dependencies in instead of constructing them | The substrate for testable code; the basis for Hexagonal Ports (§1A) |
| **Object Pool** | Reuse expensive objects instead of recreating | DB connections, threads, heavy graphics objects |
| **Lazy Initialization** | Delay creation until first use | Heavy resources you might not need |
| **RAII (Resource Acquisition Is Initialization)** | Tie resource lifetime to object lifetime | C++ memory management; file/socket handles; Python `with`, Java try-with-resources |

### 11A.2 Structural patterns — how objects compose

| Pattern | One-line intent | When you reach for it |
|---|---|---|
| **Adapter / Wrapper** | Translate one interface to another | Integrating third-party libraries; the same instinct as Anti-Corruption Layer at smaller scope |
| **Facade** | Simple front face over a complex subsystem | Hiding a tangled library behind one clean entry point |
| **Decorator** | Add responsibilities to an object dynamically | Adding logging, caching, retry to a function/object without subclassing |
| **Proxy** | Stand-in for another object, controlling access | Remote proxies, lazy-loading proxies, security proxies |
| **Composite** | Treat individual objects and compositions uniformly | Tree structures (file systems, GUI widgets, abstract syntax trees) |
| **Bridge** | Decouple abstraction from implementation so both can vary | When you have two orthogonal axes of variation |
| **Flyweight** | Share lightweight objects to avoid memory bloat | Character glyphs in a renderer, particles in a game engine |
| **Front Controller** | Single entry point routes requests | Web framework dispatch (Rails/Spring/Django all use this); related to API Gateway (§4.4) |
| **Module** | Group related code into a named unit | The unit at the heart of modular monolith (§2.2) |

### 11A.3 Behavioral patterns — how objects collaborate

| Pattern | One-line intent | When you reach for it |
|---|---|---|
| **Strategy** | Encapsulate interchangeable algorithms | Sorting comparators, retry strategies, payment-method handlers |
| **Observer / Pub-Sub** | One-to-many notification of state changes | UI event handling; the basis for Pub-Sub at system level (§4.1) |
| **Command** | Encapsulate a request as an object | Undo/redo; the basis for Command bus in DDD (§1A.5) |
| **State** | Object changes behavior based on internal state | State machines without giant switch statements |
| **Template Method** | Define algorithm skeleton; subclasses fill in steps | Framework hooks; lifecycle methods |
| **Iterator** | Sequential access to a collection without exposing its structure | Built into most languages now (`for...of`, iterators, generators) |
| **Chain of Responsibility** | Pass request through a chain of handlers until one handles it | Middleware pipelines (Express, ASP.NET); event bubbling |
| **Mediator** | Objects communicate through a central mediator instead of directly | UI dialogs; chat-room-style coordination |
| **Memento** | Capture and restore an object's state | Undo systems, snapshotting |
| **Visitor** | Add operations to a class hierarchy without changing the classes | Compilers, AST traversal |
| **Interpreter** | Define a language grammar and evaluator | DSLs, expression evaluators |
| **Specification** | Combinable boolean business rules as objects | Filtering, validation, querying — close cousin of DDD invariants |
| **Null Object** | Avoid null checks via a no-op default object | Removing `if (x != null)` boilerplate |
| **Fluent Interface** | Method chaining for a readable API | Query builders, builders, configuration DSLs |

### 11A.4 Concurrency patterns

| Pattern | One-line intent | When you reach for it |
|---|---|---|
| **Thread Pool** | Reuse a fixed set of threads for many tasks | Standard for any non-trivial concurrent work |
| **Producer-Consumer** | Decouple work creation from work execution via a queue | Async pipelines, message workers |
| **Read-Write Lock** | Allow concurrent reads, exclusive writes | High-read shared state |
| **Active Object** | Method execution decoupled from invocation, in its own thread | Actor-style concurrency (Akka, Erlang/Elixir processes) |
| **Reactor** | Async event loop dispatches I/O events to handlers | Node.js core; nginx; libuv |
| **Monitor Object** | Method-level mutual exclusion | Built into Java `synchronized`; C# `lock` |
| **Double-Checked Locking** | Reduce lock acquisition by checking first | Initialization of shared resources; notoriously easy to get wrong |
| **Lock-Free / CAS** | Compare-And-Swap atomic operations | High-performance concurrent data structures |

### 11A.5 When design patterns become a smell

Two persistent critiques worth knowing:

- **Peter Norvig's observation:** in dynamic languages (Lisp, Python, Smalltalk) about 16 of the 23 GoF patterns either disappear or become trivial language features. Many GoF patterns are workarounds for static-typed-OO language limitations. If you find yourself reaching for elaborate patterns in Python or Ruby, ask whether a closure, a higher-order function, or a metaclass would do the same job in two lines.
- **Over-engineering risk:** *FizzBuzzEnterpriseEdition* is the canonical joke implementation — solving FizzBuzz with 50 classes and every applicable pattern. It's funny because it's recognizable. The patterns are tools, not goals. Don't add a Factory just because you've named a class `WidgetFactory`.

The pragmatic rule: use a design pattern when **the absence** of the pattern is causing pain. Refactor toward patterns; don't design from them.

### 11A.6 Beyond GoF
GoF is the foundational catalog but not the last word. Worth knowing the major extensions:

- **Patterns of Enterprise Application Architecture** (Fowler, 2002) — Active Record, Data Mapper, Unit of Work, Identity Map, Service Layer, Repository. The vocabulary of server-side enterprise code.
- **Enterprise Integration Patterns** (Hohpe & Woolf, 2003) — Pipes and Filters, Message Channel, Translator, Aggregator. The vocabulary for messaging systems; still the standard reference for Kafka/RabbitMQ design.
- **Pattern-Oriented Software Architecture (POSA)** — multi-volume reference covering architectural patterns, concurrency patterns, networked-object patterns. POSA2 in particular is the concurrency reference.
- **Refactoring Guru** (https://refactoring.guru/design-patterns/catalog) — modern, visual, well-explained online catalog. The best free reference.

### 11A.7 Cross-refs
- **§0.6** — design patterns are the smallest of the three pattern levels; this section is for completeness, not for the architectural decisions the rest of the doc focuses on
- **§1A (DDD)** — Repository, Specification, Command are all design patterns reused as DDD building blocks
- **§4.1 (Pub-Sub)** — the architectural form of GoF's Observer pattern
- **§5.1 (Circuit Breaker)** — sometimes called a "design pattern" in older sources, but it's an architecture pattern by the §0.6 distinction

---

## 12. Source Index

| # | Source | Type | Why it's here |
|---|---|---|---|
| 1 | [14 software architecture design patterns to know](https://www.redhat.com/en/blog/14-software-architecture-patterns) — Vicki Walker, Red Hat | Reference article | The starting list for §1–§8 of this doc. All 14 are covered; extensions are flagged inline. |
| 2 | [Patterns of Enterprise Application Architecture](https://martinfowler.com/books/eaa.html) — Martin Fowler | Book | Canonical reference for layered, MVC, Data Mapper, Active Record, Service Layer. The vocabulary most architects share. |
| 3 | [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html) — Martin Fowler | Blog post | The naming source for the Strangler Fig pattern. Origin reference. |
| 4 | [Microservices Patterns](https://microservices.io/patterns/index.html) — Chris Richardson | Pattern catalog | The standard catalog for microservices-era patterns. Saga, CQRS, Outbox, Database-per-Service all have detailed entries here. |
| 5 | [Release It! (2nd ed.)](https://pragprog.com/titles/mnee2/release-it-second-edition/) — Michael Nygard | Book | The canonical reference for production-readiness patterns. Circuit Breaker was named here. |
| 6 | [Designing Data-Intensive Applications](https://dataintensive.net/) — Martin Kleppmann | Book | The reference for data patterns at scale — sharding, replication, consistency models, event-driven systems. |
| 7 | [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html) — Eric Evans / DDD community | Methodology | The vocabulary for bounded contexts, anti-corruption layers, hexagonal architecture. |
| 8 | [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic, Dec 2024 | Vendor framework | Cross-ref to agentic doc §4.5.1. Same "start simple, climb the ladder only when measurement shows it's needed" discipline applied to agent systems. |
| 9 | [12-Factor App](https://12factor.net/) — Adam Wiggins / Heroku | Methodology | The deployment/configuration discipline that underlies most modern app architecture. Not patterns per se but the substrate. |
| 10 | [The Software Architecture Handbook](https://www.freecodecamp.org/news/an-introduction-to-software-architecture-patterns/) — German Cocca, freeCodeCamp | Intro article | Accessible intro covering client-server, monolith/microservices, BFF, hosting models, folder structures. Source for the §2A hosting/scaling vocabulary. |
| 11 | [Sairyss/domain-driven-hexagon](https://github.com/Sairyss/domain-driven-hexagon) — Sairyss | Reference implementation + extended README | The deepest practitioner-grade treatment of DDD + Hexagonal + Clean + Secure-by-Design in one place. Source for most of §1A. Worth reading end to end. |
| 12 | [Software design pattern (Wikipedia)](https://en.wikipedia.org/wiki/Software_design_pattern) | Reference article | Establishes the design-pattern / architecture-pattern / architecture-style distinction (§0.6) and provides the GoF catalog for §11A. |
| 13 | [Design Patterns: Elements of Reusable Object-Oriented Software](https://en.wikipedia.org/wiki/Design_Patterns) — Gamma, Helm, Johnson, Vlissides (Gang of Four), 1994 | Book | The foundational design-pattern catalog. Source for §11A. |
| 14 | [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/) — Gregor Hohpe & Bobby Woolf, 2003 | Book + online catalog | The reference for messaging-system patterns. Still the standard for Kafka/RabbitMQ design. |
| 15 | [Refactoring Guru — Design Patterns Catalog](https://refactoring.guru/design-patterns/catalog) | Online catalog | Modern, visual, well-explained free reference for GoF patterns. The best lookup site. |
| 16 | [Implementing Domain-Driven Design](https://www.amazon.com/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577) — Vaughn Vernon, 2013 | Book | The practical companion to Evans's foundational DDD book. Worked examples in Java. Most referenced "how do I actually do DDD" book. |
| 17 | [Secure by Design](https://www.manning.com/books/secure-by-design) — Bergh Johnsson, Deogun, Sawano, 2019 | Book | Origin of "domain primitives," "always-valid domain model," "make illegal states unrepresentable." The security-as-structural-property treatment cited in §1A.7. |
| 18 | [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) — Robert C. Martin, 2012 | Blog post + book | The canonical "dependency direction inward" diagram. Closely related to Onion (Palermo) and Hexagonal (Cockburn). |
| 19 | [RBAC vs. ABAC vs. ACL vs. PBAC vs. DAC](https://www.strongdm.com/blog/rbac-vs-abac) — Maile McCarthy, StrongDM | Reference article | The starting taxonomy for §5A.3 authorization models. Extended in the doc with MAC and ReBAC. |
| 20 | [Working Effectively with Legacy Code](https://www.oreilly.com/library/view/working-effectively-with/0131177052/) — Michael Feathers, 2004 | Book | The canonical reference for **seams** and refactoring untestable code. Source for §1B.4. |
| 21 | [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html) — Martin Fowler | Article | The test-doubles taxonomy used in §1B.2. The vocabulary most testing literature shares. |
| 22 | [Boundaries](https://www.destroyallsoftware.com/talks/boundaries) — Gary Bernhardt, 2012 | Conference talk | Origin of "Functional Core, Imperative Shell" (§0.8.4, §1B.3). Watch this once if you haven't. |
| 23 | [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com/) — Freeman & Pryce, 2009 | Book | The TDD-as-design-discipline book. Pairs with Feathers for the testing reference set. |
| 24 | [Google Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/) — Pang et al., Google, 2019 | Paper | The paper that defined modern ReBAC. Source for §5A.3 ReBAC discussion. |
| 25 | [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) | Project + docs | The dominant externalized policy engine. The canonical example in §5A.4. CNCF graduated. |
| 26 | [BeyondCorp](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/) — Google, 2014 | Paper series | The canonical Zero Trust treatment. The model most modern enterprise security descends from. |
| 27 | [OWASP Top 10](https://owasp.org/www-project-top-ten/) | Standard / list | The canonical application-security vulnerability list. Read it if you haven't. |
| 28 | [Domain Modeling Made Functional](https://pragprog.com/titles/swdddf/domain-modeling-made-functional/) — Scott Wlaschin, 2018 | Book | The FP rebuild of DDD in F#. Worth reading even if you stay in OO; cited in §0.8.5. |
| 29 | [agentic-frameworks-knowledge-base.md](agentic-frameworks-knowledge-base.md) | Sibling doc | Cross-referenced throughout — agent stacks sit on top of the patterns in this doc. |

---

## 13. Open extensions / areas to deepen

Topics this doc gestures at but doesn't fully cover. Add as you encounter them.

- **Service Mesh patterns** (Istio, Linkerd, Consul) — sidecar pattern, mTLS, traffic policy, distributed tracing as infra rather than application code.
- **Event-Driven Architecture deep-dive** — Kafka topologies, CDC patterns (Debezium), event store schemas, streaming joins. Most teams hit ceilings on event-driven systems they didn't design for.
- **Multi-tenant patterns** — pool vs silo vs hybrid, per-tenant encryption, tenant routing, cross-tenant query patterns. Especially relevant for SaaS.
- **Data lakehouse / streaming-analytics patterns** — Delta Lake, Iceberg, Hudi; CDC into analytical stores; medallion architecture (bronze/silver/gold).
- **Frontend architecture patterns** — micro-frontends, module federation, SSR/SSG/ISR tradeoffs, the hydration problem.
- **Security architecture patterns** — zero-trust networking, secrets-management patterns, BeyondCorp shape, supply chain (SLSA, in-toto), least-privilege IAM in cloud.
- **Edge computing patterns** — CDN as compute (Cloudflare Workers, Lambda@Edge), location-aware routing, edge-DB patterns (Turso, Cloudflare D1).
- **AI/ML system patterns** — model-as-a-service, inference gateway (cross-ref agentic doc §2.9), feature stores, retraining pipelines, A/B testing on ML systems.
- **Cost architecture patterns** — chargeback/showback, tagging strategies, reserved-capacity vs on-demand vs spot, FinOps as a discipline.

The point of this doc, like its sibling, is to give your future self (and Claude in this project) a place to land when a design decision needs a reference. Add notes inline as you encounter new patterns; the index grows with your experience.
