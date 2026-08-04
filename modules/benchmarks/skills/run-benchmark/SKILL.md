---
name: run-benchmark
description: Run a benchmark and archive it as a reproducible evidence page under {{project}}_wiki/benchmarks/{work_id}.md — collect environment metadata, snapshot the commit, run the exact command, do the statistical analysis, generate a reproducible chart, and write the page per the benchmark protocol. Use when the human invokes /run-benchmark {work_id} or after an execution whose plan requires empirical evidence for a quantitative claim.
argument-hint: "{work_id}"
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep
---

# Run Benchmark

**Manual skill.** Encapsulates `modules/benchmarks/rules/benchmark_protocol_rule.md`. Human-gated (`disable-model-invocation: true`) because a run mutates state, spends time, and produces a citable result — no agent should launch it unprompted.

## Prerequisites

- An **approved plan** for `{work_id}` exists and calls for empirical evidence (a quantitative claim to back).
- The hypothesis is written and **frozen** — you do not edit it after seeing the numbers.
- The dataset/fixture and the exact command are known; any required service can be started from a documented command.

## Flow

### 1. Collect environment metadata

Gather what goes into the `environment` frontmatter block. Portable probes (use whichever fits the host OS):

```bash
# CPU
sysctl -n machdep.cpu.brand_string 2>/dev/null   # macOS
lscpu 2>/dev/null | grep -i "model name"          # Linux
# RAM
sysctl -n hw.memsize 2>/dev/null                  # macOS (bytes)
free -h 2>/dev/null                               # Linux
# OS / kernel
uname -a
# Versions — the language runtime, toolchain, and the dependency under test.
# Use the project's own version commands (runtime --version, package manifest, etc.).
```

Record `cpu`, `ram`, `os`, and the `versions` map (runtime / toolchain / dependency-under-test **and** its baseline). Add `storage` / `network` / `accelerator` only when they move the metric.

### 2. Snapshot the code under test

```bash
git rev-parse HEAD
git status --short          # the tree must be clean, or the page records the exact diff
```

Record the commit hash of the code under test **and** of the baseline. A dirty tree makes the run unreproducible — commit or stash first, or document the diff verbatim.

### 3. Control state, warm up, run

- Reset the dataset to a known baseline (§ Dataset of the plan). When ≥2 variants are compared, reset **before each variant** so a later one does not inherit mutated state.
- Fix the RNG seed where any randomness exists; note the per-rep/per-worker derivation.
- Warm up, then run the **exact command** from the plan. Persist output (raw per-item data) to `benchmarks/{work_id}.csv`.
- Capture the **wall-clock elapsed time** reported by the runner for any rate — do not reconstruct a rate as `sum(latency) ÷ N`.

Gather **statistical volume sufficient for the target CI**, not a fixed run count (rule §5.5).

### 4. Statistical analysis

Parse the raw data and compute the metrics the hypothesis is about (e.g. p50/p95/p99 latency, mean ± σ throughput, memory, accuracy). Report the interval/percentiles, the delta vs. baseline, and apply the stated outlier policy. If a tail ratio is large (e.g. `p99/p50 ≫ 10`), flag it and find the cause — do not smooth it over.

### 5. Reproducible chart

Generate `benchmarks/{work_id}.{svg|png}` from a **committed plotting script** in the project's own language (`benchmarks/scripts/plot_{work_id}.{ext}`). Prefer a dependency-light, vector output for print. The script must be versioned and re-runnable — never hand-produce the image.

### 6. Write the evidence page

Instantiate `{{project}}_wiki/benchmarks/{work_id}.md` from `{{project}}_wiki/benchmarks/_template.md`. Fill every section in order:
Hypothesis (frozen) → Setup (commits + config) → Exact command (literal) → Dataset (+ seed) → Statistical method → Results (table + Δ, tail flags) → Artifacts (csv + chart + script paths) → Analysis → Threats to validity → **Verdict**.

Choose the **Verdict** from the data: `confirmed | refuted | partially-confirmed | inconclusive`. A refutation is a valid result — preserve the original hypothesis and record the revised one; if the effect inverted the predicted direction, mark it `refuted-with-sign-inversion` and give the root cause.

### 7. Update indices and the execution

- `{{project}}_wiki/benchmarks/_index.md` — add an entry.
- `{{project}}_wiki/_meta/index.md` — register the page.
- `{{project}}_wiki/_meta/log.md` — append `## [YYYY-MM-DD] benchmark | {work_id} | summary`.
- `{{project}}_wiki/work/executions/{work_id}.md` — link `[[benchmarks/{work_id}]]` in `related[]`.

## Rules

- **Total reproducibility:** the § Exact command must run for anyone who clones the repo, with no secret env vars.
- **Raw data and chart versioned in git** — never `.gitignore`d.
- **Re-runs** append to the existing page's Re-runs table with a new `{work_id}-rerun-YYYY-MM-DD` raw file; they do **not** overwrite prior evidence. A substantially changed setup gets a **new `work_id`** and a new page.

## Anti-patterns

- ❌ Running without warm-up or without a fixed seed where randomness exists.
- ❌ **Re-running until a favorable number appears** (p-hacking). Fix the method before the run.
- ❌ **Rewriting the hypothesis after seeing results** to make it "confirm". If the human pushes to dress up a result, refuse and cite `benchmark_protocol_rule.md` §7.
- ❌ Deriving a rate as `sum(latency) ÷ N` instead of wall-clock.
- ❌ Comparing against a stale baseline.
- ❌ Hiding threats to validity or dropping a surprising finding.
- ❌ Producing the chart by hand instead of from a committed script.
- ❌ Deleting the old raw file on re-run.

## Cross-references

- `modules/benchmarks/rules/benchmark_protocol_rule.md` — the rule this skill enforces.
- `core/rules/mandatory_planning_rule.md` — the plan gate that precedes any run.
- `core/rules/git_branching_rule.md` §4.3 — the `bench/<work_id>__<scope>` branch this work runs on.
