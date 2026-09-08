# NEXUS AI — Days 7–8: Shared User Profile and File Foundation

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 7–8 |
| Main area | Shared Nexus Core platform |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT bearer token |
| Day 7 | Shared user profile and preferences |
| Day 8 | Shared file metadata, validation and local storage |
| Completion status | Completed and tested |
| Final migration revision | `20260905_04 (head)` |
| Completion confirmed | September 6, 2026 |

---

## 1. Purpose of this two-day block

Days 1–6 established the NEXUS AI backend foundation:

- FastAPI application
- PostgreSQL persistence
- SQLAlchemy ORM
- modular API routing
- Alembic schema migrations
- registration and Argon2 password hashing
- JWT login
- current-user identification
- protected owner-only routes

Days 7–8 added the next shared platform layers required by every product
module:

1. Day 7 created one expandable profile for every authenticated user.
2. Day 8 created one controlled file-upload system for Knowledge, Money and
   Work.

The resulting foundation is:

```text
Authenticated user
        ↓
Shared profile and preferences
        ↓
Shared user-owned files
        ↓
Future extraction/import pipeline
        ↓
Knowledge + Learn + Money + Work + Intelligence
```

The design remains a modular monolith. The profile, file, authentication and
database infrastructure run in one FastAPI application but are separated by
models, schemas, routers and services.

---

# Day 7 — Shared User Profile and Preferences

## 2. Problem solved on Day 7

Authentication answered:

```text
Who is making the request?
```

It did not yet answer:

```text
Which timezone should deadlines use?
Which currency should Money display?
What are the user's learning goals?
How should Work planning be personalized?
What AI, privacy and notification settings has the user selected?
```

Putting every future preference directly in the authentication-focused users
table would mix responsibilities and make that table grow continuously.

Day 7 therefore introduced a separate `user_profiles` table with a one-to-one
relationship to `users`.

## 3. One-to-one relationship

```text
users
  1
  │
  │ one-to-one
  │
  1
user_profiles
```

Each user has one profile, and each profile belongs to one user.

The database enforces this through:

- a foreign key from `user_profiles.user_id` to `users.id`
- a unique constraint on `user_profiles.user_id`

The foreign key prevents a profile from referencing a nonexistent user. The
unique constraint prevents one user from receiving multiple shared profiles.

## 4. Why identity and preferences are separated

The `users` table stores identity and security information:

| Field | Responsibility |
| --- | --- |
| `id` | Stable user identity |
| `name` | User name |
| `email` | Unique login identifier |
| `age` | Basic user information |
| `hashed_password` | One-way password hash |
| `is_active` | Account-access state |

The `user_profiles` table stores expandable product settings:

| Field | Responsibility |
| --- | --- |
| `id` | Profile primary key |
| `user_id` | Authenticated owner |
| `timezone` | Local date/time behavior |
| `preferred_currency` | Money formatting and analytics |
| `learning_goals` | Nexus Learn personalization |
| `work_preferences` | Nexus Work planning preferences |
| `ai_preferences` | AI-provider and response preferences |
| `privacy_preferences` | Data-retention and consent preferences |
| `notification_preferences` | In-app notification behavior |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

This prevents password/authentication concerns from becoming coupled to every
future module preference.

## 5. Day 7 dependency

Run from:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
```

Command:

```powershell
uv add tzdata
```

### Purpose

Python's `zoneinfo` module validates IANA timezone identifiers such as:

```text
UTC
Asia/Kolkata
Europe/London
America/New_York
```

Windows does not always include the IANA timezone database. The `tzdata`
package supplies it consistently across Windows and deployment environments.

### Files affected

```text
backend/pyproject.toml
backend/uv.lock
backend/.venv/
```

No paid service is used.

## 6. Day 7 migration

File:

```text
backend/alembic/versions/20260904_03_add_user_profiles.py
```

Revision chain:

```python
revision = "20260904_03"
down_revision = "20260902_02"
```

Migration flow:

```text
Create user_profiles table
        ↓
Add foreign key and unique constraint
        ↓
Add defaults and timestamps
        ↓
Insert one profile for every existing user
```

## 7. Profile defaults

Existing and new profiles initially use:

```text
timezone = UTC
preferred_currency = INR
learning_goals = NULL
work_preferences = NULL
ai_preferences = {}
privacy_preferences = {}
notification_preferences = {}
```

`UTC` is a universal safe starting timezone. `INR` is the useful initial
currency for this personal MVP and can be changed through the profile API.

## 8. Existing-user backfill

Day 7 already had registered users, but no profile table existed when those
accounts were created.

The migration used a data backfill:

```sql
INSERT INTO user_profiles (user_id)
SELECT id
FROM users;
```

This created a default profile for every existing user. Backfilling avoids
requiring users to register again after a schema change.

## 9. Automatic profile creation

The registration flow was updated to create both records together:

```text
POST /auth/register
        ↓
Create User
        ↓
Create UserProfile
        ↓
One database transaction
```

If the transaction succeeds, both records exist. If it fails, neither should
remain partially saved.

## 10. JSONB preferences

The following fields use PostgreSQL JSONB:

```text
ai_preferences
privacy_preferences
notification_preferences
```

Example:

```json
{
  "response_style": "detailed",
  "external_ai_enabled": false
}
```

JSONB was selected for preference groups because their internal options can
grow over time. Stable, commonly used values such as timezone and currency
remain normal relational columns.

```text
Stable/filterable setting → relational column
Expandable preference map → JSONB
```

JSONB does not replace relational design throughout the system. It is used only
where flexibility solves a real problem.

## 11. Cascade deletion

The profile foreign key uses:

```text
ON DELETE CASCADE
```

If an account is intentionally deleted, PostgreSQL removes the dependent
profile. This prevents orphan records.

## 12. Profile schemas and validation

Day 7 added profile request/response schemas.

Validation includes:

- valid IANA timezone
- three-letter currency code
- normalization from `inr` to `INR`
- length limits for learning goals and work preferences
- structured dictionaries for AI/privacy/notification preferences
- empty PATCH request rejection
- prevention of null timezone or currency

Pydantic validates the API data. PostgreSQL and SQLAlchemy store it.

## 13. Profile router

File:

```text
backend/app/routers/profile.py
```

Endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/profile/me` | Read current user's shared profile |
| PATCH | `/profile/me` | Partially update current user's profile |

Both use the authenticated user derived from the JWT.

The URL does not accept an arbitrary user ID:

```text
Bearer token
    ↓
get_current_active_user
    ↓
current_user.id
    ↓
user_profiles.user_id filter
```

This reduces the chance of an insecure direct-object-reference bug.

## 14. Profile update example

```json
{
  "timezone": "Asia/Kolkata",
  "preferred_currency": "INR",
  "learning_goals": "Complete the NEXUS AI portfolio MVP by 22 September 2026",
  "work_preferences": "Show priorities and realistic time estimates",
  "ai_preferences": {
    "response_style": "detailed",
    "external_ai_enabled": false
  },
  "privacy_preferences": {
    "delete_sensitive_imports_after_approval": true
  },
  "notification_preferences": {
    "in_app_enabled": true,
    "daily_summary": true
  }
}
```

## 15. Day 7 commands

Run from the backend directory:

```powershell
uv add tzdata
uv run alembic current
uv run alembic history
uv run alembic upgrade head
uv run alembic current
uv run alembic check
uv run uvicorn app.main:app --reload
```

Expected revision after the upgrade:

```text
20260904_03 (head)
```

Expected check result:

```text
No new upgrade operations detected.
```

## 16. Day 7 tests completed

The Day 7 completion flow covered:

1. Migration chain contained the new profile revision.
2. Upgrade created and backfilled `user_profiles`.
3. Current revision became `20260904_03 (head)`.
4. Alembic detected no pending schema changes.
5. Profile router appeared in Swagger.
6. Existing authenticated account had a default profile.
7. Profile PATCH updated the selected values.
8. Updated settings survived an application restart.
9. Invalid timezone returned 422.
10. Invalid currency returned 422.
11. Empty update returned 400.
12. Unauthenticated profile access returned 401.
13. New registration automatically created a profile.

---

# Day 8 — Shared File Upload, Metadata and Local Storage

## 17. Problem solved on Day 8

Knowledge, Money and Work all need uploaded files.

Building separate storage code for each module would cause duplicated security,
validation, metadata, ownership and deletion logic.

Day 8 created one shared flow:

```text
Knowledge ─┐
Money ─────┼── Shared file service
Work ──────┘
```

Day 8 stores and controls files. Extraction, OCR, parsing, summarization and
module-specific record creation happen later.

## 18. Supported Day 8 formats

| Extension | Intended use |
| --- | --- |
| `.pdf` | Documents, statements and work instructions |
| `.xlsx` | Structured sheets and imports |
| `.csv` | Transactions and tabular data |
| `.docx` | Knowledge and Work documents |
| `.txt` | Plain text |
| `.md` | Markdown notes |
| `.png` | Future OCR input |
| `.jpg` / `.jpeg` | Future OCR input |

PPTX was intentionally postponed until after the September 22 MVP. Old binary
Office formats `.doc` and `.xls` are not part of the initial pipeline.

## 19. File-size configuration

The default maximum upload size is:

```text
10 MB
```

Configuration defaults:

```dotenv
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIRECTORY=storage/uploads
```

No `.env` change was required because the service supplies these defaults. They
can be overridden later without changing router code.

## 20. Why `UploadFile` and multipart data are used

Browser file uploads use multipart form data. FastAPI's `UploadFile` gives the
backend a file-like interface and supports asynchronous reading.

Day 6 had already installed:

```text
python-multipart
```

Therefore Day 8 required no new dependency.

## 21. Streaming upload flow

The service reads in 1 MB chunks:

```text
Read chunk
    ↓
Increase total byte count
    ↓
Reject if over 10 MB
    ↓
Update SHA-256
    ↓
Write chunk to generated path
    ↓
Repeat until complete
```

This avoids requesting one large Python bytes object for the entire accepted
file and lets the size limit be enforced during writing.

## 22. File-validation layers

Day 8 applies:

1. authenticated-user requirement
2. filename presence
3. filename length limit
4. removal of client path components
5. extension allowlist
6. MIME-type allowlist
7. maximum-size enforcement
8. empty-file rejection
9. basic signature/structure validation
10. SHA-256 duplicate detection
11. generated server filename
12. user-specific storage directory
13. PostgreSQL ownership constraints

No single check is considered sufficient by itself.

## 23. Extension, MIME and content validation

A filename extension is user-controlled and can be misleading.

Example:

```text
plain text renamed to report.pdf
```

Day 8 checks both declared metadata and basic content:

- PDF begins with the PDF signature
- PNG begins with the PNG signature
- JPEG begins with a JPEG signature
- DOCX contains `word/document.xml`
- XLSX contains `xl/workbook.xml`
- TXT/CSV/Markdown are valid UTF-8 text without binary null bytes

The checks are a controlled MVP validation layer, not malware scanning. A later
production system can add antivirus scanning and stricter document sanitizing.

## 24. Safe generated filenames

The server does not use the original user filename as a disk path.

```text
Original: My Course Notes.pdf
Stored:   6b77...generated-uuid....pdf
```

Approximate layout:

```text
backend/storage/uploads/<user-id>/<generated-uuid>.<extension>
```

The original name remains in PostgreSQL for display and download. Generated
names prevent a client filename from selecting arbitrary server paths and avoid
collisions between users.

## 25. Storage Git protection

Day 8 added:

```text
backend/storage/.gitignore
```

It ignores runtime content while retaining the ignore rule itself.

Private uploads must never be committed to Git or GitHub.

## 26. File metadata model

Day 8 added the SQLAlchemy `StoredFile` model mapped to:

```text
files
```

| Column | Purpose |
| --- | --- |
| `id` | File metadata primary key |
| `user_id` | Authenticated owner |
| `original_filename` | User-visible filename |
| `stored_filename` | Generated physical filename |
| `storage_path` | Backend-controlled path |
| `content_type` | Normalized MIME type |
| `extension` | Validated extension |
| `size_bytes` | Exact size |
| `sha256_hash` | Exact-content fingerprint |
| `processing_status` | Import/extraction lifecycle stage |
| `failure_reason` | Processing failure explanation |
| `created_at` | Creation time |
| `updated_at` | Last update time |

The public response deliberately omits:

```text
stored_filename
storage_path
```

## 27. Processing statuses

The database check constraint accepts:

```text
uploaded
extracting
parsing
awaiting_review
completed
failed
```

Day 8 creates a file as `uploaded`. Later import work moves it through:

```text
uploaded
    ↓
extracting
    ↓
parsing
    ↓
awaiting_review
    ↓
completed
```

Failures store `failed` with `failure_reason`.

## 28. SHA-256 duplicate detection

SHA-256 creates a deterministic fingerprint from file bytes.

```text
same bytes → same hash
different bytes → practically different hash
```

The database unique constraint is:

```text
user_id + sha256_hash
```

Therefore:

- one user cannot upload the same content twice
- renaming identical content does not bypass detection
- another user can independently own the same public document

A duplicate returns `409 Conflict`. The temporary duplicate physical copy is
removed while the original record remains.

SHA-256 is appropriate for exact file fingerprints. Passwords continue to use
Argon2 because password hashing has different security requirements.

## 29. Day 8 migration

File:

```text
backend/alembic/versions/20260905_04_add_shared_files.py
```

Revision chain:

```python
revision = "20260905_04"
down_revision = "20260904_03"
```

The migration creates the `files` table, foreign key, status check, unique
constraints and indexes.

## 30. File ownership and isolation

Every file route filters by both:

```text
file ID
authenticated current user ID
```

```text
SELECT file
WHERE files.id = requested_id
AND files.user_id = current_user.id
```

Another user's record returns `404 Not Found`. Returning 404 avoids confirming
that a private file exists.

## 31. File routes

File:

```text
backend/app/routers/files.py
```

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/files/upload` | Validate and store a file |
| GET | `/files` | List current user's file metadata |
| GET | `/files/{file_id}` | Read owned metadata |
| GET | `/files/{file_id}/download` | Download owned content |
| DELETE | `/files/{file_id}` | Delete owned content and metadata |

All routes require an active authenticated account.

## 32. Listing and filtering

`GET /files` supports:

```text
skip
limit
processing_status
```

The default page size is 20 and the maximum is 100.

Example:

```text
/files?skip=0&limit=20&processing_status=uploaded
```

The query always includes the authenticated user's ID.

## 33. Download flow

```text
Request file ID
       ↓
Load metadata filtered by current user
       ↓
Resolve backend-controlled path
       ↓
Confirm physical content exists
       ↓
Stream with original filename
```

The client receives the content but not the internal storage path.

## 34. Deletion flow

```text
Authenticated owner request
        ↓
Locate owned metadata
        ↓
Remove physical file
        ↓
Delete PostgreSQL row
        ↓
204 No Content
```

The later Money pipeline will reuse this deletion capability to remove raw
sensitive imports after approved normalized transactions are saved.

## 35. Day 8 commands

Run from the backend directory:

```powershell
uv run alembic current
uv run alembic history
uv run alembic upgrade head
uv run alembic current
uv run alembic check
uv run uvicorn app.main:app --reload
```

Expected final revision:

```text
20260905_04 (head)
```

Expected schema check:

```text
No new upgrade operations detected.
```

## 36. Day 8 tests completed

The Day 8 completion flow covered:

1. Four-revision migration history.
2. Upgrade to `20260905_04 (head)`.
3. No pending Alembic operations.
4. Files router appeared in Swagger.
5. Valid TXT upload returned 201.
6. Physical storage used a generated UUID filename.
7. Runtime uploads remained ignored by Git.
8. Owner file listing worked.
9. Metadata retrieval worked.
10. Download returned the original content and filename.
11. Identical duplicate returned 409.
12. Valid CSV upload returned 201.
13. Fake PDF content returned 422 and was cleaned up.
14. Unsupported extension returned 422.
15. Unauthenticated requests returned 401.
16. A second user could not access the first user's file.
17. Delete returned 204 and removed metadata and physical content.

## 37. Local versus deployed storage

Local disk is appropriate for development because it is free and directly
inspectable.

Some free web hosts provide ephemeral filesystems, so content can disappear
after restart or redeployment. Day 8 isolated disk behavior inside:

```text
app/services/file_storage.py
```

That service boundary allows a later free-tier object-storage adapter without
rewriting Knowledge, Money and Work routers.

PostgreSQL stores metadata, not large file bytes.

## 38. Money privacy preparation

The locked future Money flow remains:

```text
Upload sensitive source
        ↓
Extract proposed transactions
        ↓
Validate and show review
        ↓
User approves
        ↓
Store normalized transactions
        ↓
Delete raw source by default
```

Day 8 provides direct deletion and privacy preferences already exist from Day
7. Automatic deletion is applied when the Money approval workflow is built.

---

# Combined Days 7–8 State

## 39. Final migration chain

```text
<base>
  ↓
20260827_01 — initial users table
  ↓
20260902_02 — authentication fields
  ↓
20260904_03 — shared user profiles
  ↓
20260905_04 — shared file metadata
```

## 40. Final API groups

```text
NEXUS AI API
├── Platform
│   ├── GET /
│   └── GET /health
├── Authentication
│   ├── POST /auth/register
│   ├── POST /auth/login
│   └── GET /auth/me
├── Users
│   ├── GET /users/{user_id}
│   ├── PATCH /users/{user_id}
│   └── DELETE /users/{user_id}
├── Profile
│   ├── GET /profile/me
│   └── PATCH /profile/me
└── Files
    ├── POST /files/upload
    ├── GET /files
    ├── GET /files/{file_id}
    ├── GET /files/{file_id}/download
    └── DELETE /files/{file_id}
```

## 41. Final project structure

```text
NEXUS_AI/
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── storage/
│   │   ├── .gitignore
│   │   └── uploads/                 # runtime, ignored
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 20260827_01_initial_users_table.py
│   │       ├── 20260902_02_add_user_authentication.py
│   │       ├── 20260904_03_add_user_profiles.py
│   │       └── 20260905_04_add_shared_files.py
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── file_schemas.py
│       ├── security.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── file_storage.py
│       └── routers/
│           ├── __init__.py
│           ├── auth.py
│           ├── users.py
│           ├── profile.py
│           └── files.py
├── frontend/
├── docs/
│   └── learning-log/
│       ├── day-01-02-project-setup-fastapi.md
│       ├── day-03-04-postgresql-sqlalchemy-user-crud-routing.md
│       ├── day-05-06-alembic-authentication-jwt.md
│       └── day-07-08-user-profile-shared-file-foundation.md
└── .gitignore
```

## 42. Concepts learned

### Day 7

- one-to-one relationship
- foreign key
- unique constraint
- data backfill
- cascade deletion
- JSONB
- flexible versus relational fields
- IANA timezone
- timezone validation
- currency normalization
- shared user preferences
- owner-derived `/me` endpoints

### Day 8

- multipart file upload
- `UploadFile`
- upload streaming
- chunk processing
- file-size limits
- extension allowlist
- MIME validation
- file signatures
- safe filenames
- UUID storage names
- SHA-256 hashing
- exact duplicate detection
- metadata/content separation
- user-specific storage
- protected downloads
- processing-state constraints
- local versus object storage

## 43. Security and privacy decisions

- Every profile and file query derives the user ID from the JWT.
- Client-supplied filenames cannot control storage paths.
- Storage paths are not exposed in public response schemas.
- Runtime uploads are excluded from Git.
- File size is limited before unlimited content is accepted.
- Extension, MIME and basic content checks are combined.
- Duplicate checks operate within one user's ownership boundary.
- Sensitive Money sources will be deleted after approved import by default.
- `.env`, JWT secrets, passwords, tokens and uploaded personal content remain
  outside Git.

## 44. Known MVP limitations

- Local storage is not durable on every free deployment platform.
- Basic signature validation is not antivirus scanning.
- Account cascade deletion currently removes file metadata; full physical-file
  cleanup is strengthened before public production use.
- Background extraction and OCR begin in Days 9–10.
- No embeddings or RAG exist yet.
- No frontend upload screen exists yet.

These limitations are recorded rather than hidden and are addressed in later
development blocks.

## 45. Git checkpoint

Run from:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI>
```

Check changes:

```powershell
git status
```

Confirm the real environment file is ignored:

```powershell
git check-ignore backend/.env
```

Confirm a runtime upload is ignored by testing its actual generated path if
desired:

```powershell
git check-ignore backend/storage/uploads/<user-id>/<generated-file>
```

Stage:

```powershell
git add .
```

Review:

```powershell
git status
```

Ensure no `.env`, token, password, private document or uploaded runtime content
is staged.

Commit:

```powershell
git commit -m "feat: add shared user profiles and file foundation"
```

Push when ready:

```powershell
git push
```

## 46. Completion state

Days 7 and 8 are complete.

NEXUS AI now has authenticated identities, expandable user preferences and a
shared controlled file layer. The next two-day block is delivered together:

```text
Day 9  — common extraction and asynchronous import jobs
Day 10 — Nexus Knowledge documents, summaries and PDF export
```

Their formal learning log will be created only after both days are implemented
and tested.
