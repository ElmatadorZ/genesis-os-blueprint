# ADR-0001 · Adopt a Cognitive Kernel with a plugin ABI

- **Status:** Accepted
- **Date:** 2026-07-22
- **Deciders:** architect (proposer) · principal (ratified)
- **Supersedes / Superseded by:** —

## Context

Early agent code tends toward a "God object": one module that holds the prompts, the tool dispatch,
the memory, the control flow, and the safety checks, growing without bound. Such a system has no
seam at which to insert policy, no single place that owns the token budget, and no way to add a new
cognitive capability without editing the core. It also cannot state, of itself, which parts obey the
current design and which are legacy — so it cannot be migrated safely.

We need a structure where (a) cognition is decomposed into replaceable parts, (b) there is exactly
one place that owns the scarce/dangerous resources (budget, the right to act, the shared truth), and
(c) conformance to the contract is checkable, not aspirational.

## Decision

We will introduce a **Cognitive Kernel** that owns the event spine, the context/token budget, the
scheduler, and nine kernel services, and exposes a small **ABI** (`name`, `abi_version`, `provides`,
`handle`, `conforms_to`) that Cognitive Subsystems plug into. **Conformance is gated at load time:**
a subsystem whose `conforms_to(kernel.abi_version)` is false does not register.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Cognitive Kernel + plugin ABI | single point for budget/policy/audit; subsystems replaceable; conformance checkable | up-front structure; migration cost for legacy code | **chosen** |
| B. Keep the monolith, add checks inline | no refactor now | safety doesn't compose; no budget owner; unbounded growth | rejected — defers the problem and compounds it |
| C. Microservices per subsystem | strong isolation | huge operational overhead for a single-node cognitive OS; latency across the lifecycle | rejected — wrong weight class |

## Consequences

- **Positive:** one place owns the budget (K1) and the policy surface (K2); subsystems are
  single-responsibility and hot-swappable; the system can report its own conformance status
  (`migrated / legacy / planned`), making a strangler-fig migration honest.
- **Negative:** existing "God object" code must be migrated behind the ABI incrementally; there is a
  real transition period where both conforming and legacy paths coexist.
- **Neutral / follow-ups:** the ABI is versioned (`MAJOR.MINOR`); a **MAJOR** bump may break
  `conforms_to` and requires a migration note.

## Compliance

Enforced by the load-time gate (spec kernel-abi §S2) and by the reference conformance tests
(`reference/tests/test_kernel.py`): a non-conforming subsystem must fail to register, and the
kernel guarantees K1–K5 must hold.
