<!--
  OPT-IN SNIPPET — paste into .agents/rules/git_branching_rule.md, as its own
  section next to the rule's other exceptions (NOT inside the docs-trivial
  exception: README §4.3 explains why they are two sections).

  Install only together with the `scope-lock` skill
  (modules/intra-team/skills/scope-lock/) and only if the project chose this
  route in modules/intra-team/README.md §4.2. Write the choice down (an ADR),
  with what it does not fix.

  Replace {{project}} and, if the shared line is not `main`, every `main` below.
  Translate the prose into {{KNOWLEDGE_LANG}} if the rule is authored in it.
-->

### Named exception — live-state publication (`_locks.md`)

> **This section exists because `{{project}}_wiki/work/relay/_locks.md` is the only page in the vault
> that is live state.** A lock must be readable by **another working tree while it is alive**. On the
> default route (versioned with the cycle) it is born and removed on the same branch and is visible for
> zero of the time it exists. The defect is structural, not hygiene.

**The exception, in exact terms.** Allowed **only** when **all** hold:

| | |
|---|---|
| **Who** | An agent taking or releasing a scope lock. |
| **What** | A direct commit to `main` touching **exclusively** `{{project}}_wiki/work/relay/_locks.md`. Any other path in the diff voids the exception. |
| **Change** | One row of the lock table: a take or a release. Never a rewrite of the file, never an edit to its protocol prose — that is a rule change and goes by PR like any other. |
| **Message** | `docs(work): take\|release scope lock on <scope> (<work_id>)` |
| **How** | `/scope-lock` (`.claude/skills/scope-lock/publish.sh`), through a throwaway `git worktree` on `main` — never `git checkout` in the active session. The script checks the staged diff before pushing and aborts if it is not exactly this path. |
| **Human gate** | **None, deliberately.** See below. |
| **Other lines** | No other protected line (`staging_*`, release lines) receives this exception. |

**Why this is a second exception and not an extension of the docs exception.** Ask: *are the two cases
safe for the same reason?* A documentation exception is safe by being **rare and human-judged** — a
person chooses the diff, and judgement is the only bound. Live-state publication is safe for the
**opposite** reason: the diff is **machine-bounded**, produced by a tool that only knows how to write one
row in one file. Two arguments, two sections.

**Why there is no per-act human gate.** Requiring approval for each lock makes a lock's visibility
depend on someone being in the session, which is the same defect class re-entered. Taking a lock only
**announces**: it blocks nobody by mechanism and undoes in one row. The safeguards that replace the gate
are the diff bound the tool enforces before the push, plus checks after the fact (module README §9).
**Every other write to `_board.md` keeps the human gate.**

**What this exception does NOT fix, said out loud.** Nothing forces an agent to take a lock. This route
changes the cost of *publishing* a lock; it creates no obligation to declare scope. An empty table is
telling the truth when it says it is empty. The mechanism delivers **visibility**; selling it as the end
of clobbering would be false.

**When the lock could not be published.** Waiving the per-act gate bets that the agent *can* act, and
that bet is not guaranteed: tool capability can vary per session without warning, with no configuration
change. **A blocked lock produces the same empty table as a forgotten one:**

| What happened | What `_locks.md` shows |
|---|---|
| No agent needed a lock | none |
| An agent wanted a lock and **could not publish it** | none |

The second is worse: a scope is being touched, another agent reads the empty table **correctly**, and
nobody knows there was a block rather than an absence.

**Required conduct.** An agent that tries to publish a lock and cannot — harness refusal, rejected push,
any reason — **records the block in the execution log, naming the intended scope, and tells the human
at once.** It never keeps touching the scope without a lock and without a mention.

The conduct does **not** ask the agent to diagnose the cause, deliberately: an agent cannot reliably
measure its own block, and an attempt to explain one has produced a plausible, checkable and **false**
explanation. Requiring a diagnosis would turn this clause into an invitation to invent a cause.

> A "blocked" state in the table was considered and refused: writing that row needs exactly the
> publication that was blocked. The channel that works when publication does not is the one that
> depends on no tool — the log and the human.
>
> ⚠ **This clause depends on the agent remembering, with no fix available.** A block leaves no
> artifact: no commit, no diff, nothing a CI check can read. It is the only safeguard for this case and
> it is declared weak; naming the conduct still beats silence, because silence is what produces the
> indistinguishable empty table.
