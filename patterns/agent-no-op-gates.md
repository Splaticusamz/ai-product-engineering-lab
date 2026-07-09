# Agent No-op Gates

Use this pattern when an autonomous or scheduled agent is allowed to make public or persistent changes, but only when the run discovers a genuinely useful artifact. The goal is to make `skip` a first-class successful outcome so automation does not manufacture low-value work to satisfy a cadence.

## Problem

Many agent loops are judged by whether they produced something. That incentive is dangerous for public repos, changelogs, content queues, dashboards, and knowledge bases. When the agent has no real improvement available, it may pad a diff with wording churn, broad summaries, fresh timestamps, or unverified claims.

A no-op gate protects the quality bar by forcing the agent to prove there is a substantive delta before it crosses the mutation boundary. The gate should run after discovery and before editing, committing, sending, or publishing.

## Required fields

| Field | What it forces | Example |
| --- | --- | --- |
| `run_goal` | The actual outcome the loop exists to create. | `maintain a reusable public AI product-engineering lab` |
| `candidate_delta` | The concrete improvement under consideration. | `new checklist for deciding when scheduled agents should skip` |
| `substance_test` | Observable proof that the delta is more than activity. | `adds a reusable decision rule not already present in patterns/` |
| `skip_conditions` | Reasons the agent must leave the target untouched. | `only timestamp, duplicate topic, no validator available, source material unsafe for public notes` |
| `mutation_boundary` | The first action that makes cleanup or review harder. | `write file`, `git commit`, `publish post`, `send notification` |
| `report_shape` | What the agent says when it skips. | `Skipped: repo already has this pattern; no commit made.` |

## Default flow

1. Refresh the target state before evaluating a candidate: branch, queue, issue, document, or deploy status.
2. Name one candidate delta in a sentence. If the agent cannot name it, stop with a no-op report.
3. Compare the candidate against nearby artifacts so duplicates do not pass as novelty.
4. Apply the substance test before mutation. A useful delta changes a decision, validator, workflow, fixture, or user-visible artifact.
5. Check the skip conditions. Any match should produce a clean no-op, not a watered-down contribution.
6. Only cross the mutation boundary after the candidate passes the gate.
7. After mutation, run the smallest validator that proves the changed artifact is still usable.

## Substance tests that work

- **decision utility:** a future operator can choose a different action because this artifact exists.
- **validator utility:** a script or checklist can reject a real failure class that previously slipped through.
- **workflow utility:** the artifact removes a repeated manual step or clarifies ownership at a handoff.
- **replay utility:** the artifact captures enough input, expected behavior, and evidence to rerun a case.
- **product utility:** a user-facing flow becomes safer, faster, more understandable, or easier to recover from.

## Good default UX

For scheduled or background systems, present no-op gates as quality protection rather than failure:

- **Run summary:** `No-op: no candidate passed the substance test.`
- **Operator dashboard:** show skipped runs beside shipped runs, with the skip reason and latest checked source.
- **Commit bot:** refuse commits that only change dates, headings, formatting churn, or generated status prose.
- **Queue worker:** mark `no useful action` separately from `blocked`, because blocked work needs intervention and clean no-ops do not.
- **Digest:** suppress routine no-op messages unless a pattern of skipped runs signals the loop has gone stale.

## Cheap validators that pay off

- **diff classifier:** fail if the diff only changes dates, whitespace, ordering, or broad filler language.
- **near-duplicate check:** compare the candidate title and summary against existing pattern names before writing.
- **evidence check:** require a command, source readback, fixture, or explicit observation for any validation claim.
- **public-safety check:** scan staged and untracked artifacts before commit, not only files already tracked.
- **skip-report check:** require skipped runs to state the checked target and the reason no mutation happened.

## Acceptance criteria

No-op gates are working when:

- automation can end successfully without changing anything,
- public or persistent surfaces receive only deltas that pass a named substance test,
- skipped runs leave the repo, queue, or document clean,
- final reports distinguish `nothing useful found` from `blocked` and `failed`,
- validators catch low-signal diffs before they become public activity.

## Anti-patterns

- Treating every scheduled run as obligated to write, commit, or publish.
- Using a fresh date, reordered bullets, or rewritten prose as proof of progress.
- Letting the agent invent a topic after duplicate checks fail.
- Reporting a no-op as failure when the correct outcome is preserving quality.
- Hiding skipped runs entirely until the automation silently becomes stale.
