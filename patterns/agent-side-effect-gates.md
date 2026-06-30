# Agent Side-Effect Gates

Use this pattern when an AI agent can change something outside its draft surface: sending messages, opening pull requests, editing records, charging money, publishing content, or triggering infrastructure. The goal is to keep fast agent execution while making irreversible or user-visible effects explicit, reviewable, and hard to trigger by accident.

## Problem

Agent products often treat every tool call like the same kind of action. Reading a file, drafting a reply, and sending that reply may all sit behind one natural-language instruction. That feels simple until a model follows stale context, over-trusts a retrieved note, or acts before the user has seen the final artifact.

A side-effect gate separates thinking, preparation, and external mutation. The agent can still do useful work autonomously, but the product makes the risky boundary visible.

## Gate levels

| Level | Allowed action | Requires | Product example |
| --- | --- | --- | --- |
| Read | Inspect data without changing it. | Normal auth and audit trail. | Search docs, read issues, fetch analytics. |
| Draft | Create a proposed artifact that has no external effect. | Saved preview with source context. | Draft an email, build a migration plan, prepare a PR body. |
| Stage | Prepare a reversible change in a contained surface. | Diff, rollback path, and reviewer-visible summary. | Create a branch, queue a campaign, stage product copy. |
| Execute | Mutate external state or expose output to users. | Explicit approval, scoped identity, and post-action verification. | Send, publish, deploy, merge, charge, delete. |

## Required fields

Represent every gated action as a small object before execution:

```json
{
  "action_id": "publish_release_notes_2026_06",
  "gate_level": "execute",
  "target": "public changelog",
  "summary": "Publish release notes for the June agent workflow update.",
  "evidence": ["diff:docs/changelog.md", "check:markdown-validator"],
  "blast_radius": "public page update only",
  "rollback": "revert the changelog commit and redeploy",
  "approval_required": true
}
```

Keep this object close to the tool call or job record. If the product cannot show the object, it cannot reliably explain what the agent is about to do.

## Default flow

1. Classify the requested action before tool execution.
2. Let the agent complete read and draft work without interruption.
3. For stage actions, show the exact diff or queued mutation plus the rollback path.
4. For execute actions, require an explicit approval event tied to the action id.
5. Run the external action using the narrowest identity that can complete the job.
6. Verify the effect from the outside, not only from the tool response.
7. Store the action object, approval event, and verification result together.

## Good default UX

- Show the action summary in verbs a user understands: "send 3 emails," not "run tool batch_send".
- Put the risky boundary at the button: "Approve and send" beats a generic "Continue".
- Keep low-risk prep fast; do not make the user approve every read or draft step.
- Render the proposed mutation before the approval button, not hidden behind an expandable log.
- Separate "edit draft" from "approve execution" so correction does not imply consent.

## Cheap validators

- **classification check:** fail if a tool marked `execute` is called without an action object.
- **approval check:** fail if `approval_required` is false for public, financial, destructive, or user-contacting effects.
- **diff check:** fail staged code or content changes that have no reviewer-visible diff.
- **rollback check:** warn when an execute action has no named rollback path.
- **verification check:** require a post-action readback for publish, deploy, merge, or send flows.

## Acceptance criteria

A side-effect gate is ready when:

- every tool that mutates external state has a declared gate level,
- the user can see what will change before approving execution,
- approvals are bound to a specific action id and cannot be reused for a different mutation,
- logs distinguish draft, stage, and execute states,
- the system records who or what approved the execute action,
- the product verifies the result after the mutation and stores that verification.

## Anti-patterns

- Asking for blanket approval at the start of a session and treating it as permission for every later mutation.
- Hiding important effects inside vague buttons like "Run workflow".
- Letting the model lower the gate level after it has already planned the action.
- Treating a successful API response as proof that users can see the intended result.
- Blocking harmless read and draft work behind the same approval flow as public execution.
