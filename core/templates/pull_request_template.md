<!--
  Installs as: .github/pull_request_template.md  (see INSTALL.md §3; other hosts:
  their own PR-template path). De-template the vault slug at install.

  Write the PR in English. No LLM attribution anywhere in it: no Co-Authored-By,
  no "Generated with ..." footer, no model or product name. The author is the human.
  Every section comes from the plan's §4.4 — copy, do not re-derive.
-->
## Summary

Work: `<work_id>` — plan: `{{project}}_wiki/work/plans/<work_id>.md`

<!-- What changed and why, in two or three lines. -->

## Testing

<!-- Each validation as the exact command plus its output (or the relevant tail).
     A validation without its command and output does not count. -->

```
$ <command>
<output>
```

## Risk

Tier: `low | medium | high` <!-- from the plan; name the REVIEW.md "Always high risk" path if one sets it -->

## How to revert

<!-- Revert the commit(s), turn a flag off, run the down migration — and what, if anything, cannot be undone. -->
