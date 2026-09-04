# MCP — {{PROJECT}}

> Catalog and configuration of the **Model Context Protocol** servers shared by the LLM agents operating in this repository. LLM-agnostic: any MCP-capable agent points at the mirrored config file for its own client (§3).
>
> This file is a **catalog**, not a gate — consult it when adding, removing, or debugging an MCP server. It is not part of the mandatory reading prefix (METHODOLOGY §9).

## Why this file exists

Every MCP client reads its configuration from a **different path** (`.mcp.json`, `.gemini/settings.json`, `.cursor/mcp.json`, …). Without one catalog, a server added for one agent is invisible to the others, and the repo drifts into per-agent capability: the same task succeeds under one agent and fails under another, for a reason nobody can see from the code. The mirrored files are the mechanism; this page is where the intent lives.

## 1. Active servers

| Server | Command | Purpose |
|---|---|---|
| `{name}` | `{binary} {args}` | {what it exposes, and why the agent should prefer it over the shell} |

State each server's **prerequisite** (binary on `PATH`, minimum version) and how to verify it before enabling.

## 2. Candidate servers (not enabled)

Servers the project may adopt later. **Do not enable one without a recorded decision** — an MCP server is a capability granted to every agent in the repo.

| Candidate | Hypothetical command | Purpose |
|---|---|---|
| `{name}` | `{binary}` | {what it would unlock} |

## 3. Where each agent reads the config

Mirrored files, one per client. Adding a server means editing **all** of them in a single change.

| Agent / client | Versioned file | Scope |
|---|---|---|
| **Claude Code** | `.mcp.json` (repo root) | Project — discovered automatically. |
| **Gemini CLI / Code Assist / Antigravity** | `.gemini/settings.json` | Project — `mcpServers` key. Add a `.gitignore` exception for this one file; the rest of `.gemini/` is personal state. |
| **Cursor** | `.cursor/mcp.json` | Project — create when someone on the team uses it. |
| **Codex / others** | — | Configure locally, pointing at the same `command`/`args`. |

All files use the same canonical JSON shape:

```json
{
  "mcpServers": {
    "{name}": {
      "command": "{binary}",
      "args": ["{...}"],
      "env": {}
    }
  }
}
```

## 4. Adding a server

1. Verify locally that it starts (`{command} {args}` in a terminal).
2. Add the entry to **`.mcp.json`**.
3. Mirror it into **`.gemini/settings.json`**.
4. Mirror it into `.cursor/mcp.json` if Cursor is in use.
5. Update the §1 table with the server's purpose and prerequisite.
6. Commit as **one change** — never fragment the mirror across commits, or the repo ships a window where agents disagree about their own capabilities.

## 5. Removing a server

The inverse of §4: remove it from every mirrored file and from the §1 table in one change. Move it to §2 if it may come back.

## 6. Anti-patterns

- ❌ Adding a server to one client only — it breaks parity between agents and produces failures that look like model differences.
- ❌ Secrets in `env`. Use shell variables (`${VAR}`) or prompt at startup. A versioned config file is a public file.
- ❌ Pointing `command` at a user-absolute path (`/Users/<name>/…`). Use a binary resolvable on `PATH`.
- ❌ Versioning per-client personal state (credentials, session history). Allow-list the single settings file, ignore the rest of its directory.
- ❌ Enabling a server that grants write access to the repo or an external system without a recorded decision. MCP capability is granted to **every** agent that opens the project, not just the one that asked.

## 7. References

- MCP specification: <https://modelcontextprotocol.io>
- Per-server documentation: link it in the §1 row.
