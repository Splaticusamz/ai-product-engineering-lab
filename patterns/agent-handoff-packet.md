# Agent Handoff Packet

Use this pattern when an AI agent finishes work that another person, agent, or future session may need to continue. The goal is to prevent the next operator from rereading the whole thread, guessing what changed, or trusting an unverified success claim.

## Problem

Agent work often fails at the seam between sessions. The first agent may have done useful work, but the next operator only sees a vague summary like "implemented the feature" or "tests pass." That summary is not enough to safely continue, review, or ship.

A good handoff packet makes continuation cheap by naming the actual state of the world.

## Required fields

| Field | What to include | Failure mode it prevents |
| --- | --- | --- |
| Objective | One sentence describing the user-visible outcome, not the internal task. | Continuing the wrong work because the implementation detail became the goal. |
| Changed surface | Exact files, routes, commands, dashboards, or external systems touched. | Missing a side effect outside the obvious diff. |
| Current state | `done`, `partial`, `blocked`, or `reverted`, plus one plain-language reason. | Treating incomplete work as shipped. |
| Verification | Real commands, URLs, screenshots, or checks that were run, with summarized output. | Trusting model confidence instead of evidence. |
| Open risks | Specific risks still present, including skipped checks and why they were skipped. | Hiding uncertainty in a cheerful final answer. |
| Next action | The smallest safe continuation step. | Forcing the next operator to rebuild the plan from scratch. |

## Minimal template

```md
## Handoff

Objective: [user-visible outcome]
Current state: [done|partial|blocked|reverted] — [reason]

Changed surface:
- [path/route/service]

Verification:
- `[command]` → [real result summary]

Open risks:
- [specific risk or "None observed"]

Next action:
- [single concrete step]
```

## Acceptance criteria

A handoff packet is usable when:

- every changed file or external surface is named,
- at least one verification item contains real output or an explicit reason no check could run,
- blocked work includes the blocker owner or missing prerequisite,
- skipped tests are labeled as skipped, not silently omitted,
- the next action is executable without reading the full prior conversation,
- irreversible or public side effects are called out separately from local edits.

## Example

```md
## Handoff

Objective: Make the admin import preview reject empty CSV rows before saving.
Current state: partial — parser rejects empty rows, but browser import flow still needs a smoke test.

Changed surface:
- `src/lib/importRows.ts`
- `src/app/admin/import/page.tsx`

Verification:
- `npm test -- importRows` → 6 tests passed, including `skips fully empty rows`.
- `npm run typecheck` → passed.

Open risks:
- Did not run Playwright because local auth seed is missing.

Next action:
- Seed a local admin user and run the import preview with `fixtures/empty-row.csv`.
```

## Implementation note

For agent products, make the packet a structured artifact rather than a paragraph. A small JSON or markdown block can be rendered in the UI, attached to a pull request, or passed to the next agent without losing the distinction between facts, risks, and recommendations.
