# Agent Dry-Run Parity

Use this pattern when an agent offers a preview, simulation, or `--dry-run` before a consequential action. The dry run must exercise the same selection, normalization, policy, and planning code as execution; otherwise the preview is reassurance theater rather than a reliable forecast.

## Problem

Teams often implement dry run as a second, simplified code path. It may count candidate records without resolving exclusions, render an approximate message instead of the final payload, or skip live authorization checks. The user approves one result, then execution recomputes a different one against changed state.

A useful dry run produces an immutable execution plan from a pinned input snapshot. Execute mode consumes that plan after checking freshness and authorization. It does not silently regenerate intent.

## Required fields

| Field | Purpose | Example |
| --- | --- | --- |
| `plan_id` | Stable reference shared by preview and execution. | `plan_01J...` |
| `input_revision` | Version, cursor, or hashes of mutable source data. | `contacts:v184` |
| `policy_revision` | Policy version used to allow, reject, or redact actions. | `outreach-policy:12` |
| `operations` | Ordered, normalized side effects with exact targets and payload hashes. | `[{"op":"send","target":"user:42","payload_hash":"sha256:..."}]` |
| `excluded` | Candidates omitted and machine-readable reasons. | `[{"target":"user:17","reason":"opted_out"}]` |
| `limits` | Cost, item-count, rate, and time boundaries. | `max_operations: 20` |
| `expires_at` | Point after which mutable state must be previewed again. | ISO 8601 timestamp |
| `plan_hash` | Digest over canonical plan fields. | `sha256:6c4...` |

## Shared planning flow

1. Load source data once and record its revision or content hashes.
2. Normalize candidates, resolve targets, apply exclusions, and evaluate policy through the production planner.
3. Materialize exact operation payloads; do not use summaries as substitutes for payloads.
4. Canonically serialize the plan and compute `plan_hash`.
5. In dry-run mode, show the plan summary, meaningful diffs, exclusions, limits, and expiry without dispatching operations.
6. In execute mode, require the approved `plan_id` and `plan_hash`, then recheck input freshness, current policy, authorization, and limits.
7. Dispatch the stored operations with idempotency keys derived from `plan_id` and operation index.
8. Record per-operation results without rewriting the approved plan.

```python
def run(mode, plan):
    assert hash_plan(plan) == plan.plan_hash
    assert not plan.is_expired()
    assert source_revision(plan) == plan.input_revision
    assert current_policy_allows(plan)

    if mode == "dry-run":
        return render_preview(plan)
    return dispatch(plan.operations, idempotency_scope=plan.plan_id)
```

## Parity tests

| Failure class | Test | Expected result |
| --- | --- | --- |
| Planner drift | Build a plan in both modes from the same fixture. | Canonical `operations`, `excluded`, and `plan_hash` are identical. |
| Source mutation | Change a selected record after preview. | Execution fails with `REPLAN_REQUIRED`; it does not refresh silently. |
| Policy tightening | Deny one operation after preview. | Execution fails closed or requests a new preview. |
| Batch truncation | Exceed the approved operation limit. | Planner rejects or explicitly truncates before approval. |
| Duplicate retry | Replay an interrupted execution. | Completed operation keys are reconciled, not dispatched twice. |
| Presentation loss | Hide an exclusion or destructive field in the summary. | Snapshot/UI test fails even though the underlying plan is valid. |

## Good default UX

- Label previews with the exact operation count, targets, estimated cost, expiry, and source revision.
- Show representative payloads plus a downloadable full manifest for large batches.
- Explain exclusions by reason; `82 selected` is misleading if 19 will be skipped.
- Invalidate approval visibly when inputs or policy require a new plan.
- Distinguish `preview generated` from `ready to execute`; authorization and freshness can still block dispatch.
- After execution, report actual outcomes against the approved operation list: succeeded, failed, skipped, and reconciled.

## Acceptance criteria

Dry-run parity is working when:

- dry run and execution invoke one production planner rather than parallel business logic,
- a preview identifies an immutable plan and exact input and policy revisions,
- execution consumes the approved operation manifest instead of recomputing it,
- changed inputs, expired plans, and stricter policy fail closed before side effects,
- retries use stable idempotency keys and reconcile ambiguous external results,
- automated tests compare canonical plans across dry-run and execute entry points,
- the user can see important exclusions, limits, and payload differences before approval.

## Anti-patterns

- Implementing dry run as `if dry_run: print(count)` before the real planner runs.
- Querying live candidates again during execution and calling the new result “the approved batch.”
- Previewing templates while leaving resolved recipients, attachments, prices, or permissions unspecified.
- Treating a matching item count as parity when targets or payloads differ.
- Allowing an expired plan to refresh automatically because the intended action “looks equivalent.”
- Using dry run to skip authorization, policy evaluation, or destructive-field rendering.
