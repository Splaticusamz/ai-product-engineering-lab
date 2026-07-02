# Agent Output Contracts

Use this pattern when an AI workflow produces an artifact that another person, script, or agent must consume: tickets, plans, code-review notes, QA reports, extraction results, or deployment summaries. The goal is to define the shape of a useful answer before generation starts so the result can be checked instead of merely admired.

## Problem

Agents are good at filling space. Without an output contract, they often return fluent text that misses the operational fields the next step needs: owner, file paths, validation commands, decision status, rollback notes, or unresolved blockers. Reviewers then waste time translating prose into a task shape, and automation cannot tell whether the artifact is complete.

An output contract is a small schema plus acceptance rules. It does not need to be a formal JSON Schema every time, but it should make missing work visible.

## Required fields

| Field | What it forces | Example |
| --- | --- | --- |
| `artifact_type` | The kind of output being produced. | `qa_report` |
| `consumer` | Who or what will use it next. | `release owner`, `scoring script`, `support agent` |
| `decision_state` | Whether the output is ready, blocked, or needs review. | `ready_for_review` |
| `claims` | Specific assertions the output makes. | `mobile checkout loads without horizontal scroll` |
| `evidence` | Commands, URLs, fixtures, screenshots, or readbacks supporting the claims. | `npm run build -> exit 0` |
| `open_questions` | Known gaps that should not be hidden in prose. | `payment provider not exercised` |
| `next_action` | The smallest useful follow-up. | `run production smoke test after deploy` |

## Minimal contract

```json
{
  "artifact_type": "implementation_plan",
  "consumer": "engineer picking up the next task",
  "decision_state": "ready_for_review",
  "claims": [
    "plan is scoped to one feature flag and one route"
  ],
  "evidence": [
    "repo inspection: app/settings/page.tsx exists",
    "validator: python3 scripts/check_plan.py plans/settings-sync.md -> exit 0"
  ],
  "open_questions": [
    "production analytics event name still needs owner approval"
  ],
  "next_action": "create the feature branch and add the failing settings-sync test"
}
```

## Default flow

1. Name the consumer before asking the agent to generate anything. A human reviewer, a CLI script, and a downstream agent need different output shapes.
2. Write the required fields into the prompt or task template, not as a vague preference after the fact.
3. Require evidence fields for every claim that affects shipping, routing, scoring, or user-visible state.
4. Allow `open_questions: []`, but do not allow the field to be omitted. Missing uncertainty is different from no uncertainty.
5. Validate the result with the cheapest parser or checklist that matches the artifact type.
6. Feed validation errors back as structured repair instructions instead of asking for a general rewrite.

## Good default UX

- Show missing required fields as repairable form errors, not as a generic failed generation.
- Keep the contract close to the artifact preview so reviewers can see why a field exists.
- Use short state labels: `draft`, `ready_for_review`, `blocked`, `executed`, `verified`.
- Let teams add local fields, but keep `claims`, `evidence`, and `open_questions` stable across workflows.
- Prefer one contract per handoff type over one giant universal schema.

## Cheap validators that pay off

- **field presence check:** fail if any required key is missing or blank.
- **claim-evidence check:** warn when a claim has no command, URL, fixture, or observation next to it.
- **state check:** block `verified` when evidence is empty or only describes edits made.
- **next-action check:** fail if `decision_state` is `blocked` and `next_action` does not name an owner or concrete unblocker.
- **schema drift check:** compare generated keys to the contract and flag unexpected fields that look like prose headings.

## Acceptance criteria

An output contract is working when:

- the consumer can use the artifact without translating freeform prose into a new format,
- missing evidence, blockers, and next actions are visible before handoff,
- validators can reject incomplete outputs with actionable messages,
- reviewers can distinguish unsupported claims from verified claims,
- the contract is small enough that agents fill it accurately under normal context limits.

## Anti-patterns

- Asking for "a concise summary" when the next step actually needs paths, commands, and ownership.
- Treating a beautiful paragraph as complete even though no parser or reviewer can route it.
- Making every field optional because the model might not know the answer.
- Hiding blockers in final prose instead of putting them in `open_questions`.
- Using one large schema for every workflow until nobody understands which fields matter.
