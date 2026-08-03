---
title: Overview — {{PROJECT}}
type: overview
scope:
  area: []
status: stub
updated: {YYYY-MM-DD}
code_refs: []
---

# Overview — {{PROJECT}}

> High-level map of the product. This is the first page a new agent reads to understand what exists before drilling into `_meta/index.md`. Fill it in during the first real work cycle — do not leave it a stub past the initial bootstrap.

## Product summary

{One paragraph: what this product/repo is, who it serves, and its current maturity.}

## Areas

<!--
Single-repo default: list the functional areas/modules of the codebase.

| Area | Where it lives | Description |
|---|---|---|
| {area} | `{path/}` | {one-line description} |
-->

_(none documented yet)_

<!--
Monorepo module only (see modules/monorepo/): replace the "Areas" section
above with an Apps × Packages matrix instead, e.g.:

## Apps

| App | Description |
|---|---|
| [[apps/{app}]] | {one-line description} |

## Packages

| Package | Responsibility | Key external deps |
|---|---|---|
| [[packages/{pkg}]] | {responsibility} | {deps} |

### Cross-dependencies

- `{app}` depends on `{package}` 📎 [`path:NN`](path).
-->

## Key domains

| Domain | Where it lives | State | Page |
|---|---|---|---|
| {domain name} | `{path/}` | {e.g. implemented / in progress / planned} | [[domains/{domain}]] |

_(none documented yet)_

## External partners

> Only relevant if the cross-team module is installed (`modules/cross-team/`) — partner teams collaborating through their own LLM, or external specs this project consumes/produces.

_(none yet)_

## How to navigate

- By scope: start at `[[{area-or-app-or-package}]]`.
- By domain: see the table above.
- By type (all entities, all services): use `grep` or the Obsidian graph.
- History: see [[_meta/log]].
- Conventions: see [[_meta/conventions]].
