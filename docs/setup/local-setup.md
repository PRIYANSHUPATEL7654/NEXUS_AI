# Local setup

## Requirements

- Windows 10 or later
- Python 3.13 managed through `uv`
- Node.js compatible with the locked frontend toolchain
- PostgreSQL
- Git
- Optional Docker Desktop for container practice

## Backend

Create `backend/.env` locally. Never commit it. Keep the existing file if the
project is already working.

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_existing_database
DB_USER=your_existing_user
DB_PASSWORD=your_private_password
JWT_SECRET_KEY=your_unique_secret_of_at_least_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SQL_ECHO=false
UPLOAD_DIRECTORY=storage/uploads
MAX_UPLOAD_SIZE_MB=10
```

Commands:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI\backend"
uv sync --frozen
uv run python -m compileall app tests alembic\versions
uv run python ..\scripts\python_hygiene.py app tests alembic\versions
uv run alembic upgrade head
uv run alembic current
uv run uvicorn app.main:app --reload
```

Expected migration:

```text
20260912_12 (head)
```

## Frontend

The development default is `http://127.0.0.1:8000`. An optional
`frontend/.env.local` can contain:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Commands:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI\frontend"
npm ci
npm run test
npm run typecheck
npm run build
npm run dev
```

Open `http://localhost:5173`.

## Dedicated PostgreSQL tests

Create `nexus_ai_test` in pgAdmin with the same owner as the normal local
database. Then run:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI\backend"
$env:TEST_DB_NAME = "nexus_ai_test"
uv run python -m unittest discover -s tests -v
Remove-Item Env:TEST_DB_NAME
```

Expected:

```text
Ran 9 tests
OK
```

## Docker Compose

Create the ignored local secret file:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI"
Copy-Item deploy\compose.env.example deploy\compose.env
notepad deploy\compose.env
```

Replace both placeholder values, save, and run:

```powershell
docker compose --env-file deploy\compose.env config
docker compose --env-file deploy\compose.env up --build
```

Open:

```text
Frontend: http://localhost:8080
API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
```

Stop without deleting data:

```powershell
docker compose --env-file deploy\compose.env down
```

Do not run `down --volumes` unless the disposable Docker database and uploads
are intentionally being deleted.
