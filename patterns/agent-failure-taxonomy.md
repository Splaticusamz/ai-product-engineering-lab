# Agent Failure Taxonomy

Use this pattern when an agentic workflow fails, stalls, or returns an artifact that cannot be trusted yet. The goal is to classify the failure before retrying, rewriting the prompt, escalating to a human, or changing product code.

## Problem

Agent failures often get collapsed into one vague bucket: "the model got it wrong." That hides the operational cause. A missing credential, stale source file, ambiguous product instruction, schema mismatch, and weak model reasoning require different fixes. If the product only records a generic failure, the next run usually repeats the same path with more tokens and less evidence.

A failure taxonomy gives operators and product surfaces a shared set of labels. The label is not the postmortem. It is the routing decision that determines which recovery path is safe.

## Failure classes

| Class | What it means | Default recovery |
| --- | --- | --- |
| `missing_prerequisite` | The agent lacks a required credential, file, dependency, approval, or source-of-truth read. | Stop automatic work and name the prerequisite. |
| `bad_input_contract` | The task request or upstream payload is ambiguous, contradictory, or missing required fields. | Return a repairable input error with examples. |
| `retrieval_staleness` | The agent used stale docs, old repo state, cached search results, or the wrong branch/product. | Refresh source-of-truth context before any retry. |
| `tool_execution` | A command, API call, browser action, or filesystem operation failed despite valid inputs. | Retry only if the next attempt changes environment, timeout, or payload. |
| `output_contract` | The generated artifact violates a schema, required field, format, or evidence requirement. | Feed validator errors back into a constrained repair pass. |
| `reasoning_gap` | The output is structurally valid but the decision is unsupported, inconsistent, or misses an obvious constraint. | Route to critique/review, not blind regeneration. |
| `side_effect_risk` | The next step could publish, send, delete, charge, merge, or expose user-visible state without sufficient approval. | Downgrade to draft/stage and require a gate. |
| `external_instability` | A provider, network, dependency registry, or hosted service is temporarily unavailable. | Apply bounded retry/backoff and preserve the last safe artifact. |

## Triage record

Capture a small record when a run fails. Keep it next to the job log, eval case, PR comment, or support trace.

```json
{
  "failure_class": "retrieval_staleness",
  "symptom": "agent edited the local clone while production was linked to a different repo",
  "evidence": [
    "git remote -v showed expected owner but Vercel metadata pointed at another project",
    "production page still served the old copy after local build passed"
  ],
  "recovery_path": "resolve deployed repo source-of-truth, reset wrong clone, then patch the live-linked repo",
  "safe_to_retry": false,
  "prevents_recurrence": "add production-repo resolution to the preflight checklist"
}
```

## Default flow

1. Reproduce or read the failing artifact before assigning a class.
2. Record the exact symptom in user-visible terms, not only an internal exception name.
3. Attach at least one piece of evidence: command output, validator message, API response, URL readback, screenshot, or source file path.
4. Pick one primary failure class. Add secondary notes only when they change the recovery path.
5. Decide whether the next action is retry, repair, refresh context, stage behind a gate, or stop with a blocker.
6. Convert repeated failures into eval fixtures or runbook checks once the same class appears twice.

## Good default UX

- Show the user a specific blocker: "Missing approval to publish" is better than "workflow failed."
- Make repairable input failures editable in place instead of asking for a full restart.
- Display stale-context failures with the source that was stale and the source that superseded it.
- Keep provider instability separate from product-contract failures so dashboards do not blame users for outages.
- Preserve the last safe draft when execution fails after useful generation work.

## Cheap validators that pay off

- **class-required check:** fail job records that have `status: failed` but no `failure_class`.
- **evidence check:** fail classifications that contain no command, URL, file path, validator message, or error excerpt.
- **retryability check:** block automatic retries for `missing_prerequisite`, `bad_input_contract`, and `side_effect_risk` unless a repair event is recorded.
- **staleness check:** require a fresh source-of-truth read after `retrieval_staleness` before the next mutation.
- **recurrence check:** warn when the same class appears twice for one workflow without a new guard, fixture, or runbook update.

## Acceptance criteria

A failure taxonomy is working when:

- operators can tell whether a run needs a retry, repair, approval, source refresh, or human review,
- failures preserve evidence that can become an eval or regression fixture,
- retries are reserved for classes that can actually improve on the next attempt,
- dashboards separate model reasoning gaps from tool outages and missing prerequisites,
- the final handoff names the recovery path instead of hiding behind a generic error.

## Anti-patterns

- Labeling every bad artifact as `reasoning_gap` because a model produced it.
- Retrying `missing_prerequisite` failures without acquiring the prerequisite.
- Treating a schema-valid output as successful when its evidence is stale or irrelevant.
- Folding approval and publishing risks into normal execution errors.
- Recording provider outages as product-quality failures without a separate instability label.
