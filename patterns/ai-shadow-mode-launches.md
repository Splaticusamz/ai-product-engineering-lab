# AI Shadow-Mode Launches

Use this pattern when an AI workflow is close to useful but should not touch the user experience, customer data, or operational state yet: routing recommendations, support-draft triage, catalogue grouping, lead scoring, content QA, or autonomous admin suggestions. The goal is to run the AI path beside the trusted path long enough to measure decision quality without pretending a demo is production readiness.

## Problem

AI product teams often choose between two bad launch shapes: hide the feature in an internal demo forever, or put a model-generated decision directly in front of users after a few hand-picked examples. Shadow mode creates a third path. The current workflow remains authoritative while the AI workflow produces a parallel decision, explanation, confidence signal, and evidence packet for review.

A good shadow-mode run answers one question: if this AI path had been live, would it have helped, stayed harmless, or created cleanup work?

## Required fields

Each shadow-mode candidate should be logged with enough structure to compare it against the real outcome later.

| Field | What it captures | Example |
| --- | --- | --- |
| `workflow_step` | The product moment being shadowed. | `incoming event categorization` |
| `trusted_decision` | The existing human, rule, or system result. | `marked as family-friendly local event` |
| `ai_decision` | The parallel AI result, including abstentions. | `category: community; confidence: 0.62` |
| `evidence_used` | Inputs the model actually relied on. | `title, venue, date, scraped description` |
| `delta` | Whether the AI matched, improved, missed, or overreached. | `matched category but invented venue capacity` |
| `review_action` | What a reviewer did with the delta. | `accept category; reject unsupported capacity claim` |
| `promotion_gate` | The condition required before live use. | `95% safe-match rate across 100 recent items` |

## Default flow

1. Pick one narrow workflow step where the trusted path already exists.
2. Define what the AI is allowed to output and what it must abstain from deciding.
3. Run the AI path in parallel without mutating records, notifying users, sending messages, or changing rankings.
4. Store only public-safe or internally approved review fields: IDs, normalized labels, evidence snippets, and reviewer outcomes.
5. Compare AI decisions against the trusted decision and tag the delta as `match`, `helpful_disagreement`, `unsafe_disagreement`, or `unsupported_claim`.
6. Review a fixed sample on a recurring cadence before tuning prompts or thresholds.
7. Promote only the smallest safe behavior first, usually draft suggestions or reviewer-prioritized queues rather than direct automation.

## Good default UX

- Label shadow outputs as `not live` so reviewers do not confuse them with production state.
- Show the trusted decision and AI decision side by side, not in separate dashboards.
- Put the evidence under the AI decision; reviewers should not have to hunt for why the model chose something.
- Include an `abstained correctly` state. Refusing to decide can be a success signal.
- Let reviewers convert a bad shadow result into a fixture while the context is fresh.

## Cheap validators that pay off

- **mutation guard:** assert the shadow job writes only to a shadow table, log, or fixture file.
- **unsupported-claim check:** fail outputs that introduce facts not present in the allowed evidence fields.
- **abstention check:** include empty, ambiguous, and low-context cases where the correct behavior is no decision.
- **threshold drift check:** compare promotion metrics by segment so one easy category does not hide failures in another.
- **review-load check:** measure how many AI deltas require human cleanup; a high apparent accuracy rate is not enough if every miss is expensive.

## Promotion criteria

Shadow mode is ready to become a live assistive feature when:

- the AI path has been evaluated on recent, unhandpicked traffic,
- unsafe disagreements and unsupported claims are below the agreed threshold,
- abstentions are visible and treated separately from failures,
- reviewers can trace every recommendation to allowed evidence,
- rollback is a configuration change, not a data repair project,
- the first live version keeps a human approval or undo path for consequential actions.

## Anti-patterns

- Calling a feature shadow-mode when the AI output already changes ranking, routing, messaging, or persisted user-visible state.
- Measuring only agreement with the existing workflow when the real opportunity is useful disagreement.
- Hiding abstentions because they make the model look less confident.
- Promoting a broad autonomous agent when only one narrow decision has earned trust.
- Reviewing aggregate accuracy without inspecting the cleanup cost of the worst misses.
