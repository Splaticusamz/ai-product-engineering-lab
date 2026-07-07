# Agent Constraint Drift Tests

Use this pattern when an AI agent must keep non-negotiable product, safety, brand, or workflow constraints across a multi-step run. The goal is to catch constraint drift before the final artifact looks polished but violates the rules that made the run useful.

## Problem

Long agent runs tend to degrade hard constraints into background preferences. A task may start with clear rules such as `one commit only`, `do not send externally`, `preserve product images`, `mobile-first`, or `cite only verified evidence`. After tool failures, retries, subagent handoffs, or summarization, the final output can satisfy the visible task while quietly dropping one of those constraints.

A constraint drift test turns the important rules into explicit checks that run at the same decision points where drift usually enters: after planning, before mutation, after generated output, and before final reporting.

## Required fields

Track each constraint as a small testable record, not as prose buried in the prompt:

| Field | What it forces | Example |
| --- | --- | --- |
| `constraint_id` | Stable name for review and logs. | `single-public-commit` |
| `source` | Where the rule came from. | `cron instruction hard rule #7` |
| `must_hold_until` | When the rule can expire. | `after push verification` |
| `failure_example` | Concrete behavior that violates it. | `second cleanup commit to fix formatting` |
| `check_method` | Manual readback, script, diff query, or UI probe. | `git rev-list --count origin/main..HEAD == 1 before push` |
| `repair_action` | What to do if drift is detected. | `squash commits before pushing` |

## Default flow

1. Extract only the constraints that would make the result unacceptable if missed. Do not test every preference.
2. Convert each constraint into a binary or near-binary check. If the check cannot fail, rewrite it.
3. Run a first pass after planning so the implementation path does not already violate the rules.
4. Re-run the relevant checks immediately before any external mutation: commit, deploy, publish, send, charge, or delete.
5. Attach the final check results to the run report using real commands, URLs, screenshots, or reviewer-visible artifacts.
6. If a constraint fails, repair the artifact before broad validation. Do not bury the miss in a caveat after shipping.

## Useful test points

| Drift point | Cheap check | Why it catches real misses |
| --- | --- | --- |
| After plan | Compare planned actions against `constraint_id` list. | Prevents a bad path from becoming momentum. |
| Before write | Confirm the output surface is allowed to change. | Stops accidental edits to adjacent files or public pages. |
| Before external action | Read back live state and required approvals. | Prevents stale state from overriding hard gates. |
| After generation | Scan for forbidden structures, missing sections, or copied sensitive material. | Catches model-style compliance without actual compliance. |
| Before final report | Match every `verified` claim to evidence. | Prevents the report from laundering untested work. |

## Cheap validators that pay off

- **commit-count check:** for scheduled public work, fail if the run would produce more than one coherent contribution.
- **surface-boundary check:** fail if a diff touches files outside the declared artifact family without explanation.
- **approval-boundary check:** fail if the run crosses from draft/stage into execute without the required approval event.
- **asset-preservation check:** fail if generated media replaces a source asset that was supposed to be preserved.
- **evidence-language check:** fail final reports that say `verified`, `deployed`, or `working` without a command, URL, or probe result.

## Acceptance criteria

Constraint drift tests are working when:

- the important rules are visible as named checks before implementation starts,
- failures point to a specific repair instead of a vague quality note,
- checks run near the risky transition rather than only at the beginning,
- final reports distinguish satisfied constraints from skipped or blocked checks,
- the system can tolerate retries and handoffs without losing the original boundaries.

## Anti-patterns

- Treating the initial prompt as durable enforcement after the agent has summarized it three times.
- Checking constraints only at final review, when the cheapest repair window has already passed.
- Writing broad rubric items such as `be safe` that cannot fail in a useful way.
- Letting subagents inherit goals without the constraints that limit how those goals may be achieved.
- Using a successful build or test suite as proof that workflow constraints were followed.
