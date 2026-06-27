# Experiment: Lightweight Agent Output Evals

## Question

What is the smallest useful eval harness for an AI product feature or agent workflow?

## Hypothesis

A tiny rubric-based scorer is enough to catch many regressions before building a full eval platform, as long as the rubric tests product usefulness instead of only syntax.

## What this experiment covers

The included scorer checks generated agent artifacts against five practical dimensions:

1. **grounding** — includes evidence, source paths, URLs, command output, or user-provided context
2. **specificity** — avoids generic advice and names concrete files, actions, or decisions
3. **actionability** — gives a clear next move or completed result
4. **safety** — distinguishes drafts from irreversible/public side effects
5. **format** — follows the expected shape for the task

This is not a replacement for human review. It is a cheap preflight check that prevents obvious low-quality output from being treated as done.

## Run

```bash
python3 scripts/score_agent_output.py experiments/lightweight-agent-evals/fixtures/sample_outputs.json
```

## Takeaway

For early AI product work, useful evals should be boring and close to the user workflow. A five-point rubric with examples catches more product failures than a complex benchmark that does not match the product surface.
