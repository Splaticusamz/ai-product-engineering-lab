# Context Pack Design

Use this pattern when an AI feature, agent, or eval needs a repeatable way to pass product context into a model. The goal is to make context explicit, bounded, and reviewable instead of hiding it inside a prompt string.

## Problem

Many AI product bugs are context bugs: the model sees stale notes, too much irrelevant retrieval, missing user intent, or instructions that conflict with the UI. When the context is assembled ad hoc, failures are hard to reproduce and harder to improve.

A context pack turns the model input into a small product artifact with named sections, budgets, and provenance.

## Pack shape

| Section | What it contains | Product reason |
| --- | --- | --- |
| User goal | The current task in the user's words, plus the requested output shape. | Keeps the model optimizing for the visible job, not the background workflow. |
| Hard constraints | Non-negotiable rules: side-effect limits, format, privacy boundaries, budget, or deadline. | Separates requirements from helpful hints. |
| Source facts | Retrieved records, file excerpts, URLs, command output, or database rows with stable ids. | Gives the reviewer a way to trace claims back to evidence. |
| Working memory | Short-lived decisions from the current session. | Prevents repeated clarification without polluting durable memory. |
| Exclusions | Known irrelevant, stale, or unsafe context that should not be used. | Reduces accidental anchoring on nearby but wrong material. |
| Output contract | Schema, required headings, max length, approval state, or next-action format. | Makes cheap validation possible before the output reaches a user. |

## Minimal schema

```json
{
  "goal": "Draft a support reply that explains the refund policy in plain language.",
  "constraints": ["Do not send automatically", "Cite the policy source"],
  "sources": [
    {"id": "policy/refunds#v3", "kind": "doc", "excerpt": "Refunds are available within 30 days..."}
  ],
  "working_memory": ["Customer already tried the self-serve refund form."],
  "exclusions": ["Ignore archived 2022 refund policy."],
  "output_contract": {"format": "markdown", "requires_approval": true}
}
```

## Assembly rules

1. Build the pack before writing the final prompt.
2. Prefer fewer high-signal sources over dumping every retrieved chunk.
3. Keep source ids stable enough to appear in logs, eval fixtures, and review screens.
4. Put safety and side-effect limits in `constraints`, not in vague instruction prose.
5. Record exclusions when a tempting source is intentionally left out.
6. Validate the output contract with code when the result will be saved, sent, or published.

## Acceptance criteria

A context pack is ready to use when:

- the user goal and output contract are visible in the same artifact,
- every factual claim source has an id or path that a reviewer can inspect,
- hard constraints are separated from optional style guidance,
- stale or intentionally excluded context is named when it could plausibly be retrieved,
- the pack is small enough to review without reading raw logs,
- a failed output can be reproduced from the saved pack plus the model/version settings.

## Cheap validators

- **budget check:** fail if any section exceeds its token or character budget.
- **source check:** fail if `sources` is empty for an output that claims evidence.
- **approval check:** fail if a pack can trigger external side effects without `requires_approval: true`.
- **staleness check:** warn when a source has no version, timestamp, or commit hash.
- **shape check:** validate required keys before calling the model.

## Anti-patterns

- Concatenating retrieval results directly into a prompt with no section labels.
- Treating durable memory, current-session notes, and source evidence as the same thing.
- Adding more context when the actual bug is a missing output contract.
- Letting the model decide whether an action needs approval.
- Logging full sensitive source text when a source id plus short excerpt would support review.

## Implementation note

For early products, a context pack can be a plain dictionary assembled next to the model call. The important upgrade is not infrastructure; it is making context a first-class object that can be inspected, validated, and reused in eval fixtures.
