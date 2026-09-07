<!--
  Installs as: .agents/peers.md
  See INSTALL.md §5-ter and modules/peer-relay/README.md.

  This is the peer REGISTRY — machine-local configuration, not product knowledge.
  It lives in .agents/ (LLM-consumed meta, outside the Obsidian vault) because it
  describes the environment, not the product.

  Fill one section per peer. Delete the examples. Authored prose in {{KNOWLEDGE_LANG}}.
-->
---
trigger: manual
---

# Peers — sibling repositories on this machine

> Consulted on demand by the `peer-relay` skill (`.claude/skills/peer-relay/SKILL.md`).
>
> **Paths are absolute by necessity** — peers live outside this repository. That makes this file
> machine-specific. If a path does not resolve, the skill **fails loudly** ("peer `X` not found at
> `<path>`"); it never guesses an alternative.
>
> **The write policy here IS the authorization, not a suggestion.** Writing into another project's
> repository is an outward-facing action: it needs an in-the-moment human gate on top of whatever
> this table permits.

## Index

| Peer | Prefix | Path | Methodology | Write allowed |
|---|---|---|---|---|
| `{peer}` | `{peer}:` | `{absolute path}` | yes/no | `{path}` only / none / via PR |

---

## `{peer}`

{One paragraph: what this project is, and why it is a peer of ours.}

- **Path:** `{absolute path}`
- **Citation prefix:** `{peer}:`
- **Remote:** `{url}`
- **Development branch:** `{branch}`
- **Wiki:** `{wiki dir}/` — or `none`
- **Methodology:** {yes — same `.agents/METHODOLOGY.md`, modules X/Y installed | no}
- **Knowledge language:** {lang}
- **Read:** {allowed, whole repo | allowed, paths X and Y}
- **Write:** {**only** `<path>` — authorized by the human on YYYY-MM-DD | none, read-only | via PR}
- **Inbox** (our messages to them): `{peer}:{wiki}/work/relay/`
- **Outbox** (their messages to us): `{{project}}_wiki/work/relay/`
- **Their board:** `{peer}:{wiki}/work/relay/_board.md`

### Absorption entry points

Read **in this order**, and stop when the question at hand is answered. Never sweep the whole repo.

1. `{peer}:{wiki}/overview.md` — what the project is.
2. `{peer}:{wiki}/work/_index.md` — what is in flight. **Generated**, do not edit.
3. `{peer}:{wiki}/work/relay/_board.md` — active locks and agreements. **Read before writing anything.**
4. `{peer}:{wiki}/_meta/index.md` — knowledge catalog. To **search**, not to read end to end.
5. `{peer}:{...}` — whatever else is load-bearing in that repo.

### Quirks — what no index tells you

> **Do not skip this section.** Orientation in someone else's repository fails on details, not on
> the map: a stale `_index.md`, a local-only tag, a dead lock, a doc that contradicts the code.
> Each quirk you record here is a wrong conclusion a future agent will not draw.

- **(a)** {e.g. "`{peer}:{wiki}/decisions/_index.md` is stale (`updated: …`) and omits N later ADRs.
  Read the directory, not the index."}
- **(b)** {e.g. "the freeze tag is local, not pushed — `git tag` shows it in their clone only."}
- **(c)** {e.g. "their wiki is written in another language — section headings are `## Em andamento`,
  not `## In progress`. Never pattern-match on a heading name; list headings first."}

---

## Installing the counterpart in a peer

For a peer to talk back, it needs the `peer-relay` module installed and a **mirrored**
`.agents/peers.md` — pointing here, with our prefix, our inbox (`{{project}}_wiki/work/relay/`), and
whatever write policy **our** owner grants. Procedure: `INSTALL.md` §5-ter.

Mirroring is neither automatic nor verified: if one side declares an inbox the other does not know,
the message is written and never read. **When installing the counterpart, diff the two registries
side by side.**
