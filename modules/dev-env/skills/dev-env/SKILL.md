---
name: dev-env
description: Bring up, tear down, and inspect the Docker environments under docker/<service>/. Invoke when the human types `/dev-env up|down|status|logs|exec <service>` or explicitly asks to prepare a database/broker/cache locally for validation, a PoC, or a benchmark. Waits for the healthcheck before returning from `up`. Governed by .agents/rules/dev_environment_rule.md.
disable-model-invocation: true
allowed-tools: Bash(docker *) Bash(cp *) Read
---

# Dev Environment — Skill

**Manual skill.** Wraps `docker compose` for the services under `docker/<service>/`. Governance lives in [`.agents/rules/dev_environment_rule.md`](../../../.agents/rules/dev_environment_rule.md) — this skill materializes that rule's three lifecycle modes without re-implementing policy per compose file.

## Prerequisites

- **Docker Engine + Docker Compose v2.20+** (`docker compose`, no hyphen).
- `docker/<service>/docker-compose.yml` exists.
- `docker/<service>/.env.example` is versioned.

On the first `up` for a service, if `docker/<service>/.env` is missing, the skill **auto-copies** `.env.example` → `.env` and tells the human it did so.

## Commands

### `up <service> [--ephemeral | --benchmark]`

1. Validate:
   - `docker --version && docker compose version` (≥ 2.20).
   - `docker/<service>/docker-compose.yml` exists.
2. If `docker/<service>/.env` is absent: `cp .env.example .env`, report it.
3. Mode:
   - **persistent (default)** — `docker compose up -d --wait`.
   - **`--ephemeral`** — same `docker compose up -d --wait`, but the skill records intent: `down -v` is expected once the run ends.
   - **`--benchmark`** — export `COMPOSE_PROJECT_NAME=<project>-<service>-bench-<run_id>` before `up`, isolating the volume per run.
4. Confirm healthy:
   ```bash
   docker inspect --format='{{.State.Health.Status}}' <container_name>
   ```
   If it is not `healthy` within ~60s, **fail** and print `docker compose logs` — never proceed as if it worked.
5. Print connection info (host `localhost`, port read from `.env`, default credentials).

### `down <service> [--clean]`

1. `cd docker/<service> && docker compose down`.
2. With `--clean`: add `-v` (drops named volumes).
3. In `--benchmark` mode, `--clean` is implicit.

### `status`

Scan `docker/*/` and, for each service:
```bash
docker compose -f docker/<service>/docker-compose.yml ps
```
Summarize in a single table: service | state | port | healthy.

### `logs <service> [-f]`

`cd docker/<service> && docker compose logs [--follow]`.

### `exec <service> <command>`

`cd docker/<service> && docker compose exec <main-service> <command>`.

Example: `/dev-env exec postgres psql -U postgres -d app`.

## Anti-patterns

- ❌ Bare `docker run` (violates `dev_environment_rule.md` §10).
- ❌ Skipping `--wait` on `up` (race condition in smoke tests).
- ❌ `down --clean` in `persistent` mode without human confirmation — can delete daily-dev data.
- ❌ Ignoring healthcheck output — if it is not healthy within 60s, **fail** and print `docker compose logs`. Never proceed as if it succeeded.
- ❌ Touching containers/volumes outside the scope of `docker/<service>/` (e.g. `docker rm` on unrelated containers on the host).

## Fit with the work cycle

- Before any test/PoC that depends on an external service: `up <service> [--ephemeral]` → run the test/PoC → `down <service> [--clean]`. See `dev_environment_rule.md` §8 — an unhealthy dependency makes the run defective, not a code bug.
- Benchmark-flavored work: always `--benchmark` mode (per-run isolated volume).
- Daily dev: default (`persistent`) mode, volume kept across sessions.

## Service catalog

See `docker/README.md` (canonical source) for the current roster of services, their default ports, and default credentials.
