# Conventions extension — benchmarks module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section after §4 "Page types".
> Do **not** create a separate file in the target project — these belong in the one canonical
> conventions doc so every agent finds them there. Remove the `⟪…⟫` markers when pasting.
>
> This extension is only installed when the **benchmarks module** is active (INSTALL.md §5-ter).
> It adds the specialized `⚠ unverified <metric>` seal, the `benchmark` page type, and the
> portable `environment` frontmatter block.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Empirical evidence (benchmarks module)

A project that installs the benchmarks module makes **quantitative or empirical claims** — measured numbers about the system (latency, throughput, cost, accuracy, memory, conversion, error rate, …). Every such number needs a **reproducible evidence page** under `benchmarks/`, per `benchmark_protocol_rule.md`.

### The `⚠ unverified <metric>` seal

This is a **second, empirical axis** of uncertainty, distinct from the base `⚠ unverified` marker (§2):

| Marker | Means | Cleared by |
|---|---|---|
| `⚠ unverified` (base) | **No citation yet** — a technical claim without a `file:line` anchor. | Adding the `file:line` citation. |
| `⚠ unverified <metric>` | **A quantitative claim without a reproducible page** — a *number* asserted with no `benchmarks/` evidence behind it. | Publishing the benchmark page and citing it. |

Use the metric name in the seal: `⚠ unverified perf`, `⚠ unverified cost`, `⚠ unverified accuracy`, `⚠ unverified memory`, … A sealed number **MUST NOT** be cited in a commit, README, ADR, or changelog. The two axes are independent: anchoring a `file:line` does **not** make a throughput number true, and a benchmarked number still needs its `file:line` where it touches code.

### Page type: `benchmark`

Add to the §4 "Knowledge" page-type table:

| `type` | Directory | Content |
|---|---|---|
| `benchmark` | `benchmarks/` | A reproducible evidence page backing a quantitative claim. Frozen hypothesis, exact command, versioned raw data + chart, and an explicit verdict (`confirmed \| refuted \| partially-confirmed \| inconclusive`). `status`: `draft → stable → stale`. |

`benchmark` pages **are** subject to `stale`: when a `code_refs` file changes after `updated`, the page must be re-run (lint flags it). They are cataloged in `benchmarks/_index.md` and `_meta/index.md`.

### The `environment` frontmatter block

`benchmark` pages extend the base frontmatter with a portable `environment` block (generalizing hardware/OS/version details into stable keys) plus an optional `parallelism` block:

```yaml
---
title: {Short claim} — {YYYY-MM-DD}
type: benchmark
work_id: {YYYY-MM-DD_slug}
scope: { area: [] }          # or apps/packages in a monorepo
status: draft                # draft | stable | stale
updated: {YYYY-MM-DD}
environment:
  cpu: "..."                 # e.g. 8-core x86-64, 3.2 GHz
  ram: "..."                 # e.g. 32 GB
  os: "..."                  # e.g. Linux 6.8 / macOS 14.5 / Windows 11
  versions:                  # runtime + toolchain + the dependency under test AND its baseline
    runtime: "..."
    toolchain: "..."         # if relevant
    dependency: "..."
  # storage / network / accelerator: optional — add only when they move the metric
parallelism:                 # optional — only when the workload runs concurrently
  workers: 4                 # isolates / threads / processes
  per_worker: 4              # concurrent units per worker
  seed: "42; per-rep = 42 + rep*1000"
sources: []
code_refs: []                # files this page measures — lint uses these to detect `stale`
related: []
---
```

| Field | Meaning |
|---|---|
| `environment.cpu` / `.ram` / `.os` | Host the measurement ran on — the minimum needed to judge external validity. |
| `environment.versions` | Map of the language runtime, the toolchain (if relevant), and the dependency under test **with its baseline** version. |
| `parallelism` | Present only when the workload is concurrent: `workers`, `per_worker`, and the RNG `seed` (with its per-rep/worker derivation) for determinism. |

### Branch type: `bench`

The benchmarks module registers the ephemeral branch type **`bench`** (`bench/<work_id>__<scope>`, source `dev`, PR target `dev`) with `git_branching_rule.md` §4.3. Valid only while this module is installed.

⟪ END drop-in section ⟫
