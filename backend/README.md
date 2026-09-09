# NEXUS AI backend

FastAPI backend for the NEXUS AI ecosystem. It provides JWT authentication,
owner-filtered PostgreSQL operations, shared file/import processing, Knowledge,
Learn, Money, Work, Intelligence and Notification APIs.

## Development

```powershell
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Configuration

Local development may use `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and
`DB_PASSWORD`. Production may instead use one `DATABASE_URL`. Both use the
`postgresql+psycopg` SQLAlchemy driver internally.

Other important settings are `JWT_SECRET_KEY`, `CORS_ORIGINS`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `SQL_ECHO`, `UPLOAD_DIRECTORY` and
`MAX_UPLOAD_SIZE_MB`. See `../docs/deployment/free-tier-deployment.md`.

## Tests

```powershell
uv run python -m unittest tests.test_contracts tests.test_services -v
```

The guarded PostgreSQL suite requires a disposable `TEST_DB_NAME` that differs
from `DB_NAME` and contains `test`.
