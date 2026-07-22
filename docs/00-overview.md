# 00 · Overview — the 10-minute tour

This document is the front door to the architecture. Read it, and you will know what every
other document is *for*.

## The one-sentence version

> A layered cognitive OS in which **subsystems are plugins behind a stable kernel ABI**, every
> action passes a **fail-closed policy surface**, the **model is a swappable provider**, and every
> mission is **graded against reality, not against its own claims.**

## The problem it solves

An autonomous agent is a machine that takes actions in the world on your behalf. Two failure
modes matter more than any other:

1. **It does the wrong thing** — acts outside its mandate, or takes an irreversible step nobody
   authorised.
2. **It lies about what it did** — reports success it did not achieve, so you cannot trust its
   own account and cannot learn from it.

Capability-first frameworks make failure mode #1 *more* likely (more tools, more autonomy) and do
nothing about #2 (the system's self-report is taken at face value). This architecture attacks
both directly:

- Failure mode #1 is contained by the **Policy Hook Surface** (§03): nothing happens without an
  explicit, audited, fail-closed *allow*.
- Failure mode #2 is contained by the **Reality Grading Loop** (§05): a mission's success is
  decided by observable evidence, never by the model saying "done."

## The five things to understand, in order

### 1. It is layered, and the layers are contracts (→ [§01](01-layered-architecture.md))
Interface → OS Core → Cognitive Kernel → Policy Hook Surface → Cognitive Subsystems → Runtime
Kernel → Hardware. Each layer talks to its neighbours through a defined interface, so you can
replace any one layer — swap the UI, swap the model runtime, add a new subsystem — without
touching the others.

### 2. The Cognitive Kernel is a real kernel (→ [§02](02-cognitive-kernel-abi.md))
It does what an OS kernel does, for cognition instead of processes: it owns the **event bus**,
the **context/token budget** (so no single step can blow the model's context window), the
**scheduler** (which routes work to the right subsystem), and it exposes a stable **ABI** that
subsystems plug into. A subsystem either *conforms to the ABI* or it does not load.

### 3. Every action crosses the Policy Hook Surface (→ [§03](03-policy-hook-surface.md))
Between "the agent wants to do X" and "X happens" there is always a hook: `PRE_PLAN`, `PRE_ACT`,
`PRE_VALIDATE`, `PRE_COMMIT`, `PRE_RESPONSE`. Policies at each hook return allow/deny. The rules
are simple and strict: **most-restrictive-wins**, **fail-closed** (an error denies), and **every
decision is written to an audit log.** This is where "capability must not outrun accountability"
becomes literal code.

### 4. The model is a Provider, not a dependency (→ [§04](04-capability-provider-model.md))
The system needs *capabilities* — reasoning, planning, execution — not a specific model. A
**Capability Provider** supplies a capability; a local 7B model, a frontier API, a specialist
agent, or a human can all be providers of "reasoning." The router picks a provider; the rest of
the system never knows or cares which one answered. This is what makes the architecture outlive
any single model generation.

### 5. Missions are graded against reality (→ [§05](05-reality-grading-loop.md))
When a mission completes, it does not get to declare victory. It **stakes a hypothesis** ("the
report file will exist at path P with content C"), and a versioned judge grades that hypothesis
against the **filesystem and ledger**. If reality disagrees, a belief is revised — and the whole
chain, from event to graded belief, is traceable. Honesty stops being a virtue you hope for and
becomes a property you measure.

Holding all five together is **[Governance & the Constitution](06-governance-and-constitution.md)**:
the rules themselves change only by ceremony — an agent may propose an amendment, only the human
principal may ratify it — and tripwires make drift structurally impossible.

## The load-bearing law

Every mechanism above exists to serve one rule:

> **Capability must never outrun accountability.**

The trap this guards against is subtle: the day you plug in a much stronger model, a voice says
"the grading, the ceremony, the audit — we don't need those anymore, the model is smart now."
That is exactly backwards. A weak model under strong governance is slow but safe; a strong model
under weak governance is fast but dangerous. **As the engine strengthens, the governance
tightens — never the reverse.**

## Where to go next

- Want the shape of the system? → [§01 Layered Architecture](01-layered-architecture.md)
- Want to implement it? → [`specs/`](../specs/) has the framework-agnostic contracts.
- Want to see it run? → [`reference/examples/run_mission.py`](../reference/examples/run_mission.py)
- Lost on a term? → [§07 Glossary](07-glossary.md)
