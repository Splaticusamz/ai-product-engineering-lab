# Agent Approval Leases

Use this pattern when an agent needs human approval for a risky action and may execute later, retry after a failure, or resume from a queue. Treat approval as a scoped, expiring lease rather than a permanent boolean so old consent cannot authorize a materially different action.

## Problem

A stored `approved: true` flag loses the context that made the approval safe. The target can change, a draft can be edited, prices can move, credentials can rotate, or a queued run can resume days later. Reusing that flag turns a reasonable approval into ambient permission.

An approval lease binds consent to an action fingerprint, target, limits, and expiry. Execution must revalidate the lease immediately before the side effect, not only when work enters the queue.

## Required fields

| Field | Purpose | Example |
| --- | --- | --- |
| `approval_id` | Stable audit identifier. | `apr_01J...` |
| `action` | Exact side-effect class. | `publish_release` |
| `target` | Resource and environment. | `github:org/repo@production` |
| `payload_hash` | Digest of the reviewed material or normalized parameters. | `sha256:8b1...` |
| `limits` | Hard boundaries such as amount, recipients, or item count. | `max_cost_cents: 0`, `max_recipients: 1` |
| `approved_by` | Human or policy principal that granted the lease. | `user:42` |
| `issued_at` | Start of the validity window. | ISO 8601 timestamp |
| `expires_at` | End of the validity window. | ISO 8601 timestamp |
| `consumed_at` | Prevents reuse when approval is single-use. | `null` until execution |
| `revoked_at` | Immediate cancellation independent of expiry. | `null` until revoked |

## Validation flow

Run these checks in one transaction or equivalent compare-and-set operation immediately before execution:

1. Load the lease by `approval_id`; reject missing, revoked, consumed, or expired leases.
2. Recompute the action fingerprint from normalized execution parameters.
3. Require exact matches for `action`, `target`, and `payload_hash`.
4. Enforce every numeric and set-based limit against live values.
5. Recheck mutable safety policy, authentication, and target existence. Approval does not bypass current policy.
6. Atomically mark a single-use lease consumed before dispatch, or reserve it with an idempotency key.
7. Record the lease ID, fingerprint, policy version, and external result in the audit event.

```python
def authorize(lease, request, now):
    if lease.revoked_at or lease.consumed_at or now >= lease.expires_at:
        return "REAPPROVAL_REQUIRED"
    if request.action != lease.action or request.target != lease.target:
        return "REAPPROVAL_REQUIRED"
    if fingerprint(request.payload) != lease.payload_hash:
        return "REAPPROVAL_REQUIRED"
    if exceeds_limits(request, lease.limits):
        return "REAPPROVAL_REQUIRED"
    return "LEASE_VALID"
```

## Invalidation matrix

| Change after approval | Reuse lease? | Reason |
| --- | --- | --- |
| Retry with the same idempotency key after a timeout | Maybe | First confirm the external system did not complete the action. |
| Whitespace-only draft normalization included in the hash contract | Yes | The reviewed semantic payload is unchanged. |
| Recipient, repository, environment, or account changes | No | The target boundary changed. |
| Price, quantity, permissions, or attached file changes | No | Risk or reviewed payload changed. |
| Policy becomes stricter before execution | No | Approval cannot override current safety rules. |
| Worker restarts while the lease remains valid | Yes | Restart alone does not change scope, but all checks still rerun. |

## Product UX

- Show the user the target, irreversible effect, meaningful limits, and expiry before approval.
- On payload edits, visibly invalidate the prior approval and explain which field changed.
- Distinguish `expired`, `revoked`, `already used`, and `scope changed`; each suggests a different recovery path.
- Keep reapproval cheap by preserving the draft and highlighting the delta from the previously reviewed version.
- For batches, approve a fixed manifest or bounded query snapshot, not an open-ended instruction such as “process the rest.”

## Acceptance criteria

Approval leases are working when:

- changing any bound action, target, payload, or limit forces reapproval,
- expired and revoked leases fail closed before external dispatch,
- concurrent workers cannot consume a single-use lease twice,
- retries reconcile external state before attempting another side effect,
- audit records can reconstruct exactly what was approved and what executed,
- stricter live policy can reject an otherwise valid lease.

## Anti-patterns

- Storing approval as a reusable boolean on the user or job.
- Hashing a display summary while executing unbound hidden parameters.
- Checking expiry when dequeuing but not immediately before dispatch.
- Extending a lease automatically because execution was delayed.
- Treating approval as an exception to authentication, policy, or spending limits.
- Retrying a consumed lease without an idempotency key or external reconciliation.
