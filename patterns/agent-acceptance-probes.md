# Agent Acceptance Probes

Use this pattern when an AI feature looks plausible in a demo but has not yet earned trust: generated plans, support drafts, product recommendations, extraction summaries, code patches, or autonomous task runs. The goal is to add a few cheap probes that catch false readiness before a full eval suite exists.

## Problem

Teams often jump from one happy-path demo to either shipping or building an oversized benchmark. Both moves hide the same risk: the feature may only work when the prompt, context, and reviewer are unusually friendly. An acceptance probe is a tiny, named scenario that stresses one product promise with a fixture, expected behavior, and a pass/fail check.

The probe is not a leaderboard score. It is a release gate for the next product decision.

## Required fields

Each probe should fit in a short record that a human or script can run repeatedly:

| Field | What it forces | Example |
| --- | --- | --- |
| `promise` | The user-facing claim being tested. | `agent can summarize blockers without hiding missing evidence` |
| `fixture` | The smallest realistic input that triggers the promise. | `task log with one passing command and one skipped deploy` |
| `expected_behavior` | What a trustworthy output must do. | `marks deploy as unverified and names the skipped smoke test` |
| `failure_signal` | The concrete thing that makes the probe fail. | `claims production is verified without a URL or command output` |
| `check_method` | Manual checklist, parser, snapshot, or script. | `python3 scripts/check_agent_artifact.py fixture.json` |
| `release_gate` | What decision this probe protects. | `allow scheduled agent reports to auto-send` |

## Default flow

1. Pull one promise from the product surface, not from a model capability list.
2. Write a fixture that includes one uncomfortable edge case: stale context, missing evidence, ambiguous approval, empty data, or conflicting instructions.
3. Define the expected behavior in terms a reviewer could reject, not vague quality language.
4. Add a failure signal that is easy to spot in a diff or validator output.
5. Run the probe manually first, then automate only the stable parts.
6. Keep probes small enough that a failure points to one repair path.
7. Retire or rewrite probes when the product promise changes.

## Good default UX

- Show probe status next to the feature's readiness claim: `3/4 probes passing` is more honest than `looks good`.
- Link each failing probe to the exact fixture and expected behavior.
- Separate `not run`, `failed`, and `blocked`; they require different release decisions.
- Let product owners add fixtures from real review misses after removing private or identifying material.
- Prefer named probes such as `missing-evidence-summary` over opaque case IDs.

## Cheap validators that pay off

- **unsupported-claim probe:** fixture has partial evidence; output must avoid verified language for untested steps.
- **stale-context probe:** fixture includes an older source and a newer source; output must cite the newer one.
- **approval-boundary probe:** fixture asks for a public or destructive action; output must stage or ask instead of executing.
- **empty-input probe:** fixture contains no usable records; output must return a clean empty state, not hallucinated examples.
- **conflicting-instruction probe:** fixture includes two incompatible goals; output must name the conflict before choosing a path.

## Acceptance criteria

Acceptance probes are working when:

- each probe protects one user-visible promise or release decision,
- a failing probe produces a specific repair target instead of a general quality complaint,
- fixtures are small, public-safe, and realistic enough to survive prompt changes,
- validation output can be pasted into a pull request or release note,
- the team learns whether to ship, repair, or expand eval coverage without running a heavy benchmark.

## Anti-patterns

- Calling a broad benchmark an acceptance probe when failures cannot be traced to a product promise.
- Writing probes from idealized examples that never include missing evidence or stale context.
- Treating manual reviewer taste as the only pass/fail check for operational claims.
- Letting probes become permanent paperwork after the protected release decision is gone.
- Using private customer logs as fixtures instead of sanitized, minimal reproductions.
