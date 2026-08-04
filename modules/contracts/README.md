# Contracts module — atomic changes to a versioned cross-boundary contract

> **OPTIONAL module.** Install only when **the project exposes a versioned contract that other code, teams, or systems depend on** — a public package/library API, a database schema/migration, a wire/IPC/network protocol, a serialized event/message schema, or an FFI ABI. If nothing outside a change's own module consumes the interface, you do **not** need this module: an internal refactor is already covered by the core `mandatory_planning_rule.md`, and no cross-boundary contract exists to protect.

## 1. What this module protects

The failure mode is always the same: someone changes the **shape** of an interface, the change's own module still builds and its own tests still pass, and the break surfaces somewhere else — in a downstream caller, a replica, a protocol peer, an event replay, a foreign-language binding — often in production, often as data corruption rather than a clean error. Tests local to the changed module do not catch it because the *consumer* is what breaks.

This module makes such a change **all-or-nothing**. A change to a cross-boundary contract becomes an **architectural decision** that must ride on a dedicated branch, be recorded in an ADR with real alternatives, and land in a **single PR that updates the definition, the implementation, every consumer, the tests, and the knowledge page together** — behind an independent contract version with a runtime/CI compatibility check. It generalizes a production project's FFI/ABI-stability discipline to **any** versioned boundary.

## 2. What this adds

| Artifact | Path | Purpose |
|---|---|---|
| `contract_change_rule` (rule) | `.agents/rules/contract_change_rule.md` | `trigger: always_on`. Defines what counts as a cross-boundary contract, the `contract/` branch, the ADR requirement, the atomic single-PR update, independent `MAJOR.MINOR` versioning + compatibility check, the hot-path regression gate, and the `⚠ contract-drift` lint. |
| Contract ADR template | `{{project}}_wiki/decisions/_templates/adr-contract.md` | ADR skeleton specialized for a contract change: `type: adr`, the mandatory before/after diff table, and the ≥2-discarded-alternatives section. |
| Conventions extension | appended into `{{project}}_wiki/_meta/conventions.md` | Adds the `contract_version` frontmatter field and the specialized `⚠ contract-drift` tag. See `conventions-extension.md`. |

**No skill.** This module is a rule + a template + a conventions drop-in; the discipline is enforced by the always-on rule and the PR checklist, not by an invocable command.

## 3. How it composes

- **Core branching rule** (`core/rules/git_branching_rule.md`). That rule already reserves `contract` as a **module-registered ephemeral branch type** (its §4.3 extension hook); installing this module makes `contract/<work_id>__<scope>` valid. The branching rule owns the branch syntax and the plan-approval creation gate; this module owns **what must ride on the branch** (the atomic PR contents). If the **monorepo module** is installed instead of the core branching rule, the same `contract` type applies with that rule's `dev_<app>` / `dev_packages` sourcing.
- **Benchmarks module** (`modules/benchmarks/`, if installed). When a contract sits on a hot/critical path, the rule's §3.5 requires re-running the affected benchmark pages and **aborting the merge on a regression beyond the stated threshold**. If the benchmarks module is absent, the ADR instead records how the hot-path risk was assessed.
- **Planning rule** (`core/rules/mandatory_planning_rule.md`). An approved plan is the precondition for the `contract/` branch, same as any ephemeral branch.
- **Cross-team module** (`modules/cross-team/`, if installed). Consumers **outside** the repo cannot be updated in your PR; when a contract change affects a partner team, pair this rule's versioning with a cross-team handoff so the partner's LLM ingests the new shape.

## 4. Install

See `INSTALL.md` §5-quater (contracts module). In short:

1. Copy `rules/contract_change_rule.md` → `.agents/rules/contract_change_rule.md`.
2. Copy `templates/adr-contract.md` → `{{project}}_wiki/decisions/_templates/adr-contract.md`.
3. Append `conventions-extension.md` (the `⟪…⟫` drop-in) into `{{project}}_wiki/_meta/conventions.md`, after §4 "Page types".
4. Confirm the installed branching rule's `contract` type hook is active (core `git_branching_rule.md` §4.3 — it references this module by name).
5. Register the rule in the project's rule catalog / `CLAUDE.md` entry point so agents read it in the mandatory set.

ADRs and contract pages are authored in **{{KNOWLEDGE_LANG}}**, like the rest of the wiki. The **Decision** section of a contract ADR, however, reproduces the literal contract shape (signatures, DDL, message layout) — that stays in whatever language/notation the interface itself uses.

## 5. Opt-in escalations (NOT default)

The proven core is the rule above: a `contract/` branch, an ADR with a before/after table, an atomic PR, and an independent `MAJOR.MINOR` version. Heavier machinery is available but installed **only when a concrete pain justifies it** (the seed-vs-accretion principle — see `docs/design-rationale.md`):

- **Machine-readable contract as the source of truth in CI.** Promote the contract from a prose page + definition file to a single schema artifact (JSON Schema / OpenAPI / protobuf / a generated ABI header) that CI validates on every side. *Escalate when:* the contract is large and drifts silently, and `⚠ contract-drift` keeps firing after the fact instead of a build failing before merge. Until then, the `contract` page's diff table plus the §3.4 compatibility check is enough.
- **Automated consumer-compatibility matrix.** Test the new contract version against a matrix of consumer versions (backward/forward), gated in CI. *Escalate when:* released consumers you do not control span multiple contract versions and manual reasoning about compatibility stops being reliable.

Both are **not defaults**. Start with the proven core; add an escalation only when its triggering pain actually appears.
