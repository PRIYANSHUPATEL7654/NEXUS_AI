# NEXUS AI — Days 15–16: Intelligence Orchestration and Responsive PWA

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 15–16 |
| Day 15 | Nexus Intelligence read-only orchestration layer |
| Day 16 | Responsive React/TypeScript PWA foundation |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Frontend | React, TypeScript and Vite |
| Authentication | JWT bearer token with Argon2 password hashing |
| Starting migration | `20260910_10` |
| Ending migration | `20260911_11 (head)` |
| Starting API version | `0.10.0` |
| Ending API version | `0.11.0` |
| Implementation status | Package produced |
| Assistant-side validation | Completed successfully |
| Windows/PostgreSQL/browser confirmation | Pending at the time of handoff |
| Documentation status | Complete |

---

## Purpose and completed outcome

Days 15–16 connect the existing NEXUS modules into the first unified daily-use
experience.

Before Day 15, Knowledge, Learn, Money and Work had working backend workflows,
but each module had to be tested independently. Day 15 added a controlled
Intelligence layer that can read owned data from all four modules, calculate a
daily brief, explain recommended next actions, route simple natural-language
questions to allowed tools, and retain a compact audit record.

Before Day 16, Swagger was the primary interface. It correctly exposed the API,
but it required users to copy database IDs manually. Day 16 added the first
responsive web interface with real authentication, session restoration,
profile display, dashboard cards, recommendations, Ask Nexus, desktop/mobile
navigation, and an installable PWA foundation.

This block deliberately does not attempt to build a general chatbot. It creates
value by connecting the structured information the user has intentionally
saved in NEXUS AI.

The Day 16 module pages are intentionally placeholders. Their complete forms,
lists and review flows belong to Days 17–18.

---

## Block target

| Day | Deliverable |
| --- | --- |
| 15 | Nexus Intelligence read-only orchestration, daily brief, recommendations, search and audit records |
| 16 | Responsive React frontend shell, authentication, dashboard and installable PWA foundation |

Starting checkpoint: API `0.10.0`, migration `20260910_10`.

Ending target: API `0.11.0`, migration `20260911_11 (head)`.

The Intelligence MVP is intentionally local and deterministic. It uses NEXUS
data and explainable Python rules; it does not require a paid LLM key. All tools
in this block are read-only. Later agent actions that write or delete data must
ask the user for confirmation.

## 1. Copy safely

Stop Uvicorn. Extract the package outside the repository. Copy `backend` and
`frontend` into the NEXUS_AI root and replace matching backend files. The final
structure must contain sibling folders:

```text
NEXUS_AI/
├── backend/
├── frontend/
└── docs/
```

Also place the finished Day 13–14 document at:

```text
docs/learning-log/day-13-14-money-files-analytics-work-planning.md
```

## 2. Backend environment and migration

The default CORS configuration already permits the two local Vite origins. If
you maintain an explicit backend `.env`, merge this optional value into it:

```dotenv
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Never replace an existing `.env` with an example file.

Run from `backend`:

```powershell
uv run alembic current
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Expected:

```text
20260911_11 (head)
No new upgrade operations detected.
```

Start the API:

```powershell
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Expected version: `0.11.0`.

## 3. Day 15 architecture

The new Intelligence layer does not duplicate module business rules. It calls
the same PostgreSQL-backed data through a controlled service layer:

```text
Authenticated request
        ↓
Intelligence router
        ↓
Allowed read-only tool
        ↓
Owned Knowledge/Learn/Money/Work rows
        ↓
Explainable result + compact audit record
```

The audit table stores operation metadata and result shape, not the user's full
Ask message or entire returned private record set.

## 4. Authenticate for backend tests

In Swagger, log in with the account used for Days 11–14 and press Authorize.
Verify:

```text
GET /auth/me
```

All Intelligence results use the user ID derived from this bearer token. Do not
send a user ID in an Intelligence request body.

## 5. Inspect the tool registry

Run:

```text
GET /intelligence/tools
```

Expected eight read-only tools:

1. `search_user_documents`
2. `summarize_document`
3. `get_learning_progress`
4. `get_revision_queue`
5. `get_money_summary`
6. `get_budget_status`
7. `get_pending_tasks`
8. `get_project_progress`

Each descriptor tells the client which parameters are required and optional.

## 6. Test cross-module search

Use a term that appears in one of your real documents, topics, transactions,
projects or tasks:

```text
GET /intelligence/search?q=NEXUS&limit=20
```

Expected: `query`, `total` and ranked results. Each result includes the module,
record type, real record ID, title, short snippet and frontend route. The search
uses only records owned by the authenticated account.

Also test a query with no matches. Expected: `200`, `total=0`, empty results.

## 7. Test the daily brief

```text
GET /intelligence/daily-brief
```

Expected:

- greeting based on the profile timezone;
- local date and timezone;
- one summary sentence;
- four cards: Learning, Work, Money and Knowledge;
- owned approved data only;
- overdue work and learning gaps reflected when present.

If the displayed time/date is wrong, update `/profile/me` with a valid IANA
timezone such as `Asia/Kolkata`. The server falls back to UTC only when the
profile is missing or invalid.

## 8. Test explainable recommendations

```text
GET /intelligence/recommendations
```

Each recommendation contains:

- module;
- priority from 1–5;
- visible title;
- reason;
- evidence list;
- suggested action;
- frontend route.

No opaque model score is used in this MVP. A recommendation must be traceable
to a recorded skill gap, pending/overdue task, monthly totals or missing
Knowledge content.

## 9. Run individual tools

Money summary:

```text
POST /intelligence/tools/get_money_summary/run
```

```json
{
  "parameters": {
    "year": 2026,
    "month": 9,
    "currency": "INR"
  }
}
```

Budget comparison—the limit is supplied by the caller and is not bank data:

```text
POST /intelligence/tools/get_budget_status/run
```

```json
{
  "parameters": {
    "monthly_limit": "15000",
    "year": 2026,
    "month": 9,
    "currency": "INR"
  }
}
```

Learning queue:

```text
POST /intelligence/tools/get_revision_queue/run
```

```json
{
  "parameters": { "limit": 5 }
}
```

Pending work:

```text
POST /intelligence/tools/get_pending_tasks/run
```

```json
{
  "parameters": { "limit": 10 }
}
```

Project estimate—first obtain the project from `GET /work/projects`:

```text
POST /intelligence/tools/get_project_progress/run
```

```json
{
  "parameters": { "project_id": YOUR_REAL_PROJECT_ID }
}
```

Document summary—first obtain the document from
`GET /knowledge/documents`:

```text
POST /intelligence/tools/summarize_document/run
```

```json
{
  "parameters": { "document_id": YOUR_REAL_DOCUMENT_ID }
}
```

This tool retrieves the latest saved summary. It does not silently regenerate
or overwrite one.

## 10. Test Ask Nexus intent routing

Run `POST /intelligence/ask` with these bodies one at a time:

```json
{ "message": "What should I focus on today?" }
```

```json
{ "message": "What did I spend this month?" }
```

```json
{ "message": "What should I revise next?" }
```

```json
{ "message": "What work is pending?" }
```

```json
{ "message": "Find NEXUS architecture in my records" }
```

Expected: an intent, concise answer, tools used, structured data and run ID.
This is a safe orchestration baseline, not an attempt to compete with a general
chatbot.

## 11. Verify audit behavior and failures

```text
GET /intelligence/runs?limit=30
```

The most recent operations should appear. For Ask requests,
`request_payload` contains `message_length`, not the original private message.

Run an invalid tool:

```text
POST /intelligence/tools/not_enabled/run
```

```json
{ "parameters": {} }
```

Expected `422` and a failed audit row. Run project progress with an unowned or
nonexistent project ID; expected `404`.

## 12. Day 15 ownership test

Authorize as User A and search a phrase unique to User A. Save a User A project
ID. Authorize as User B:

- searching the unique phrase must not expose User A's record;
- running project progress with User A's project ID must return `404`;
- User B's daily brief must contain only User B's counts/totals.

## 13. Prepare Node for Day 16

Open a second PowerShell terminal at the NEXUS_AI root:

```powershell
cd frontend
node --version
npm --version
```

This package uses Vite 8. Use Node `20.19+` or `22.12+`. If the installed Node
is older, install a current Node LTS release before continuing.

## 14. Install and configure the frontend

From `frontend`:

```powershell
npm install
Copy-Item .env.example .env
npm run typecheck
npm run build
```

The local `.env` contains:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`.env` is git-ignored. Vite environment variables are compiled into browser
code, so never put passwords, JWTs, database URLs or API secrets in any
`VITE_...` value.

## 15. Start the responsive application

Keep the FastAPI terminal running. In the frontend terminal:

```powershell
npm run dev
```

Open:

```text
http://localhost:5173
```

Use an existing NEXUS account or register a new one. A successful login opens
the unified Today dashboard. The token remains in browser local storage for
this MVP and is removed on Sign out.

## 16. Test authentication behavior

1. Log in with a valid account.
2. Refresh the page; the session should be restored through `/auth/me`.
3. Enter an invalid password; the backend message should appear.
4. Sign out; the login screen should return.
5. Refresh again; the signed-out state should remain.

## 17. Test the unified dashboard

After login, verify:

- the greeting uses the signed-in user's name;
- four module cards render without entering IDs;
- counts/totals correspond to Swagger results;
- recommendations contain reason and action text;
- Ask Nexus answers the sample Money and Work prompts;
- the profile page shows the current account;
- Knowledge, Learn, Money and Work links open their module placeholders.

The module placeholders are intentional for this block. The Knowledge/Learn
workflows are connected to screens in Day 17; Money/Work are connected in Day
18. The dashboard and authentication are real now.

## 18. Test responsive behavior

Open browser developer tools and switch to a phone viewport such as 390×844.
Verify:

- the desktop sidebar becomes a bottom navigation bar;
- the mobile header remains visible;
- cards become one or two columns without horizontal page scrolling;
- forms and buttons remain tappable;
- profile content becomes one column.

Then test a tablet width and a full laptop width.

## 19. Test the production PWA build

Service-worker registration is intentionally enabled only for production
builds. Stop `npm run dev`, then run:

```powershell
npm run build
npm run preview
```

Open `http://localhost:4173`. In browser developer tools, check Application:

- manifest name is `NEXUS AI`;
- 192×192 and 512×512 icons load;
- display mode is `standalone`;
- service worker is active;
- reloading the app shell after going offline works.

Do not expect live backend data while offline. The service worker deliberately
does not cache authenticated API responses containing private data.

Phone installation over a laptop LAN address may be blocked because service
workers require a secure context. Use mobile emulation now. Real phone
installation is tested after the HTTPS deployment in Day 22.

## 20. Cold-start behavior

The free backend may sleep. The dashboard shows a waiting message and Retry
button instead of pretending that an empty response is real data. This is part
of the free-tier product design; it is not a database failure by itself.

## 21. Final checks

Backend:

```powershell
uv run alembic current
uv run alembic check
```

Frontend:

```powershell
npm run typecheck
npm run build
```

Git safety:

```powershell
git status
git check-ignore backend/.env
git check-ignore frontend/.env
git check-ignore frontend/node_modules
```

Inspect staged files carefully. Never commit `.env`, JWTs, database URLs,
uploaded private documents, generated user exports or `node_modules`.

## 22. Git checkpoint after all tests pass

```powershell
git add .
git status
git commit -m "feat: add intelligence dashboard and responsive pwa shell"
git push
```

Only do this after the backend, build and browser tests pass.

## Completion and handoff report

The implementation package was produced and passed assistant-side structural
validation. The actual Windows/PostgreSQL/browser results should still be
recorded using `DAY-15-16-TEST-RESULTS-TEMPLATE.md` in the next chat if they were
not completed before moving conversations.

For a failure, preserve the exact command or endpoint, request, response,
browser console output, full backend traceback, current Alembic revision and
first unfinished test. Do not begin Days 17–18 on top of a broken checkpoint.

---

# Day 15 Technical Reference — Nexus Intelligence

## 23. Why Intelligence was added after the domain modules

An orchestration layer is only useful when it has reliable capabilities to
orchestrate. Days 9–14 had already produced owned Knowledge documents, learning
topics, transactions, projects and tasks. Day 15 could therefore combine real
data instead of creating a chatbot that answers without understanding the
user's NEXUS records.

The sequence is:

```text
Authenticated user
        ↓
Nexus Intelligence endpoint
        ↓
Allowed read-only tool or deterministic intent route
        ↓
Knowledge / Learn / Money / Work owned query
        ↓
Structured result and explainable answer
        ↓
Compact intelligence_runs audit record
```

This is a controlled orchestrator. LangChain, LangGraph, MCP and an external
LLM can later call the same tool contracts, but they are not required to prove
the architecture.

## 24. Files added or replaced for Day 15

| File | Change | Responsibility |
| --- | --- | --- |
| `backend/app/models.py` | Replaced | Adds `IntelligenceRun` and User relationship |
| `backend/app/main.py` | Replaced | Registers Intelligence router and local CORS |
| `backend/app/intelligence_schemas.py` | Added | Request/response contracts |
| `backend/app/routers/intelligence.py` | Added | Authenticated HTTP endpoints and audit writes |
| `backend/app/services/intelligence.py` | Added | Tool registry, owned queries, brief, recommendations and intents |
| `backend/alembic/versions/20260911_11_add_intelligence_audit.py` | Added | Creates `intelligence_runs` |
| `backend/.env.additions.example` | Added | Documents optional local CORS origins |

Replacing `models.py` and `main.py` was required because the new model must join
the existing relationship graph and the new router must be included by the
FastAPI application. The real backend `.env` must never be replaced by an
example file.

## 25. `intelligence_runs` table

| Field | Purpose |
| --- | --- |
| `id` | Audit record identifier |
| `user_id` | Authenticated owner |
| `operation` | Search, brief, recommendations, Ask or tool operation |
| `tool_name` | Tool used where applicable |
| `status` | `completed` or `failed` |
| `request_payload` | Safe request metadata, not unrestricted raw private input |
| `result_summary` | Compact metadata about the result |
| `created_at` | Server timestamp |

The table has indexes for `user_id` and `operation`, a foreign key to `users`,
and a status check constraint. Deleting a user cascades to that user's audit
records.

## 26. Registered tools

| Tool | Reads | Result |
| --- | --- | --- |
| `search_user_documents` | Knowledge and cross-module search foundation | Ranked owned matches |
| `summarize_document` | Latest owned saved Knowledge summary | Summary content/availability |
| `get_learning_progress` | Goals and topics | Levels and gaps |
| `get_revision_queue` | Non-mastered topics | Largest gaps first |
| `get_money_summary` | Approved Money transactions | Income, expenses, net and count |
| `get_budget_status` | Approved Money totals plus caller limit | Remaining amount and over-budget flag |
| `get_pending_tasks` | Owned incomplete Work tasks | Urgency-ordered list |
| `get_project_progress` | One owned Work project and its tasks | Progress and remaining estimate range |

All tools are read-only in this release. A future tool that writes, approves,
deletes or sends anything must show the proposed action and require explicit
confirmation.

## 27. Cross-module search

Search examines owned records in:

- Knowledge document title, description and extracted text;
- Learn topic title and description;
- Money transaction description and category;
- Work project title and description;
- Work task title, description and notes.

Results include module, record type, record ID, title, snippet, relevance score
and frontend route. The score is a transparent keyword/title weighting, not a
claimed semantic-embedding model.

This baseline should remain until pgvector and RAG are introduced with proper
user filtering and evaluation.

## 28. Daily brief calculation

The brief uses the profile timezone to derive the user's local date and
greeting. It then produces four sections:

| Section | Data source |
| --- | --- |
| Learning | Topics whose current level is below target level |
| Work | Pending tasks and overdue count |
| Money | Current-month approved income/expenses/net |
| Knowledge | Owned saved document count |

The summary sentence prioritizes overdue work and the largest learning gap.
When no urgent item exists, it says so instead of inventing a task.

## 29. Explainable recommendations

Recommendations are based on recorded evidence:

- largest Learn skill gap;
- overdue or next pending Work task;
- expenses exceeding recorded income;
- missing Knowledge documents.

Each recommendation contains module, priority, title, reason, evidence, action
and route. This makes the output inspectable and suitable for later evaluation.

## 30. Ask Nexus MVP

Ask Nexus currently uses deterministic intent routing:

| User wording | Intent/tool |
| --- | --- |
| today, focus, daily, brief | Daily brief |
| spend, expense, money, income | Money summary |
| learn, study, revision, skill, quiz | Revision queue |
| work, task, deadline, project, pending | Pending Work |
| anything else | Cross-module search |

This intentionally narrow behavior gives consistent zero-cost results. A later
LLM router must not bypass ownership or tool permissions.

## 31. Intelligence security and privacy

- Every endpoint depends on `get_current_active_user`.
- Domain queries combine record ownership with the authenticated user ID.
- Requests do not accept a trusted user ID from the client.
- Cross-user document/project IDs return no result or 404.
- The Ask audit stores message length and selected intent/tool rather than the
  complete private question.
- Results are not automatically sent to an external model.
- Tools cannot mutate domain records.

---

# Day 16 Technical Reference — Responsive React PWA

## 32. Why the frontend begins here

Swagger remains valuable for engineering tests, but it is not the daily-use
product. Database IDs appeared prominently because Swagger exposes path
parameters directly. The frontend now begins hiding those implementation
details behind authenticated requests, cards, navigation and selected objects.

The Day 16 frontend solves normal access for:

- registration;
- login;
- current-user profile;
- session restoration;
- daily brief;
- recommendations;
- Ask Nexus;
- module navigation;
- responsive laptop/mobile layout.

Days 17–18 complete the record-specific module interfaces.

## 33. Files introduced for Day 16

```text
frontend/
├── public/
│   ├── icons/icon-192.png
│   ├── icons/icon-512.png
│   ├── manifest.webmanifest
│   └── sw.js
├── scripts/create_icons.py
├── src/
│   ├── api/client.ts
│   ├── auth/AuthContext.tsx
│   ├── components/Shell.tsx
│   ├── pages/DashboardPage.tsx
│   ├── pages/LoginPage.tsx
│   ├── pages/ModulePage.tsx
│   ├── pages/ProfilePage.tsx
│   ├── App.tsx
│   ├── main.tsx
│   ├── styles.css
│   ├── types.ts
│   └── vite-env.d.ts
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## 34. API client

`src/api/client.ts` centralizes:

- API base URL;
- JSON request handling;
- form-encoded OAuth login;
- bearer authorization header;
- backend error extraction;
- network/cold-start message;
- typed authentication and Intelligence calls.

The base URL comes from:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Values prefixed with `VITE_` are browser-visible. Passwords, JWT secrets,
database URLs and other server secrets must never be placed there.

## 35. Authentication context

The React authentication context:

1. loads the access token from local storage;
2. calls `/auth/me` to validate it and retrieve the current user;
3. removes it when the backend returns 401;
4. supports login and registration;
5. restores the session after refresh;
6. removes the token during logout.

Local-storage bearer tokens are an MVP compromise. Before a broad public
release, plan short-lived access tokens plus a secure HttpOnly refresh/session
mechanism.

## 36. Responsive shell

Desktop layout includes:

- dark sidebar;
- NEXUS navigation;
- profile shortcut;
- install button when the browser exposes it;
- sign-out control.

Mobile layout includes:

- sticky top header;
- account avatar;
- fixed bottom navigation;
- one/two-column responsive cards;
- safe-area padding for phone screens.

The current lightweight hash router keeps dependencies small. A full routing
library should be added only when nested module pages make it useful.

## 37. Today dashboard

After authentication, the dashboard requests the daily brief and
recommendations concurrently. It shows:

- date/timezone and greeting;
- Learning, Work, Money and Knowledge cards;
- explainable next actions;
- Ask Nexus prompt shortcuts;
- a retry state for backend/network failure;
- a cold-start waiting message.

The dashboard uses live backend data. The module detail pages are placeholders
until their complete frontend workflows are built.

## 38. PWA foundation

The PWA includes:

- a manifest with application name, colours, start URL and standalone display;
- 192px and 512px icons;
- service-worker registration in production builds;
- application-shell caching;
- install-prompt support where the browser provides it.

Authenticated API responses are deliberately not precached. Offline mode can
open the shell but should not pretend that private data is fresh.

Actual phone installation is best verified after HTTPS deployment. Mobile
layout can be tested now through browser device emulation.

## 39. Local CORS

The backend allows the local Vite origins by default:

```text
http://localhost:5173
http://127.0.0.1:5173
```

If the backend `.env` explicitly defines `CORS_ORIGINS`, merge those values
without overwriting existing secrets.

---

# Validation and Quality Record

## 40. Assistant-side validation completed

The generated Days 15–16 package passed:

- Python compilation;
- assembled SQLAlchemy mapper configuration;
- FastAPI OpenAPI generation;
- 66 total API paths in the assembled application;
- presence of all seven Intelligence paths;
- Intelligence table mapping;
- validation of all 11 migration revision links;
- exactly one Alembic head: `20260911_11`;
- frontend dependency installation;
- TypeScript type checking;
- Vite production build;
- PWA 192px and 512px icon-path checks;
- package ZIP integrity.

The successful Vite build produced the normal `dist/index.html`, CSS asset and
JavaScript asset output. Generated `node_modules` and `dist` directories were
excluded from the downloadable source package.

## 41. User-environment validation to retain

The user's real Windows/PostgreSQL/browser environment remains authoritative.
The checkpoint should record:

```powershell
uv run alembic current
uv run alembic check
npm run typecheck
npm run build
```

Expected migration output:

```text
20260911_11 (head)
No new upgrade operations detected.
```

Also retain results for:

- existing-user login;
- optional new registration;
- refresh/session restoration;
- four dashboard sections;
- recommendations;
- Ask Nexus intents;
- Intelligence audit history;
- invalid-tool handling;
- cross-user isolation;
- desktop layout;
- mobile emulation;
- PWA production preview;
- restart persistence;
- Git secret/ignore checks.

## 42. Known limitations at this checkpoint

- Individual Knowledge/Learn/Money/Work screens are not complete yet.
- Ask Nexus is deterministic intent routing, not an open-ended LLM.
- Search is keyword-based rather than embedding/vector search.
- Recommendations are rule-based.
- There are no write-capable agents.
- The service worker does not make private backend data available offline.
- Phone installation should wait for HTTPS deployment.
- The token remains in local storage for the MVP.
- Free hosting may have cold starts.

These limitations are planned boundaries, not hidden defects.

---

# Concepts and Skills Practised

## 43. Backend and architecture skills

- orchestration above independent domain modules;
- controlled tool registry design;
- deterministic intent routing;
- cross-module PostgreSQL queries;
- authenticated ownership propagation;
- explainable recommendations;
- audit-safe request/result metadata;
- SQLAlchemy relationships and JSONB;
- Alembic schema evolution;
- CORS configuration;
- FastAPI response models and error handling.

## 44. Frontend and product skills

- React components and context;
- TypeScript API/data contracts;
- token-based authentication flow;
- protected application rendering;
- async loading/error/cold-start states;
- responsive desktop/mobile layouts;
- accessible form and navigation structure;
- environment-specific API configuration;
- production type checking and build;
- PWA manifest/service worker/installability foundation.

## 45. AI and ML interpretation

No trained ML or deep-learning model was added in this block. That is a sound
engineering decision, not missing AI.

Day 15 establishes the interfaces through which future models can be evaluated
and safely used. The current transparent baseline provides something a future
model must outperform while preserving ownership, explainability and cost.

Possible later evolution:

```text
Current deterministic tool contract
        ↓
Optional LLM/tool router
        ↓
LangGraph state and multi-step workflow
        ↓
MCP/external tools with explicit permissions
        ↓
Evaluation, confirmation and audit
```

---

# Final Checkpoint and Next Work

## 46. Stable checkpoint

```text
Project: NEXUS AI
Completed implementation block: Days 15–16
API target: 0.11.0
Alembic target: 20260911_11 (head)
Intelligence tools: 8 read-only tools
Intelligence API paths: 7
Frontend: responsive authenticated PWA foundation
Assistant-side validation: passed
User-environment validation: retain/confirm in the next chat
```

## 47. Next two-day block

After the Day 15–16 test gate is stable:

- Day 17: complete Knowledge and Learn frontend workflows;
- Day 18: complete Money and Work frontend workflows.

The frontend must fetch records through list endpoints, display human-readable
titles and descriptions, and keep database IDs internally in React state. The
user must not be asked to memorize or guess record IDs.

Future code must inspect the current repository before changing shared files.
Any new schema change requires a new Alembic migration whose `down_revision`
points to the current head. Already applied migrations must never be edited.
