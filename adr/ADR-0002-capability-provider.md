# ADR-0002 · Model/resource as a swappable Capability Provider

- **Status:** Accepted
- **Date:** 2026-07-22
- **Deciders:** architect (proposer) · principal (ratified)
- **Supersedes / Superseded by:** —

## Context

An agent built *around* one model fuses its identity to that model's quirks and its vendor's
lifecycle. When the model changes — a new version, a different provider, a move from cloud to a
sovereign local box — the agent breaks. Yet the system does not actually need a *specific model*; it
needs *capabilities*: reasoning, planning, execution, validation. Those capabilities can be supplied
by very different things: a local 7B model, a frontier API, a specialist agent, a rule engine, or a
human.

We also need the system to degrade honestly when a preferred provider is unavailable (no API key,
GPU busy, offline), and to respect *data sovereignty* (some data may not leave the box at all).

## Decision

We will express the system's needs as **Capabilities** and supply each through a swappable
**Capability Provider** (`name`, `provides`, `available()`, `invoke()`). A deterministic, auditable
**Router** selects a provider per request by a documented priority (hard constraints like
sovereignty first, then determinism, then cost/fit). Callers request a capability and never learn
which provider answered. A provider lacking prerequisites returns `available()=false` and is
**skipped silently**, not errored.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Capability Provider + Router | model-independent; graceful degradation; human-as-provider; sovereignty enforceable | indirection; a router to keep deterministic | **chosen** |
| B. Hard-wire one model | simplest today | breaks on every model change; no fallback; no sovereignty story | rejected — mortgages the future |
| C. Adapter per model, chosen at build time | some portability | no runtime fallback; no per-request routing (cost/sovereignty) | rejected — too static |

## Consequences

- **Positive:** a frontier model is a *provider upgrade*, not a rewrite; offline/keyless operation
  degrades honestly; sovereignty is a hard, enforceable constraint (spec capability-contract IN1);
  a human is representable as the highest-authority provider.
- **Negative:** the Router must be kept deterministic and inspectable, or the audit trail becomes
  fiction; per-request routing adds a small decision cost.
- **Neutral / follow-ups:** this is the mechanism that makes it *tempting* to drop governance when a
  strong provider is added — explicitly countered by ADR-0003 and docs §06 (governance tightens as
  the provider strengthens).

## Compliance

Enforced by spec capability-contract (RT1–RT4 deterministic, auditable, never-fabricate; AV1
skip-not-error; IN1 sovereignty). The reference `providers.py` ships a deterministic offline
provider so conformance can be tested without any network or key.
