---
trigger: always_on
---

# Contract Change Rule (contracts module)

> Installed only when the project **exposes a versioned cross-boundary contract that other code, teams, or systems depend on** (a public package/library API, a database schema/migration, a wire/IPC/network protocol, a serialized event/message schema, or an FFI ABI). If nothing outside the change's own module consumes the interface, this rule does not apply and must not be installed — an internal refactor is governed by `mandatory_planning_rule.md` alone.

## 1. Core directive

**STOP.** Before altering any **cross-boundary contract**, you MUST treat the change as an **architectural decision**, not an edit. A silent divergence between a contract's definition and one of its consumers surfaces as a runtime failure — a broken deploy, a rejected message, a segfault, a data-corruption bug — that typically escapes the changed module's own tests and only appears where the *consumer* runs. This rule makes such a change **all-or-nothing**: the contract, every consumer, the tests, and the knowledge page move together, in one reviewed PR, behind an ADR. It is **non-negotiable** for any LLM agent and is the contract-layer counterpart of `mandatory_planning_rule.md`.

## 2. What counts as a cross-boundary contract

A **cross-boundary contract** is any interface whose shape is depended on by code you do **not** change in the same edit — code owned by another module, another team, another process, or a future/older version of your own system. This rule activates when a change touches the **observable shape** of one of these:

| Contract kind | The versioned surface | Typical consumers |
|---|---|---|
| **Public API** | Exported functions/types/signatures of a package or library (the barrel/`index`/public headers). | Downstream apps, other packages, third-party callers. |
| **Database schema** | Table/column/index shape, a migration, a stored-procedure signature. | Every reader/writer of the DB, replicas, analytics jobs. |
| **Wire / IPC / network protocol** | Message framing, RPC method signatures, endpoint request/response shape, status codes. | Any peer speaking the protocol, across versions. |
| **Event / message schema** | The serialized shape of an event, a queue payload, a topic record. | Producers and consumers, replays of persisted events. |
| **FFI ABI** | A `extern "C"` signature, a struct layout passed across the language boundary, a memory-ownership convention. | The foreign-language binding, at load time. |

**What activates the rule:** adding / removing / renaming a surface member; changing a parameter, field, return, or status; changing a type, layout, encoding, or nullability; changing ownership/lifetime semantics (who allocates/frees, who acks/retries); changing a default that a consumer relies on.

**What does NOT activate it:** a change entirely behind the contract (internal refactor, optimization, added logging) that leaves the observable shape **byte-identical for every consumer**. That still follows `mandatory_planning_rule.md` — it just does not need an ADR or a `contract/` branch.

> If you are unsure whether a change is observable to a consumer, treat it as **observable** and follow this rule. The cost of a needless ADR is minutes; the cost of a silent break is a production incident.

## 3. Mandatory workflow

### 3.1. Dedicated `contract` branch

A contract change gets its **own ephemeral branch**, registered as the `contract` type with the core branching rule (`core/rules/git_branching_rule.md` §4.3):

```
contract/<work_id>__<scope>
```

- Source: `dev` (or the monorepo module's `dev_<app>` / `dev_packages` per that rule). PR target: same.
- Example: `contract/2026-08-04_add-cursor-pagination__public-api`.
- The creation gate is the core rule's (§4.6): an **approved** plan at `{{project}}_wiki/work/plans/{work_id}.md` must exist first.

A `feat/` or `fix/` branch is **never** valid for a contract change — the `contract/` type exists precisely to make the change visible in the branch name and to key the PR checklist below.

### 3.2. ADR (Architecture Decision Record)

Create `{{project}}_wiki/decisions/{YYYY-MM-DD}_{slug}.md` (`type: adr`, `status: accepted` at execution time) from `modules/contracts/templates/adr-contract.md`. Minimum content:

- **Context** — why the contract must change.
- **Decision** — the **exact** new shape: the full new signature / schema DDL / message layout / field list. Not a description of it — the literal target shape.
- **Consequences** — is it breaking? The migration plan, the deprecation window (if breaking), the compatibility story for old consumers.
- **Discarded alternatives — ≥ 2, each with the reason for discard.** An ADR without them is rejected: it is not a decision record, it is a changelog entry.
- **Before/after diff table** — mandatory. One row per changed member:

  | Member | Before | After | Change |
  |---|---|---|---|
  | `listOrders` | `(customerId) -> Order[]` | `(customerId, cursor?) -> Page<Order>` | breaking: return type |

### 3.3. Atomic single-PR update

In **one** PR, none of these may merge alone:

1. **The contract definition** — the source of truth for the shape (public barrel / schema migration / `.proto` / event-schema file / C header).
2. **The implementation** — the code that satisfies the new shape.
3. **Every consumer** — each caller/reader in the repo, updated to the new shape. (Consumers outside the repo are handled by the versioning + compatibility check of §3.4, and — if the cross-team module is installed — a handoff.)
4. **Tests, including a regression test** — a test that fails against the old shape and passes against the new one, pinned to the exact change.
5. **The knowledge page** — the `contract`-type page describing the interface (`{{project}}_wiki/contracts/…` or the relevant page), refreshed to the new shape with `file:line` citations and its `updated:` date bumped.

**The PR is atomic.** A green build on the contract file while a consumer still speaks the old shape is exactly the failure this rule exists to prevent.

#### Checklist — additive (MINOR) change

An additive change (a new member, a new optional field, a new endpoint) that breaks no existing consumer follows this order:

1. **Declare the new surface** in the contract-definition file; if it is the family's first bump this cycle, increment the MINOR version constant (§3.4).
2. **Implement** the new member.
3. **Build / compile / migrate green** — no new warnings.
4. **Verify the new surface is actually exported/available** across the boundary (it is in the public barrel / the schema is applied / the symbol is present / the schema validates) — not merely written in source.
5. **Update consumers / bindings** that will use it (an additive change may have none yet — that is allowed).
6. **Bump the MINOR version constant** and any generated artifact.
7. **Compatibility check covers the new member** (the handshake / schema-version assertion / codegen-diff check of §3.4 accounts for it).
8. **Smoke test** — exercise the new path end to end (a PoC/example, or extend an existing one).
9. **Test** — a regression case in the suite.
10. **ADR** — with the before/after diff table (§3.2).
11. **Knowledge page** — the `contract` page updated with a new row + `code_refs` to the definition and implementation.

> **MAJOR (breaking) needs more.** A removal, a type change, a layout change, or any change that invalidates an existing consumer additionally requires: a **migration plan** in the ADR, a **deprecation window** where old and new coexist (where the platform allows), a MAJOR version bump, and — for a released contract — coordinated consumer rollout. Do not treat a breaking change as a MINOR checklist with one extra line; plan the migration explicitly.

### 3.4. Independent versioning + compatibility check

The contract is versioned **`MAJOR.MINOR`, independently of the product/package version**:

- **MAJOR** — a breaking change (removal, incompatible type/layout/semantics change).
- **MINOR** — an additive, backward-compatible change (a new member/field/endpoint).

Pin the version in the contract itself (a version constant, a schema `version` field, a protocol handshake value) and assert it **where the platform allows**:

- **Runtime handshake** — the consumer checks the contract version on connect/load and refuses an incompatible MAJOR (e.g. a protocol version exchange, an ABI-version function checked when the library loads, a schema-version row asserted at startup).
- **CI check** — a build-time assertion that the definition and its consumers agree: a **generated-vs-handwritten diff** (regenerate the binding/client/schema and diff it against the committed one — a mismatch fails the build), a schema-compatibility gate (e.g. backward-compat check on the message schema), or a migration-applies check.

The tolerance is the standard one: a consumer built for `MAJOR.m` accepts a linked/served `MAJOR.n` when `n ≥ m` (additive is safe forward), and rejects a different `MAJOR`.

### 3.5. Regression validation on hot/critical paths

If the changed contract sits on a **hot or critical path** (a query path, a serialization/parsing loop, a high-frequency message, a thread/IPC hop) **and the benchmarks module is installed** (`modules/benchmarks/`):

- Re-run every benchmark page whose `code_refs` touch a file changed in this PR.
- Archive the result as a **new** benchmark page keyed to this `work_id`, citing the ADR.
- **If any principal metric regresses beyond the stated threshold** (default 5%, or whatever the benchmark page declares), **abort the merge** and revise.

If the benchmarks module is not installed, state in the ADR's Consequences whether a hot path is affected and how the risk was assessed.

### 3.6. Lint drift detection

The knowledge-lint pass flags contract pages that fell behind their definition:

- Every contract-definition file (public barrel / schema / `.proto` / event schema / header) SHOULD have a `contract`-type page whose `code_refs` point at it.
- If `git log` shows the **definition file changed after the describing page's `updated:` date**, the lint marks the page **`⚠ contract-drift`** — the specialized form of the base `⚠ unverified` tag (see the conventions extension). The page is out of date with the shape it documents until reconciled.
- An ADR of `type: adr` mentioning a contract in the last N days without a same-dated update to the corresponding `contract` page is likewise flagged.

## 4. Anti-patterns

- ❌ Update the contract without updating its consumers in the **same** PR ("I'll fix the callers next").
- ❌ A `feat/` or `fix/` branch for a contract change — use `contract/`.
- ❌ An ADR with fewer than two discarded alternatives, or with no before/after diff table — it violates §3.2.
- ❌ A MINOR bump for a change that removes or reshapes an existing member — that is MAJOR (breaking).
- ❌ Regenerate a binding/client/schema from the definition and commit it **blindly**, without diffing against the hand-maintained one (§3.4).
- ❌ Ship a breaking change with no migration plan and no deprecation window.
- ❌ Skip the regression benchmark on a hot path when the benchmarks module is present (§3.5).
- ❌ Bump the contract version but leave the runtime/CI compatibility check unaware of the new member.
- ❌ Edit the contract page without bumping `updated:`, leaving a false-green page that lint cannot flag as drifted.

## 5. Precedence / Cross-reference

This rule is part of the broader methodology in `.agents/METHODOLOGY.md`. On conflict, **this rule prevails for everything about changing a cross-boundary contract**; the methodology prevails for the work cycle and the wiki. It composes with:

- `core/rules/git_branching_rule.md` — which **registers the `contract` branch type** (§4.3) this rule governs; that rule owns the branch syntax and creation gate, this one owns what must ride on the branch.
- `core/rules/mandatory_planning_rule.md` — the approved plan is the precondition for the `contract/` branch.
- `modules/benchmarks/` (if installed) — the regression gate of §3.5.
- The conventions extension (`modules/contracts/conventions-extension.md`) — the `⚠ contract-drift` tag and the `contract_version` frontmatter field.
