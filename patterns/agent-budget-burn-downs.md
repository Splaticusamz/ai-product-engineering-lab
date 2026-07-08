# Agent Budget Burn-downs

Use this pattern when an AI agent can spend money, tokens, credits, wall-clock time, or scarce queue capacity while chasing an open-ended product task. The goal is to keep exploration useful without letting automation quietly turn into an uncapped bill.

## Problem

Agent runs often start with a reasonable budget assumption: one model call, one scrape, one render, one deploy, one batch. The cost risk appears when retries, fallback providers, parallel workers, or background loops stack up. A final report that says `completed after retries` is not enough if nobody can see how much budget was consumed, what stopped further spending, or which output quality threshold justified continuing.

A budget burn-down makes the agent declare the spending envelope before the run, decrement it near every expensive action, and stop with a useful partial artifact instead of improvising one more paid attempt.

## Required fields

| Field | What it forces | Example |
| --- | --- | --- |
| `budget_id` | Stable handle for the run or workflow. | `hero-image-variants-2026-07` |
| `meter` | The constrained unit. | `USD`, `model_tokens`, `gpu_minutes`, `render_jobs`, `wall_clock_minutes` |
| `starting_budget` | Explicit maximum before work begins. | `6 render jobs` |
| `burn_events` | Append-only ledger of expensive actions. | `render_03: failed safety filter; 1 job consumed` |
| `stop_condition` | The gate that prevents more spend. | `stop after 2 failed provider attempts or 4 acceptable variants` |
| `quality_threshold` | Why spending continues or stops. | `variant must preserve source product and pass mobile crop check` |
| `fallback_artifact` | Useful output if the budget is exhausted. | `ranked prompt set plus failure notes, no new render` |

## Default flow

1. Set the budget before the first expensive action. If the budget cannot be named, downgrade to a spike or ask for approval before spend.
2. Define the quality threshold in observable terms: test result, reviewer-visible screenshot, score floor, fixture match, or specific user journey.
3. Record every burn event at the point of action, including failed attempts. Failed calls still count.
4. Recompute the remaining budget before starting retries, provider fallbacks, or parallel workers.
5. Stop when the stop condition fires. Ship the fallback artifact rather than hiding the exhausted budget behind vague progress language.
6. In the final report, include starting budget, consumed budget, remaining budget, and the artifact that justified the spend.

## Cheap validators that pay off

- **pre-spend gate:** fail the run if an expensive action is about to execute without `starting_budget`, `stop_condition`, and `quality_threshold`.
- **retry cap check:** fail if retries can multiply cost beyond the starting budget.
- **parallel multiplier check:** estimate worst-case burn as `workers * attempts * unit_cost` before launching workers.
- **empty-output check:** require a fallback artifact when the budget reaches zero without a shippable result.
- **report reconciliation:** compare final spend claims against the burn-event count before sending the report.

## Good default UX

For product teams, expose budget burn-downs as operational context, not accounting theater:

- **Run header:** `4 of 6 render jobs used; stop after 2 more failures.`
- **Retry prompt:** `This fallback will spend up to 2 extra calls. Continue, switch to draft-only, or stop?`
- **Batch dashboard:** remaining budget, current worker count, worst-case remaining cost, and cancel button.
- **Final artifact card:** result preview, spend consumed, failed attempts, and the fallback artifact if quality threshold was not met.

## Acceptance criteria

Agent budget burn-downs are working when:

- every expensive run has a named maximum before the first spend,
- retries and parallelism cannot exceed the declared envelope by accident,
- failed paid attempts are visible instead of erased from the narrative,
- the agent has a useful zero-budget output path,
- final reports reconcile claimed validation with actual burn events.

## Anti-patterns

- Treating a budget as a vibe such as `keep it cheap` instead of a countable limit.
- Recording only successful generations or API calls.
- Letting fallback providers double the spend because they feel like recovery rather than new work.
- Continuing to spend after the output is already good enough for the decision at hand.
- Reporting polished results without naming the attempts that were discarded.
