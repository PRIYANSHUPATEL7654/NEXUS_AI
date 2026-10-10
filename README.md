# NEXUS AI

NEXUS AI is a unified, privacy-first personal AI ecosystem for Knowledge,
Learning, Money, Work and explainable cross-module Intelligence. It is one
responsive React PWA backed by one FastAPI API, PostgreSQL database, user
identity, file/import pipeline and ownership model.

## MVP checkpoint

```text
API version: 0.12.0
Alembic head: 20260912_12
Primary client: responsive installable React PWA
Payment requirement: none
```

## Modules

- **Today** - daily brief, explainable recommendations, quick actions and Ask
  Nexus.
- **Knowledge** - private files, extraction, search, summaries and PDF export.
- **Learn** - goals, topics, progress, skill gaps and local quizzes.
- **Money** - manual or reviewed imports, categorization, duplicate review,
  analytics and CSV export.
- **Work** - projects, tasks, document-to-plan drafts and low/high estimates.
- **Intelligence** - owned cross-module search and audited read-only tools.
- **Notifications** - owned import-review, import-failure and overdue-task
  notices.

## Technology

- Python 3.13, FastAPI, SQLAlchemy, Alembic and PostgreSQL
- React 19, TypeScript and Vite
- JWT bearer authentication and Argon2 password hashing
- Docker and Docker Compose
- GitHub Actions CI
- Deployment-ready for a free-tier PostgreSQL provider, Docker web host and
  HTTPS static frontend host

## Local development

Detailed instructions: [`docs/setup/local-setup.md`](docs/setup/local-setup.md)

Backend:

```powershell
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. API documentation is available at
`http://127.0.0.1:8000/docs`.

## Release checks

```powershell
cd backend
uv run python -m compileall app tests alembic\versions
uv run python ..\scripts\python_hygiene.py app tests alembic\versions
uv run python -m unittest tests.test_contracts tests.test_services -v
uv run alembic heads

cd ..\frontend
npm run test
npm run typecheck
npm run build
```

The full PostgreSQL integration suite requires the guarded `TEST_DB_NAME`
described in the local setup document.

## Docker learning environment

```powershell
Copy-Item deploy\compose.env.example deploy\compose.env
# Edit deploy\compose.env locally and replace both placeholders.
docker compose --env-file deploy\compose.env up --build
```

Open `http://localhost:8080`. The API remains at `http://127.0.0.1:8000`.
`deploy/compose.env` is ignored by Git.

## Documentation

- [Architecture](docs/architecture/system-architecture.md)
- [Local setup](docs/setup/local-setup.md)
- [Free-tier deployment](docs/deployment/free-tier-deployment.md)
- [Operations and rollback](docs/deployment/operations-and-rollback.md)
- [Security and privacy](docs/security/security-and-privacy.md)
- [Final MVP QA](docs/testing/final-mvp-qa.md)
- [Demo and screenshot script](docs/product/demo-script.md)
- [Known limitations and roadmap](docs/product/known-limitations-and-roadmap.md)
- [Learning logs](docs/learning-log/)

## Privacy and secret safety

Never commit `.env`, hosted connection strings, JWT secrets, uploaded private
files, financial exports, `node_modules`, `.venv` or build output. The GitHub
repository is intended to remain private during development. Platform secrets
belong only in the hosting provider or GitHub encrypted-secret interface.

## portfolio status

This repository is currently a private personal MVP and learning project.
