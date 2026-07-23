# Agent Ambiguous Side-effect Reconciliation

Use this pattern when an agent can trigger an external mutation and the caller may lose the response after dispatch. It covers the dangerous state where a timeout, dropped connection, worker crash, or provider `5xx` leaves the system unsure whether an email was sent, a payment was created, a deployment started, or a record changed.

## Problem

A failed request is not the same as a failed effect. If a provider accepts a write and the response disappears, blindly retrying can duplicate the real-world action. Marking the job failed can also lie: the effect may already be visible to users.

"Exactly once" is rarely an honest distributed-systems promise. A safer product contract is:

1. assign one durable identity to the intended effect,
2. reuse that identity across transport retries,
3. reconcile provider and target state before another write,
4. expose `outcome_unknown` until evidence proves what happened.

This pattern complements approval gates and retry budgets. Approval answers whether an effect may happen. A retry budget limits attempts. Reconciliation answers whether the approved effect already happened.

## Operation record

Create and persist the operation before dispatch. Do not reconstruct it from chat history after a worker restarts.

```json
{
  "operation_id": "op_01K4R7H2J8",
  "intent_type": "send_release_email",
  "target_ref": "campaign:release-42",
  "payload_fingerprint": "sha256:canonical-payload-digest",
  "idempotency_key": "effect:op_01K4R7H2J8",
  "approval_ref": "approval_8Q2",
  "status": "dispatching",
  "provider_request_id": null,
  "attempt_count": 1,
  "dispatched_at": "2026-07-23T16:40:00Z",
  "reconcile_after": "2026-07-23T16:40:05Z",
  "last_observation": null
}
```

The fields do different jobs:

| Field | Rule | Failure it prevents |
| --- | --- | --- |
| `operation_id` | Allocate once, before any network call. | A restart inventing a second logical action. |
| `payload_fingerprint` | Hash a canonical form of every effect-relevant field. | Reusing one key for a changed recipient, amount, or artifact. |
| `idempotency_key` | Derive from the operation, never from attempt number. | A retry bypassing provider deduplication. |
| `approval_ref` | Bind the operation to the exact approved intent. | Reconciliation becoming permission for a modified action. |
| `status` | Persist state transitions atomically. | Two workers both deciding the operation is safe to replay. |
| `provider_request_id` | Save as soon as one is available. | Losing the strongest provider lookup handle. |
| `last_observation` | Store source, time, normalized result, and evidence reference. | Repeating inconclusive lookups without an audit trail. |

Do not put raw secrets or full sensitive payloads in the operation ledger. Store protected references and a fingerprint sufficient to compare intent.

## State model

Use explicit states rather than overloading `failed`:

| State | Meaning | Write allowed? |
| --- | --- | --- |
| `prepared` | Durable intent exists but dispatch has not begun. | Yes, after current approval and policy checks. |
| `dispatching` | A worker atomically claimed the first dispatch. | Only the claiming worker. |
| `outcome_unknown` | Dispatch may have reached the provider, but no authoritative result was received. | No, until reconciliation authorizes a same-key replay. |
| `reconciling` | One worker holds the reconciliation lease and is querying evidence. | No. |
| `confirmed` | Provider or target evidence matches the intended effect. | No; terminal success. |
| `confirmed_absent` | Authoritative evidence proves no effect occurred. | A same-key replay may be allowed. |
| `conflict` | An effect exists but its target or fingerprint does not match. | No; escalate. |
| `manual_review` | Evidence stayed inconclusive past the bounded window. | No automatic replay. |

Transitions into `dispatching` and `reconciling` need a database compare-and-set, row lock, or expiring lease. An in-memory flag does not protect against a second worker.

## Reconciliation flow

1. Persist the canonical intent, fingerprint, approval reference, and stable idempotency key.
2. Atomically claim `prepared -> dispatching`, then call the provider with that key.
3. If an authoritative success or failure arrives, store it. If the response is ambiguous, commit `outcome_unknown` before retrying anything.
4. Claim a reconciliation lease so only one worker investigates or replays the operation.
5. Query the provider by idempotency key or provider request ID when that API exists.
6. Independently inspect the target system for a stable effect marker, such as message ID, payment metadata, deployment commit, or mutation version.
7. Normalize observations into `match`, `absent`, `conflict`, or `inconclusive`; do not let free-form model judgment choose the state.
8. Confirm success on a matching effect. Escalate a conflict. Replay only after authoritative absence and only with the original key and identical fingerprint.
9. Back off while the provider's documented consistency window is open. After the bounded window, move inconclusive work to `manual_review` with an evidence packet.
10. Release the lease and emit one state-transition event. Do not alert on every poll.

The reconciliation adapter should be deterministic application code. A model can summarize evidence for an operator, but it should not decide that a duplicate charge or send is "probably safe."

## Outcome matrix

| Observation | Decision | Next action |
| --- | --- | --- |
| Provider lookup returns the same key and matching payload fingerprint. | `confirmed` | Save provider ID and readback evidence. |
| Target contains exactly one effect with the operation marker and expected fields. | `confirmed` | Adopt it even if the original response was lost. |
| Provider reports a completed key but effect-relevant fields differ. | `conflict` | Freeze automation and escalate with both fingerprints. |
| Authoritative provider lookup says the key was never accepted. | `confirmed_absent` | Recheck approval and policy, then replay with the same key. |
| Target is empty but the provider is eventually consistent. | `inconclusive` | Wait and poll within the bounded reconciliation window. |
| No lookup API exists and the target cannot identify a unique effect. | `manual_review` | Do not replay automatically. Improve the integration contract. |
| A second worker finds a terminal state. | Existing terminal state | Return the stored result without dispatch. |

Absence is weaker evidence than presence. A missing row in a lagging read replica, an empty search page, or a delayed webhook is not authoritative proof that a write failed.

## Idempotency contract

Provider support must be verified, not inferred from a request header name. Record these semantics per tool:

- key scope: endpoint, account, tenant, region, or global,
- retention window: how long replay protection lasts,
- payload behavior: whether the provider rejects a reused key with changed fields,
- concurrency behavior: what happens when identical keys arrive simultaneously,
- lookup path: how to retrieve a result after losing the response,
- terminal exceptions: which errors prove rejection before execution,
- sandbox parity: whether test mode behaves like production.

If the provider offers no durable idempotency, add a first-party effect marker where possible. Examples include a unique metadata field on a payment, a deterministic external record ID, or an operation ID embedded in deployment metadata. A local dedupe table alone cannot prove what happened after the request crossed the network boundary.

## Good default UX

- Show `Checking whether the action completed` instead of immediately reporting failure.
- Keep the approved action visible and disable duplicate submit controls while the outcome is unknown.
- Distinguish `confirmed`, `not completed`, and `needs review`; do not flatten them into success/error.
- When review is required, show the target, intended effect, dispatch time, lookup attempts, and safest next action.
- If a matching external effect is adopted, tell the user it completed and was recovered after a lost response.
- Never ask the user to click "try again" when the product itself cannot determine whether retrying is safe.

## Cheap validators that pay off

- **stable-key retry:** inject a timeout after provider acceptance and assert every replay uses the original idempotency key.
- **payload drift:** mutate one effect-relevant field and assert the stored fingerprint blocks replay under the old key.
- **worker race:** run concurrent reconcilers and assert only one lease holder can dispatch.
- **lost-response recovery:** return success from the fake provider, drop the response, then prove lookup adopts the existing effect without a second mutation.
- **eventual-consistency delay:** hide the effect for several reads and assert the worker waits instead of treating early absence as proof.
- **conflict fixture:** return the same key with a different target or amount and assert automation enters `conflict`.
- **retention expiry:** advance a fake clock beyond provider key retention and assert automatic replay fails closed.
- **terminal readback:** require every `confirmed` operation to contain a provider ID or target evidence reference.

Run these with a fake provider and fake clock. Real sleeps and production side effects make the tests slower without proving the state machine.

## Acceptance criteria

Ambiguous side-effect reconciliation is ready when:

- every write-capable tool documents its idempotency and lookup semantics,
- the operation record exists before external dispatch,
- retries preserve both the operation identity and payload fingerprint,
- ambiguous transport failures cannot enter a normal retry path,
- reconciliation is single-writer across concurrent workers,
- matching effects are adopted rather than duplicated,
- absence must be authoritative before an automatic replay,
- inconclusive outcomes stop at a bounded review state,
- user-facing status never claims failure or success without corresponding evidence,
- tests cover lost responses, delayed visibility, payload conflicts, concurrent workers, and expired dedupe windows.

## Anti-patterns

- Generating a new idempotency key for every HTTP attempt.
- Treating timeout, connection reset, or gateway `5xx` as proof the write did not happen.
- Marking an operation successful from a local queue acknowledgment without provider or target evidence.
- Retrying because a webhook has not arrived yet.
- Asking a model to infer whether two loosely described effects are the same.
- Using eventual-consistency reads as authoritative absence checks.
- Holding reconciliation state only in worker memory.
- Reusing an approval or idempotency key after changing effect-relevant payload fields.
- Polling forever instead of moving the operation to a bounded manual-review state.
