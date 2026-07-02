# Agent Escalation Packets

Use this pattern when an AI agent cannot safely finish a task on its own and must hand the next decision to a human, another agent, or a slower review workflow. The goal is to stop cleanly with useful context instead of leaving a vague failure message that forces the next operator to rediscover the same facts.

## Problem

Many agent failures are reported as conversational dead ends: "I could not complete this" or "permission is missing." That may be honest, but it is rarely operational. The next person still needs to know what was attempted, what changed, what evidence was collected, and what exact decision would unblock progress.

An escalation packet turns a stalled run into a reusable handoff artifact. It preserves the useful work, names the remaining risk, and makes the next action narrow enough that a reviewer can approve, reject, or redirect without replaying the whole session.

## Escalation triggers

Escalate instead of retrying when any of these are true:

| Trigger | Why automatic continuation is risky | Example packet focus |
| --- | --- | --- |
| Missing authority | The agent cannot grant itself approval for a public, financial, destructive, or user-contacting action. | Exact approval needed and blast radius. |
| Missing credential | Another attempt will fail until a secret, login, or integration is configured. | Credential scope and verification command. |
| Ambiguous product intent | Multiple reasonable choices change user-visible behavior. | Decision options with tradeoffs. |
| Repeated structural failure | Retries changed inputs but hit the same validator, build, or API contract failure. | Failed attempts and smallest reproducible case. |
| Evidence conflict | Sources, logs, or tool outputs disagree in a way the agent cannot resolve safely. | Conflicting claims and source ids. |

## Required fields

Represent the escalation as a compact object before ending the run:

```json
{
  "task": "Deploy the catalogue admin route",
  "current_state": "Build passes locally; production deploy is blocked by missing provider auth.",
  "attempts": [
    "npm run build -> exit 0",
    "vercel deploy --prod -> auth token missing"
  ],
  "blocked_by": "Vercel account token with project deploy scope",
  "risk_if_forced": "A guessed deploy target could publish the wrong project.",
  "decision_needed": "Provide deploy auth or choose local-only handoff.",
  "safe_next_action": "Run vercel whoami, then deploy the current commit after auth is restored."
}
```

## Default flow

1. Classify the blocker before writing the final report: authority, credential, ambiguity, repeated structural failure, or evidence conflict.
2. Preserve concrete evidence from the last useful attempt: command, exit status, URL readback, diff, validator finding, or API response summary.
3. Separate completed work from unsafe or impossible work. Do not make the reviewer infer what is already done.
4. State the narrowest decision needed. Avoid broad asks like "what should I do?" when the real ask is "approve this deploy target."
5. Name the safest next action after the decision, including the command or product step that should be run first.
6. Include rollback or blast-radius notes when the next action mutates public state, data, infrastructure, or spending.
7. Keep the packet short enough to fit in the issue, PR, job report, or handoff surface where the next operator will actually see it.

## Good default UX

- Show the blocker as a decision card, not as a generic error toast.
- Put the exact approval or credential scope next to the resume button.
- Let the reviewer copy the safe next command without opening raw logs.
- Keep failed attempts visible, but collapse long traces behind the one-line reason they matter.
- Make the packet durable: attach it to the job record, PR, issue, or incident note rather than only the chat transcript.

## Cheap validators that pay off

- **blocker-class check:** fail escalation reports that do not identify one blocker class.
- **evidence check:** require at least one attempted command, observation, or source id.
- **decision check:** fail reports whose `decision_needed` is a broad question instead of a specific approval, credential, or product choice.
- **resume check:** require one safe next action that can be executed after the decision.
- **mutation check:** require blast-radius or rollback notes when the next action can publish, send, charge, delete, or change production state.

## Acceptance criteria

An escalation packet is ready when:

- completed work and blocked work are clearly separated,
- every blocker is tied to evidence rather than a guess,
- the decision needed is specific enough for a reviewer to answer in one pass,
- the safe next action is executable and scoped,
- retry history shows what changed between attempts when retries happened,
- risky continuation paths name their blast radius or rollback path,
- another operator can resume without rereading the whole session transcript.

## Anti-patterns

- Ending with "blocked" but no command, URL, or source that proves where it blocked.
- Asking for open-ended guidance when only one approval or credential is missing.
- Retrying a structural failure until the budget is spent, then omitting the failed attempts.
- Mixing speculative root cause with observed evidence in the same sentence.
- Hiding partial completed work because the overall task was not fully finished.
- Treating escalation as failure instead of the safest completed state for the current authority boundary.
