# Production operations and rollback

## Health and startup

The backend exposes `GET /health`. Render uses it as the service health path and
the Docker image uses it for its container health check. A successful response
is:

```json
{"status":"healthy"}
```

The container startup order is:

```text
load platform secrets
-> connect to PostgreSQL
-> alembic upgrade head
-> start one Uvicorn process
-> health checks begin
```

## Logs

- Render: inspect deployment and runtime logs for migration, startup, request
  status and uncaught exception output.
- Neon: inspect connection/activity information and plan usage.
- Cloudflare Pages: inspect build logs and deployment history.
- GitHub: retain the exact failing step and full first traceback from Actions.

`SQL_ECHO` is false in production so SQL statement logging does not flood logs
or unnecessarily expose record values. Uvicorn access logs remain available.

## Cold starts

A zero-cost backend or database may suspend when idle. The first request after
idle time can therefore be slower. The frontend already reports that the
backend may be waking rather than immediately claiming data was lost.

Do not add a paid uptime monitor or artificial keep-alive traffic to bypass a
free service's intended limits. Diagnose repeated failures from provider logs.

## Application rollback

For a frontend-only regression:

1. Open Cloudflare Pages deployments.
2. Select the last known-good Git commit/deployment.
3. Roll it back or redeploy that commit.
4. Run the smoke checker again.

For backend code regression without a destructive schema change:

1. Identify the last green `NEXUS CI` commit.
2. Revert the faulty commit using Git rather than rewriting shared history.
3. Push the revert to `main`.
4. Let CI pass.
5. Redeploy the known-good backend.
6. Verify `/health`, `/docs`, login and one owned list endpoint.

Example:

```powershell
git log --oneline -10
git revert COMMIT_HASH
git push origin main
```

Review the selected hash before running `git revert`.

## Migration failure

Never edit an already applied migration. Do not use `alembic stamp` to hide a
failed production migration.

1. Stop the failing deployment from repeatedly restarting.
2. Preserve the complete Alembic traceback and current database state.
3. Determine whether the migration transaction rolled back.
4. Fix the cause locally against a disposable PostgreSQL database.
5. Create a new forward-fix revision when the schema itself must change.
6. Rerun compile, tests, `alembic upgrade head` and `alembic check`.
7. Deploy only after CI passes.

Revision `20260912_12` is additive. Earlier application code ignores the new
table, so code rollback does not require deleting it.

## Data protection

Before a future destructive migration, use the PostgreSQL provider's available
backup/export mechanism or `pg_dump`. Verify the export without posting its
contents publicly. Free-plan backup retention may be limited.

The current hosted upload directory is temporary. PostgreSQL recovery does not
restore missing uploaded file bytes. Durable object storage and backup policy
remain post-MVP requirements.
