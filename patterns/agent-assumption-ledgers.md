# Agent Assumption Ledgers

Use this pattern when an agent must keep moving with incomplete context: missing product owner input, stale docs, partial API access, ambiguous UX intent, or unavailable production data. The goal is not to eliminate assumptions. The goal is to make each assumption explicit, cheap to reverse, and visible before it becomes a silent product decision.

## Problem

AI workflows often blur three very different states: verified facts, reasonable assumptions, and guesses made to keep a run moving. When those states are mixed together, a reviewer cannot tell whether the agent inspected the source of truth or merely inferred it from similar projects. The failure mode is subtle: the artifact looks complete, but it encodes hidden product choices that nobody approved.

An assumption ledger is a small table captured beside the plan, PR, QA report, or generated artifact. It records what the agent assumed, why the assumption was acceptable for this run, how it was bounded, and what signal would invalidate it.

## Ledger fields

| Field | What it records | Example |
| --- | --- | --- |
| `assumption` | The specific statement being treated as true for now. | `The checkout page should keep the existing one-column mobile layout.` |
| `basis` | The evidence or constraint that made the assumption reasonable. | `Existing route uses one-column cards; no redesign request in ticket.` |
| `risk_if_wrong` | The user, product, or engineering impact if the assumption fails. | `Desktop polish may be acceptable, but mobile conversion could regress.` |
| `blast_radius` | The surfaces allowed to depend on this assumption. | `CSS layout only; no pricing, inventory, or checkout logic.` |
| `reversal_path` | The smallest follow-up if the assumption is invalidated. | `Revert the layout class change and keep the validation script.` |
| `invalidating_signal` | The observation that should force rework or escalation. | `Owner asks for two-column desktop merchandising above 768px.` |

## Default flow

1. Separate facts from assumptions before making the first mutation. Facts have source reads; assumptions have rationale and limits.
2. Keep assumptions small enough that they can be reversed without unwinding unrelated work.
3. Tie each assumption to a surface: file paths, routes, workflows, data fields, or user-visible copy.
4. Mark assumptions that affect public posting, money, auth, data deletion, legal claims, or user contact as escalation-only.
5. Revisit the ledger after validation. Promote assumptions to facts only when a real source, command, API response, or user decision supports them.
6. Include unresolved assumptions in the final handoff instead of hiding them in confident prose.

## Good default UX

- Show the ledger as a collapsible review block next to the diff or artifact preview.
- Use short status labels: `assumed`, `verified`, `invalidated`, `escalated`.
- Let reviewers accept or reject an assumption without rewriting the whole artifact.
- Keep high-risk assumptions pinned open; low-risk implementation defaults can stay collapsed.
- Link each assumption to the exact evidence read or validation command when it changes status.

## Cheap validators that pay off

- **evidence split check:** fail if an item is labeled `verified` without a source read, command output, URL, fixture, or user decision.
- **blast-radius check:** warn when an assumption has no affected path, route, API, or workflow named.
- **risk-gate check:** block automatic execution when an unresolved assumption touches money, auth, deletion, public posting, or private data.
- **reversal check:** fail assumptions that influence code or public copy but do not name a rollback or edit path.
- **handoff check:** require unresolved assumptions to appear in PR bodies, QA reports, or final run summaries.

## Acceptance criteria

An assumption ledger is useful when:

- reviewers can distinguish verified facts from bounded assumptions at a glance,
- every assumption has a named invalidating signal,
- high-risk assumptions cannot silently advance to execution,
- the final artifact can be changed when an assumption is wrong without discarding the whole run,
- later agents can inspect the ledger and continue from the real decision state.

## Anti-patterns

- Writing "assumption: standard behavior" without naming the actual behavior or affected surface.
- Treating an assumption as verified because the model has seen similar projects before.
- Letting a low-risk implementation default expand into product strategy, pricing, or public claims.
- Removing the ledger from the final summary once the work appears to pass tests.
- Asking the user to resolve every tiny assumption instead of bounding safe defaults and escalating only the risky ones.
