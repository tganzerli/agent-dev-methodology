# Peer-relay module — agent↔agent messaging across sibling repos on one machine

> **OPTIONAL module.** Install only when this project coordinates with **another project in a separate repository that lives on the same machine**, whose agent can *read* your files but does not *share* your checkout — a companion library, a research repo, a sibling product. If the other side is a partner team with **no access** to your code, use `cross-team` instead. If the other agent works **your** repo, use `intra-team`. Requires **intra-team** installed first: this module inherits its machinery rather than duplicating it.

## 1. The premise — a third value on a binary axis

`cross-team` and `intra-team` are mirror images, and `modules/intra-team/README.md` states the axis they split on: *"they differ on one axis — does the reader share your repository?"*

That axis has been treated as binary. It is not.

| | `cross-team` | `intra-team` | **`peer-relay`** |
|---|---|---|---|
| Reader **shares** your repo | no | yes | **no** |
| Reader **can read** your repo | no | yes | **yes** |
| Governing rule | **self-contained** — inline everything | **reference-first** — point, don't paste | **reference-first, qualified** |

Both existing rules fail in the middle case, and they fail in opposite directions:

- **Self-contained wastes the access that exists.** The reader *can* open your file; forcing every algorithm inline reproduces content that will drift.
- **Reference-first produces ambiguity and dead links.** `lib/router.dart:9` exists in *both* repos and means different things. `[[wikilinks]]` do not resolve across vaults. `work_id`s collide, because both projects use `YYYY-MM-DD_slug`.

## 2. What this adds

| Artifact | Path | Purpose |
|---|---|---|
| `peer-relay` skill | `.claude/skills/peer-relay/SKILL.md` | Four flows: `absorb` (orient in the peer's repo), `send` (author + deliver), `read` (our inbox), `board`. |
| Peer registry | `.agents/peers.md` | Where each peer is, what to read to orient, what may be written. **The absorption mechanism.** |
| Peer message template | `{{project}}_wiki/work/relay/_templates/peer-message.md` | Extends intra-team's `message.md` with two namespaces, an Orientation section, and a third closing ask. |
| Frontmatter extension | appended into `{{project}}_wiki/_meta/conventions.md` | `peer`, `peer_work_refs`, the qualified-citation rule, claim-state with origin. |

It reuses intra-team's `work/relay/` directory, its five `msg_role`s, its stable-ID ask table, and its `_board.md`. **Nothing is duplicated.**

## 3. The three rules that are the module

### 3.1. Every file citation carries a repo prefix

🔒 A `file:line` without a prefix is a **format error**, not a style preference. `peer:path/to/file.ext:12` for the reader's repo; `{{project}}:path/to/file.ext:12` for yours. Prefixes come from the registry. `work_id`s are namespaced the same way on crossing.

`[[wikilinks]]` are valid **only** for pages in the reader's vault. For yours, use a prefixed file path — a wikilink into your vault is a dead link in their Obsidian.

### 3.2. The asymmetry: they *can* open your file, but they *won't*

This is the rule that took a real exchange to learn, and the one authors get wrong.

| Citation target | Treatment |
|---|---|
| **Reader's repo** | reference-first, pure. They will open it. Do not re-paste. |
| **Your repo** | reference-first **plus an inline summary that stands alone.** They are in another checkout with another context loaded. The citation is provenance; the claim must survive without it. |

"Reference-first" invites you to just point. Across repos, just pointing produces a round trip.

### 3.3. Claim-state carries origin

intra-team tags claims `✅ landed` / `⚠ in-flight` / `🔒 intent`. Across repos, `landed` alone answers nothing — landed **where**? Write `✅ landed (project@branch)`. A project whose repo has no commits yet reports almost everything as `⚠ in-flight`, and saying so is honesty, not hedging.

## 4. The registry is the absorption mechanism

Without it an agent cannot know the peer exists, where it is, what it may write, or where to start reading. With it, orientation is bounded: read the declared entry points **in order**, stop when the question is answered, never sweep the peer's repo.

The registry's highest-value field is **Quirks** — the things no index tells you. A stale `decisions/_index.md`, a git tag that was never pushed, a coordination lock left open on closed work. Each quirk recorded is a wrong conclusion a future agent does not draw. In the project this module came from, the first three quirks recorded were all cases where an index actively misled a reader.

## 5. Gates

- `absorb` and `read` are **autonomous**.
- `send` carries a **double human gate**: approve the text, then approve the write into another project's repository. These are different decisions, and the second is irreversible from your side — you have no commit rights there to undo it.
- `board` is human-gated, as in intra-team.
- 🔒 The registry's write policy is a ceiling, not a floor: `work/relay/` only means no code, no branch, no commit.

## 6. Mirroring

A peer that should answer needs this module installed and a **mirrored** registry pointing back. Mirroring is neither automatic nor verified — if one side declares an inbox the other does not know, the message is written and never read. **Diff the two registries side by side when installing the counterpart.**
