# NEXUS AI — Days 13–14: Money File Imports, Analytics and Work Planning

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 13–14 |
| Day 13 | Money files, duplicate review, analytics and export |
| Day 14 | Work projects, document-to-plan parsing and effort estimates |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT bearer token |
| Starting migration | `20260908_08` |
| Ending migration | `20260910_10 (head)` |
| Completion status | Completed and confirmed by the user |
| Documentation status | Complete |

---

## Completed outcome

This block converted the privacy-first Money design into multi-format imports
and created the first usable Nexus Work planning workflow. No bank, payment app,
SMS inbox or financial-account permission is requested. A user uploads a local
file or pastes text, reviews generated drafts, and explicitly approves the
records that become permanent.

The Work side follows the same safe pattern. A PDF or other supported document
is treated as untrusted input, converted to editable task drafts and approved
only after the user checks estimates, assumptions and warnings.

The implementation and validation record below is deliberately detailed so it
can be used later for revision, troubleshooting, portfolio explanation and
deployment preparation.

---

## Status before this block

- Days 1-10 completed
- Day 11 Learn completed after recovery
- Day 12 Money manual/pasted-text workflow completed
- Current starting migration: `20260908_08`
- Expected ending migration: `20260910_10`

The expected ending migration was reached. The API version for the completed
block is `0.10.0`.

## What this package adds

### Day 13 - Nexus Money

- CSV, XLSX and text-based/table PDF transaction imports
- reuse of shared `/files` and `/imports` processing
- reviewable Money drafts instead of automatic permanent inserts
- same-user duplicate matching by date, amount, type and similar description
- explicit confirmation before possible duplicates can be approved
- source row/table information
- income, expense and net totals
- category breakdown
- monthly trend
- five largest expenses
- downloadable transaction CSV

### Day 14 - Nexus Work

- projects and optional client name
- manual tasks and subtasks
- priority, complexity, status, due date and dependencies
- low/high effort range and actual minutes
- PDF/DOCX/XLSX/CSV/TXT work-document extraction through shared imports
- rule-based task proposals
- review/edit/delete/approve flow
- project estimate and Work dashboard
- authenticated ownership on every query

## 1. Copy the package

Stop the backend. Extract the ZIP outside the repository, then copy the
package's `backend` folder into:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI\
```

Choose **Replace the files in the destination**.

The four replacements are deliberate. Do not copy only the new files because
`models.py`, `money.py`, `money_schemas.py` and `main.py` contain required
connections to the new database columns/routes.

## 2. Install the one explicit dependency

From:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend
```

run:

```powershell
uv add pdfplumber
```

`pdfplumber` detects table cells/rows inside text-based transaction PDFs. The
existing extraction service still provides OCR fallback when native PDF text is
not usable.

## 3. Apply migrations

```powershell
uv run alembic current
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Expected final output:

```text
20260910_10 (head)
No new upgrade operations detected.
```

Migration `20260909_09` adds Money file links, source locations, duplicate
review metadata and transaction fingerprints. Migration `20260910_10` adds
Work projects, tasks, import plans and task drafts.

## 4. Start the API

```powershell
uv run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Expected version: `0.10.0`.

Authorize with the same user used in Days 11-12 and confirm with:

```text
GET /auth/me
```

# Day 13 - Money files, duplicates and analytics

## 5. Understand duplicate policy

Identical values are not prohibited by a database uniqueness constraint.
Someone can genuinely pay the same shop the same amount twice on one date.

Instead, an import draft becomes a possible duplicate when the same user has an
approved transaction with:

- same transaction date
- same amount
- same income/expense type
- same or at least 80% similar normalized description

The warning does not delete data. Approval returns `409` until the user either
deletes/corrects the suspected drafts or sets
`confirm_possible_duplicates=true`.

## 6. Test a unique CSV import

Upload:

```text
test-files/day13-money-new-import-sample.csv
```

through:

```text
POST /files/upload
```

Copy the returned real file ID. Create the shared extraction job:

```text
POST /imports
```

```json
{
  "file_id": YOUR_FILE_ID,
  "target_module": "money"
}
```

Copy the import-job ID. Poll:

```text
GET /imports/{import_job_id}
```

until status is `awaiting_review`. Then create Money drafts:

```text
POST /money/imports/from-job/{import_job_id}
```

```json
{
  "default_currency": "INR"
}
```

Expected: three drafts (Bookstore, Pharmacy, Freelance), `source_type=file`,
source locations containing CSV row numbers, and normally no duplicate flags.

Approve:

```text
POST /money/imports/{money_batch_id}/approve
```

```json
{
  "delete_raw_text": true,
  "confirm_possible_duplicates": false
}
```

Expected: three permanent transactions and status `approved`.

## 7. Test XLSX parsing

Repeat upload -> shared import -> poll -> Money conversion using:

```text
test-files/day13-money-import-sample.xlsx
```

Expected: five drafts and source locations such as `Sheet Transactions, row 2`.
If the matching Day 12 entries already exist, some/all drafts should have:

```text
possible_duplicate = true
duplicate_transaction_id = an existing transaction ID
```

Try approval with confirmation false. Expected `409`. For a safe test, cancel:

```text
POST /money/imports/{batch_id}/cancel
```

## 8. Test PDF table parsing

Repeat the same three-stage flow with:

```text
test-files/day13-money-statement-sample.pdf
```

Expected extraction method includes `pdfplumber_tables_v1`, five drafts and
source locations containing PDF page/table details. Cancel after checking when
they are duplicates.

For scanned statements, the shared document extractor can use Tesseract, but
OCR results must always be reviewed because dates/amounts can be misread.

## 9. Test pasted-text duplicate protection directly

Paste a transaction that already exists:

```text
POST /money/imports/pasted-text
```

```json
{
  "text": "Paid INR 250 for Team lunch on 6 September 2026",
  "default_currency": "INR"
}
```

Expected draft:

```text
possible_duplicate = true
duplicate_transaction_id = existing matching ID
```

Attempt normal approval:

```json
{
  "delete_raw_text": true,
  "confirm_possible_duplicates": false
}
```

Expected: `409 Conflict`.

Normal action: delete/correct the draft or cancel the batch. Only when it is a
genuine second payment should approval use:

```json
{
  "delete_raw_text": true,
  "confirm_possible_duplicates": true
}
```

## 10. Test analytics

```text
GET /money/analytics/summary?currency=INR
```

Optional date filter:

```text
GET /money/analytics/summary?date_from=2026-09-01&date_to=2026-09-30&currency=INR
```

Verify income total, expense total, net, transaction count, category breakdown,
monthly trend and largest expenses.

## 11. Download Money CSV

```text
GET /money/transactions/export.csv
```

Optional:

```text
GET /money/transactions/export.csv?date_from=2026-09-01&date_to=2026-09-30
```

Swagger should download `nexus-money-transactions.csv`.

# Day 14 - Work projects, tasks and document planning

## 12. Create a manual project

```text
POST /work/projects
```

```json
{
  "title": "NEXUS AI MVP",
  "description": "Complete and deploy the usable NEXUS AI MVP",
  "client_name": null,
  "status": "in_progress",
  "due_date": "2026-09-22"
}
```

Copy the returned project ID.

## 13. Create a manual task

```text
POST /work/projects/{project_id}/tasks
```

```json
{
  "title": "Test Day 13 Money imports",
  "description": "Verify CSV, XLSX, PDF, duplicates, analytics and export",
  "parent_task_id": null,
  "status": "in_progress",
  "priority": 5,
  "complexity": 3,
  "due_date": "2026-09-10",
  "estimated_minutes_low": 90,
  "estimated_minutes_high": 150,
  "dependencies": [],
  "notes": "Use only synthetic test files"
}
```

## 14. Upload a work assignment

Upload either:

```text
test-files/day14-work-assignment-sample.pdf
```

or the text version:

```text
test-files/day14-work-assignment-sample.txt
```

Use `POST /files/upload`, then:

```text
POST /imports
```

```json
{
  "file_id": YOUR_FILE_ID,
  "target_module": "work"
}
```

Poll `GET /imports/{import_job_id}` until `awaiting_review`.

## 15. Generate a reviewable work plan

```text
POST /work/imports/from-job/{import_job_id}
```

To create a new project during approval:

```json
{
  "project_id": null,
  "fallback_project_title": "Customer Support Dashboard"
}
```

To attach tasks to the manual NEXUS project, supply its real project ID instead.

Expected response includes:

- proposed project title
- task drafts
- priority/complexity
- due dates when explicit
- low/high minute estimate per task
- total low/high estimate
- confidence
- assumptions
- warnings/source locations

The estimate is transparent rule-based MVP logic. It does not claim to be a
trained model yet because there is not enough completed-task history.

## 16. Edit a work draft

Retrieve real IDs with:

```text
GET /work/imports
GET /work/imports/{plan_import_id}
```

Then:

```text
PATCH /work/imports/drafts/{draft_id}
```

```json
{
  "title": "Implement protected customer and request APIs",
  "priority": 5,
  "complexity": 4,
  "estimated_minutes_low": 180,
  "estimated_minutes_high": 300
}
```

Expected confidence becomes `1.000` and warnings clear.

## 17. Approve the plan

```text
POST /work/imports/{plan_import_id}/approve
```

```json
{
  "create_project_if_missing": true
}
```

Expected: status approved, a real project ID, task count, and total range. The
drafts become permanent Work tasks only now.

## 18. Track tasks and actual effort

```text
GET /work/projects
GET /work/tasks?project_id={project_id}
```

Complete one real task:

```text
PATCH /work/tasks/{task_id}
```

```json
{
  "status": "completed",
  "actual_minutes": 120,
  "notes": "Completed and tested"
}
```

The completion timestamp is set automatically. The actual minutes are retained
for a later ML estimator after sufficient user history exists.

## 19. Read estimates and dashboard

```text
GET /work/projects/{project_id}/estimate
GET /work/dashboard
```

The project estimate returns pending tasks only. The dashboard returns active
projects, pending/blocked/completed/overdue tasks and remaining low/high time.

## 20. Required security checks

With User A, retain one project ID, task ID, Money batch ID and Work plan ID.
Authorize as User B and confirm these return `404`:

```text
GET /work/projects/{user_a_project_id}
PATCH /work/tasks/{user_a_task_id}
GET /money/imports/{user_a_batch_id}
GET /work/imports/{user_a_plan_id}
```

## 21. Restart persistence and final migration check

Stop/start Uvicorn, reauthorize, and verify transactions/projects/tasks remain.
Then:

```powershell
uv run alembic current
uv run alembic check
```

Expected:

```text
20260910_10 (head)
No new upgrade operations detected.
```

Do not proceed past a migration error or a server traceback. Copy the complete
error, endpoint, body and response for diagnosis.

## 22. Git checkpoint after all tests pass

```powershell
git status
git check-ignore backend/.env
git add .
git status
git commit -m "feat: add money file analytics and work planning"
git push
```

Verify `.env`, tokens, uploaded private files and runtime storage are not staged.

## Completion message

Fill `DAY-13-14-TEST-RESULTS-TEMPLATE.md` or report each test result. Final
Days 13-14 learning-log documentation is produced only after actual Windows and
PostgreSQL testing is confirmed. That confirmation has now been received, so
this file is the final learning-log record for the block.

---

# Completed-State Reference

## What Day 13 proves

Day 13 demonstrates that one ingestion architecture can accept several user
formats without coupling the application to a bank or financial institution.
The extraction layer and financial interpretation layer have separate jobs:

1. shared Files stores the uploaded object and its hash;
2. shared Imports extracts rows or text and records warnings;
3. Money converts extracted material into transaction drafts;
4. duplicate detection compares proposed drafts with the same user's approved
   history;
5. the user edits or deletes uncertain drafts;
6. approval creates permanent transactions inside one database transaction;
7. analytics reads only approved transaction records.

This separation matters. A parsing failure cannot corrupt an approved
transaction. A duplicate warning cannot silently delete a real payment. A
financial chart cannot count a draft that the user has not accepted.

## What Day 14 proves

Day 14 demonstrates a document-assisted workflow rather than an unrestricted
agent. The backend can derive a first project plan from a work document, but
the plan remains proposed data until it is reviewed and approved.

The low/high estimate range is more honest than a single exact number. It
represents uncertainty from incomplete requirements, dependencies and task
complexity. Actual minutes can later be compared with that range, creating the
training data needed for a future personalized estimation model.

## Important database relationships

| Relationship | Meaning |
| --- | --- |
| User → Money import batches | Every batch belongs to exactly one account |
| Money batch → Transaction drafts | A batch contains editable proposed rows |
| Draft → Possible duplicate transaction | Optional warning link to an owned permanent record |
| Approved transaction → Source batch/file | Keeps provenance without bank access |
| User → Work projects | Projects cannot be read across accounts |
| Project → Work tasks | Tasks are grouped under a user-owned project |
| Work plan import → Task drafts | Extracted proposals remain separate from real tasks |
| Task → Parent task | Optional hierarchy for subtasks |

## Duplicate behavior to remember

The database intentionally does not enforce uniqueness on transaction date,
amount and description. Real life permits two equal payments on the same day.
Duplicate detection is therefore a review mechanism, not an automatic deletion
rule.

A matching imported transaction is allowed only after explicit confirmation.
This preserves a legitimate repeated purchase while protecting the user from
accidental double import. The batch ID, draft ID and final transaction ID are
expected to differ because they represent different workflow stages.

## Privacy and security decisions

- Files and records are filtered by the authenticated `user_id`.
- A caller cannot retrieve another user's records merely by guessing an ID.
- Raw pasted financial text can be deleted during approval.
- Structured values remain useful without access to a bank or payment app.
- Imported Work content is never executed as instructions.
- Draft review occurs before permanent file-derived records are created.
- Duplicate confirmation is explicit and auditable.

## Error interpretation guide

| Status | Typical meaning in this block |
| --- | --- |
| `200` | Read, update or action completed |
| `201` | A new resource was created |
| `204` | Delete/cancel succeeded without a response body |
| `401` | Token missing, invalid or expired |
| `404` | Record absent or not owned by the authenticated user |
| `409` | State conflict, especially unconfirmed duplicate drafts |
| `422` | Request data or extracted values failed validation |

## Skills practiced

### Backend engineering

- modular FastAPI routers and Pydantic contracts;
- SQLAlchemy relationships, indexes and constraints;
- Alembic upgrades across dependent modules;
- service-layer parsing and normalization;
- transactional approval workflows;
- ownership-aware queries;
- safe file ingestion and provenance;
- deterministic analytics and downloadable reports.

### Data and ML preparation

The parser and estimate rules are transparent baselines, not falsely labelled
deep-learning models. They create clean labelled data. Later improvements can
compare model predictions with user corrections and actual completion times.
This is a stronger ML path than adding a model before reliable data and
evaluation exist.

### Product engineering

- privacy-first finance design;
- uncertainty shown with confidence, assumptions and ranges;
- user confirmation at irreversible boundaries;
- safe duplicate handling;
- shared platform capabilities reused by multiple modules.

## Final completion record

```text
API version: 0.10.0
Alembic revision: 20260910_10 (head)
Money: file imports, duplicate review, analytics and CSV export completed
Work: projects, tasks, file-to-plan drafts, approval and estimates completed
Next block: Days 15-16 — Nexus Intelligence and responsive PWA frontend
```

Do not edit an already applied migration to add later features. Future schema
changes must use a new Alembic revision.
