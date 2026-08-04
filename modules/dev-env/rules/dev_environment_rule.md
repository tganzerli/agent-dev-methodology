---
trigger: always_on
---

# Dev Environment Rule

## 1. Core directive

Every **external service dependency** of the project (databases, brokers, caches, mock/stub servers, any service that speaks a real TCP/UDP protocol and is not the local language runtime/toolchain) lives in a versioned container, declared under `docker/<service>/`, and is operated exclusively through the `dev-env` skill (`.claude/skills/dev-env/SKILL.md`).

Reason: reproducibility across machines, friction-free onboarding, clean multi-OS CI, and controlled setup for benchmarks. If the project keeps an ADR for this decision, cross-reference it here.

## 2. What counts as an "external dependency"

**Counts:**
- Databases (SQL or document/key-value, relational or not).
- Backend servers used as a **dependency of integration tests** (e.g. an HTTP/API server spun up as a fixture, not the code under test itself).
- Message brokers / queues.
- Stubs and mocks that speak TCP/UDP for real (SFTP, SMTP, mock-OAuth, mock object storage).

**Does not count** (local prerequisites, documented in plain READMEs, not containerized):
- The build toolchain (language SDK, compiler, package manager).
- CLI tools used by benchmarks or scripts (a DB client, `jq`, load-generators, ad-hoc scripts).
- IDEs and LSPs.

The dividing line is simple: **if the `up → work → down` lifecycle makes sense for the piece, it is an external dependency and belongs in `docker/`.** If instead it is something a developer installs once and keeps in `$PATH`, it is a local prerequisite, not a container.

## 3. Mandatory layout

```
docker/
├── README.md                       ← navigable catalog of environments
└── <service>/                      ← one directory per service
    ├── docker-compose.yml          ← Compose v2 (no `version:` key)
    ├── .env.example                ← default variables, VERSIONED in Git
    ├── .env                        ← local copy with overrides, GITIGNORED
    └── README.md                   ← usage, modes, service-specific troubleshooting
```

Anti-layouts:
- ❌ A single monolithic `docker/docker-compose.yml` covering multiple unrelated services.
- ❌ `docker/<service>/data/` (a bind mount into the working tree) — pollutes or leaks into Git.
- ❌ `docker-compose.<service>.yml` at the repo root — breaks the navigable catalog.

## 4. `docker-compose.yml` requirements

Every compose file is **required** to have:

1. **No `version:` key** — Compose v2 ignores it; its presence signals a stale compose file.
2. A predictable **`container_name`** (e.g. `<project>-<service>-dev`).
3. **`environment`** read from `.env` with sane defaults via `${VAR:-default}`.
4. **`ports`** configurable via `.env` (`${X_PORT:-default}:internal`).
5. A **`healthcheck`** that returns success when the service is actually ready. The `dev-env` skill depends on it for `up --wait` — without one, "up" cannot mean "ready."
6. **Named volumes** (never bind mounts under `./data`). Naming convention: `<project>-<service>-dev-data`.
7. A **`restart`** policy (e.g. `unless-stopped`) when the service is primarily used in `persistent` mode.

## 5. Lifecycle — three modes

| Mode | When to use | Cleanup |
|---|---|---|
| **persistent** | Daily dev work, long sessions. | Volumes kept across sessions. Explicit cleanup only (`down --clean`). |
| **ephemeral** | Smoke tests, short validations, migration/PoC steps. | Automatic `down -v` once the run ends (Ctrl-C or explicit). |
| **benchmark** | Runs that need isolated, throwaway state. | A dedicated per-run volume/project name, discarded after the run. Pairs naturally with a `benchmarks` module if one is installed — one clean environment per measured run, no cross-contamination between runs. |

The `dev-env` skill materializes all three modes on top of a single, standard compose file. Naming and cleanup policy live in the skill, not duplicated per service.

## 6. Secrets and configuration

- **`.env.example` is versioned**, with defaults adequate for local dev (weak/default credentials are fine here — this is not production).
- **`.env` is gitignored** (`docker/**/.env` covered by `.gitignore`).
- **No real secret ever appears in `docker-compose.yml`** — always through a variable.
- **Do not use Compose's declarative `secrets:`** at this stage — see §7 of the README for when that escalation is warranted.

## 7. Mandatory healthcheck — examples

The healthcheck's job is to make "the service answered on its port" observable and scriptable. Below are examples for two common shapes of service; they are illustrative, not an exhaustive or fixed roster — any external dependency needs an equivalent check for *its* readiness signal.

A SQL database:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-app}"]
  interval: 2s
  timeout: 5s
  retries: 15
  start_period: 5s
```

A document database:
```yaml
healthcheck:
  test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping').ok"]
  interval: 2s
  retries: 20
```

## 8. Precondition for tests and PoCs that depend on an external service

Before running any test, smoke check, or PoC that talks to an external service, verify the service is healthy (`docker compose ps` reports `healthy`, or `/dev-env status`). A service that is silently down or still starting is a **defective run**, not evidence of a driver/code bug. Do not diagnose application-level failures until the dependency's health has been confirmed; re-run once it is healthy before trusting the result.

## 9. Adding a new service

1. Create `docker/<service>/docker-compose.yml` following §4.
2. Create `docker/<service>/.env.example`.
3. Create `docker/<service>/README.md` documenting usage, default credentials, and troubleshooting.
4. Update the table in `docker/README.md`.
5. Update the project's conceptual/cross-cutting page for the dev environment, if one exists.
6. Validate with `/dev-env up <service>` and record the result (execution log or ADR, per the project's methodology).

## 10. Anti-patterns

- ❌ Ad-hoc `docker run` — not reproducible, not versioned.
- ❌ Secrets committed in `docker-compose.yml`.
- ❌ Bind mounts under `./data`.
- ❌ No healthcheck.
- ❌ Monolithic compose covering multiple unrelated services.
- ❌ A `version:` key in the compose file (Compose v2 ignores it; signals a stale file).
- ❌ Hardcoded ports with no `.env` override.
- ❌ A README that says "install X on your machine" instead of "run `/dev-env up X`."

## 11. Cross-reference

- Operational skill: `.claude/skills/dev-env/SKILL.md`
- Module README: `modules/dev-env/README.md` (this rule ships as part of the `dev-env` module)
- If the project's `METHODOLOGY.md` has a dedicated section on environment reproducibility, keep it aligned with §8 above (the "unhealthy dependency ⇒ defective run, not a bug" precondition).
