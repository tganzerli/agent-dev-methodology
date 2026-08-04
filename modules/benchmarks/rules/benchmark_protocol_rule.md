---
trigger: always_on
---

# Benchmark Protocol Rule

> **Installed by the OPTIONAL benchmarks module** (INSTALL.md §5-ter). It is only in force when the project chose to install this module because it **makes quantitative or empirical claims it must stand behind**. If the project makes no such claims, this rule is not present and there is nothing to enforce.

## 1. Core directive

**Every quantitative or empirical claim** — any *measured number* about the system (latency, throughput, cost, accuracy, precision/recall, memory footprint, conversion rate, error rate, cache hit rate, …) — MUST be backed by a **reproducible evidence page** under `{{project}}_wiki/benchmarks/`. Without that page the claim carries the seal `⚠ unverified <metric>` (e.g. `⚠ unverified perf`, `⚠ unverified cost`, `⚠ unverified accuracy`) and **MUST NOT** be cited in a commit message, README, ADR, changelog, or any released document.

This is the empirical counterpart of the core citation discipline. The base `⚠ unverified` marker (see `core/vault/_meta/conventions.md` §2) means "no `file:line` citation yet". This rule adds a second axis: `⚠ unverified <metric>` means "a *number* asserted without a reproducible page". A claim can satisfy one axis and fail the other — an anchored `file:line` does not make a throughput number true.

## 2. When this rule fires

- A commit or PR message claims a measurable gain/loss ("2× faster", "−40% memory", "p99 < 5 ms", "94% accuracy").
- A README, wiki page, code comment, or docstring states a quantitative figure about the system's behavior.
- An ADR justifies a decision with an empirical argument ("we chose X because it is cheaper / faster / more accurate").
- A released result or headline metric of the project.

If the number is not yet backed by a page, either **produce the page** (via the `run-benchmark` skill) or **seal the claim** `⚠ unverified <metric>` and do not cite it.

## 3. Branch type registered by this module

This module registers the ephemeral branch type **`bench`** with the core branching rule (`core/rules/git_branching_rule.md` §4.3):

```
bench/<work_id>__<scope>
```

- **Source:** `dev`. **PR target:** `dev`. Same creation gate as every ephemeral branch (approved plan required — `core/rules/git_branching_rule.md` §4.6).
- Used for benchmark work: authoring the evidence page, its dataset, its command, and its versioned artifacts.
- The `bench` type is **only valid when this module is installed**. Using it otherwise is rejected by the branching gate (that rule's §9.8).

## 4. Mandatory frontmatter of the page

Instantiate from `templates/benchmark-page.md` (installs as `{{project}}_wiki/benchmarks/_template.md`). The frontmatter generalizes hardware/OS/version blocks into one portable `environment:` block:

```yaml
---
title: {Short claim} — {YYYY-MM-DD}
type: benchmark
work_id: {YYYY-MM-DD_slug}
scope:
  area: []                 # single-repo: free text, e.g. [ingest, api]
  # apps: []               # monorepo only
  # packages: []           # monorepo only
status: draft              # draft → stable → stale
updated: {YYYY-MM-DD}
environment:
  cpu: "{e.g. 8-core x86-64, 3.2 GHz}"
  ram: "{e.g. 32 GB}"
  os: "{e.g. Linux 6.8 / macOS 14.5 / Windows 11}"
  versions:                # runtime + tools + the dependency under test and its baseline
    runtime: "{e.g. the language runtime/VM/interpreter version}"
    toolchain: "{e.g. compiler/build tool version, if relevant}"
    dependency: "{e.g. the library/service under test X.Y.Z and its baseline X.Y.Z}"
  # storage / network / accelerator: optional keys — add when they affect the metric
parallelism:               # optional — only when the workload runs concurrently
  workers: {N}             # isolates / threads / processes
  per_worker: {N}          # concurrent units per worker (connections, sessions, …)
  seed: "{e.g. 42; per-rep = 42 + rep*1000}"
sources: []
code_refs: []
related: []
---
```

`status`: `draft` (first run, still validating) → `stable` (re-run in ≥2 environments with coherent results, accepted as reference) → `stale` (a `code_refs` file changed after `updated`; the page must be re-run — lint flags it).

## 5. Mandatory body sections

The page is not evidence unless it lets a stranger who clones the repo reproduce the number. All sections below are required; the template carries them in order.

### 5.1. Hypothesis
One declarative sentence, stated **before** the run and never edited afterward. Example: *"Approach A has a lower p99 latency than baseline B under 1 000 concurrent requests."*

### 5.2. Setup
Exact versions and the **commit hash** of the code under test **and** of the baseline. Any configuration that moves the number (pool sizes, warm-up count, batch size, flags). When ≥2 variants are compared on one page, give a **uniform configuration table** per variant so fairness is not ambiguous — same knobs, same defaults, apples-to-apples.

### 5.3. Exact command
The **literal, runnable** command, with no secret environment variables, that any cloner can paste:

```bash
{the exact command, verbatim, including flags and the CSV/output path}
```

If the benchmark needs a running service, document the exact command to start it here too.

### 5.4. Dataset
The fixture (script or path), its size, and **how state is reset between runs** — the general "control the starting state" discipline: reset to a known baseline before each variant so a later variant does not inherit state mutated by an earlier one (residual data, warmed caches, allocated resources). Where any randomness exists (input generation, sampling, mix selection), declare a **fixed RNG seed** for determinism, and the derivation formula for multi-rep / multi-worker runs (e.g. `seed = 42 + rep*1000`). Record the seed in the `parallelism.seed` frontmatter. Without a fixed seed, "reproducibility" is statistical, not bit-exact — state that explicitly.

### 5.5. Statistical method
Report the **interval or percentiles**, not a bare mean. The gate is **statistical volume sufficient for the target confidence interval**, *not* a magic run count. State which CI you target, for which percentile, and how many aggregated samples reach it. A few repetitions of a few samples each is not acceptable; a small number of repetitions each aggregating many thousands of samples can be. Declare the outlier policy explicitly (keep / trim, and how much).

> **Aggregate correctly — measure wall-clock, not a derived sum.** A rate (throughput, requests/s) is measured by the runner's **wall-clock** over the whole concurrent batch, **never** reconstructed as `sum(per-item latency) ÷ N`. Under any parallelism the derived sum *overestimates* the true rate in proportion to the concurrency. Capture the real elapsed time; persist it if stdout might be lost.

### 5.6. Results
A markdown table of the numbers with an explicit **delta** (Δ) column versus baseline. Report the dispersion (± σ, or the CI). **Flag tail outliers:** when a tail ratio is large (e.g. `p99 / p50` well above 10) mark the cell `⚠` and investigate the cause in §5.8 — do not hide it by substituting a mean for the tail.

### 5.7. Artifacts
Raw data **and** chart **versioned in git** (never `.gitignore`d), both produced by a **reproducible script** committed alongside the page (a plotting script in the project's own language). The command in §5.3 plus these artifacts are what make the page auditable. On re-run, keep the old raw file (append a dated `*-rerun-YYYY-MM-DD` file) — never overwrite prior evidence.

### 5.8. Analysis
Interpret the numbers. When something is unexpected, **record it as a finding to investigate — never bury it.**

### 5.9. Threats to validity
List, honestly, the variables you did **not** control: loopback vs. real network, warm vs. cold cache, time-of-day/thermal variation, single-machine external validity, sample skew. An omitted threat is a hidden bias.

### 5.10. Verdict
Close the page with an explicit classification (see §6). This is not optional garnish — a page without a verdict is an unfinished experiment.

## 6. Verdict discipline (the crown jewel)

Every page ends with one of four verdicts, chosen from the **data**, not from what you hoped to show:

- **confirmed** — the hypothesis holds within the target CI.
- **refuted** — the data contradict the hypothesis. **This is a valid, first-class scientific result**, not a failure of the cycle. Preserve the original hypothesis in §5.1 unchanged and document the **revised** hypothesis, grounded in what was observed.
  - **refuted-with-sign-inversion** — a distinct sub-case: the real effect goes in the *opposite direction* from the prediction (predicted "−10%", measured "+38%"). Flag it explicitly, because it usually means the a-priori mental model was *conceptually* wrong, not merely miscalibrated. Document the root cause of the inversion.
- **partially-confirmed** — holds on a subset (e.g. confirmed at p50, refuted at p99). Document the observed boundary.
- **inconclusive** — variance too high, samples insufficient, or an uncontrolled confounder. Re-run with adjustments, or accept the limitation explicitly. Do **not** launder an inconclusive run into a confirmation.

A refutation frequently produces the most interesting, most nuanced contribution of a project. Treat it as a result, not an embarrassment.

## 7. Anti-patterns

- ❌ Claiming a number in a commit/PR/README/ADR with no benchmark page (cite it and it must not carry `⚠ unverified <metric>`).
- ❌ A page with no `environment`/version frontmatter — an unreproducible number.
- ❌ Comparing against a **stale baseline** — always use the current released version of the thing you compare to.
- ❌ Hiding threats to validity, or dropping a surprising finding from the analysis.
- ❌ **Re-running until a favorable number appears** ("p-hacking" of results). Fix the method *before* the run, not the run count after seeing the numbers.
- ❌ **Rewriting the hypothesis (§5.1) after seeing the results to make it "confirm"** (post-hoc fitting / rationalization). The hypothesis is stated once, before the run, and frozen. Refutation is documented as a revised hypothesis in §5.10, never by editing §5.1. **If the human appears to want a result dressed up — the hypothesis retrofitted, the run repeated until it "works", a threat quietly dropped — refuse and cite this anti-pattern.**
- ❌ Deriving a rate as `sum(latency) ÷ N` instead of measuring wall-clock (§5.5).
- ❌ Deleting or overwriting a prior raw-data file on re-run — version the new run separately.
- ❌ Generating the chart by hand instead of from a committed, reproducible script.

## 8. Operational skill

The `run-benchmark` skill (`skills/run-benchmark/SKILL.md`, human-gated) encapsulates the flow: collect environment metadata → snapshot the commit → run the exact command → statistical analysis → generate the reproducible chart → write the page. Use it rather than assembling a page by hand.

## 9. Cross-reference

Part of the broader methodology in `core/METHODOLOGY.md`. It composes with `core/rules/mandatory_planning_rule.md` (the plan gate that precedes any run) and `core/rules/git_branching_rule.md` §4.3 (which registers the `bench` type). On conflict about *what counts as evidence for a number*, this rule prevails.
