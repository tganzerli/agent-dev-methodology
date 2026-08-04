---
title: {YYYY-MM-DD} — {contract change, short}
type: adr
work_id: {YYYY-MM-DD_slug}
scope:
  # Single-repo: area (free text). Monorepo: apps/packages.
  area: []
status: accepted            # proposed | accepted | superseded | deprecated
updated: {YYYY-MM-DD}
contract_version: {MAJOR.MINOR}   # the contract's version AFTER this change (see conventions extension)
supersedes: []
superseded_by: ""
sources: []
code_refs:                  # the contract-definition file + implementation this ADR changes
  - {path/to/contract-definition}
related:
  - contracts/{the-contract-page}
---

# {YYYY-MM-DD} — {contract change, short}

> ADR for a **cross-boundary contract change** (`contract_change_rule.md`). Written in **{{KNOWLEDGE_LANG}}**.
> Delete these guide lines before saving. Every `{...}` is an author field.

## Context

{Why must the contract change? Which consumers depend on the current shape, and what forces the change (a new requirement, a bug in the shape itself, a performance lever)? State whether the contract is already released to consumers you do not control — that decides whether a breaking change needs a deprecation window.}

- **Contract kind:** {public API | database schema | wire/IPC protocol | event/message schema | FFI ABI}
- **Definition file:** `{path}`
- **Change class:** {MINOR (additive) | MAJOR (breaking)}

## Decision

{The EXACT new shape — the literal target, not a description. Paste the full new signature / schema DDL / message layout / field list / symbol declaration. A reader must be able to reproduce the contract from this section alone.}

```
{new signature / DDL / .proto message / event schema / extern "C" declaration}
```

Contract version: `{old MAJOR.MINOR}` → **`{new MAJOR.MINOR}`** ({MINOR additive | MAJOR breaking}).

### Before/after diff table (mandatory)

One row per changed member. `—` means "did not exist / was removed".

| Member | Before | After | Change |
|---|---|---|---|
| `{member}` | `{old shape}` | `{new shape}` | {new (additive) \| type change (breaking) \| removed (breaking) \| semantics} |
| `{member}` | `{old shape}` | `{new shape}` | {…} |
| {unchanged members} | unchanged | unchanged | — |

## Consequences

- **Breaking?** {yes/no}. {If yes: who breaks, and the migration plan — the steps a consumer takes to adopt the new shape, and the deprecation window during which old and new coexist. If no: state why every existing consumer stays valid (additive-forward).}
- **Compatibility check:** {the runtime handshake and/or CI check that now covers the new member — schema-version assertion, protocol handshake value, ABI-version function, generated-vs-handwritten diff. See `contract_change_rule.md` §3.4.}
- **Atomic PR scope:** {list — contract definition, implementation, the consumers updated, the tests (incl. the regression test), the knowledge page. Confirm none merged alone.}
- **Hot path / regression:** {if a hot/critical path is affected and the benchmarks module is installed, link the benchmark page keyed to this work_id and the measured delta vs threshold. Otherwise state why no benchmark was needed.}
- **Knowledge page:** {the `contract` page updated in this PR, with its new `updated:` date.}

## Discarded alternatives (≥ 2, mandatory)

1. **{Alternative}.** {Why discarded — the concrete reason, not "we preferred the other one".}
2. **{Alternative}.** {Why discarded.}
{Add more as needed. Fewer than two → this ADR is invalid per §3.2.}
