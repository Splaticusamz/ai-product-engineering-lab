# Agent Runbook Smoke Tests

Use this pattern when an autonomous or scheduled agent workflow is supposed to perform a small recurring job: publish one artifact, refresh a feed, triage an inbox, sync a database, or report that nothing changed. The goal is to prove the runbook still works without turning every run into a broad integration test.

## Problem

Agent runbooks often fail in quiet ways. The model may still return a confident final note while the job skipped the source-of-truth check, wrote to the wrong branch, used stale credentials, or validated only the draft file instead of the artifact that will become public.

A runbook smoke test is a narrow executable check that sits beside the operating instructions. It does not judge taste or strategy. It verifies that the run touched the expected surfaces, preserved safety gates, and collected enough evidence for a reviewer to trust the result.

## Required fields

Each recurring agent job should declare a compact smoke contract before execution:

| Field | What it proves | Example |
| --- | --- | --- |
| `job_goal` | The visible outcome the run is allowed to produce. | `one useful public repo contribution` |
| `allowed_surfaces` | Files, APIs, branches, or products the run may mutate. | `patterns/*.md`, `origin/main` |
| `preflight_checks` | Source-of-truth reads that must happen before mutation. | `git status`, `git rev-list origin/main...HEAD` |
| `mutation_evidence` | Diff, API response, or generated artifact path. | `git diff -- patterns/agent-runbook-smoke-tests.md` |
| `validation_commands` | Commands that must pass after mutation. | `python3 scripts/validate_markdown.py` |
| `stop_condition` | When the run should end without forcing output. | `no substantive diff after inspection` |

## Default flow

1. Read the runbook and the current repo or product state before choosing work.
2. Check that the local state matches the intended source of truth.
3. Make one bounded change that fits `job_goal` and `allowed_surfaces`.
4. Run the smallest validators that cover the changed artifact and the public safety rules.
5. Capture real command output, including skipped-run evidence when nothing changed.
6. Commit, publish, send, or mutate only after validation passes and the diff is still scoped.
7. Read back the external state after the side effect: remote commit, deployed URL, synced record, or queue status.

## Cheap validators that pay off

- **scope check:** fail if the diff touches paths outside `allowed_surfaces` without an explicit escalation note.
- **preflight check:** fail if the final report claims a source-of-truth read that is not present in the run log.
- **artifact check:** fail if a recurring contribution changes only metadata, dates, generated caches, or whitespace.
- **validation check:** fail if the job changed markdown or code but does not name the command that exercised it.
- **readback check:** warn when a public side effect has no remote or production confirmation after the write.

## Acceptance criteria

A runbook smoke test is ready when:

- a new operator can tell exactly what the job is allowed to change,
- skipped runs are treated as successful only when the stop condition is satisfied,
- every public mutation has at least one validator and one readback,
- command output is specific enough to distinguish real execution from a generated summary,
- the smoke test catches wrong-branch, stale-source, empty-diff, and unvalidated-artifact failures.

## Anti-patterns

- Treating a polished final message as proof that the recurring job actually ran.
- Running a broad test suite while skipping the one check that covers the changed artifact.
- Making the agent find work after it has already committed to producing a public side effect.
- Reporting "nothing to do" without showing the inspection that made the skip legitimate.
- Letting a scheduled job auto-expand its scope because the original small task was blocked.
