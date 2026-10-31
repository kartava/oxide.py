# Local Artifacts

This file is normative. Read [README.md](README.md) before you change it.

The repo has no issue tracker. Specs, design docs, ADRs, wayfinder maps and tickets are markdown files in the repo.

## Where they live

The artifacts sit flat in `docs/`, with no per-effort subfolder:

| File | Lifetime | Holds |
|---|---|---|
| `docs/spec.md` | Durable | The library's shape. One file, updated in place. |
| `docs/<kebab-name>.md` | Durable | One feature's design. No `-design` suffix. |
| `docs/adr/` | Durable | The ADRs. |
| `docs/map.md` | Temporary | The wayfinder map of the current effort. |
| `docs/tickets.md` | Temporary | The tickets of the current effort. |
| `CONTEXT.md` | Durable | The glossary, at the repo root. |

## Lifetimes

- A new feature updates `docs/spec.md` in place. The repo has one spec.
- `map.md` and `tickets.md` hold one effort at a time. Delete them when the effort lands.

## Shapes

| File | Shape |
|---|---|
| `spec.md` | `to-spec` |
| `<kebab-name>.md` | `new-design` |
| `adr/`, `CONTEXT.md` | `domain-modeling` |
| `map.md` | `wayfinder` |
| `tickets.md` | `to-tickets` |

## Writing rules

These apply to every durable doc: `spec.md`, design docs, `adr/` and `CONTEXT.md`. A doc is a reference a reader scans, not an essay a reader follows.

- **Lead with the decision.** State the fact, then the reason. No build-up, no rhetorical question, no metaphor.
- **Present tense, no history.** Describe the model as it is. Words that narrate the past — "used to", "no longer", "began as", "was the first choice", "earlier choice", "was reversed" — are findings. Git holds history.
- **Rejected options are short and complete.** `**Option.** Rejected: <reason>.` One or two sentences each. Keep every one; they are why the doc exists.
- **Three or more parallel items of one shape are a table.** Release paths, columns, decisions, consumers. Two items are a sentence.
- **One home per table.** A table lives in the doc that owns the decision; every other doc cites it by path (`adr/0004`) and does not repeat it.
- **Cite, do not repeat.** A rationale that an ADR already carries is one sentence plus the ADR number.
- **Flows are mermaid diagrams.** `sequenceDiagram` for messages between parts, `stateDiagram-v2` for status changes, `flowchart` for branching. Not numbered lists.
- **Bullets are one or two sentences.** A bullet that needs a paragraph is a section.
- **No orientation prose.** Cut "this section describes", "it is worth noting", "as discussed above".
- **Cross-file references are relative markdown links.** `[adr/0004](adr/0004-cancellation-window-starts-at-submit.md)`, `[CONTEXT.md](../CONTEXT.md)`. The label is the short form, the target is the path from the citing file. Backticks only for paths in another repo.
