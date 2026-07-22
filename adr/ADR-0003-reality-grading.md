# ADR-0003 · Grade missions against reality, not self-report

- **Status:** Accepted
- **Date:** 2026-07-22
- **Deciders:** architect (proposer) · principal (ratified)
- **Supersedes / Superseded by:** —

## Context

If a system's learning loop rewards the model's *self-reported* success, it trains the model to
*look* successful rather than to *be* honest — because a confident false "done" is rewarded exactly
like a true one. Over time this selects for plausible fabrication. We want the opposite: a system
that is sometimes willing to report "I failed," and that only earns reward when reality confirms the
outcome. This requires that success be decided by observable evidence, and that the grader be
insulated from the model's claims.

## Decision

We will require a completed mission to **stake a falsifiable hypothesis** (a concrete, checkable
prediction with an evidence query, a pinned **judge version**, and a horizon) instead of declaring
success. A versioned judge grades the hypothesis against **evidence** (filesystem + ledger) under
the discipline of **Evidence Normalization**: *a provider's assertion is never evidence.* Confirmed
hypotheses produce an immutable **Validated Episode** (artifact hash + judge version); refuted ones
trigger a **Belief Revision** attributed to `Reality (outcome)`; insufficient data yields an honest
**abstain** ("no data yet"), never a fake zero. The judge version is pinned at stake time; upgrading
the judge requires a Migration Note through the governance ceremony.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Stake hypothesis, grade vs evidence | trains honesty; auditable; corrigible; immutable history | requires an evidence query per mission; deferred grading (Outcome Clock) | **chosen** |
| B. Trust the model's self-report | trivial | trains fabrication; unauditable; no learning integrity | rejected — actively harmful |
| C. Human grades everything manually | high quality | does not scale; not zero-intervention; inconsistent | rejected — but humans remain the judge-of-last-resort via governance |

## Consequences

- **Positive:** honesty becomes a measured property, not a hope; the system can change its mind when
  reality disagrees (mechanised corrigibility); every belief traces back to evidence; fabrication
  cannot survive grading, reinforcing the `PRE_ACT` anti-fabrication policy.
- **Negative:** each mission must express a checkable hypothesis (some outcomes are hard to make
  falsifiable); grading is deferred to a horizon, so feedback is not instant.
- **Neutral / follow-ups:** the judge is versioned and will improve (`rg-1 → rg-2 …`); changing it is
  a governed act (Migration Note), because it silently redefines "success."

## Compliance

Enforced by the reference `reality_grading.py` (Evidence Normalization: the judge reads the
filesystem/ledger, not claims) and by the governance rule that judge changes carry a Migration Note
(docs §06). The `PRE_RESPONSE` disclosure policy additionally forbids surfacing a claimed outcome
that evidence does not back.
