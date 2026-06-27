# Experiment: Contribution Engine

## Question

Can an automated GitHub workflow create credible public activity without producing fake commits?

## Hypothesis

Yes, if each run is constrained to produce a small useful artifact with a real topic, a durable file path, and a verification step. The automation should skip commits when it has nothing substantive to add.

## Non-goals

- Commit streak farming
- Timestamp-only updates
- README whitespace churn
- Fabricated benchmarks or fake usage data

## Contribution quality bar

A generated contribution is acceptable only if it adds one of:

1. a reusable checklist or pattern,
2. a runnable script,
3. an experiment note with a concrete question and takeaway,
4. a small refactor/improvement to existing artifacts,
5. a result derived from a real command or public source.

## First implementation

A scheduled Hermes job will run twice daily. It will inspect this repo, choose one small applied-AI/product-engineering improvement, edit files, run lightweight validation, commit, and push only if there is a real diff.

## Why twice daily

Multiple commits per day can be useful if they represent real work. Past that, activity starts looking synthetic. Two good contributions per day beats six obvious filler commits.
