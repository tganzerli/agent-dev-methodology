# Conventions extension — contracts module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section after §4 "Page types".
> Do **not** create a separate file in the target project — these fields and tags belong in the
> one canonical conventions doc so every agent finds them there. Remove the `⟪…⟫` markers when
> pasting.
>
> This extension is only installed when the **contracts module** is active (INSTALL.md §5-quater). It adds
> the specialized `⚠ contract-drift` tag and the `contract_version` frontmatter field used by
> `contract`-type pages and contract ADRs.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Contract frontmatter and tags (versioned cross-boundary contracts)

A **cross-boundary contract** — a public API surface, a database schema, a wire/IPC protocol, an event/message schema, or an FFI ABI — is documented on a `contract`-type page and changed through the process in `contract_change_rule.md`. Such a page, and any `adr` page recording a contract change, carries one extra frontmatter field.

### `contract_version`

```yaml
---
title: ...
type: contract                 # contract page; or `adr` for a contract-change ADR
status: draft                  # base lifecycle stub|draft|stable|stale still applies
contract_version: 2.4          # MAJOR.MINOR of the contract this page documents (or, on an ADR,
                               #   the version AFTER the change). Decoupled from the product version.
updated: 2026-08-04
code_refs:                     # MUST include the contract-definition file (barrel/schema/.proto/header)
  - lib/api/public.<ext>
related: []
---
```

| Field | Applies to | Values | Meaning |
|---|---|---|---|
| `contract_version` | `type: contract` pages and contract-change `adr` pages | `MAJOR.MINOR` | The contract's version. **MAJOR** = breaking (removal/incompatible change); **MINOR** = additive (new member). Versioned **independently of the product/package version**. On an ADR, record the version **after** the change. |

### `⚠ contract-drift` — specialized drift tag

The base convention marks an unbacked technical claim `⚠ unverified` (§2: "no citation yet"). A `contract` page adds a **stricter, automated** marker:

| Tag | Meaning | Raised by |
|---|---|---|
| `⚠ unverified` | Base: a claim has no `file:line` citation yet. | Author, until a citation is added. |
| `⚠ contract-drift` | The **contract-definition file changed after this page's `updated:` date** — the documented shape may no longer match the code. Stricter than `⚠ unverified`: the claim *was* cited, but the cited source moved underneath it. | The knowledge-lint pass (`git log` of a `code_refs` definition file vs `updated:`), per `contract_change_rule.md` §3.6. |

A page flagged `⚠ contract-drift` stays flagged until an agent re-reads the definition, reconciles the documented shape (updating the before/after history if the shape changed), and bumps `updated:`. Do not clear the tag by touching `updated:` alone — reconcile the content first.

⟪ END drop-in section ⟫
