# Reference implementation — `genesis_kernel`

A **runnable, dependency-free** (standard-library-only) reference for the architecture described in
[`../docs`](../docs) and specified in [`../specs`](../specs). It exists to be *read* and to be the
*conformance oracle* — when your own implementation disagrees with a spec on a lifecycle or
fail-closed question, this code is the tie-breaker.

## Run it

```bash
cd reference
python examples/run_mission.py     # end-to-end tour + full audit trace
python tests/test_kernel.py        # deterministic, offline conformance checks
# or, with pytest installed:
python -m pytest
```

No API key, no network, no GPU. The reference ships a deterministic offline `EchoProvider` in place
of a model, so the whole thing runs anywhere Python 3.9+ runs.

## What the demo shows

`examples/run_mission.py` runs five things and prints why each decision was made:

| Demo | Proves |
|---|---|
| Mission A — legitimate audit | the full lifecycle: `PRE_PLAN → PRE_ACT → PRE_VALIDATE → PRE_COMMIT → PRE_RESPONSE` |
| Reality Grading | a hypothesis is graded against the workspace (evidence), producing a Validated Episode |
| Mission B — fabrication attempt | `shadow.fabrication` denies at `PRE_ACT` (never-fabricate, mechanised) |
| Mission C — over-budget goal | `gps2` denies at `PRE_PLAN` (budget never overflows) |
| Mission D — write under read-only mandate | `gps2` denies at `PRE_PLAN` (mandate enforced) |
| Capability routing | a `sovereign` request skips a provider that leaves the box |

## Package map

| File | Role | Spec |
|---|---|---|
| `genesis_kernel/abi.py` | core types: `Event`, `Context` (budget), `Subsystem`, `Decision` | [kernel-abi](../specs/kernel-abi.md) |
| `genesis_kernel/kernel.py` | the Cognitive Kernel — drives the lifecycle, K1–K5 | kernel-abi §3–4 |
| `genesis_kernel/hooks.py` | Policy Hook Surface — most-restrictive-wins, fail-closed, audited | [policy-hook-contract](../specs/policy-hook-contract.md) |
| `genesis_kernel/policies.py` | the seed policies (`gps2`, `shadow.fabrication`, …) | policy-hook-contract §6 |
| `genesis_kernel/providers.py` | Capability Provider + deterministic Router + `EchoProvider` | [capability-contract](../specs/capability-contract.md) |
| `genesis_kernel/reality_grading.py` | stake hypothesis → grade vs evidence → Validated Episode | [docs §05](../docs/05-reality-grading-loop.md) |
| `genesis_kernel/telemetry.py` | the audit spine — `explain()` renders the whole trace | kernel-abi K3 |
| `genesis_kernel/subsystems/` | Planning, Execution, Validation, Memory, Governance | [docs §01](../docs/01-layered-architecture.md) |

## How to extend it

- **Plug in a real model:** write a `CapabilityProvider` whose `invoke` calls your model, set
  `leaves_box`/`deterministic` honestly, and `kernel.register_provider(...)` it *before* the
  `EchoProvider`. Everything above is untouched — that is the whole point of the provider model.
- **Add a subsystem:** subclass `Subsystem`, implement `handle`, keep `abi_version = "0.2"`, and
  `register_subsystem`. A wrong `abi_version` is refused at registration, by design.
- **Add a policy:** subclass `Policy`, pick a `point`, return a `Decision`. Registering it can only
  make the system more careful (most-restrictive-wins).

## A note on scope

This is a *reference*, not a production framework. It favours legibility over performance and
completeness — the persistence is a dict, the "model" is deterministic, the Outcome Clock fires
inline. The value is the shape of the contracts, not the throughput. See the warranty disclaimer in
[`../LICENSE`](../LICENSE).
