# AI Output Review Loop

Use this pattern when an AI feature generates work that a user may edit, approve, publish, send, or save. The goal is to make review feel like a product surface, not a text box with a model behind it.

## Problem

Many AI product flows collapse three separate jobs into one screen:

1. generate an answer,
2. decide whether it is trustworthy,
3. take an external action.

That makes the user do invisible QA. A better loop exposes state, evidence, and the next safe action.

## Review states

| State | User question | Product requirement |
| --- | --- | --- |
| Drafted | Did the model produce something usable? | Show the output next to the input brief and constraints. |
| Grounded | Why should I trust this? | Attach sources, command output, retrieved records, or explicit assumptions. |
| Checked | What could be wrong? | Run schema, policy, citation, or task-specific validators before approval. |
| Editable | Can I fix it quickly? | Provide inline edits, regenerate controls, and preserve the original draft. |
| Approved | Am I comfortable with the side effect? | Require an explicit user action before posting, emailing, buying, deleting, or deploying. |
| Logged | Can we learn from this? | Store the outcome, failure reason, and accepted revision without retaining unnecessary private content. |

## Acceptance criteria

A generated artifact is ready for user approval only when:

- the source input or brief is visible without opening another tool,
- assumptions are labeled separately from verified facts,
- every external side effect is still blocked behind an explicit approval control,
- the user can edit the output before the side effect runs,
- at least one cheap validator has run successfully or failed with a clear reason,
- the product records whether the output was accepted, edited, rejected, or retried.

## Cheap validators that pay off

Start with validators that catch boring failures before building a full eval stack:

- **shape check:** JSON schema, required markdown headings, required email fields, or max length,
- **grounding check:** at least one cited source, retrieved record id, command output, or file path when the task claims evidence,
- **action check:** public or irreversible actions require an approval flag that defaults to false,
- **privacy check:** block obvious secrets, private labels, or unsupported retention of user-provided content,
- **diff check:** for code or document edits, show the actual changed lines before approval.

## UX examples

- A support-reply drafter shows the customer message, the proposed reply, cited policy snippets, and buttons for `Edit`, `Regenerate`, `Send`, and `Save as macro`.
- A code-agent summary links to changed files, includes the exact verification command output, and labels unresolved risks before the user merges.
- A research assistant separates `Found evidence` from `Open questions` and refuses to label the report complete if every claim came from the model alone.

## Anti-patterns

- A single `Generate` button that immediately posts or sends the result.
- Hiding retrieval context behind a debug drawer that normal users never open.
- Treating schema-valid output as product-valid output.
- Logging full prompts and user documents by default because they may be useful later.

## Implementation note

The fastest version is usually a two-column review screen: left side input/evidence, right side editable draft and approval controls. Add automation around that loop only after users can understand and correct the output.