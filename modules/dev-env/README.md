# Dev-env module — reproducible external-service environments

> **OPTIONAL module.** Install when the project depends on external services (database, broker, cache, etc.) that must be reproducible across machines and CI. If the project has zero external service dependencies (a pure library, a stateless CLI with no DB/broker/cache), you do **not** need this module.

## 1. What this adds

| Artifact | Path | Purpose |
|---|---|---|
| `dev_environment_rule.md` | `.agents/rules/dev_environment_rule.md` | The discipline: every external service dependency lives in a versioned container under `docker/<service>/`, with a required healthcheck, three lifecycle modes, and the precondition that an unhealthy dependency makes a test run *defective*, not a code bug. `trigger: always_on`. |
| `dev-env` skill | `.claude/skills/dev-env/SKILL.md` | Operates `docker compose` for every service under `docker/<service>/`: `up \| down \| status \| logs \| exec`, waiting for the healthcheck before returning from `up`. Human-gated (`disable-model-invocation: true`). |
| `docker/` layout convention | `docker/<service>/{docker-compose.yml, .env.example, .env, README.md}` | The catalog structure every service directory follows — see rule §3. |

This module does not touch the knowledge vault. `docker/` sits at the **repo root**, alongside the code, not inside `{{project}}_wiki/`.

## 2. The core idea

Any service that is not the local language runtime/toolchain, but that the project talks to over a real protocol (a database, a broker, a cache, a mock server), is an **external dependency**. The dividing line the rule uses:

> If the `up → work → down` lifecycle makes sense for the piece, it is an external dependency and belongs in `docker/`.

Things that do **not** count — and stay as plain, locally-installed prerequisites documented in a README, not containerized — are the build toolchain (SDK, compiler, package manager), CLI tools used by scripts/benchmarks, and IDEs/LSPs. Nobody containerizes their own compiler.

## 3. Layout

```
docker/
├── README.md                       ← navigable catalog of environments
└── <service>/
    ├── docker-compose.yml          ← Compose v2, no `version:` key
    ├── .env.example                ← versioned defaults
    ├── .env                        ← gitignored local overrides
    └── README.md                   ← usage, modes, troubleshooting
```

One directory per service — never a monolithic root-level compose file covering several unrelated services. Every compose file carries a predictable `container_name`, env via `.env` with `${VAR:-default}`, configurable ports, named volumes (no `./data` bind mounts), and — non-negotiably — a **healthcheck**. The `dev-env` skill's `up --wait` depends on that healthcheck to know the service is actually ready, not just started.

## 4. Lifecycle modes

Three modes, materialized by the skill on top of one standard compose file — the policy is not re-implemented per service:

- **persistent** — daily dev, long sessions; volumes kept between sessions.
- **ephemeral** — smoke tests, short validations, PoC/migration steps; `down -v` once the run ends.
- **benchmark** — isolated per-run volume/project name, discarded after the run. Pairs naturally with a `benchmarks` module if the kit has one installed: one clean environment per measured run, no cross-contamination.

## 5. Precondition this module enforces

Before any test or PoC that depends on an external service, its health must be confirmed (`docker compose ps` healthy, or `/dev-env status`). A silently-down or still-starting service makes the run **defective**, not evidence of a driver/application bug — see rule §8. This precondition is the module's main defect-attribution win: it stops "flaky test" investigations that are actually "the container wasn't ready yet."

## 6. Adding a new service — checklist

1. `docker/<service>/docker-compose.yml` per rule §4 (healthcheck, named volume, `.env`-driven ports, no `version:`).
2. `docker/<service>/.env.example`, versioned.
3. `docker/<service>/README.md` — usage, default credentials, troubleshooting.
4. Update the table in `docker/README.md`.
5. Validate with `/dev-env up <service>` before considering the service done.

## 7. Install

See `INSTALL.md` §5-quinquies (dev-env module). In short:

1. Copy `rules/dev_environment_rule.md` → `.agents/rules/dev_environment_rule.md`.
2. Copy `skills/dev-env/` → `.claude/skills/dev-env/`.
3. Register `dev-env` in `.claude/skills/_index.md` (mark it manual-only).
4. Create `docker/README.md` (empty catalog table) at the repo root; add `docker/**/.env` to `.gitignore`.
5. As each service is added, follow the checklist in §6.

## 8. Opt-in escalations (NOT default)

The pattern above is the proven core — versioned compose per service, required healthcheck, three lifecycle modes. Two heavier ideas are **not** part of the default install; reach for them only when a concrete pain justifies the machinery:

- **Declarative Compose `secrets:`.** Instead of `.env`-sourced variables, mount secrets as files via Compose's `secrets:` block. *Escalate when:* the project moves past "weak dev defaults are fine" (e.g. shared/remote dev environments, or compliance requirements touch local tooling). Until then, `.env.example` (versioned) + gitignored `.env` is enough — this is dev tooling, not production.
- **Multi-service orchestration** (dependency ordering across services, a single `docker compose` invocation spanning `docker/*/`). *Escalate when:* services genuinely need to come up together and depend on each other's health (e.g. an app-under-test that requires both a DB and a broker live). Until then, one compose file per service, brought up independently by the skill, keeps the catalog simple and each service's blast radius small.

Both are deliberately excluded from the default — the seed-vs-accretion principle (see `docs/design-rationale.md`): start with the proven core, add an escalation only when its triggering pain actually shows up.
