---
name: wiki-index
description: Deterministically generate a knowledge sub-index ({{project}}_wiki/<dir>/_index.md — decisions, cross-cutting, sources/external, postmortems) from each page's frontmatter `summary`/`status`. Replaces hand-editing those catalogs, which drift silently by omission. Use after creating, renaming or removing a page in one of those directories, after changing a page's summary/status, or to resolve an _index.md merge conflict (regenerate, never hand-merge).
argument-hint: "<dir> | --all [--check]"
allowed-tools: Bash(python3 *), Read
---

# Wiki Index

The knowledge-side sibling of `/work-index`: a sub-index stops being a hand-kept showcase and becomes the **deterministic output** of the pages' frontmatter. See `.agents/METHODOLOGY.md` §5.5.

## Usage

```bash
python3 .claude/skills/wiki-index/generate.py decisions --check --root .   # dry-run; exit 1 on drift
python3 .claude/skills/wiki-index/generate.py decisions --root .           # write
python3 .claude/skills/wiki-index/generate.py --all --check --root .       # every configured dir with pages
```

The vault is auto-detected (a single `*_wiki/`); pass `--vault <name>` otherwise.

## Line format and limit

`- [[dir/page]] — summary · _status_`. The `summary` is one sentence, **at most 250 chars**: past that the entry has become a digest, and the generator warns (`/wiki-lint` gates on it). A page without `summary` still appears, degraded to its `title`, with a warning — a page must never disappear from its catalog, since invisibility is the defect this exists to remove.

## Configured directories

| Dir | Expected `type` | Order |
|---|---|---|
| `decisions` | `adr` | date, newest first |
| `cross-cutting` | — (mixed by nature; type check off) | alphabetical |
| `sources/external` | `source` | date, newest first |
| `postmortems` | `postmortem` | date, newest first |

## Catalog labels (vault language)

Titles and the `Pages (n)` heading default to English. A vault written in another language translates them **once**, in the `catalog-labels` block of `_meta/conventions.md` — one `` - `key`: value `` line per label (`decisions`, `cross-cutting`, `sources/external`, `postmortems`, any other dir; `pages` with `{n}`; `generated`, a one-line banner with `{dir}`). Every run reads the block, so `/wiki-lint`'s drift check agrees with what you generated. `--label KEY=VALUE` overrides one label for a single run — persist it in the block, or the next check reports drift.

Adding a directory is one entry in `DIRS` at the top of `generate.py`, not a new skill (also add it to `INDEXED_DIRS` in `wiki-lint/lint.py`). An unlisted dir passed explicitly works with defaults.

## When NOT to use

- To change a page's description — that lives in its `summary:`. Editing the generated file is work the next regeneration erases.

## Anti-patterns

- ❌ Hand-editing a generated `_index.md` (its frontmatter says `status: generated`).
- ❌ Keeping a second list of the same pages (e.g. in `_meta/index.md`) — point at the generated file instead. In the installation this skill comes from, two lists of the same ADRs held 17 and 23 of 27.
- ❌ Resolving a merge conflict in the index by hand instead of regenerating.
