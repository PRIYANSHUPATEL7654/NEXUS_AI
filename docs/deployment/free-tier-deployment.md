# Free-tier deployment

## Target architecture

This MVP deployment uses three independently replaceable services:

| Layer | Suggested service | Required capability |
| --- | --- | --- |
| PostgreSQL | Neon free plan | Managed PostgreSQL connection string with TLS |
| Backend | Render free web service | Docker deployment and `/health` checking |
| Frontend | Cloudflare Pages free plan | Static Vite build, HTTPS and custom environment variable |

Free-plan terms can change. Confirm that the selected plan shows zero cost and
does not enable paid overages or automatic billing before creating each
resource.

## Step 1 - Push a safe private GitHub checkpoint

Run the complete local release gate first. Then inspect exactly what Git will
upload:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI"
git status
git diff --check
git ls-files | Select-String -Pattern "(^|/)(\.env|\.venv|node_modules|dist|storage/uploads)(/|$)"
```

The final command should produce no output. Never proceed if a real environment
file, upload or financial export is listed.

Commit and push only after review:

```powershell
git add .
git status
git commit -m "Complete NEXUS AI Docker CI and deployment readiness"
git push origin main
```

Open the GitHub Actions tab. `NEXUS CI` must pass before deployment.

## Step 2 - Create managed PostgreSQL

In Neon:

1. Create a free project in a nearby region.
2. Keep the generated database and role names.
3. Copy the pooled PostgreSQL connection string.
4. Require TLS/SSL in the connection string.
5. Do not place the connection string in GitHub files or chat.

The backend accepts one production variable:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

It converts normal PostgreSQL URLs to the `psycopg` SQLAlchemy driver
internally.

## Step 3 - Generate the JWT secret locally

Generate a unique value in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the result directly into the Render secret field. Do not save it in the
repository, screenshots or documentation.

## Step 4 - Deploy the Docker backend

In Render:

1. Choose New -> Blueprint.
2. Connect the private GitHub repository.
3. Render reads the root `render.yaml`.
4. Confirm the service uses the `backend` root and Docker runtime.
5. Select only a zero-cost/free instance.
6. Enter secret environment values when requested.

Required Render variables:

| Variable | Value source |
| --- | --- |
| `DATABASE_URL` | Neon connection string |
| `JWT_SECRET_KEY` | Newly generated private secret |
| `CORS_ORIGINS` | Temporary `https://placeholder.invalid` until frontend exists |

The remaining non-secret settings come from `render.yaml`. The container runs:

```text
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Expected startup log includes:

```text
Running upgrade 20260911_11 -> 20260912_12, add notifications
Starting NEXUS AI API
```

Open the assigned backend URL followed by `/health`.

Expected:

```json
{
  "status": "healthy"
}
```

Open `/docs` and verify API version `0.12.0`.

## Step 5 - Deploy the HTTPS frontend

In Cloudflare Pages:

1. Create a Pages project from the same private GitHub repository.
2. Set the root directory to `frontend`.
3. Use build command `npm run build`.
4. Use output directory `dist`.
5. Add the build variable below.

```text
VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND
```

Do not include a trailing slash. Deploy and copy the final HTTPS Pages origin,
for example `https://your-project.pages.dev`.

The files `_headers` and `_redirects` are copied by Vite into the production
artifact. They provide safe static headers, service-worker cache rules and SPA
fallback behavior.

## Step 6 - Lock backend CORS to the real frontend

Return to Render and replace `CORS_ORIGINS` with the exact Pages origin:

```text
CORS_ORIGINS=https://YOUR-PROJECT.pages.dev
```

Use comma-separated exact origins only when both a Pages domain and custom
domain are genuinely active. Do not use `*` for the authenticated production
API.

Redeploy/restart the backend, then reload the frontend with `Ctrl+Shift+R`.

## Step 7 - Run deployment smoke checks

From the repository root:

```powershell
$env:NEXUS_API_URL = "https://YOUR-RENDER-BACKEND"
$env:NEXUS_FRONTEND_URL = "https://YOUR-PROJECT.pages.dev"
python scripts\deployment_smoke.py
Remove-Item Env:NEXUS_API_URL
Remove-Item Env:NEXUS_FRONTEND_URL
```

Expected ending:

```text
PASS API health
PASS API version and required routes
PASS frontend HTML
PASS PWA manifest
PASS service worker
Deployment smoke checks passed
```

The script sends no credentials and creates no user data.

## Step 8 - Production migration check

Startup applies the migration before Uvicorn. Confirm the Render log contains a
successful Alembic upgrade and no `relation does not exist` error.

Do not run `alembic downgrade` against production as a casual test. If migration
startup fails, stop deployment, preserve the log and follow the rollback guide.

## Step 9 - Phone PWA installation

1. Open the final Cloudflare Pages HTTPS URL on the phone.
2. Sign in and verify Today loads.
3. In Chrome, select Install app or Add to Home screen.
4. Launch NEXUS from the new home-screen icon.
5. Confirm standalone display and the six-module bottom navigation.

HTTPS is required for production service-worker and install behavior.

## Official service references

- Render free services: <https://render.com/docs/free>
- Render Blueprint specification: <https://render.com/docs/blueprint-spec>
- Neon plans: <https://neon.com/docs/introduction/plans>
- Cloudflare Pages Git integration: <https://developers.cloudflare.com/pages/get-started/git-integration/>
- Cloudflare Pages build configuration: <https://developers.cloudflare.com/pages/configuration/build-configuration/>
- GitHub Actions: <https://docs.github.com/actions>
