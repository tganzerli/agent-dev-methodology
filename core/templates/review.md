<!--
  Installs as: REVIEW.md  (repository root)
  See INSTALL.md §3 and METHODOLOGY.md §4.4.1.

  Read by the `reviewer` role on EVERY agent review — keep it short: each line
  is paid in tokens on every review. CLAUDE.md/AGENTS.md teach the agent how to
  WRITE here; this file teaches it how to REVIEW here.

  Written by the owner of the code (solo project: you). Content in
  {{KNOWLEDGE_LANG}}; paths and identifiers in English. Replace the example rows.
-->
# REVIEW.md — {{PROJECT}}

## What failure looks like here

> Not code style rules — the **smell** a reviewer looks for in each area. One row per area that has a failure mode of its own.

| Area / paths | Failure looks like | How to check |
|---|---|---|
| Docs, README, comments | **It lies** — states behaviour or defaults the code does not have | Compare the claim with the code it describes |
| Config, env, endpoints | **It misroutes** — points at the wrong environment, database or service | Trace the value to where it is consumed |
| `{path/area}` | {failure} | {check} |

## Always high risk

> A change touching these paths is tier `high` regardless of size (METHODOLOGY §4.4.1). The planner reads this list when assigning the tier.

- {e.g. `auth/`, payments, data migrations, CI/release workflows, public contracts, installers}

## Skip

> Paths the reviewer does not review.

- Generated files, lockfiles, vendored code.
- `{{project}}_wiki/work/` (the trio is reviewed by the human, not by the reviewer).

## Do not flag (known false positives)

> One line per pattern the reviewer flagged and the human marked `wrong` or `intentional`. Each line cites its origin `work_id`.

- {`pattern` — why it is intentional} (origin: {work_id})

## Limits

- Max nits per round: **3**.
- Every finding carries `file:line` and the literal excerpt — no guesses from names.
- The report opens with the finding count, and says `Nothing to fix.` when there is nothing.
