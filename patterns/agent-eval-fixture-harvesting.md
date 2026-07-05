# Agent Eval Fixture Harvesting

Use this pattern when a real agent run fails, a reviewer corrects an AI-generated artifact, or a production workflow exposes a repeatable edge case. The goal is to turn lived failures into small eval fixtures before the details disappear into chat history or incident notes.

## Problem

Agent products often collect the weakest possible feedback signal: thumbs up, thumbs down, or a freeform complaint. That signal may be useful for analytics, but it is too thin to prevent the same failure on the next run. The practical unit of improvement is a fixture: input, expected behavior, observed failure, and the validator that would catch it.

Fixture harvesting is the habit of converting a concrete miss into a replayable case while the evidence is still fresh. It keeps evals grounded in real product behavior instead of synthetic benchmark tasks that never touch the messy parts of the workflow.

## Required fields

Each harvested fixture should be small enough to review in a pull request and complete enough to replay later.

| Field | What it captures | Example |
| --- | --- | --- |
| `source_event` | Where the case came from. | `support review`, `failed cron run`, `PR comment` |
| `user_goal` | The outcome the user or operator actually wanted. | `publish exactly one useful repo contribution` |
| `input_context` | The minimal prompt, payload, files, or state needed to replay the case. | `repo path, branch state, runbook excerpt` |
| `bad_output` | The specific artifact or behavior that failed. | `final report claimed validation without command output` |
| `expected_behavior` | What a passing run should do instead. | `stop, run validator, include real output` |
| `validator` | The cheapest check that catches the failure. | `assert evidence contains command + exit code` |
| `privacy_notes` | What was redacted or generalized before committing publicly. | `customer name replaced with role label` |

## Default flow

1. Capture the failure within the same work session, before the operator forgets the decisive context.
2. Reduce the case to the smallest input that still reproduces the wrong decision or bad artifact.
3. Write the expected behavior as an operational rule, not as a vague quality preference.
4. Add a deterministic validator first: parser assertion, fixture comparison, schema check, or checklist gate.
5. Redact private material at the boundary. Keep roles, constraints, and failure shape; remove names, secrets, and raw conversations.
6. Run the fixture against the current workflow and record whether it fails, passes, or is parked for a future harness.
7. Link the fixture back to the product rule or runbook it protects so it does not become orphaned test data.

## Minimal fixture shape

```json
{
  "id": "agent-report-validation-evidence-001",
  "source_event": "scheduled public repo maintenance run",
  "user_goal": "make one small, substantive contribution and report real validation output",
  "input_context": [
    "repo is clean and even with origin/main",
    "markdown artifact was changed",
    "runbook requires python3 scripts/validate_markdown.py"
  ],
  "bad_output": "final response says 'validation passed' but includes no command name, exit status, or output summary",
  "expected_behavior": "run the validator and include a compact output summary in the final report",
  "validator": "fail reports with validation claims that lack a command string and observed result",
  "privacy_notes": "public-safe synthetic repo state; no private content included"
}
```

## Cheap validators that pay off

- **replayability check:** fail fixtures that do not name the minimal input context or artifact path needed to rerun the case.
- **expectation check:** fail fixtures where `expected_behavior` describes taste instead of an observable decision or output.
- **privacy check:** require `privacy_notes` before committing fixtures derived from real users, clients, or internal runs.
- **validator check:** warn when a fixture has no parser, assertion, or manual checklist item that would catch the failure.
- **coverage check:** group fixtures by failure class so one workflow does not accumulate ten examples of the same mistake while ignoring missing-prerequisite or side-effect-risk cases.

## Acceptance criteria

Fixture harvesting is working when:

- real failures become replayable cases within one or two work sessions,
- each case contains enough context to reproduce the important decision without exposing private material,
- validators reject the bad output before a human has to explain the same correction again,
- product rules and runbooks gain coverage as incidents happen,
- old fixtures remain readable enough that a new maintainer can tell why the case exists.

## Anti-patterns

- Saving the full transcript instead of reducing the failure to the decision boundary.
- Writing fixtures only for embarrassing model mistakes while ignoring tool, context, and approval-gate failures.
- Calling a case an eval when no validator or review checklist can distinguish pass from fail.
- Committing private payloads because they are easier than constructing a safe minimal example.
- Letting harvested cases drift away from the workflow they are supposed to protect.
