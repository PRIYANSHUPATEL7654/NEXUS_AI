# NEXUS AI — Days 5–6: Alembic Migrations and JWT Authentication

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 5–6 |
| Main area | Shared Nexus Core backend foundation |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migration tool | Alembic |
| Password hashing | pwdlib with Argon2 |
| Token library | PyJWT |
| Package manager | uv |
| Day 5 status | Completed and tested |
| Day 6 status | Completed and tested |
| Final database revision | `20260902_02 (head)` |
| Final verification date | September 4, 2026 |

---

## 1. Purpose of this two-day block

Days 1–2 created the initial FastAPI application. Days 3–4 connected it to
PostgreSQL, introduced SQLAlchemy, created persistent users, completed CRUD,
added validation, and separated user endpoints into a router.

At the end of Day 4, two important platform problems remained:

1. Database tables were still being created automatically with
   `Base.metadata.create_all()`, so there was no controlled schema history.
2. Users had no passwords, login mechanism, access tokens, or protected routes.

Days 5–6 solved those problems:

- Day 5 introduced Alembic and placed the existing PostgreSQL schema under
  migration control.
- Day 6 performed the first real schema upgrade and built the authentication
  foundation shared by every future NEXUS AI module.

The resulting platform flow is:

```text
SQLAlchemy model change
        ↓
Reviewed Alembic migration
        ↓
PostgreSQL schema upgrade

Registration
        ↓
Pydantic validation
        ↓
Argon2 password hash
        ↓
PostgreSQL user

Login
        ↓
Password verification
        ↓
Signed JWT access token
        ↓
Current-user dependency
        ↓
Protected owner-only endpoint
```

---

# Day 5 — Alembic Migration Foundation

## 2. Problem solved on Day 5

Before Day 5, the application used:

```python
Base.metadata.create_all(bind=engine)
```

This asks SQLAlchemy to create tables that do not exist when FastAPI starts.
It was useful for the first database lesson, but it was not sufficient for a
long-lived application.

`create_all()` does not provide:

- a chronological database-change history
- revision identifiers
- deliberate upgrade steps
- deliberate downgrade steps
- reliable coordination between development and deployment databases
- reviewable SQL/schema evolution

NEXUS AI will eventually run locally and on a hosted PostgreSQL database.
Both databases must be able to reach the same known schema version. Day 5
therefore introduced Alembic before authentication changed the users table.

## 3. What Alembic is

Alembic is SQLAlchemy's database migration tool.

A migration is a versioned Python file containing instructions that change a
database schema.

Examples include:

- create a table
- add a column
- remove a column
- create an index
- add a foreign key
- rename a column
- change a constraint

Conceptually:

```text
Migration 1: create users table
        ↓
Migration 2: add authentication fields
        ↓
Migration 3: add user profile table
        ↓
Future migrations
```

Each migration has:

```text
revision
down_revision
upgrade()
downgrade()
```

`revision` identifies the migration. `down_revision` points to the previous
migration. `upgrade()` moves the schema forward, while `downgrade()` describes
the reverse operation.

## 4. Alembic installation

Run from:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
```

Command:

```powershell
uv add alembic
```

### Command explanation

| Part | Meaning |
| --- | --- |
| `uv` | Project package and environment manager |
| `add` | Adds a dependency and updates the lock file |
| `alembic` | SQLAlchemy migration framework |

Files/environments affected:

```text
backend/pyproject.toml
backend/uv.lock
backend/.venv/
```

## 5. Alembic project files

Day 5 added:

```text
backend/
├── alembic.ini
└── alembic/
    ├── env.py
    ├── README
    ├── script.py.mako
    └── versions/
```

### `alembic.ini`

Contains Alembic-level configuration such as the migration script directory and
logging configuration.

The private database password was not placed in this file.

### `alembic/env.py`

Connects Alembic to the application's existing SQLAlchemy engine and metadata.

Important concepts:

```python
from app import models
from app.database import Base, engine

target_metadata = Base.metadata
```

Importing the models ensures that SQLAlchemy knows which tables belong to the
metadata. `target_metadata` lets Alembic compare the ORM definitions with the
actual PostgreSQL schema.

### `script.py.mako`

Template Alembic uses when generating new migration files.

### `versions/`

Stores migration history. Migration files must be committed to Git because
they are part of the application source code.

## 6. First Alembic connection check

Command:

```powershell
uv run alembic current
```

The first output showed:

```text
Context impl PostgresqlImpl.
Will assume transactional DDL.
```

Alembic also queried PostgreSQL for a table named `alembic_version`.

No revision was initially displayed because:

- the users table existed before Alembic
- no migration revision had been assigned to the existing database
- the `alembic_version` bookkeeping table did not yet contain a revision

This was expected and confirmed that Alembic could connect successfully.

## 7. Initial users-table migration

Day 5 added:

```text
backend/alembic/versions/20260827_01_initial_users_table.py
```

Revision information:

```python
revision = "20260827_01"
down_revision = None
```

The migration represents the Day 4 users schema:

| Column | Type | Rules |
| --- | --- | --- |
| `id` | Integer | Primary key |
| `name` | `VARCHAR(100)` | Required |
| `email` | `VARCHAR(255)` | Required, unique index |
| `age` | Integer | Required |

For a new empty database, its `upgrade()` creates the users table and unique
email index.

Its `downgrade()` removes the index and users table. That downgrade must not be
run casually because dropping the table deletes user data.

## 8. Why the existing database was stamped

The local database already contained the users table. Executing the initial
migration against it would have tried to create the same table again.

Therefore, the existing database used:

```powershell
uv run alembic stamp head
```

Stamping records a migration revision without executing its `upgrade()`.

```text
Existing users table
        ↓
alembic stamp head
        ↓
Create/update alembic_version
        ↓
Record 20260827_01
        ↓
Do not recreate users
```

This was a one-time baseline adoption operation. New empty databases will use:

```powershell
uv run alembic upgrade head
```

so the initial migration actually creates the users table.

## 9. Day 5 verification commands

Migration history:

```powershell
uv run alembic history
```

Current revision:

```powershell
uv run alembic current
```

Expected after stamping:

```text
20260827_01 (head)
```

Model/schema comparison:

```powershell
uv run alembic check
```

Expected:

```text
No new upgrade operations detected.
```

## 10. Removing automatic schema creation

After the baseline was confirmed, `app/main.py` stopped importing the database
engine for table creation and removed:

```python
Base.metadata.create_all(bind=engine)
```

Alembic is now the single mechanism responsible for database schema changes.

The new lifecycle is:

```text
Modify SQLAlchemy model
        ↓
Create and review migration
        ↓
Run alembic upgrade head
        ↓
Start/deploy the application
```

## 11. Day 5 result

At the end of Day 5:

- Alembic was installed.
- Alembic connected to the existing PostgreSQL database.
- The users-table baseline migration existed.
- The current database was stamped at `20260827_01`.
- ORM metadata and PostgreSQL agreed.
- FastAPI no longer created tables during startup.
- Existing data remained intact.

---

# Day 6 — Password Hashing, JWT, and Protected Routes

## 12. Problem solved on Day 6

Before Day 6, anyone who could call the API could use the public user CRUD
endpoints. There was no password or proof of identity.

Day 6 added:

- account registration
- secure password hashing
- login credential verification
- signed JWT access tokens
- token expiration
- current-user lookup
- active/inactive account enforcement
- protected API routes
- owner-only user-profile operations
- a real database schema upgrade

## 13. Authentication dependencies

Run from the backend directory:

```powershell
uv add "pwdlib[argon2]" pyjwt python-multipart
```

| Dependency | Purpose |
| --- | --- |
| `pwdlib[argon2]` | Hashes and verifies passwords with Argon2 |
| `pyjwt` | Encodes and decodes signed JWTs |
| `python-multipart` | Reads OAuth2 form data used by login and Swagger |

No paid service is required.

## 14. Private JWT configuration

A random secret was generated with:

```powershell
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

This command prints a cryptographically random 64-character hexadecimal value.
The actual generated value is private and is not stored in this document.

The following settings were added to `backend/.env`:

```dotenv
JWT_SECRET_KEY=<private-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Meaning:

| Variable | Purpose |
| --- | --- |
| `JWT_SECRET_KEY` | Private value used to sign and validate tokens |
| `JWT_ALGORITHM` | Selected signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |

The real `.env` remains excluded from Git. A safe `.env.example` contains only
placeholders and can be committed.

## 15. Authentication schema migration

Day 6 added:

```text
backend/alembic/versions/20260902_02_add_user_authentication.py
```

Migration chain:

```python
revision = "20260902_02"
down_revision = "20260827_01"
```

The migration added:

| Column | Type | Purpose |
| --- | --- | --- |
| `hashed_password` | `VARCHAR(255)` | Stores the one-way password hash |
| `is_active` | Boolean | Allows an account to be disabled without deleting it |

### Legacy-user handling

Users created before Day 6 had no passwords. The migration preserved them with:

```text
hashed_password = NULL
is_active = false
```

They cannot log in. New registrations receive an Argon2 password hash and are
created active.

This avoided:

- deleting existing Day 3–4 data
- inventing passwords
- assigning insecure shared passwords
- accidentally enabling passwordless accounts

## 16. First real Alembic upgrade

Before upgrading, the database was at:

```text
20260827_01
```

The migration history contained the new head:

```text
20260827_01 -> 20260902_02 (head)
```

The schema was upgraded using:

```powershell
uv run alembic upgrade head
```

Unlike `stamp`, `upgrade` executed the migration and altered the users table.

After the operation:

```powershell
uv run alembic current
```

reported:

```text
20260902_02 (head)
```

## 17. Password hashing

Passwords are never saved directly.

```text
Plain password
      ↓
Argon2 password hashing
      ↓
Salted one-way hash
      ↓
users.hashed_password
```

Hashing differs from encryption:

```text
Encryption
= designed to be reversed with a key

Password hashing
= deliberately one-way; login performs verification
```

Registration calls the hashing function before the SQLAlchemy object is saved.
API response schemas never include either the plain password or stored hash.

## 18. JWT access tokens

JWT means JSON Web Token.

After successful login, NEXUS AI creates a signed token containing:

- `sub`: the user's ID as the token subject
- `exp`: the token expiration time

Conceptual flow:

```text
Verified user ID + expiration
        ↓
Sign with JWT_SECRET_KEY
        ↓
Return access token
        ↓
Client sends Authorization header
        ↓
Backend validates signature and expiration
        ↓
Load current user from PostgreSQL
```

The authorization header format is:

```text
Authorization: Bearer <access-token>
```

A signed JWT is not a place for passwords or sensitive financial/document data.

## 19. Security module

Day 6 added:

```text
backend/app/security.py
```

Its responsibilities include:

- reading private JWT configuration
- rejecting a missing or short JWT secret
- hashing passwords
- verifying passwords
- creating access tokens
- decoding and validating tokens
- reading the token's subject
- loading the user from PostgreSQL
- rejecting inactive accounts

Important dependencies:

```text
get_current_user
        ↓
decode JWT
        ↓
read user ID
        ↓
db.get(User, user_id)

get_current_active_user
        ↓
get_current_user
        ↓
check is_active
```

These FastAPI dependencies can be reused by Knowledge, Learn, Money, Work, file,
notification, and Intelligence routes.

## 20. Authentication router

Day 6 added:

```text
backend/app/routers/auth.py
```

Router configuration:

```text
prefix = /auth
Swagger tag = Authentication
```

Endpoints:

| Method | Endpoint | Purpose | Success |
| --- | --- | --- | --- |
| POST | `/auth/register` | Create password-protected account | 201 |
| POST | `/auth/login` | Verify credentials and return JWT | 200 |
| GET | `/auth/me` | Return authenticated active user | 200 |

### Registration flow

```text
JSON request
    ↓
UserRegister validation
    ↓
Normalize email to lowercase
    ↓
Check duplicate email
    ↓
Hash password
    ↓
Create active User
    ↓
Commit to PostgreSQL
    ↓
Return UserResponse without password/hash
```

### Login form

`/auth/login` uses `OAuth2PasswordRequestForm`. The standard form calls the
identifier field `username`, but NEXUS AI places the user's email in that field.

Successful response:

```json
{
  "access_token": "<signed-token>",
  "token_type": "bearer"
}
```

Incorrect credentials return `401 Unauthorized` with a generic message so the
API does not reveal whether a particular email exists.

Inactive users return `403 Forbidden` after valid credential verification.

## 21. Authentication versus authorization

```text
Authentication
= proving who the user is

Authorization
= deciding what that user may access
```

A valid token authenticates a user. It does not permit that user to read or
change another account.

Day 6 applied owner checks to the user router. A request for a different user ID
returns `403 Forbidden`.

## 22. User-router security change

The old public endpoints were removed:

```text
POST /users
GET /users
```

Registration now belongs to `/auth/register`. Ordinary accounts are not given a
public list of all users.

Protected user endpoints are:

| Method | Endpoint | Rule |
| --- | --- | --- |
| GET | `/users/{user_id}` | Requested ID must match token user |
| PATCH | `/users/{user_id}` | Only the owner may update |
| DELETE | `/users/{user_id}` | Only the owner may delete |

This is the first concrete user-data isolation rule in NEXUS AI.

Future document, learning, transaction, work, memory, and tool queries must also
filter by the authenticated user's ID.

## 23. Logout behavior

Day 6 uses short-lived access tokens without refresh tokens or a server-side
revocation table.

At this stage, logout means:

```text
Client removes stored access token
        ↓
Future protected requests have no token
        ↓
API returns 401
```

Refresh tokens and server-side revocation are later improvements. The system
does not pretend that a no-op backend logout endpoint invalidates a stateless
token.

## 24. Day 6 testing completed

The completed test sequence covered:

1. Migration history contained both revisions.
2. `alembic upgrade head` added authentication columns.
3. `alembic current` reported `20260902_02 (head)`.
4. `alembic check` reported no new upgrade operations.
5. FastAPI started after the schema upgrade.
6. Registration created an active account with status 201.
7. Duplicate registration returned 409.
8. Password and hash were absent from the registration response.
9. Login returned a bearer access token.
10. Incorrect credentials returned 401.
11. Authorized `/auth/me` returned the current user.
12. A request without authorization returned 401.
13. The owner could retrieve and update their profile fields.
14. Access to another user ID returned 403.

Final user-provided Alembic verification on September 4, 2026:

```text
20260902_02 (head)
No new upgrade operations detected.
```

PostgreSQL sequence-detection logging for `users_id_seq` was normal. Alembic
recognized it as the sequence owned by the integer users primary key and did
not propose an unnecessary migration.

## 25. HTTP status codes used

| Status | Meaning | Authentication use |
| --- | --- | --- |
| 200 OK | Request succeeded | Login, current user, profile read/update |
| 201 Created | Resource created | Registration |
| 204 No Content | Success without a response body | Account deletion |
| 400 Bad Request | Request lacks a meaningful update | Empty PATCH |
| 401 Unauthorized | Missing/invalid credentials | Bad login or token |
| 403 Forbidden | Identity known but action not allowed | Inactive account or another user's ID |
| 409 Conflict | Resource conflicts with existing data | Duplicate email |
| 422 Unprocessable Entity | Validation failed | Invalid email, password length, age, or name |

## 26. Final structure after Day 6

```text
NEXUS_AI/
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic/
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 20260827_01_initial_users_table.py
│   │       └── 20260902_02_add_user_authentication.py
│   └── app/
│       ├── __init__.py
│       ├── database.py
│       ├── main.py
│       ├── models.py
│       ├── schemas.py
│       ├── security.py
│       └── routers/
│           ├── __init__.py
│           ├── auth.py
│           └── users.py
├── frontend/
├── docs/
│   └── learning-log/
│       ├── day-01-02-project-setup-fastapi.md
│       ├── day-03-04-postgresql-sqlalchemy-user-crud-routing.md
│       └── day-05-06-alembic-authentication-jwt.md
└── .gitignore
```

## 27. Final backend capability

```text
NEXUS AI Core Backend
├── FastAPI application
├── PostgreSQL persistence
├── SQLAlchemy ORM
├── Alembic schema history
│   ├── initial users baseline
│   └── authentication upgrade
├── Registration
├── Argon2 password hashing
├── OAuth2 password-form login
├── JWT access tokens
├── Current-user identification
├── Active/inactive account support
├── Protected routes
├── Owner-only user access
├── Pydantic validation
└── Structured HTTP error responses
```

## 28. Concepts learned

### Day 5

- database migration
- schema evolution
- Alembic configuration
- migration revision
- migration chain
- `revision`
- `down_revision`
- `upgrade()`
- `downgrade()`
- Alembic metadata
- `alembic_version`
- baseline migration
- `alembic stamp head`
- `alembic current`
- `alembic history`
- `alembic check`
- removal of `create_all()`

### Day 6

- authentication
- authorization
- password hashing
- Argon2
- password verification
- JWT
- signing secret
- token claims
- token subject
- token expiration
- bearer authentication
- OAuth2 password form
- protected dependencies
- current-user lookup
- inactive accounts
- owner-only access
- legacy-data migration
- HTTP 401 versus 403

## 29. Important engineering decisions

### Alembic owns the database schema

FastAPI startup no longer silently creates tables. Every schema change must have
a reviewed migration.

### Passwords are hashed locally

No external authentication payment or AI service is required for password
hashing. Plain passwords are never stored.

### Tokens contain minimal identity data

The token identifies the user and expires. Structured personal data remains in
PostgreSQL rather than being placed inside the JWT.

### Existing users are preserved safely

Legacy rows are inactive because they have no password. They were not deleted
or given fabricated credentials.

### User isolation begins at the API layer

Protected routes load identity from the validated token. They do not trust a
user ID supplied in prompt text or an unverified request body.

### Refresh tokens remain later work

The MVP begins with a short-lived access token. Refresh-token storage and
revocation will be added only when the PWA authentication lifecycle requires
them.

## 30. Common errors and fixes

### Alembic prints no current revision

Possible cause: the database has not been stamped or upgraded.

Check:

```powershell
uv run alembic history
uv run alembic current
```

Do not stamp an unknown database without first confirming its schema.

### `relation "users" already exists`

Possible cause: the initial baseline migration was executed against the legacy
database rather than stamped.

The existing Day 4 database needed `stamp head` for the baseline. New empty
databases need `upgrade head`.

### JWT secret missing or too short

Check that the real `backend/.env` contains:

```dotenv
JWT_SECRET_KEY=<private-value-with-at-least-32-characters>
```

Save the file and restart Uvicorn. Never commit or send the value.

### Login endpoint returns multipart/form error

Install:

```powershell
uv add python-multipart
```

### Login returns 401 for an old user

Expected for pre-Day-6 users. They do not possess password hashes and remain
inactive. Register a new account through `/auth/register`.

### Protected route returns 401

The token may be missing, malformed, signed with a different secret, expired,
or reference a deleted user. Log in again and authorize Swagger with the new
token.

### Protected route returns 403

The user is authenticated, but the account is inactive or the route targets a
different user ID.

### Alembic detects `users_id_seq`

PostgreSQL uses the sequence to generate integer IDs. Alembic can log that it
recognized the owned sequence and omitted it from migration proposals. This is
normal when the final result says no new upgrade operations were detected.

## 31. Git checkpoint

Run from the project root:

```text
C:\MY DATA\GITHUB DATA\NEXUS_AI>
```

Check the working tree:

```powershell
git status
```

Confirm that the private `.env` is ignored:

```powershell
git check-ignore backend/.env
```

Expected output:

```text
backend/.env
```

Stage the completed work and documentation:

```powershell
git add .
```

Review exactly what is staged:

```powershell
git status
```

Ensure that `backend/.env` is not staged. `.env.example` is safe because it
contains placeholders rather than secrets.

Commit:

```powershell
git commit -m "feat: add Alembic migrations and JWT authentication"
```

If the private GitHub remote is configured and you are ready to upload:

```powershell
git push
```

`git commit` creates the local snapshot. `git push` uploads commits to the
configured remote.

## 32. Completion state

Days 5 and 6 are complete.

NEXUS AI now has a versioned PostgreSQL schema and an authenticated user
identity that can safely own future profiles, files, documents, learning
records, transactions, work items, memories, notifications, and AI tool calls.

The next two-day block is:

```text
Day 7: shared user profile and preferences
Day 8: shared file metadata, ownership, and controlled upload foundation
```

The formal Days 7–8 learning log will be created only after both days are
implemented and tested.
