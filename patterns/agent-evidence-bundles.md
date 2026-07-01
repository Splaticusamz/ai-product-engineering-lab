# Agent Evidence Bundles

Use this pattern when an AI agent finishes work that someone else must trust: code changes, data cleanup, production checks, research synthesis, or any workflow where the final answer should be backed by inspectable proof. The goal is to make verification portable instead of burying it in chat history or transient logs.

## Problem

Agent outputs often sound more certain than their evidence supports. A model may say a build passed, a page was checked, or a dataset was cleaned, but the useful proof lives in scattered terminal output, browser state, API responses, and local assumptions. When the next reviewer cannot reconstruct what was checked, they either re-run everything or trust a summary blindly.

An evidence bundle is a small, structured packet that travels with the artifact. It names the claim, the command or observation that supports it, the scope of what was not checked, and the next verification step if the environment changes.

## Required fields

| Field | What it captures | Example |
| --- | --- | --- |
| `claim` | The specific result being asserted. | `checkout form accepts a valid test inquiry` |
| `artifact` | The file, URL, commit, dataset, or job output under review. | `app/contact/page.tsx` |
| `evidence_type` | Command, browser smoke test, API readback, fixture diff, or manual observation. | `command` |
| `evidence` | Exact command/output excerpt, URL/status, or screenshot reference. | `npm run build -> exit 0` |
| `scope` | What the evidence does and does not cover. | `desktop build only; no payment provider call` |
| `freshness` | When or from which revision the evidence was captured. | `commit 3b8e2a1` |
| `follow_up` | The cheapest future check that would increase confidence. | `submit one production form after deploy` |

## Minimal packet

```json
{
  "claim": "pattern notes pass the repository markdown gate",
  "artifact": "patterns/agent-evidence-bundles.md",
  "evidence_type": "command",
  "evidence": "python3 scripts/validate_markdown.py -> Validated 8 markdown files.",
  "scope": "Markdown structure only; does not judge product usefulness.",
  "freshness": "working tree before commit",
  "follow_up": "Run public_content_guard.py before publishing."
}
```

## Default flow

1. Write the claim before collecting proof. If the claim is vague, the evidence will be vague too.
2. Capture the smallest external check that could falsify the claim: test command, HTTP status, API readback, validator output, or visible UI state.
3. Store the exact command and a short output excerpt, not a paraphrase like "tests passed".
4. Record the scope honestly. A local unit test does not prove production wiring; a production smoke test does not prove every edge case.
5. Attach the bundle to the final artifact: PR body, release note, incident note, generated report, or handoff packet.
6. If verification fails, keep the failed evidence and update the claim instead of deleting the inconvenient output.

## Good default UX

- Put evidence next to the claim it supports, not in a separate debug log users will never open.
- Use short proof chips for common checks: `build: pass`, `smoke: 200`, `guard: no findings`.
- Make stale proof visually obvious when the artifact changes after the bundle was captured.
- Let reviewers expand raw output only when they need detail; keep the default view high-signal.
- Prefer one decisive check over five noisy checks that do not map to the user-visible claim.

## Cheap validators that pay off

- **claim-output match:** fail if a report claims validation but contains no command, URL readback, or fixture reference.
- **exit-code check:** require command evidence to include pass/fail status or an exit code.
- **scope check:** warn when evidence uses absolute language such as "fully verified" without a stated boundary.
- **freshness check:** mark bundles stale when the referenced file, URL version, or commit changes after capture.
- **negative-evidence check:** require failed checks to remain visible in incident or debugging bundles.

## Acceptance criteria

An evidence bundle is ready when:

- every user-visible claim has at least one supporting observation,
- the observation is specific enough for another builder to re-run or inspect,
- the bundle names what was not covered,
- freshness is tied to a revision, timestamped job, or production readback,
- failed checks are represented as evidence rather than omitted from the story,
- a reviewer can decide the next cheapest confidence-building action without asking the original agent.

## Anti-patterns

- Saying "verified" when the only evidence is that the agent edited the file without errors.
- Pasting entire logs with no claim mapping, forcing reviewers to hunt for the important line.
- Treating a provider success response as proof that the user-visible result works.
- Updating the artifact after tests pass and shipping the stale evidence bundle anyway.
- Hiding partial or failed checks because they make the final report look less clean.
