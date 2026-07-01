# Agent Retry Budgets

Use this pattern when an AI product or internal agent can retry work after a failed tool call, invalid output, missing dependency, or flaky external service. The goal is to make retries useful and bounded instead of letting an agent burn time, money, or user trust while looping on the same failure.

## Problem

Retries are easy to add and hard to reason about. A model sees an error, asks for another attempt, and the system often complies without tracking what changed between attempts. If each retry uses the same prompt, same tool input, and same missing prerequisite, the agent is not recovering; it is repeating.

A retry budget turns recovery into a first-class product rule: how many attempts are allowed, what must change between attempts, when to downgrade the task, and when to hand the problem to a human or a safer workflow.

## Budget shape

| Field | What it records | Why it matters |
| --- | --- | --- |
| `operation` | The user-visible job or tool family being retried. | Prevents one flaky subtask from consuming the whole session. |
| `max_attempts` | The hard limit for automatic retries. | Creates a stop condition before cost or latency gets silly. |
| `change_required` | What must be different before the next attempt. | Blocks blind repetition with the same failing input. |
| `failure_classes` | Known transient vs structural failure categories. | Lets the product retry network flakes without retrying bad requirements forever. |
| `fallback` | The downgrade path after the budget is spent. | Keeps the user moving with a partial result, draft, or clear blocker. |
| `evidence` | Error excerpts, status codes, validation messages, or command output. | Makes postmortems and eval fixtures possible. |

## Minimal schema

```json
{
  "operation": "generate_product_summary",
  "max_attempts": 3,
  "attempt": 2,
  "change_required": "Use shorter source excerpts and require JSON-only output.",
  "failure_classes": ["schema_validation", "provider_timeout"],
  "fallback": "Save a draft summary with validation errors attached for review.",
  "evidence": ["validator: missing required key benefits", "provider: timeout after 30s"]
}
```

## Default flow

1. Classify the failure before retrying: transient, invalid input, invalid output, missing permission, or product ambiguity.
2. Retry transient failures only when the next attempt has a different backoff, timeout, provider, or narrowed payload.
3. Retry invalid output only after changing the output contract, examples, validator feedback, or source context.
4. Do not retry missing permission, missing credentials, destructive side effects, or ambiguous product intent automatically.
5. Decrement the budget at the operation level, not globally across unrelated work.
6. When the budget is spent, return the best safe artifact plus the exact blocker and the next manual action.
7. Store attempts with enough evidence to become a regression fixture later.

## Good default UX

- Show users that recovery is bounded: "Retrying with a smaller file, attempt 2 of 3."
- Replace vague spinner copy with the concrete change being made before the next attempt.
- Offer a safe fallback before the final retry when latency is user-visible.
- Keep failed attempts inspectable, but collapse noisy provider traces by default.
- Treat repeated validation failures as a product bug, not as user error.

## Cheap validators that pay off

- **blind-repeat check:** fail if attempt `n + 1` has the same normalized input and no recorded `change_required`.
- **permission check:** block automatic retries for auth, billing, approval, or destructive-action errors.
- **latency check:** warn when the projected retry path exceeds the screen or workflow's user-tolerance budget.
- **fallback check:** fail workflows that have `max_attempts > 1` but no fallback artifact or escalation path.
- **evidence check:** require at least one machine-readable error class or validator message per failed attempt.

## Acceptance criteria

A retry budget is ready when:

- every retryable operation has a visible maximum attempt count,
- each attempt records what changed from the previous attempt,
- structural failures stop quickly instead of consuming the transient-failure budget,
- the fallback gives the user a useful artifact or a specific blocker,
- logs preserve enough evidence to reproduce the failure in an eval fixture,
- dashboards can separate recovered transient failures from repeated product-contract failures.

## Anti-patterns

- Retrying a model call with the exact same prompt and hoping randomness fixes a schema error.
- Hiding retries behind a spinner until the user gives up.
- Counting only provider errors while ignoring validator failures and tool-side exceptions.
- Spending the retry budget on prerequisites the agent cannot satisfy, such as missing credentials.
- Treating a fallback as failure when it is actually the safest completed state for the user.
