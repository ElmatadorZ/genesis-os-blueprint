# 07 · Glossary

Terms of art used throughout the blueprint, in one place. Where a term has a home chapter, it is
linked.

### ABI (Kernel ABI)
The stable structural contract a subsystem must satisfy to plug into the Cognitive Kernel — `name`,
`abi_version`, `provides`, `handle()`, `conforms_to()`. Conformance is a **load-time gate**, not a
warning. → [§02](02-cognitive-kernel-abi.md)

### Abstain
A judge verdict meaning "not enough evidence to decide." Rendered as an honest "no data yet,"
**never** as a fake zero. → [§05](05-reality-grading-loop.md)

### Belief Revision
The automatic lowering of confidence in a belief when reality refutes a hypothesis that belief
predicted. Attributed to `Reality (outcome)`. Corrigibility, mechanised. → [§05](05-reality-grading-loop.md)

### Capability
A cognitive faculty the system needs (`REASONING`, `PLANNING`, `MEMORY`, `EXECUTION`, `VALIDATION`,
`GOVERNANCE`) — distinct from *who* supplies it. → [§04](04-capability-provider-model.md)

### Capability Provider
Anything that can supply a capability: a local model, a frontier API, a specialist agent, a rule
engine, or a human. Exposes `available()` and `invoke()`. → [§04](04-capability-provider-model.md)

### Cognitive Kernel
The core layer that owns the event spine, the token budget, the scheduler, and the ABI, and
guarantees budget-never-overflows, nothing-acts-unpoliced, everything-recorded. → [§02](02-cognitive-kernel-abi.md)

### Cognitive Subsystem
A single-responsibility "thinking part" (Memory, Planning, Validation, Execution, Governance) that
conforms to the ABI. Receives an `Event` + `Context`, returns an `Event` or `None`. → [§01](01-layered-architecture.md)

### Constitution
The system's governing rules: registered policies, ABI version, active judge, ownership rules,
standing orders. Amends only by ceremony. → [§06](06-governance-and-constitution.md)

### Context
The kernel object that owns the **token budget** and carries the working set; guarantees the model's
context window cannot silently overflow via `spend()`. → [§02](02-cognitive-kernel-abi.md)

### Evidence Normalization
The rule that a provider's *assertion* is not evidence; only the filesystem and ledger are. The
judge reads reality, never the model's claim of success. → [§05](05-reality-grading-loop.md)

### Fail-closed
The invariant that an error, timeout, or missing datum in a policy evaluation results in **deny**,
never allow. → [§03](03-policy-hook-surface.md)

### Hypothesis
A falsifiable, checkable prediction about the state of the world that a completed mission stakes, in
place of a self-declared "success." → [§05](05-reality-grading-loop.md)

### Judge (versioned)
The grader that checks a hypothesis against evidence. Versioned (`rg-1`, `rg-2`, …); the version is
pinned into each hypothesis at stake time; upgrades carry a Migration Note. → [§05](05-reality-grading-loop.md)

### Migration Note
The required companion to any judge-version change, explaining what changed and why — because
altering how "success" is graded is a governed act, not a bare version bump. → [§05](05-reality-grading-loop.md) / [§06](06-governance-and-constitution.md)

### Most-restrictive-wins
The rule for combining multiple policies at a hook: **deny if any policy denies.** Makes new safety
policies monotonic. → [§03](03-policy-hook-surface.md)

### Observed Phenomenon
Something the system *did* that is recorded but not yet judged as needing a fix — tagged *recurring /
contextual / incidental*. Contrast "bug" (already known wrong). → [§06](06-governance-and-constitution.md)

### Outcome Clock
The mechanism that fires at a hypothesis's horizon to trigger grading with zero human
intervention. → [§05](05-reality-grading-loop.md)

### Policy Hook Surface
The row of lifecycle hooks (`PRE_PLAN`, `PRE_ACT`, `PRE_VALIDATE`, `PRE_COMMIT`, `PRE_RESPONSE`)
where policies vote allow/deny before each cognitive step. → [§03](03-policy-hook-surface.md)

### Principal
The human who holds final authority — the source of mission and intent, and the only party who may
ratify a constitutional amendment. Never "a resource to be routed." → [§06](06-governance-and-constitution.md)

### Provenance Graph
The single canonical store in which every belief is reachable backward to the events that produced
it (forward + reverse trace). → [§05](05-reality-grading-loop.md) / [§06](06-governance-and-constitution.md)

### Sovereignty (of data)
A routing constraint meaning data may not leave the box; a `sovereign` request is **blocked** from
cloud providers, not merely dispreferred. → [§04](04-capability-provider-model.md)

### Standing Order
A durable governance directive, e.g. "observation precedes optimization" — freezing architectural
change during an evidence-gathering window, integrity fixes excepted. → [§06](06-governance-and-constitution.md)

### State Ownership Principle
"There is one canonical store of truth; every other store is a read-only projection over it, never a
second source." Enforced by a tripwire. → [§06](06-governance-and-constitution.md)

### Tripwire
A CI-style check that fails the build when an architectural invariant is violated (e.g. an
unsanctioned new state store), moving discipline from human diligence into the build. → [§06](06-governance-and-constitution.md)

### Validated Episode
The immutable record written when a hypothesis is confirmed, carrying the artifact hash and the
judge version at stake time. → [§05](05-reality-grading-loop.md)

### The load-bearing law
> **Capability must never outrun accountability.** The reason governance *tightens* as the model
> *strengthens*, never the reverse. → [§00](00-overview.md) / [§06](06-governance-and-constitution.md)
