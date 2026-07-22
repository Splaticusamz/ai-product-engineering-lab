# Agent Circuit Breakers

Use this pattern when many agent jobs share a model, tool, provider, credential, or workflow stage that can fail repeatedly. A retry budget limits one job. A circuit breaker protects the whole system from sending more work into a dependency or behavior that is already failing.

## Problem

An agent worker can follow its local retry policy and still create a fleet-wide failure loop. Fifty jobs may each make three reasonable attempts against the same unavailable API, invalid prompt release, expired credential, or unsafe output path. The result is avoidable spend, noisy incidents, duplicate side effects, and users waiting on work that cannot currently succeed.

A circuit breaker aggregates failure evidence across jobs, opens a narrowly scoped circuit, and routes new work to a safe fallback until a controlled probe proves recovery. It is not a substitute for timeouts, retries, rate limits, or provider health checks. It decides when normal execution should stop.

## State model

| State | Normal work | Probe work | Transition |
| --- | --- | --- | --- |
| `closed` | Allowed | Not needed | Open when a rolling failure policy trips. |
| `open` | Blocked or routed to fallback | Blocked until `retry_after` | Move to half-open after cooldown or an explicit operator reset. |
| `half_open` | Blocked | Allow a small fixed number of safe probes | Close after the success threshold; reopen on a qualifying failure. |

Persist the state outside individual workers. Transitions need an atomic compare-and-set or lease so a hundred workers do not all become the first half-open probe.

## Scope before threshold

The scope key is more important than the trip count. Make it narrow enough to preserve healthy traffic and broad enough to stop the shared failure.

```text
(provider, capability, model_or_api_version, tenant_or_credential, environment)
```

Examples:

- Open `image-provider / generate / model-v4 / credential-a / production` when that model endpoint is timing out.
- Open `email-tool / send / api-v2 / tenant-42 / production` when one tenant's credential is revoked.
- Open `planner / structured-output / prompt-8f31 / all-tenants / production` when a prompt release causes schema failures across unrelated inputs.
- Do not open a provider-wide circuit because one user uploaded an unsupported file.

Avoid unbounded high-cardinality keys such as raw user IDs or request hashes. Define the allowed dimensions and retention policy before the breaker ships.

## Failure classification

Count only failures that predict another request in the same scope will also fail.

| Failure class | Shared circuit signal? | Default response |
| --- | --- | --- |
| Provider timeout, connection failure, or sustained `5xx` | Yes | Trip the dependency scope after the rolling threshold. |
| Rate limit | Yes, but keep it separate from outage errors | Respect provider reset metadata and reduce concurrency. |
| Revoked or expired credential | Yes, scoped to that credential or tenant | Open immediately and request credential repair. |
| Repeated schema-invalid model output across varied inputs | Yes, scoped to model plus prompt version | Fall back to the last known-good route or human review. |
| Safety-policy rejection caused by a release regression | Yes, scoped to the changed policy or prompt lane | Stop automated execution and preserve drafts for review. |
| Invalid user input or unsupported file | No shared trip | Return an actionable validation error for that request. |
| Missing per-job approval | No shared trip | Pause only the affected job. |
| Business-rule rejection | Usually no | Treat it as a product result unless the rule itself is malfunctioning. |

Use machine-readable error classes. Searching free-form exception text for words such as `timeout` will produce unstable trip behavior.

## Breaker policy

Keep the policy explicit and versioned with the workflow:

```json
{
  "scope": ["provider", "capability", "model_version", "credential", "environment"],
  "window_seconds": 60,
  "minimum_requests": 20,
  "open_when_failure_rate_gte": 0.5,
  "open_immediately_on": ["credential_revoked", "unsafe_release_regression"],
  "cooldown_seconds": 120,
  "half_open_max_probes": 3,
  "close_after_successes": 3,
  "fallback": "queue_draft_for_review"
}
```

A minimum request count prevents two failures during low traffic from looking like a 100% outage. Immediate-open classes are reserved for failures where another attempt is predictably unsafe or useless.

## Execution flow

1. Derive the circuit scope from trusted runtime configuration, not model-authored fields.
2. Read the current state before reserving provider capacity or spending tokens.
3. If open, return the named fallback and `retry_after`; do not consume the job's retry budget.
4. If half-open, atomically claim one probe slot. All other jobs continue using the fallback.
5. Execute with the same timeout, validation, authorization, and side-effect controls used in closed state.
6. Record a classified outcome against the scope and policy version.
7. Atomically transition the state when the rolling or probe threshold is met.
8. Emit one event for the transition, not one alert for every blocked request.

For external mutations, the half-open probe must be read-only or use a provider-supported idempotency key against a disposable target. Never test recovery by sending a real customer message, charging a card, publishing content, or deleting data.

## Fallback contract

Opening a circuit should create a useful degraded state rather than a vague failure:

- save model input and safe intermediate artifacts without storing secrets,
- mark the job `deferred_dependency` instead of `failed` when automatic replay is allowed,
- show the affected capability and next retry time in user language,
- route to a last known-good model only when output contracts and safety policy remain equivalent,
- cap the deferred queue and expire work that would be stale or dangerous to replay,
- require fresh approval before replaying time-sensitive or user-visible mutations.

Do not silently switch to a cheaper or less capable model if that changes the promised result. A fallback is part of the product contract, not an infrastructure trick.

## Cheap validators that pay off

- **scope isolation:** a synthetic tenant credential failure opens only that credential's circuit.
- **single-probe concurrency:** concurrent half-open claims produce no more than the configured probe count.
- **non-signal exclusion:** invalid input and missing approval never increase the shared failure numerator.
- **fallback preservation:** blocked jobs retain their safe draft and expose a stable reason code.
- **mutation safety:** every half-open probe for a write-capable tool is rejected unless it is provably non-mutating or idempotent on a disposable target.
- **recovery hysteresis:** one success cannot close a circuit that requires three successful probes.
- **queue bound:** deferred work stops accumulating at the configured count, age, or cost ceiling.

Test transitions with a fake clock and deterministic outcome stream. Sleeping through real cooldowns makes the suite slow and leaves race conditions untested.

## Acceptance criteria

A circuit breaker is ready when:

- repeated shared failures stop normal calls before each job exhausts its own retries,
- circuit keys isolate healthy tenants, credentials, models, and capabilities,
- state transitions and half-open probe claims are atomic across workers,
- user mistakes and per-job approval failures cannot trip shared circuits,
- open-state responses provide a bounded fallback and honest retry timing,
- write-capable recovery probes cannot create an unapproved real-world effect,
- dashboards expose state, scope, policy version, trip reason, blocked count, and recovery result,
- operators can force open or reset a circuit with an audited action,
- recovery tests prove both successful closure and immediate reopening on a failed probe.

## Anti-patterns

- Giving every worker an in-memory breaker and assuming the fleet shares state.
- Opening one global `model_provider_down` flag for a model-specific or tenant-specific error.
- Counting validation errors, policy denials, and outages in one undifferentiated failure rate.
- Allowing every waiting job to probe as soon as the cooldown expires.
- Closing on elapsed time without a successful controlled probe.
- Replaying a deferred queue without checking staleness, approval, idempotency, and current policy.
- Treating a breaker as a way to hide recurring failures instead of fixing the dependency or release.
