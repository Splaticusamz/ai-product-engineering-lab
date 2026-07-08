# Agent Decision Records

Use this pattern when an autonomous or semi-autonomous AI agent must choose a path without stopping for a human answer. The goal is to make the decision auditable without turning every run into a meeting.

## Problem

Agents often make reasonable local choices that become hard to review later: choosing a data source, skipping a test, changing scope, accepting a degraded integration, or deciding that a reversible action is safe. If the final artifact only says `done`, reviewers cannot tell whether the agent made a sound tradeoff or silently guessed.

An agent decision record is a compact note captured at the moment of choice. It records the option selected, the options rejected, the evidence available, the blast radius, and the repair path if the choice is wrong.

## Required fields

| Field | What it forces | Example |
| --- | --- | --- |
| `decision_id` | Stable handle for logs, review, and follow-up. | `ADR-003-use-local-json-fixture` |
| `trigger` | The event that required a choice. | `external API unavailable during eval run` |
| `chosen_path` | The action the agent took. | `use a checked-in synthetic fixture for scorer validation` |
| `rejected_paths` | Alternatives considered, not a blank rationale. | `wait for API`, `skip validation`, `mock scorer output` |
| `evidence` | Real observations that supported the choice. | `curl timed out after 20s twice; unit scorer accepts fixture input` |
| `blast_radius` | What can go wrong if the choice is bad. | `fixture may not cover provider-specific response fields` |
| `reversibility` | How quickly the choice can be undone. | `replace fixture path with live fetch when API returns` |
| `follow_up_gate` | The condition that reopens the decision. | `before publishing benchmark numbers` |

## Default flow

1. Create a decision record only for choices that change scope, evidence quality, user-visible behavior, cost, data handling, or external side effects.
2. Keep the record close to the work: a run log entry, PR note, issue comment, or `decisions/` file for larger experiments.
3. Write down at least two rejected paths. If there was only one possible path, it probably is not a decision record.
4. Attach command output, URLs, errors, diffs, or fixture names as evidence. Do not use confidence language as evidence.
5. Mark the follow-up gate before continuing. A decision without a reopen condition becomes stale policy.
6. At final review, scan open decision records and either close them, convert them into tasks, or call out the residual risk.

## Good default UX

For product surfaces that expose AI autonomy, decision records should not read like legal paperwork. Show the smallest useful artifact:

- **Inline disclosure:** `Used cached inventory data because the live sync failed twice. Refresh before sending purchase orders.`
- **Reviewer drawer:** selected path, rejected paths, evidence links, and one-click `re-run with live data` action.
- **Run summary:** `3 decisions made; 1 requires human review before publish.`
- **Escalation chip:** visible only when blast radius crosses a configured threshold.

## Decision thresholds

| Decision type | Record? | Reason |
| --- | --- | --- |
| Naming a local variable | No | No material product or workflow risk. |
| Choosing between two equivalent UI labels | Usually no | Capture only if brand, legal, or conversion risk is real. |
| Skipping a flaky integration test | Yes | Evidence quality changed and the final claim may overstate validation. |
| Falling back from live API data to fixture data | Yes | Data freshness changed and later metrics could mislead. |
| Publishing, charging, deleting, emailing, or deploying | Yes, plus approval gate if needed | External side effects require an audit trail. |

## Cheap validators that pay off

- **Rejected-path count:** fail records with fewer than two rejected paths for non-trivial choices.
- **Evidence link check:** fail records that do not contain at least one command, URL, error excerpt, file path, or artifact identifier.
- **Blast-radius label:** require one of `local`, `repo`, `user-visible`, `external`, or `irreversible`.
- **Follow-up freshness:** flag records whose reopen condition has passed but remains unresolved.
- **Final-claim match:** compare final report claims against open decisions that weakened validation.

## Acceptance criteria

Agent decision records are working when:

- reviewers can reconstruct why the agent moved without asking for hidden reasoning,
- risky autonomy is visible before the final artifact is treated as complete,
- reversible choices stay lightweight and do not block momentum,
- degraded evidence is not laundered into strong final claims,
- every open decision has a concrete gate for revisit or closure.

## Anti-patterns

- Recording every tiny implementation preference until the useful decisions are buried.
- Writing `the agent decided this was best` without rejected paths or evidence.
- Hiding a failed dependency behind polished output instead of naming the fallback.
- Letting a temporary fallback become permanent because no follow-up gate was set.
- Treating the decision record as approval for an irreversible external action.
