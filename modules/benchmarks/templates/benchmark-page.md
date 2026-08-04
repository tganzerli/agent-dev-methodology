<!--
  Installs as: {{project}}_wiki/benchmarks/_template.md
  See INSTALL.md §5-ter and modules/benchmarks/rules/benchmark_protocol_rule.md §4–6.

  Authored CONTENT (all prose) is written in {{KNOWLEDGE_LANG}}.
  Frontmatter keys/values stay English. The section order below mirrors
  benchmark_protocol_rule.md §5 exactly — do not drop or reorder sections
  when instantiating a real page; a page without a Verdict is unfinished.

  A benchmark page is evidence: the Exact command (§ "Exact command") plus the
  versioned Artifacts must let a stranger who clones the repo reproduce the
  number. If it does not, the claim stays sealed `⚠ unverified <metric>`.
-->
---
title: {Short claim} — {YYYY-MM-DD}
type: benchmark
work_id: {YYYY-MM-DD_slug}
scope:
  area: []                   # single-repo: free text, e.g. [ingest, api]
  # apps: []                 # monorepo only
  # packages: []             # monorepo only
status: draft                # draft → stable → stale
updated: {YYYY-MM-DD}
environment:
  cpu: "{e.g. 8-core x86-64, 3.2 GHz}"
  ram: "{e.g. 32 GB}"
  os: "{e.g. Linux 6.8 / macOS 14.5 / Windows 11}"
  versions:
    runtime: "{the language runtime / VM / interpreter version}"
    toolchain: "{compiler / build tool version, if relevant}"
    dependency: "{the library or service under test X.Y.Z, and its baseline X.Y.Z}"
  # storage: "{e.g. NVMe SSD}"      # optional — add when it moves the metric
  # network: "{e.g. loopback / 1Gb LAN}"
  # accelerator: "{e.g. GPU model}"
parallelism:                 # optional — only when the workload runs concurrently
  workers: {N}               # isolates / threads / processes
  per_worker: {N}            # concurrent units per worker
  seed: "{e.g. 42; per-rep = 42 + rep*1000}"
sources: []
code_refs: []                # code files this page measures — lint uses these to detect `stale`
related: []
---

# {Title}

## Hypothesis

> One declarative sentence, stated BEFORE the run. Freeze it — never edit to match the results (see the rule §7 anti-patterns).

{e.g. "Approach A has a lower p99 latency than baseline B under 1 000 concurrent requests."}

## Setup

- **Code under test:** commit `{hash}` — `{path/to/thing}`
- **Baseline:** `{name}` `{X.Y.Z}` at commit `{hash}` (use the CURRENT released version)
- **Configuration that moves the number:** {warm-up count, pool/batch sizes, flags, …}

<!-- When ≥2 variants are compared on this page, give a uniform per-variant knob table
     so fairness is unambiguous (same defaults, apples-to-apples):

| Variant | {knob 1} | {knob 2} | {knob 3} |
|---|---|---|---|
| A | … | … | … |
| B | … | … | … |
-->

## Exact command

```bash
# Literal, runnable by anyone who clones the repo. No secret env vars.
{the exact command, verbatim — including flags and the output/CSV path}
```

<!-- If a running service is required, the exact command to start it goes here too. -->

## Dataset

- **Fixture:** `{path or generation script}`
- **Size:** {N records / M MB}
- **State reset between runs:** {how you return to a known baseline before each variant}
- **RNG seed (if any randomness):** `{seed}` — derivation for multi-rep/worker: `{formula}`. Without a fixed seed, reproducibility is statistical, not bit-exact.

## Statistical method

- **Target interval:** {which CI, for which percentile}
- **Sample volume:** {reps × samples/rep = aggregated samples — enough to reach the target CI, not a magic run count}
- **Metrics:** {e.g. p50, p95, p99 latency; mean ± σ of throughput}
- **Outlier policy:** {keep / trim X% — state it explicitly}
- **Rate = wall-clock:** throughput measured by the runner's elapsed time over the whole concurrent batch — NOT `sum(latency) ÷ N`.

## Results

> Include an explicit Δ column vs. baseline and report dispersion. Flag a large tail ratio (e.g. p99/p50 ≫ 10) with `⚠` and address it in Analysis.

| Metric | Baseline | Under test | Δ |
|---|---|---|---|
| {throughput (mean ± σ)} | | | |
| {p50 latency} | | | |
| {p95 latency} | | | |
| {p99 latency} | | | |
| {memory / cost / accuracy …} | | | |

## Artifacts

> Raw data AND chart versioned in git (never `.gitignore`d), both produced by a committed, reproducible script in the project's own language.

- Raw data: `benchmarks/{work_id}.csv`
- Chart: `benchmarks/{work_id}.{svg|png}`  (vector preferred for print)
- Plotting script: `benchmarks/scripts/plot_{work_id}.{ext}`

## Analysis

{Interpret the numbers. An unexpected result is a finding to investigate — record it, never bury it.}

## Threats to validity

{Variables NOT controlled: loopback vs. real network, warm vs. cold cache, time-of-day/thermal drift, single-machine external validity, sample skew. List them honestly.}

## Verdict

> Exactly one, chosen from the data (rule §6):

- **{confirmed | refuted | partially-confirmed | inconclusive}** — {one line grounded in the results}.

<!-- If refuted: preserve the Hypothesis above unchanged; state the REVISED hypothesis here.
     If the effect inverted the predicted direction, classify it "refuted-with-sign-inversion"
     and document the root cause of the inversion. -->

## Re-runs

| Date | Environment | Result (summary) | Raw data |
|---|---|---|---|
| {YYYY-MM-DD} | {host / OS} | {e.g. p99 = 3.8 ms} | `benchmarks/{work_id}-rerun-{date}.csv` |
