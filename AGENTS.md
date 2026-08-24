# Codex project instructions

## Objective

Build the academic BI proof of concept described in `docs/scope.md`. Keep the implementation deliberately narrow, reproducible and auditable.

## Required reading before changes

1. `docs/scope.md`
2. `docs/architecture.md`
3. `docs/replication-guide.md`
4. the latest entry in `docs/logbook/bitacora.tex`

## Non-negotiable rules

- Run the application and development tools through Docker. Do not require host Python, Node.js, PostgreSQL or SQL Server.
- `docker compose up --build -d` must create an isolated project network, PostgreSQL, SQL Server/AdventureWorks, backend and frontend without touching unrelated containers.
- Never commit `.env`, credentials, tokens, database volumes, `.bak` files or real third-party data.
- Treat AdventureWorks as read-only. Frontend restrictions never replace FastAPI authorization or SQL Server permissions.
- The LLM may propose and explain; deterministic validators and explicit human approval must precede execution.
- Preserve the current phase boundary. Do not implement business modules unless the active task explicitly requests the next iteration.
- RBAC is mandatory but currently scaffolded. When implemented, authorization belongs in FastAPI and menus only reflect backend permissions.

## Definition of done for every Codex change

1. Add or update proportional tests.
2. Run the narrow checks while developing, then run `make verify` before handoff.
3. Update `docs/logbook/bitacora.tex` with decisions, files, verification results, incidents and pending work.
4. Regenerate `docs/logbook/bitacora.pdf` with `make logbook`.
5. Update README/architecture/replication docs when commands, ports, images or environment variables change.
6. Report any check that could not run; never mark a pending check as successful.

## Git and delivery

- Stable/release branch: `main`.
- Integration and default branch: `develop`.
- Start `feature/*`, `fix/*`, `docs/*` and `chore/*` branches from `develop`; merge them back through pull requests.
- Promote tested changes from `develop` to `main` through a release pull request. Never develop directly on `main`.
- Use Conventional Commits.
- Work on focused branches and merge through pull requests once GitHub is connected.
- CI must pass before publishing. CD publishes every custom image to GHCR using branch, SHA and version tags.
- Never push, change package visibility or delete remote resources without the user's explicit target/visibility decision.

## Architecture boundaries

- `system`: technical health only.
- `security`: authentication and RBAC.
- `parameters`: approved settings and connections.
- `metadata`: deterministic source introspection.
- `copilot`: structured LLM proposals only.
- `etl`: preview, validation, execution and traceability.
- `analytics`: KPIs, charts and explainable insights.
- `forecasting`: linear regression, MAPE and RMSE.
- `reports`: academic evidence and reports.

Keep dependencies flowing through explicit interfaces; do not let modules execute arbitrary LLM-produced SQL.
