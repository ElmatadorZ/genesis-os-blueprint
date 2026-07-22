# SPEC · Cognitive Kernel ABI — v0.2

Status: **Stable draft.** Normative. Framework- and language-agnostic.
Keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY** are used per RFC 2119.

This document specifies the contract between the Cognitive Kernel and a Cognitive Subsystem, and
the guarantees the kernel provides. An implementation *conforms to ABI v0.2* iff it satisfies every
**MUST** below. The reference implementation in `reference/genesis_kernel/` is the tie-breaking
oracle when this prose is ambiguous.

## 1. Data types

### 1.1 Event
```
Event {
    type      : string           # REQUIRED. Namespaced, e.g. "mission.plan", "chat.respond".
    payload   : map<string, any> # REQUIRED (MAY be empty).
    id        : string           # REQUIRED. Unique, stable for the life of the event.
    ts        : number           # REQUIRED. Unix seconds at creation.
    caused_by : string | null    # OPTIONAL. id of the event that produced this one (audit spine).
}
```
- An Event **MUST** be treated as immutable once created. A subsystem that needs to "change" an
  event **MUST** emit a new Event with `caused_by` set to the original's `id`.

### 1.2 Context
```
Context {
    budget_tokens : integer      # REQUIRED. Hard ceiling for the run.
    used_tokens   : integer      # REQUIRED. Monotonically non-decreasing.
    working_set   : map          # REQUIRED. The current working memory for the run.
    trace         : list<string> # REQUIRED. Append-only human-readable audit trail.
    spend(n) -> void             # REQUIRED. See §3.1.
}
```

### 1.3 Capability
An enum-like closed set. v0.2 defines: `REASONING`, `PLANNING`, `MEMORY`, `EXECUTION`,
`VALIDATION`, `GOVERNANCE`. Implementations **MAY** extend the set but **MUST NOT** redefine an
existing member's meaning.

### 1.4 Decision (see also policy-hook-contract.md)
```
Decision { allow : bool, reason : string, policy : string }
```

## 2. The Subsystem contract

A Subsystem **MUST** expose:
```
Subsystem {
    name        : string              # REQUIRED. Unique within a kernel instance.
    abi_version : string              # REQUIRED. The ABI it targets, e.g. "0.2".
    provides    : list<Capability>    # REQUIRED. MAY be empty.
    handle(event: Event, ctx: Context) -> Event | null   # REQUIRED.
    conforms_to(abi_version: string) -> bool             # REQUIRED.
}
```

Rules:
- **S1.** `conforms_to(v)` **MUST** return true only if the subsystem fully satisfies ABI version
  `v`. It **MUST** be a pure predicate (no side effects).
- **S2.** At registration the kernel **MUST** call `conforms_to(kernel.abi_version)` and **MUST**
  refuse to register the subsystem if it returns false. (Load-time gate — no partial conformance.)
- **S3.** `handle` **MUST NOT** perform an external side effect (filesystem, network, process)
  directly. It **MUST** instead request the effect by emitting an Event that the kernel routes to
  the Execution service behind `PRE_ACT`. (Separation of decision from action.)
- **S4.** `handle` **MUST** account for any non-trivial model/compute usage via `ctx.spend()`
  before performing it, and **MUST** propagate a `BudgetExceeded` rather than catching and
  continuing silently.
- **S5.** A Subsystem **MUST NOT** import or call another Subsystem directly. Subsystems compose
  only through the kernel (events). (No engine→engine dependencies.)
- **S6.** `handle` returning `null` signals "lifecycle complete for this event." Returning an Event
  signals "continue with this next event."

## 3. Kernel guarantees

An implementation of the kernel **MUST** provide:

- **K1 — Budget never overflows.** `Context.spend(n)` **MUST** raise `BudgetExceeded` when
  `used_tokens + n > budget_tokens`, and **MUST NOT** increment `used_tokens` in that case.
- **K2 — Nothing acts unpoliced.** Before invoking a subsystem for lifecycle stage *X*, the kernel
  **MUST** evaluate the hook for *X* (§policy-hook-contract) and **MUST NOT** invoke the subsystem
  if the combined Decision is deny.
- **K3 — Everything recorded.** For every event dispatched, every hook decision, and every outcome,
  the kernel **MUST** emit a Telemetry record. A dispatched event with no record is a conformance
  failure.
- **K4 — Deterministic routing.** Given identical Scheduling inputs, the kernel **MUST** route to
  the same subsystem/provider. Routing **MUST** be inspectable (recorded in trace).
- **K5 — Fail-closed dispatch.** If any part of the lifecycle raises unexpectedly, the kernel
  **MUST** terminate the run with an error outcome and a Telemetry record; it **MUST NOT** silently
  produce a "success" response.

### 3.1 `spend` semantics (normative)
```
spend(n):
    require n >= 0
    if used_tokens + n > budget_tokens:
        raise BudgetExceeded(requested=n, used=used_tokens, budget=budget_tokens)
    used_tokens += n
```

## 4. The lifecycle (normative order)

For a request the kernel **MUST** drive the following ordered stages, evaluating the named hook
*before* each stage and skipping the stage on deny:

1. `PRE_PLAN`  → **Planning** subsystem
2. `PRE_ACT`   → **Execution** subsystem
3. `PRE_VALIDATE` → **Validation** subsystem
4. `PRE_COMMIT` → **commit** (persist via Memory)
5. `PRE_RESPONSE` → **respond** (surface to Interface)

A conforming kernel **MAY** loop stages 1–3 for multi-step missions, but **MUST** evaluate the
corresponding hook on every iteration.

## 5. Versioning

- The ABI version is a string `MAJOR.MINOR`. A **MINOR** bump is backward-compatible (adds optional
  fields/capabilities). A **MAJOR** bump **MAY** break `conforms_to`.
- The kernel **MUST** expose its `abi_version`. Subsystems targeting a different **MAJOR** **MUST**
  fail S2.

## 6. Conformance checklist

An implementation is ABI-v0.2 conformant iff: S1–S6 hold for all subsystems; K1–K5 hold for the
kernel; the lifecycle order in §4 is honoured; and the reference `test_kernel.py` analogue passes
against the implementation. See `policy-hook-contract.md` and `capability-contract.md` for the two
companion contracts.
