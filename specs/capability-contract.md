# SPEC · Capability Provider Contract — v0.2

Status: **Stable draft.** Normative. RFC 2119 keywords.

Specifies how a capability is requested and how a provider supplies it, so that *who* answers a
cognitive request is swappable without changing the caller. Reference:
`reference/genesis_kernel/providers.py`.

## 1. Capabilities

The closed v0.2 set (see kernel-abi §1.3): `REASONING`, `PLANNING`, `MEMORY`, `EXECUTION`,
`VALIDATION`, `GOVERNANCE`. A request names *one* capability.

## 2. The Provider interface

```
CapabilityProvider {
    name      : string                 # REQUIRED. Unique; recorded in every result + audit.
    provides  : list<Capability>       # REQUIRED. Non-empty.
    available() -> bool                # REQUIRED. See §3.
    invoke(capability: Capability, request: Request) -> Result   # REQUIRED. See §4.
}

Request { capability, payload : map, constraints : Constraints }
Result  { ok : bool, output : any, provider : string, meta : map }
Constraints { sovereign : bool, deterministic : bool, max_cost : number|null, ... }
```

- **PR1.** `available()` **MUST** be cheap and side-effect-free. It answers "could I serve a request
  right now?" (key present, GPU free, human on-call).
- **PR2.** A provider **MUST** only accept `invoke` for a capability in its `provides`.
- **PR3.** `Result.provider` **MUST** equal the provider's `name`. (No anonymous results — every
  answer is attributable.)

## 3. Availability gating

- **AV1.** A provider whose prerequisites are absent (missing key, offline, no capacity) **MUST**
  return `available() = false` and **MUST** be **skipped silently** by the router — *not* treated
  as an error. (A missing optional provider is not a failure.)
- **AV2.** `available() = true` **MUST NOT** be assumed to guarantee `invoke` success; `invoke` may
  still fail and **MUST** then return `Result.ok = false` with a reason in `meta`.

## 4. Invocation

- **IN1.** `invoke` **MUST** honour `Constraints.sovereign`: a provider that would move data off the
  box **MUST** refuse (return `ok=false`) a `sovereign=true` request rather than serve it. Sovereign
  data being blocked from a cloud provider is a *hard* constraint, not a preference.
- **IN2.** When `Constraints.deterministic = true`, a provider that cannot guarantee a reproducible
  result **SHOULD** return `available()=false` for that request (so the router picks a deterministic
  peer) rather than serve a non-reproducible answer into a grading path.
- **IN3.** `invoke` **MUST NOT** silently substitute a different capability than requested.

## 5. The Router

```
route(request) -> Result:
    for provider in providers_ordered_by_policy(request.capability):   # DETERMINISTIC order
        if request.capability not in provider.provides:  continue
        if not provider.available():                     continue      # skip, not error (AV1)
        if violates(provider, request.constraints):      continue      # e.g. sovereignty (IN1)
        result = provider.invoke(request.capability, request)
        record_routing(request, provider, result)                      # audit which + why
        if result.ok:  return result
    return Result(ok=False, output=None, provider="*", meta={"reason": "no provider could serve"})
```

- **RT1.** Provider ordering **MUST** be deterministic and inspectable. Given identical inputs, the
  router **MUST** try providers in the same order. (Determinism of routing is required for a
  truthful audit trail — see kernel-abi K4.)
- **RT2.** The router **MUST** record which provider was chosen and why (or why each was skipped).
- **RT3.** When no provider can serve, the router **MUST** return an explicit failure. It **MUST
  NOT** fabricate a result. (Mirrors the Reality Grading anti-fabrication rule.)
- **RT4.** Ordering policy **SHOULD** consider, in a documented priority: sovereignty/hard
  constraints first, then determinism if required, then cost/latency, then capability fit.

## 6. Human-as-provider (informative)

A human **MAY** be modelled as a `CapabilityProvider` (typically for `GOVERNANCE` or a high-stakes
`EXECUTION`): `available()` reflects on-call status; `invoke` blocks on human input. This is how the
architecture keeps a human *in authority* while treating their participation with the same uniform
interface as any other provider — the human is the highest-authority provider, never a routed
resource. See docs §04 and §06.

## 7. Conformance checklist

Conformant iff: Provider exposes the §2 interface with attributable results (PR1–PR3); availability
gating skips-not-errors (AV1–AV2); invocation honours sovereignty and determinism and never
substitutes capabilities (IN1–IN3); and the router is deterministic, auditable, and never fabricates
(RT1–RT4).
