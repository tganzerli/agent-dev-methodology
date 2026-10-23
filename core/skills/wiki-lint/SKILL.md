---
name: wiki-lint
description: Check wiki health by script — generated-catalog drift, trio errors, missing or digest-sized summaries, broken wikilinks, incomplete frontmatter, hand-kept index format, rule citations that no longer resolve; warnings for stale pages, orphans, stalled work and unquoted ` #` in a summary/title. Gates ratchet against a measured baseline; read-only, never edits a page. Also lists the 🔒 gates of the normative docs. Use when the human invokes /wiki-lint or asks for a periodic health check of the wiki.
argument-hint: "[--only g1,g2] [--stale-days N] [--json] [--gates]"
disable-model-invocation: true
---

# Wiki Lint

Wiki health per `.agents/METHODOLOGY.md` §6.3. **Read-only:** it reports; changes wait for the human.

```bash
python3 .claude/skills/wiki-lint/lint.py --root .            # report; exit 0 ok · 1 regression · 2 usage
python3 .claude/skills/wiki-lint/lint.py --root . --json     # structured output
python3 .claude/skills/wiki-lint/list_gates.py --markdown    # the 🔒 gate list (METHODOLOGY §6.5)
```

## Why it is a script

As prose checks an agent ran by reading the whole wiki, the lint cost enough that it did not run, and in one installation 8 pages violated a written norm for months. A convention with no verification is a suggestion (METHODOLOGY §6.6).

## The ratchet

A gate fails when its count **rises above** the baseline in `{{project}}_wiki/_meta/lint-baseline.json` — not when it is non-zero. A gate born red is backlog, and it teaches everyone to ignore the exit code.

- **Adopting on a vault with old debt:** `lint.py --init-baseline` once (refuses if the file exists), commit the file. The lint enters green; any regression turns it red.
- **After fixing pages:** the report says `↓ below baseline`; run `lint.py --lower-baseline` and commit it. That is what makes the debt monotonic.
- **Raising a baseline is a conversation, not a commit.** It is the one move that destroys the tool.
- A fresh install has no file: every baseline is 0.

## Gates (exit code) and warnings (human reading)

| Check | Kind | Definition |
|---|---|---|
| `catalog-drift` | gate | `work-index --check` (drift **or** trio error) and `wiki-index <dir> --check` for each generated catalog. |
| `missing-summary` | gate | Page in a generated-catalog dir without `summary`. |
| `summary-too-long` | gate | `summary` over 250 chars — a catalog entry turned digest. |
| `frontmatter` | gate | Knowledge page missing `title`/`type`/`status`/`updated` (templates `_*` exempt). |
| `broken-wikilink` | gate | `[[target]]` with no page, scanned in the vault and `.agents/`. Code spans/fences and placeholder targets (`{`, `*`, `…`) are examples, not links. |
| `index-format` | gate | Hand-kept catalogs (`_meta/index.md`, non-generated `_index.md`): ≤20 KB, one physical line per entry, ≤300 chars per line. `wiki-sync`'s script runs this one after every sync. |
| `rule-citation` | gate | A `file:line` in `.agents/METHODOLOGY.md`, `.agents/rules/`, `.agents/llm/` whose file is gone or whose line is past the end; a cited script path that does not exist. Existence and range only — citations are point-in-time (conventions §2), so content is never compared with today's file. |
| `stale` | warning | A `code_refs` file committed after the page's `updated`. |
| `orphan` | warning | Knowledge page with no inbound wikilink. |
| `stalled` | warning | Task/plan/execution `open`/`approved`/`in_progress` for more than `--stale-days` (default 14). |
| `yaml-comment` | warning | An unquoted `summary`/`title` holding ` #` — YAML (and every kit parser) drops the rest as a comment, so `summary: merged in PR #29` catalogs as "merged in PR". Quote the value. A warning: the YAML is valid, only probably not what was meant. |

**Not scripted — judgement, report them by hand when asked:** contradictions between pages, and topics mentioned on many pages with no page of their own. Flag for the human; never resolve automatically.

## Who calls it

| Trigger | Consequence |
|---|---|
| CI on every PR (template `core/ci/methodology-checks.yml` in the kit) | Fails the check — the mechanism that makes the lint run at all |
| `sync_bookkeeping.py` (end of `/wiki-sync`) | `--only index-format` |
| `/wiki-lint` | When the human asks |

A lint that answers correctly and that nothing invokes is the same as no lint: in one installation a red gate survived on `main` because only the manual trigger existed.

> **A local run lints the working tree, not the commit.** Untracked files count: in one installation an unversioned plan made `catalog-drift` pass locally and fail in a clean clone of the same commit. To see what CI sees:
>
> ```bash
> T=$(mktemp -d); git clone -q . "$T/p" && python3 "$T/p/.claude/skills/wiki-lint/lint.py" --root "$T/p"
> ```

## Output and log

Report in the terminal, gates first. Optionally append to `{{project}}_wiki/_meta/log.md` (append only, never read it):

```markdown
## [YYYY-MM-DD] lint | N gates above baseline, M warnings
```

## Anti-patterns

- ❌ Raising a baseline so the lint passes.
- ❌ Editing pages from the lint (marking `stale`, inserting `⚠`) — the script is read-only by design.
- ❌ Reporting `{{project}}_wiki/work/` pages as `stale` — they are historical.
- ❌ "Fixing" a `rule-citation` or any `file:line` in a closed trio against today's file — annotate instead (conventions §2).
- ❌ Adding a gate without planting a violation once and seeing it fail (METHODOLOGY §6.7).
