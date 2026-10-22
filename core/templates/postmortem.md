---
title: {Short name of the failure}
type: postmortem
scope:
  area: []
status: draft                # stub | draft | stable | stale
updated: {YYYY-MM-DD}
summary: One sentence, at most 250 chars — the line the catalogs show (/wiki-index).
introduced_by: {commit hash or work_id that introduced the bug}
fixed_by: {work_id of the fix}
detected_by: {test | agent review | human review | production | user report | …}
sources: []
code_refs: []
related: []
---

<!--
  Installs as: {{project}}_wiki/postmortems/_template.md
  See METHODOLOGY.md §5.6 and §4.4.2.

  Authored CONTENT is written in {{KNOWLEDGE_LANG}}. Frontmatter keys/values
  stay English. A postmortem is a KNOWLEDGE page (thematic, living): the lesson
  a costly bug taught, not the chronology of fixing it — that is the execution.
  Blameless: it examines which layer missed the bug, never who.
-->

# {Title}

## What happened

{The observable failure, in two or three sentences. Link the fix execution: [[work/executions/{ID}]].}

## Root cause

{The defect, with `file:line`.}

## Which layer should have caught it

> One answer, from the earliest layer that could have: plan risk tier · plan verification · tests · agent review · human review. Then: why it did not.

## Lesson promoted to

> Where the lesson now lives, so it does not depend on anyone re-reading this page. At least one:

- Rule clause: {file:line, with provenance pointing back here — METHODOLOGY §10.1}
- Lint / check / test: {path}
- Skill or agent-instruction line: {path}
- `REVIEW.md` "What failure looks like" row: {area}

## Reviewer replay case

> The case the `reviewer` must catch whenever its instructions, `REVIEW.md` or its model tier change (METHODOLOGY §4.4.2). Leave empty only if the bug could not have been seen in a diff.

- **Diff to replay:** `git diff {base}..{introducing commit}`
- **Context given:** plan [[work/plans/{ID}]] §4.1/§4.4 (as it was at the time)
- **Expected finding:** `[Important] path/file.ext:NN — {what the reviewer must say}`
- **Last replay:** {YYYY-MM-DD} — {caught | missed} — {what changed in the reviewer}
