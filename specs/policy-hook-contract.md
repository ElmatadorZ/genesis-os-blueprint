# SPEC · Policy Hook Contract — v0.2

Status: **Stable draft.** Normative. RFC 2119 keywords.

Specifies the Policy Hook Surface: the hook points, the Policy interface, and the three invariants
(most-restrictive-wins, fail-closed, fully audited). The reference is
`reference/genesis_kernel/hooks.py`.

## 1. Hook points

The closed set of lifecycle hook points for v0.2:

| HookPoint | Fires before | Cognitive stage |
|---|---|---|
| `PRE_PLAN` | goal decomposition | Planning |
| `PRE_ACT` | an action with outside effect | Execution |
| `PRE_VALIDATE` | correctness checking | Validation |
| `PRE_COMMIT` | persisting results durably | commit |
| `PRE_RESPONSE` | surfacing anything to the human | respond |

Implementations **MAY** add hook points but **MUST NOT** remove or reorder these, and **MUST**
keep each hook strictly *before* its stage.

## 2. The Policy interface

```
Policy {
    name  : string        # REQUIRED. Unique; appears in every Decision and audit record.
    point : HookPoint      # REQUIRED. The single hook this policy attaches to.
    evaluate(event: Event, ctx: Context) -> Decision   # REQUIRED. SHOULD be side-effect-free.
}

Decision { allow : bool, reason : string, policy : string }
```

- **P1.** `evaluate` **SHOULD** be a pure function of `(event, ctx)`. It **MUST NOT** perform an
  external mutation (it may *read* evidence to decide).
- **P2.** `evaluate` **MUST** populate `Decision.policy` with its own `name` and `Decision.reason`
  with a human-readable justification, for *both* allow and deny.

## 3. Combination rule — most-restrictive-wins

The kernel's Policy service, for a given `(point, event, ctx)`:

```
check(point, event, ctx) -> Decision:
    decisions = []
    for policy in policies_registered_at(point):        # in stable registration order
        d = safe_evaluate(policy, event, ctx)           # see §4 fail-closed
        record_audit(point, d)                          # §5 — ALWAYS, allow or deny
        decisions.append(d)
        if not d.allow:
            return d                                     # first deny is final (short-circuit OK)
    return Decision(allow=True, reason="all policies allowed", policy="*")
```

- **C1.** The combined result **MUST** be deny if *any* policy denies. There is no weighting,
  quorum, or override.
- **C2.** A hook with **no** registered policies **MUST** return allow (an empty surface permits;
  the *default* posture at an unpoliced point is permit, so safety comes from *registering*
  policies, never from implicit denial of un-hooked points). Designers **SHOULD** register at least
  one policy at every safety-relevant point.
- **C3.** Short-circuit on first deny is permitted, but every *evaluated* policy **MUST** still be
  audited (C2 of §5). Implementations **MAY** evaluate all policies for richer audit.

## 4. Fail-closed — the load-bearing invariant

```
safe_evaluate(policy, event, ctx) -> Decision:
    try:
        d = policy.evaluate(event, ctx)
        if d is not a well-formed Decision:
            return Decision(allow=False, reason="malformed decision", policy=policy.name)
        return d
    except any error / timeout:
        return Decision(allow=False, reason="policy error: <detail>", policy=policy.name)
```

- **F1.** Any exception, timeout, or malformed return from `evaluate` **MUST** yield **deny**.
- **F2.** A policy that cannot reach the data it needs to decide **MUST** deny (it **MUST NOT**
  guess "allow" to keep a feature working).
- **F3.** Fail-closed **MUST NOT** be disable-able by configuration. (No `fail_open=true`.)

## 5. Audit — every decision recorded

- **A1.** For every policy evaluated at a hook, the system **MUST** write an audit record
  containing at least: `point`, `policy`, `allow`, `reason`, `event.id`, timestamp.
- **A2.** The audit record **MUST** be written for **allow** as well as deny. ("Why did it refuse?"
  and "why did it permit?" are equally answerable.)
- **A3.** Audit records **MUST** be append-only. A missing record for an evaluated policy is a
  conformance failure, not a silent success.

## 6. Reference policies (informative)

Illustrative, not normative — the seed policies shipped in the reference:

| Policy | Point | Denies when |
|---|---|---|
| `gps2` | `PRE_PLAN` | goal exceeds budget or falls outside declared mandate |
| `shadow.fabrication` | `PRE_ACT` | the action's declared intent is to fabricate/forge evidence |
| `cvl.quality_gate` | `PRE_VALIDATE` | validation has not run / wrong gate for the work type |
| `warrant.cee_c1` | `PRE_COMMIT` | a belief would be persisted with no provenance chain |
| `disclosure.d1` | `PRE_RESPONSE` | a response would claim an outcome not backed by evidence |

## 7. Conformance checklist

Conformant iff: the five hook points exist and fire before their stages (§1); Policy exposes the
§2 interface; combination is most-restrictive-wins (C1–C3); fail-closed holds and is not
disable-able (F1–F3); and every evaluated decision is audited append-only (A1–A3).
