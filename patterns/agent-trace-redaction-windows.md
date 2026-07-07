# Agent Trace Redaction Windows

Use this pattern when an AI product needs useful traces for debugging, evals, audits, or handoffs, but the raw run may contain user text, retrieved records, credentials, internal URLs, or commercially sensitive context. The goal is to preserve the decision shape without turning observability into a second data leak.

## Problem

Agent traces are tempting to store forever because they explain why a workflow behaved the way it did. The same trace can also contain the most sensitive material in the system: copied source documents, tool outputs, user messages, file paths, prompts, environment names, and failed payloads. If everything lands in one generic log stream, the team has to choose between blind debugging and over-retention.

A redaction window makes trace handling explicit. The product keeps the full trace only inside a short, access-limited window, extracts the durable fields needed for learning, then drops or masks the raw material before it becomes default operational history.

## Trace layers

| Layer | Retention intent | Safe contents | Example |
| --- | --- | --- | --- |
| `raw_window` | Short-lived incident/debugging access. | Full trace with restricted access and expiry. | 24-hour encrypted run log for a failed import. |
| `review_summary` | Human triage and handoff. | Sanitized excerpts, decisions, error classes, and evidence ids. | `model cited source_12 but ignored newer source_18`. |
| `eval_fixture` | Regression learning. | Minimal public-safe or internal-safe reproduction. | JSON case with fake names and same failure class. |
| `metrics` | Trend monitoring. | Counts, latency, cost, pass/fail states, labels. | `unsupported_claim: 3 of 50 runs`. |

Do not let the `raw_window` quietly become the product's permanent memory. If a field is needed after the window closes, promote a safer derived version on purpose.

## Required fields

Every trace policy should name the boundary before the workflow ships:

| Field | What it forces | Example |
| --- | --- | --- |
| `trace_owner` | Who can approve access or retention changes. | `support engineering lead` |
| `raw_ttl` | How long full traces remain available. | `24h` |
| `redaction_rules` | What gets removed, masked, or replaced. | `emails -> role labels; tokens -> secret handle` |
| `durable_fields` | What survives after the window. | `failure_class, evidence_id, validator_message` |
| `access_path` | Where reviewers request raw access during the window. | `incident ticket with run id` |
| `deletion_check` | How expiry is verified. | `nightly job reports expired trace count = 0` |

## Default flow

1. Classify the run before logging: draft assist, user-facing decision, external mutation, incident, or eval capture.
2. Store raw traces only in the narrowest place that supports the classification, with expiry attached at write time.
3. Generate a `review_summary` immediately so most debugging does not require raw access.
4. Replace direct identifiers with stable handles that can be resolved by authorized systems, not by public notes or screenshots.
5. Promote only durable fields needed for quality loops: failure class, validator output, source ids, decision delta, retry count, and verified command or URL evidence.
6. Convert useful misses into sanitized fixtures while the reviewer still remembers what mattered.
7. Prove expiry with a check that runs outside the agent path that created the trace.

## Good default UX

- Show reviewers the sanitized summary first and make raw access an explicit action with a reason.
- Label time remaining in the raw window: `raw trace expires in 18h` beats hidden retention rules.
- Keep evidence ids clickable for authorized users without copying full source text into the summary.
- Let a reviewer mark `fixture candidate` from the summary view, then walk them through redaction before saving.
- Show when a trace has expired and which durable fields remain, instead of returning a vague missing-log error.

## Cheap validators that pay off

- **ttl check:** fail trace writes that do not include an expiry timestamp for raw payloads.
- **durable-field check:** fail if a permanent log stores full user input, retrieved source text, or tool payloads when a handle would work.
- **secret-pattern check:** scan summaries and fixtures for tokens, keys, webhooks, and copied credentials before commit or export.
- **fixture-minimality check:** require a short explanation of which details were changed and why the failure still reproduces.
- **access-audit check:** record raw trace reads separately from normal summary views.

## Acceptance criteria

A trace redaction window is working when:

- the team can debug common failures from sanitized summaries without opening raw traces,
- raw traces have a visible expiry and a tested deletion path,
- durable logs keep enough evidence to reproduce product failures without retaining unnecessary source material,
- eval fixtures preserve the failure shape while removing direct identifiers and copied payloads,
- raw access is auditable and tied to a reason,
- public or cross-team artifacts never require readers to inspect sensitive raw context.

## Anti-patterns

- Saving every prompt, retrieved document, and tool response forever because it might be useful later.
- Redacting only final answers while keeping raw inputs in screenshots, background logs, or fixture files.
- Using irreversible hashing for values that still need authorized resolution during an incident.
- Treating metrics as anonymized when small segment counts can reveal the original run.
- Making deletion a manual cleanup step that nobody verifies after the retention window closes.
