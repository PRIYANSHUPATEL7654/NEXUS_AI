# NEXUS AI — Days 17–18: Complete Module Frontend Workflows

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 17–18 |
| Day 17 | Knowledge and Learn frontend workflows |
| Day 18 | Money and Work frontend workflows |
| Frontend | React 19, TypeScript and Vite |
| Backend checkpoint | FastAPI `0.11.0` |
| Database checkpoint | Alembic `20260911_11 (head)` |
| Schema changes | None |
| Completion status | Completed and confirmed by the user |
| Documentation status | Complete |

---

## Completed outcome

Days 17–18 replaced the four module placeholders with real, authenticated,
responsive workflows. Knowledge, Learn, Money and Work now operate through the
backend routes completed during Days 7–14. No duplicate backend API was added,
and no database migration was required.

The most important usability rule is that people choose documents, goals,
topics, batches, projects and tasks by readable names. PostgreSQL IDs are loaded
from authenticated list endpoints and kept internally in React state. No screen
asks the user to guess an ID.

The complete Windows, PostgreSQL and browser test gate passed before this log
was finalized.

## Architecture

```text
React page
  -> typed module API client
  -> bearer-authenticated FastAPI route
  -> current user dependency
  -> owner-filtered SQLAlchemy query
  -> PostgreSQL / shared file storage
  -> typed response rendered as a human-readable choice
```

The existing hash router and PWA shell were preserved. Four dedicated pages
were mounted by `App.tsx`, while reusable module types, API helpers and status
components prevent each page from reimplementing networking behavior.

## Files added

- `frontend/src/api/modules.ts`
- `frontend/src/components/ModuleUi.tsx`
- `frontend/src/module-types.ts`
- `frontend/src/pages/KnowledgePage.tsx`
- `frontend/src/pages/LearnPage.tsx`
- `frontend/src/pages/MoneyPage.tsx`
- `frontend/src/pages/WorkPage.tsx`

## Files updated

- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/styles.css`

No backend file, model, dependency manifest or applied migration was changed.

## Shared frontend infrastructure

`api/client.ts` now exports the common authenticated `request()` function and
adds an authenticated blob-download helper. The download helper reads the
server's `Content-Disposition` filename, creates a temporary object URL, starts
the download and revokes the URL afterward.

`api/modules.ts` maps UI operations to the exact backend contracts. It contains
shared file upload, import creation, import listing, retry and bounded polling.
Polling stops when a job reaches `awaiting_review`, `completed` or `failed`, and
times out with an honest status message instead of pretending the import was
successful.

`module-types.ts` represents backend response shapes for shared files/imports
and all four modules. `ModuleUi.tsx` provides consistent notices, loading,
empty-state, status, date, currency and duration presentation.

# Day 17 — Nexus Knowledge

## Workflow

```text
select file -> POST /files/upload -> POST /imports
-> poll GET /imports/{id} -> awaiting_review
-> POST /knowledge/documents/from-import/{id}
-> document library/detail/text/summaries
```

The screen provides:

- title search and readable document selection;
- optional title, description and comma-separated tags;
- visible import progress, warnings, failure reason and retry;
- conversion of an existing awaiting-review import;
- extracted-text preview and character count;
- short, detailed, revision-notes and key-insights summaries;
- summary history and authenticated PDF download;
- explicit confirmation before deleting a Knowledge document.

Deleting a Knowledge document does not blindly remove the shared stored file.
The backend returns its import to `awaiting_review`, preserving the staged
workflow.

# Day 17 — Nexus Learn

## Data discovery

- Goals come from `GET /learn/goals`.
- Topics come from `GET /learn/topics` and are filtered by selected goal.
- Knowledge choices come from `GET /learn/quiz-ready-documents`.
- Progress, gaps, readiness, questions and score are loaded for the selected
  named topic.

## Workflow coverage

- create, select, prioritize, pause, complete and delete a goal;
- add topics with current/target levels;
- connect or change an owned Knowledge source;
- record percentage, study minutes and notes;
- show progress history and ranked skill gaps;
- show the exact readiness reason before quiz generation;
- generate one to ten deterministic local questions;
- display four options without returning the correct index beforehand;
- reveal correctness and source explanation only after submission;
- refresh the cumulative score after every answer.

The readiness UI preserves the backend rule: a topic needs a linked owned
Knowledge document with a readable sentence and at least four meaningful
keywords. The frontend does not weaken validation to force quiz creation.

# Day 18 — Nexus Money

## Privacy and staging

The page states that NEXUS does not request bank, UPI, SMS, payment-app or
brokerage access. Data arrives through manual entry, pasted text or a file the
user explicitly chooses.

```text
manual entry -> permanent transaction

paste/upload -> parsed drafts -> edit/delete -> duplicate review
-> explicit approve or cancel -> permanent transactions
```

The review screen exposes parser warnings, source location and confidence.
Possible duplicates remain visible and disable approval until explicitly
confirmed. The user can choose to delete raw pasted text during approval.

Analytics now render income, expenses, net, transaction count, spending by
category, monthly trend and largest expenses. Filters use type, category and
date range. CSV export uses an authenticated download rather than exposing a
token in a URL.

# Day 18 — Nexus Work

The Work page includes:

- named project selection and creation;
- project status updates;
- task creation with status, priority, complexity, due date and low/high range;
- human-readable dependency selection;
- task filtering, status/completion updates and actual-minute recording;
- task deletion confirmation;
- Work dashboard totals and selected-project remaining estimate;
- assignment file upload and shared import processing;
- optional existing-project selection;
- editable generated task drafts;
- confidence, assumptions, warnings and aggregate estimate range;
- explicit plan approval or cancellation;
- automatic project creation only when selected by the approval flow.

Generated tasks never become permanent before review. Estimate ranges remain
low/high values rather than presenting false single-number precision.

## Security decisions

- The bearer token is attached by the common API client.
- The browser never submits a `user_id` for owned operations.
- Every selected key originated in a current-user list response.
- Cross-user 404 behavior remains a backend responsibility and passed testing.
- File and PDF downloads remain authenticated.
- Money and Work imports retain draft-review-approval boundaries.
- Destructive actions require confirmation.

## Validation and error states

The module pages provide visible loading, empty, success, warning and error
states. Expected HTTP errors remain meaningful:

- `409` for duplicate upload, reused import or unconfirmed Money duplicates;
- `404` for absent/not-owned records;
- `422` for unsupported files, inadequate quiz content and invalid ranges;
- `409` when an import has not reached review state.

The UI does not silently turn failed or partial imports into permanent domain
records.

## Commands practiced

From `frontend`:

```powershell
npm install
npm run typecheck
npm run build
npm run dev
```

From `backend`:

```powershell
uv run alembic current
uv run alembic check
uv run uvicorn app.main:app --reload
```

`npm run typecheck` checks TypeScript without producing a deployment build.
`npm run build` performs TypeScript project compilation and the optimized Vite
build. Alembic stayed unchanged because this block used existing data contracts.

## Assistant-side validation

- Python compilation passed.
- SQLAlchemy mapper configuration passed.
- FastAPI OpenAPI generation passed.
- API version remained `0.11.0`.
- All 66 backend paths remained present.
- 49 frontend module route patterns matched real OpenAPI paths.
- Alembic had one `20260911_11` head.
- TypeScript checking passed.
- Vite production build passed.
- ZIP integrity and forbidden-path checks passed.

## User-confirmed test outcome

- Knowledge workflow: passed
- Learn workflow: passed
- Money workflow: passed
- Work workflow: passed
- Windows/PostgreSQL persistence: passed
- Browser and responsive behavior: passed

## Skills practiced

- typed API integration;
- React state and effects;
- authenticated uploads/downloads;
- asynchronous polling;
- staged review workflows;
- accessible form controls;
- responsive working-surface design;
- ownership-safe entity selection;
- analytics presentation;
- validation and error diagnosis.

## Completed checkpoint

```text
Days completed: 1–18
API version: 0.11.0
Alembic head: 20260911_11
Knowledge/Learn/Money/Work frontend placeholders: removed
Next block: Days 19–20 — unified UX, notifications and automated tests
```
