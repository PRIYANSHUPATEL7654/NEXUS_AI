# NEXUS AI - Days 19-20: Unified UX, Notifications and Automated Testing

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 19-20 |
| Day 19 | Unified daily-use UX and in-app notifications |
| Day 20 | Automated tests, evaluation fixtures and regression coverage |
| Backend | Python 3.13, FastAPI and SQLAlchemy |
| Frontend | React 19, TypeScript and Vite |
| Starting API checkpoint | `0.11.0` |
| Ending API checkpoint | `0.12.0` |
| Starting Alembic revision | `20260911_11` |
| Ending Alembic revision | `20260912_12 (head)` |
| Completion status | Completed and confirmed by the user |
| Documentation status | Complete |

---

## Completed outcome

Days 19-20 turned the separate module workspaces into a more coherent daily
product and added a repeatable release-safety layer. The Today screen gained
direct actions, authenticated cross-module search received a dedicated results
screen, profile preferences became editable, and owned in-app notification
records now highlight imports requiring review, failed imports and overdue Work
tasks.

The responsive shell was refined for regular phone use. The bottom navigation
now exposes Today, Knowledge, Learn, Money, Work and Intelligence using larger
icons, labels, touch targets and a clear active state. Search and Profile remain
available from the mobile header.

Day 20 added deterministic fixtures and automated checks for backend services,
OpenAPI contracts, frontend API mappings, ownership boundaries, PostgreSQL
flows, UI states, TypeScript and production builds. The complete Windows,
PostgreSQL and browser gate passed before this document was finalized.

## Architecture and data flow

```text
Authenticated React shell
  -> POST /notifications/sync
  -> owner-filtered ImportJob and WorkTask queries
  -> deduplicated Notification records
  -> list/count/read APIs
  -> human-readable notification center
```

```text
Search text
  -> GET /intelligence/search?q=...
  -> authenticated user from JWT
  -> owner-filtered Knowledge/Learn/Money/Work queries
  -> deterministic local ranking
  -> grouped React result cards
```

No user ID is accepted from notification or search request bodies. Ownership is
always derived from the authenticated JWT user.

# Day 19 - Unified usability and notifications

## 1. Today quick actions

The Today dashboard now provides direct links for:

- adding a Knowledge document;
- adding a Money transaction;
- adding a Work task;
- continuing Learn goals and quizzes;
- searching all owned NEXUS records.

These actions route to the existing module workspaces. They do not duplicate
backend APIs or ask the user to enter database IDs.

## 2. Unified search screen

The new Search page calls the existing owner-safe endpoint:

```http
GET /intelligence/search?q=Atlas&limit=30
```

The results are grouped into Knowledge, Learn, Money and Work sections. Each
result shows its title, record type and a useful snippet. The backend returns a
record ID, but React retains it internally and shows human-readable choices.

Search remains deterministic PostgreSQL substring matching. It does not send
private content to an external model and is not presented as semantic/vector
search.

## 3. Profile and preferences

The Profile screen now loads and saves the real existing contracts:

```http
GET /profile/me
PATCH /profile/me
```

Editable settings include:

- IANA timezone;
- three-letter preferred currency;
- learning goals;
- work preferences;
- local-processing preference;
- minimal-retention preference;
- in-app notification settings;
- import update notices;
- overdue Work reminders.

Pydantic continues to validate timezones, currency format and field limits.

## 4. Notification database model

Migration `20260912_12_add_notifications.py` was added after the applied
`20260911_11` revision. No existing migration was modified.

The `notifications` table contains:

| Column | Purpose |
| --- | --- |
| `id` | Internal primary key |
| `user_id` | Owning user foreign key |
| `kind` | Event type such as `import_review` or `task_overdue` |
| `module` | Knowledge, Learn, Money, Work or system |
| `title` | Human-readable notification title |
| `message` | Safe detail shown to the owner |
| `severity` | Info, success, warning or urgent |
| `route` | Internal module route |
| `is_read` | Current read state |
| `dedupe_key` | Same-user event deduplication key |
| `created_at` | Creation timestamp |
| `read_at` | Optional read timestamp |

The database enforces valid modules, valid severity values, a cascading user
foreign key and a unique `(user_id, dedupe_key)` constraint.

## 5. Notification endpoint contracts

| Method | Route | Behavior |
| --- | --- | --- |
| `POST` | `/notifications/sync` | Creates missing owned event records |
| `GET` | `/notifications` | Lists owned notifications |
| `GET` | `/notifications/unread-count` | Returns owned unread count |
| `PATCH` | `/notifications/{notification_id}/read` | Marks one owned record read |
| `POST` | `/notifications/read-all` | Marks all owned records read |
| `DELETE` | `/notifications/{notification_id}` | Deletes one owned record |

Example synchronization response:

```json
{
  "created_count": 1,
  "unread_count": 1
}
```

Synchronization currently recognizes:

- shared import jobs in `awaiting_review`;
- shared import jobs in `failed`;
- Work tasks whose due date has passed and whose status is not completed or
  cancelled.

Running synchronization repeatedly does not create duplicate records for the
same event key.

## 6. Notification interface

The authenticated shell synchronizes notices when it loads or changes route.
The desktop utility header and mobile header expose the unread count and a
notification panel. A user can open a notice, mark all notices read, or follow
the notice to its module.

Notification failure is deliberately non-blocking. A temporary notification
request problem does not prevent Knowledge, Learn, Money or Work from loading.

## 7. Responsive mobile navigation

The mobile bottom dock now includes all six main areas:

1. Today
2. Knowledge
3. Learn
4. Money
5. Work
6. AI

The navigation uses vector interface icons, larger touch areas, readable labels,
a blue selected state, safe-area spacing and keyboard focus styling. The dock
is fixed above the phone edge without covering the final page content. Desktop
continues to use the left sidebar.

## 8. Accessibility and PWA usability

The shell includes a keyboard-visible `Skip to main content` link and an
addressable main-content region. Search forms use search semantics and labels,
the current navigation link uses `aria-current`, notification buttons expose
their unread state, error messages use alerts, and reduced-motion preferences
remain supported.

Profile explains installation through Chrome/Edge or Android home-screen
controls. Production installation still requires HTTPS, while localhost is
accepted during development.

# Day 20 - Automated tests and evaluation

## 9. Backend contract tests

`backend/tests/test_contracts.py` checks:

- SQLAlchemy mapper configuration;
- API version `0.12.0`;
- single Alembic head `20260912_12`;
- the complete Notification model column contract;
- all new Day 19 routes;
- every frontend API method/path against the generated FastAPI OpenAPI schema.

This prevents a frontend path from silently drifting away from its backend
router.

## 10. Deterministic service fixtures

The test fixtures cover:

- dated Money expenses;
- income classification;
- skipped-line warnings;
- Work project titles and action extraction;
- Work due-date parsing and task counts;
- quiz readiness and four-option generation;
- short and revision-note summary formats;
- five Ask Nexus intent families;
- the eight allowed read-only Intelligence tools.

Fixture files are stored under:

```text
backend/tests/fixtures/
```

## 11. PostgreSQL integration and ownership regression

The integration suite runs only when `TEST_DB_NAME` is explicitly set. It
refuses to continue unless the name contains `test` and differs from the normal
`DB_NAME`.

It verifies a representative flow:

```text
create owned project
  -> create overdue owned task
  -> synchronize notification
  -> verify deduplication and unread count
  -> reject another user's read request with 404
  -> mark owned notification read
  -> delete owned notification
  -> reject another user's project lookup with 404
```

A second integration case saves similar Knowledge titles for two users and
confirms that each search sees only its owner's record.

## 12. Frontend automated tests

The frontend test script uses the existing React, ReactDOM and Vite toolchain;
no additional test dependency was added. It bundles the actual TypeScript
modules, mocks `fetch`, and verifies:

- bearer authorization headers;
- JSON content type;
- URL encoding for Intelligence search;
- Profile PATCH behavior;
- FastAPI validation error propagation;
- alert semantics for error notices;
- readable status labels;
- empty-state rendering.

## 13. Commands practiced

Backend compilation and deterministic tests:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI\backend"
uv run python -m compileall app tests alembic\versions
uv run python -m unittest tests.test_contracts tests.test_services -v
```

Full guarded PostgreSQL tests:

```powershell
$env:TEST_DB_NAME = "nexus_ai_test"
uv run python -m unittest discover -s tests -v
Remove-Item Env:TEST_DB_NAME
```

Migration checks:

```powershell
uv run alembic upgrade head
uv run alembic current
uv run alembic heads
```

Frontend tests and production validation:

```powershell
cd "C:\MY DATA\GITHUB DATA\NEXUS_AI\frontend"
npm ci
npm run test
npm run typecheck
npm run build
```

## 14. Security and privacy decisions

- Notification ownership comes from the JWT, never a request body.
- Notification lookup, update and deletion use both record ID and owner ID.
- Search applies the same owner filter independently to every module query.
- Import notifications do not bypass draft-review-approval flows.
- Notification preference changes are owner-scoped Profile updates.
- No push, email, SMS or third-party notification permission was introduced.
- No bank, payment-app or brokerage integration was introduced.
- No external model receives search text or owned record contents.
- Test-database deletion has an explicit name guard.
- The release ZIP contains no `.env`, secret, virtual environment, uploaded
  private file, `node_modules` or production build directory.

## 15. Validation and error behavior

- Search requires at least two characters.
- Notification list limits are bounded from 1 to 100.
- Not-owned notifications return `404` without revealing their owner.
- Invalid profile timezones and currencies return validation errors.
- Empty search results show a meaningful empty state.
- Backend cold-start/network failures remain visible through the shared API
  error behavior.
- Notification availability never hides the primary module interface.

## 16. Troubleshooting lessons

### Missing notification table

If the API reports that `notifications` does not exist, run:

```powershell
uv run alembic upgrade head
uv run alembic current
```

### PostgreSQL integration tests are skipped

Set the temporary dedicated database name before running discovery:

```powershell
$env:TEST_DB_NAME = "nexus_ai_test"
```

### Old toolbar or JavaScript remains visible

Unregister the localhost service worker, clear localhost site data and reload
with `Ctrl+Shift+R`. This is a cache refresh, not a source-code problem.

### Multiple Alembic heads

Do not edit, stamp or delete migrations. Inspect `alembic heads` and `alembic
history`, then diagnose the branch before continuing.

## 17. Files added

- `backend/alembic/versions/20260912_12_add_notifications.py`
- `backend/app/notification_schemas.py`
- `backend/app/routers/notifications.py`
- `backend/app/services/notifications.py`
- `backend/tests/__init__.py`
- `backend/tests/test_contracts.py`
- `backend/tests/test_postgres_integration.py`
- `backend/tests/test_services.py`
- `backend/tests/fixtures/intelligence_intents.json`
- `backend/tests/fixtures/transaction_samples.json`
- `backend/tests/fixtures/work_plan_samples.json`
- `frontend/scripts/test_frontend.mjs`
- `frontend/src/pages/SearchPage.tsx`
- `docs/testing/day-20-evaluation-fixtures-and-known-limits.md`

## 18. Files updated

- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/services/intelligence.py`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/api/modules.ts`
- `frontend/src/components/Shell.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/styles.css`
- `frontend/src/types.ts`

## 19. Confirmed test outcome

| Gate | Result |
| --- | --- |
| Python import/compilation | Passed |
| SQLAlchemy mappings | Passed |
| FastAPI OpenAPI generation | Passed |
| Frontend/API contract mapping | Passed |
| Alembic single-head check | Passed |
| Dedicated PostgreSQL integration | Passed |
| Auth/ownership regression | Passed |
| Parser, quiz, summary and Intelligence fixtures | Passed |
| Frontend automated tests | Passed |
| TypeScript typecheck | Passed |
| Vite production build | Passed |
| Windows browser workflow | Passed |
| Responsive toolbar and PWA shell | Passed |

## 20. Skills practiced

- durable notification modeling;
- deduplication and event synchronization;
- authenticated cross-module search;
- preference-driven behavior;
- responsive navigation design;
- accessible application-shell semantics;
- OpenAPI contract testing;
- deterministic parser/evaluation fixtures;
- PostgreSQL test isolation;
- ownership regression testing;
- frontend API mocking and server rendering;
- release-gate thinking.

## Completed checkpoint

```text
Days completed: 1-20
API version: 0.12.0
OpenAPI paths: 72
Alembic head: 20260912_12
Notification schema/API/UI: complete
Unified search and profile preferences: complete
Automated backend/frontend evaluation: complete
Responsive six-module mobile toolbar: complete
Next block: Days 21-22 - Docker, CI/CD, free-tier deployment and final MVP QA
Deadline: September 22, 2026
```
