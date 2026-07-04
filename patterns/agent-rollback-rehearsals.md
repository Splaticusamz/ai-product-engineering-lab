# Agent Rollback Rehearsals

Use this pattern when an autonomous agent is about to make a reversible but user-visible change: deploy a site, migrate a schema, publish a public artifact, rotate configuration, or enable a recurring automation. The goal is to prove the rollback path before the forward action makes the system harder to recover.

## Problem

Agents are good at moving forward and bad at noticing that "reversible" often means "reversible only if someone remembered the previous state." A deployment can be rolled back if the previous build id is known. A content change can be reverted if the exact diff is isolated. A config edit can be undone if the old value is captured without leaking secrets.

A rollback rehearsal is a small preflight artifact that names the previous state, the intended mutation, the restore command or edit, and the signal that would trigger recovery. It does not require performing the rollback every time. It requires making the rollback executable enough that a later operator is not forced to reconstruct it during an incident.

## Required fields

| Field | What it records | Example |
| --- | --- | --- |
| `surface` | The route, branch, table, workflow, config key, or file set being changed. | `origin/main + patterns/*.md` |
| `forward_action` | The exact command, API call, deploy, or edit that will create the new state. | `git commit && git push origin main` |
| `state_snapshot` | The readback needed to return to the previous state. | `HEAD before commit: abc1234` |
| `rollback_action` | The smallest safe restore path. | `git revert <new_commit> && git push origin main` |
| `trigger_signal` | The observation that should start rollback instead of more patching. | `validator fails on main after push` |
| `owner_gate` | Whether rollback can run automatically or needs approval. | `auto for revert-only public note; approval for data deletion` |

## Default flow

1. Capture the current state immediately before mutation: commit SHA, deployment id, schema version, config key name, or artifact checksum.
2. Keep the forward action narrow enough that one rollback action can explain it. If the change needs unrelated rollback paths, split it.
3. Write the rollback action in command-shaped language, even if it will be executed manually.
4. Mark rollback triggers that require immediate action versus investigation first.
5. Keep secrets out of the snapshot. Store secret names, versions, or checksums rather than raw values.
6. After the forward action, verify both the new state and the rollback handle: new commit id, deploy id, migration version, or content hash.
7. Include the rollback handle in the final report or PR body when the change is public, scheduled, or production-facing.

## Cheap validators that pay off

- **snapshot check:** fail if a public mutation has no previous commit, deploy id, version, or state handle.
- **scope check:** warn when one forward action touches surfaces that need different rollback mechanics.
- **command-shape check:** fail rollback text that says only "revert if broken" without naming the command or edit path.
- **trigger check:** require at least one measurable rollback signal, such as failed smoke test, 5xx spike, missing page text, or schema read failure.
- **secret check:** block snapshots that include raw tokens, credentials, customer data, or internal webhook URLs.

## Acceptance criteria

A rollback rehearsal is useful when:

- another operator can identify the previous state without reading the whole session log,
- the rollback action is smaller than the forward action,
- the trigger signal is concrete enough to prevent argument during an incident,
- sensitive values are referenced by handle instead of copied into public notes,
- the final delivery names the new state and the restore handle together.

## Anti-patterns

- Calling a change reversible because Git exists while committing unrelated files together.
- Capturing rollback notes at the start of a long run and not refreshing them before the side effect.
- Treating rollback as failure instead of a normal safety control for fast shipping.
- Writing a restore plan that depends on private chat context unavailable to the next operator.
- Continuing to patch forward after a rollback trigger has fired and the blast radius is still unknown.
