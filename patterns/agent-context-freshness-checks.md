# Agent Context Freshness Checks

Use this pattern when an AI agent relies on memory, cached search results, previous tool output, or a long-running task state before making a recommendation or taking action. The goal is to make stale context visible before it turns into a wrong edit, duplicate ticket, bad deploy, or misleading status report.

## Problem

Agent workflows often mix live facts with remembered facts. A model may know what the repo looked like an hour ago, what a user preferred last week, or what a previous command returned before another job changed the branch. If the product does not force a freshness check, the agent can sound confident while acting on obsolete state.

A freshness check is a small readback step tied to a claim. It does not mean re-reading everything. It means refreshing the specific source of truth that would change the next action.

## Required fields

| Field | What it proves | Example |
| --- | --- | --- |
| `claim` | The fact the agent is about to rely on. | `main is up to date with origin/main` |
| `source_of_truth` | Where the fact must be refreshed from. | `git fetch + origin/main` |
| `freshness_window` | How old the readback may be before it expires. | `5 minutes for deploy state` |
| `readback` | The command, API response, URL, or file path just checked. | `git status --short -> clean` |
| `decision_if_changed` | What the agent will do if the fact is no longer true. | `pull before editing, or stop on conflict` |

## Default flow

1. List only the facts that can change the next action: branch state, deployment alias, issue status, quota, inventory, auth scope, or user approval.
2. Attach each fact to one source of truth. Avoid vague sources like "the docs" when a specific file, API endpoint, or CLI command exists.
3. Set a freshness window based on blast radius. A read-only research summary can tolerate older context than a publish, merge, send, or deploy action.
4. Refresh the fact immediately before the dependent action, not only at the start of the session.
5. If the readback disagrees with the plan, pause the action and record the changed condition instead of forcing the original path.

## Cheap validators that pay off

- **age check:** fail if a cached readback is older than the declared freshness window.
- **source check:** fail if a claim has no explicit source of truth.
- **side-effect check:** require fresh branch, deploy, auth, or approval state before public or irreversible actions.
- **conflict check:** block execution when the latest readback contradicts the planned mutation.
- **summary check:** require final reports to separate `checked_now` facts from assumptions or carried context.

## Acceptance criteria

A freshness check is working when:

- the agent can point to the exact live readback behind any action-changing claim,
- stale memories or previous tool output cannot override a newer source of truth,
- public side effects refresh their target state immediately before execution,
- reports say when important facts were checked, not just what the agent believed,
- the workflow stays narrow enough that refresh steps do not become busywork.

## Anti-patterns

- Treating a clean status from the start of a long session as proof that the branch is still clean before commit.
- Using project memory as the source of truth for live deployment, billing, auth, or inventory state.
- Re-running broad discovery instead of refreshing the one fact that can invalidate the next step.
- Reporting "verified" when the last evidence came from generated prose or an old screenshot.
- Continuing with the original plan after a readback shows the target moved.
