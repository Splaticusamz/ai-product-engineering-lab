# Agentic Feature Readiness Checklist

Use this before shipping an AI feature to real users.

## 1. User value

- [ ] The feature removes a concrete user task, not just adds an AI interaction.
- [ ] The user can describe what success looks like before the model runs.
- [ ] The output has a clear next action: accept, edit, retry, save, publish, send, or discard.

## 2. Control surface

- [ ] The user can inspect the input context used by the model.
- [ ] The user can constrain tone, scope, format, or sources without prompt engineering.
- [ ] The feature has undo or non-destructive review before external side effects.

## 3. Quality and evals

- [ ] There is a small golden set of representative tasks.
- [ ] Failures are categorized: hallucination, wrong source, wrong format, unsafe action, low usefulness.
- [ ] Model output is checked against schema or invariants before being shown as complete.
- [ ] At least one regression test covers a previously observed bad output.

## 4. Cost and latency

- [ ] The system knows the worst-case token/call path.
- [ ] Slow paths have progress states and cancellation.
- [ ] Expensive calls are cached or avoided when context has not changed.

## 5. Trust and safety

- [ ] The user sees which actions are drafts vs externally visible changes.
- [ ] Public posting, purchases, deletions, and sensitive disclosures require explicit approval.
- [ ] Logs avoid storing private user content unless retention is intentional.

## 6. Product polish

- [ ] Empty states teach the user what to try next.
- [ ] Error states explain what failed and what remains safe.
- [ ] The feature is still useful when the model fails.

## Good default UX

AI features should behave like a competent junior operator:

1. clarify only when ambiguity changes the outcome,
2. draft useful work from available context,
3. show evidence and uncertainty,
4. ask before irreversible side effects,
5. remember durable user preferences.
