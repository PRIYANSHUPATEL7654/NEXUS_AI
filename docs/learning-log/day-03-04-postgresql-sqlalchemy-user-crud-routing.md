# NEXUS AI — Days 3–4: PostgreSQL, SQLAlchemy, User CRUD, and Modular Routing

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 3–4 |
| Main area | Nexus Core backend foundation |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| PostgreSQL driver | psycopg |
| Package manager | uv |
| Day 3 status | Completed and tested |
| Day 4 status | Completed and tested |

---

## 1. Purpose of this two-day block

Days 1–2 created the initial FastAPI application and introduced endpoints,
requests, responses, Pydantic validation, Swagger UI, status codes, Git, and the
basic NEXUS AI architecture.

At the end of Day 2, user data could be accepted and returned by the API, but it
was not stored permanently. Restarting the application would lose any data held
only in Python memory.

Days 3–4 solved two foundation-level problems:

1. Day 3 connected FastAPI to PostgreSQL through SQLAlchemy and added permanent
   user storage.
2. Day 4 completed the user CRUD API, strengthened validation, and moved
   user-related endpoints into a dedicated FastAPI router.

The resulting flow is:

~~~text
Client / Swagger UI
        ↓
FastAPI endpoint
        ↓
Pydantic request validation
        ↓
SQLAlchemy session and ORM model
        ↓
psycopg PostgreSQL driver
        ↓
PostgreSQL nexus_ai database
~~~

---

# Day 3 — PostgreSQL and SQLAlchemy Persistence

## 2. Problem solved on Day 3

Before Day 3, the API could process a user request, but the user was not stored
in a persistent database.

Day 3 added:

- PostgreSQL as the primary relational database
- SQLAlchemy as the Python database toolkit and ORM
- psycopg as the PostgreSQL driver
- python-dotenv for loading database configuration from a private .env file
- a SQLAlchemy User model
- a database session dependency
- permanent user creation and retrieval
- duplicate-email protection
- transaction rollback
- appropriate 404 and 409 API responses

---

## 3. Why PostgreSQL was selected

PostgreSQL was selected as the primary NEXUS AI database because the ecosystem
will eventually require:

- structured relational data
- reliable transactions
- database constraints
- joins and complex queries
- JSON support
- analytics
- full-text search
- pgvector for embeddings and vector similarity search

An important distinction learned on Day 3 was:

~~~text
SQL
= a language used to communicate with relational databases

PostgreSQL
= a relational database management system that understands SQL
~~~

PostgreSQL stores the actual data. SQLAlchemy does not replace PostgreSQL.

---

## 4. Database technology flow

~~~text
FastAPI
   ↓
SQLAlchemy
   ↓
psycopg
   ↓
PostgreSQL
~~~

### PostgreSQL

The actual database system that stores the NEXUS AI data permanently.

### SQLAlchemy

A Python database toolkit and ORM. It allows Python classes and objects to be
mapped to database tables and rows.

### psycopg

The driver that performs the low-level communication between Python and
PostgreSQL.

### python-dotenv

Loads configuration values from a .env file into environment variables.

---

## 5. Day 3 dependency installation

### Command

Run from:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
~~~

Command:

~~~powershell
uv add sqlalchemy "psycopg[binary]" python-dotenv
~~~

### Command explanation

| Part | Meaning |
| --- | --- |
| uv | The package and environment manager used by the backend |
| add | Adds one or more dependencies to the project |
| sqlalchemy | Installs SQLAlchemy |
| psycopg[binary] | Installs psycopg with its ready-to-use binary package |
| python-dotenv | Installs support for reading values from .env |

### Files and directories affected

The command updated:

~~~text
backend/pyproject.toml
backend/uv.lock
backend/.venv/
~~~

The command did not create or modify the PostgreSQL database.

---

## 6. PostgreSQL database

The database created for the project was:

~~~text
nexus_ai
~~~

The connection configuration was stored in:

~~~text
backend/.env
~~~

Conceptual .env structure:

~~~dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nexus_ai
DB_USER=postgres
DB_PASSWORD=<private-password>
~~~

The actual password must never be written in documentation, source code, Git,
GitHub, screenshots, or messages.

The project .gitignore includes at least:

~~~gitignore
.venv/
__pycache__/
*.pyc
.env
~~~

---

## 7. database.py responsibilities

File:

~~~text
backend/app/database.py
~~~

This file is responsible for the shared database infrastructure.

It contains the following concepts:

- load_dotenv()
- environment variables
- SQLAlchemy URL.create()
- create_engine()
- SessionLocal
- DeclarativeBase
- Base
- get_db()

### Loading environment variables

~~~python
load_dotenv()
~~~

This loads values from the backend .env file into the process environment.

### Database URL

SQLAlchemy needs a database URL containing the driver, user, password, host,
port, and database name.

URL.create() was preferred because it constructs the connection URL safely from
separate configuration values.

Conceptually:

~~~text
postgresql + psycopg
database username
database password
localhost
port 5432
nexus_ai database
~~~

### Engine

The SQLAlchemy engine manages database connectivity.

~~~text
Python application
      ↓
SQLAlchemy engine
      ↓
Database connections
      ↓
PostgreSQL
~~~

The engine is not the same as one request-specific database session.

### SessionLocal

SessionLocal is a session factory. Calling it creates a new SQLAlchemy session
for database work.

### Base

Base is the parent class used by SQLAlchemy ORM models.

Every model that inherits from Base becomes part of SQLAlchemy's model
metadata.

### get_db()

get_db() creates a session for an API request and ensures that it is closed
after the request finishes.

Conceptual lifecycle:

~~~text
API request arrives
        ↓
get_db() opens a session
        ↓
endpoint performs database work
        ↓
response or exception occurs
        ↓
session is closed
~~~

Closing the session is important because database connections are limited
resources.

---

## 8. SQLAlchemy User model

File:

~~~text
backend/app/models.py
~~~

The Python User model is mapped to the PostgreSQL users table.

~~~text
Python class User
        ↕ ORM mapping
PostgreSQL users table
~~~

The table contains:

| Field | Purpose |
| --- | --- |
| id | Unique primary key generated for each user |
| name | User's name |
| email | Unique email address |
| age | User's age |

Important model concepts:

### Primary key

The primary key uniquely identifies each row.

~~~text
User 1 → id 1
User 2 → id 2
~~~

### nullable=False

The column must contain a value and cannot be NULL.

### unique=True

The database prevents two rows from using the same value. It is used for the
email column.

### index=True

PostgreSQL creates an index that can make email lookup more efficient.

### ORM mapping

A SQLAlchemy User object represents a row in the users table.

~~~python
new_user = User(
    name="Priyanshu",
    email="priyanshu@example.com",
    age=23
)
~~~

After the object is added and committed, PostgreSQL stores it as a row.

---

## 9. Pydantic schema versus SQLAlchemy model

File:

~~~text
backend/app/schemas.py
~~~

An important distinction learned was:

~~~text
Pydantic schema
= validates the API request and controls the API response

SQLAlchemy model
= represents a database table and its rows
~~~

They can contain similar fields, but they serve different layers.

~~~text
Incoming JSON
     ↓
Pydantic UserCreate
     ↓
Endpoint
     ↓
SQLAlchemy User
     ↓
PostgreSQL users table
~~~

Day 3 introduced:

- UserCreate
- UserResponse

UserCreate represented the expected client input. UserResponse included the
database-generated ID and allowed Pydantic to read SQLAlchemy object attributes.

---

## 10. Day 3 user creation flow

Endpoint:

~~~text
POST /users
~~~

Complete conceptual flow:

~~~text
JSON request
    ↓
UserCreate validation
    ↓
create SQLAlchemy User object
    ↓
db.add(new_user)
    ↓
db.commit()
    ↓
PostgreSQL INSERT
    ↓
db.refresh(new_user)
    ↓
UserResponse
    ↓
JSON response
~~~

### db.add()

Adds the new object to the current SQLAlchemy session.

It prepares the object for insertion but does not by itself permanently save
the row.

### db.commit()

Commits the database transaction. After a successful commit, PostgreSQL stores
the row permanently.

### db.refresh()

Reloads the object from PostgreSQL so generated or database-controlled values,
such as the ID, are available in the response.

---

## 11. Day 3 single-user retrieval

Endpoint:

~~~text
GET /users/{user_id}
~~~

The endpoint used:

~~~python
user = db.get(User, user_id)
~~~

db.get() searches for a row using the model's primary key.

If the user is not found, the API returns:

~~~text
404 Not Found
~~~

If found, the SQLAlchemy object is converted into a UserResponse and then JSON.

---

## 12. Transactions and duplicate emails

The email column has a unique database constraint.

When a duplicate email is inserted, PostgreSQL rejects the operation and
SQLAlchemy raises IntegrityError.

The endpoint handles the failure using:

~~~python
except IntegrityError:
    db.rollback()
~~~

### Why rollback is necessary

After a failed database transaction, the session cannot safely perform more
work until the failed transaction is rolled back.

~~~text
Database operation fails
        ↓
Session enters failed transaction state
        ↓
db.rollback()
        ↓
Session becomes usable again
~~~

The API returns:

~~~text
409 Conflict
~~~

because the requested email conflicts with an existing user.

---

## 13. Temporary table creation approach

The project currently uses:

~~~python
Base.metadata.create_all(bind=engine)
~~~

This creates missing tables based on SQLAlchemy metadata.

It is suitable for the current learning stage, but it is not a full database
migration system.

Alembic will be introduced later when the roadmap genuinely requires controlled
schema changes. It was intentionally not introduced during Days 3–4.

---

## 14. Day 3 persistence test

Persistence was verified by:

1. Creating a user through POST /users.
2. Retrieving the user.
3. Stopping Uvicorn with Ctrl+C.
4. Restarting the FastAPI server.
5. Retrieving the same user again.

The user remained available because PostgreSQL stored the row permanently.

---

## 15. Day 3 error encountered and fixed

### Error

~~~text
ModuleNotFoundError: No module named 'app'
~~~

### Cause

Uvicorn was started from:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI>
~~~

From that directory, the app package was not in the expected import location
for the command being used.

### Fix

Change to the backend directory:

~~~powershell
cd backend
~~~

Then run:

~~~powershell
uv run uvicorn app.main:app --reload
~~~

Correct terminal location:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
~~~

---

# Day 4 — User CRUD and Modular API Routing

## 16. Problem solved on Day 4

At the end of Day 3, the API could create a user and retrieve one user.

It did not yet provide:

- listing users
- pagination
- partial updates
- deletion
- email-format validation
- strong age and name validation
- modular organization for future NEXUS Core endpoints

User endpoints also lived directly inside main.py. That structure would become
difficult to manage as authentication, documents, knowledge, files, search, and
memory are added.

Day 4 completed the user CRUD API and introduced APIRouter.

---

## 17. Day 4 dependency installation

Run from:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
~~~

Command:

~~~powershell
uv add email-validator
~~~

### Purpose

Pydantic's EmailStr type uses email-validator to validate the basic structure of
email addresses.

It rejects values such as:

~~~text
hello
12345
not-an-email
~~~

It accepts structurally valid values such as:

~~~text
priyanshu@example.com
~~~

It checks format; it does not verify whether the email account actually exists.

### Files affected

~~~text
backend/pyproject.toml
backend/uv.lock
backend/.venv/
~~~

---

## 18. Router package

Day 4 added:

~~~text
backend/app/routers/
├── __init__.py
└── users.py
~~~

The routers directory groups API endpoints by domain.

Future examples may include:

~~~text
routers/
├── users.py
├── auth.py
├── documents.py
├── knowledge.py
├── files.py
└── search.py
~~~

This remains one modular-monolith FastAPI application, not multiple
microservices.

---

## 19. Final Day 4 Pydantic schemas

File:

~~~text
backend/app/schemas.py
~~~

Important implementation:

~~~python
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    age: int = Field(
        ge=1,
        le=120
    )


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    email: EmailStr | None = None

    age: int | None = Field(
        default=None,
        ge=1,
        le=120
    )


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
~~~

### UserBase

Contains the common name, email, and age fields.

### UserCreate

Inherits the fields required when creating a user.

### UserUpdate

All fields are optional so PATCH can update only selected fields.

### UserResponse

Contains the shared user fields plus the database-generated ID.

### Validation rules

| Field | Rule |
| --- | --- |
| name | Minimum 2 and maximum 100 characters |
| email | Must have a valid email structure |
| age | Minimum 1 and maximum 120 |

---

## 20. APIRouter configuration

File:

~~~text
backend/app/routers/users.py
~~~

The router is configured as:

~~~python
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
~~~

### prefix

The /users prefix is automatically added to each route in the file.

~~~text
router route ""
      + prefix "/users"
      = /users
~~~

~~~text
router route "/{user_id}"
      + prefix "/users"
      = /users/{user_id}
~~~

### tags

The Users tag groups the user endpoints together in Swagger UI.

---

## 21. Final user CRUD endpoints

| CRUD operation | Method | Endpoint | Successful status |
| --- | --- | --- | --- |
| Create | POST | /users | 201 Created |
| Read multiple | GET | /users | 200 OK |
| Read one | GET | /users/{user_id} | 200 OK |
| Update | PATCH | /users/{user_id} | 200 OK |
| Delete | DELETE | /users/{user_id} | 204 No Content |

CRUD means:

~~~text
C = Create
R = Read
U = Update
D = Delete
~~~

Relational database equivalents:

~~~text
Create → INSERT
Read   → SELECT
Update → UPDATE
Delete → DELETE
~~~

---

## 22. Listing users with pagination

Endpoint:

~~~text
GET /users
~~~

The endpoint supports:

~~~text
skip
limit
~~~

Example:

~~~text
/users?skip=0&limit=10
~~~

### skip

The number of records to ignore from the beginning.

### limit

The maximum number of records to return.

Validation:

~~~text
skip: default 0, minimum 0
limit: default 10, minimum 1, maximum 100
~~~

Pagination prevents the API from trying to return every user when the table
eventually contains a large number of rows.

SQLAlchemy query:

~~~python
statement = (
    select(User)
    .offset(skip)
    .limit(limit)
)

users = db.scalars(statement).all()
~~~

Conceptual SQL:

~~~sql
SELECT *
FROM users
OFFSET 0
LIMIT 10;
~~~

The response model is:

~~~python
list[UserResponse]
~~~

because the endpoint returns a JSON list of users.

---

## 23. Partial user updates

Endpoint:

~~~text
PATCH /users/{user_id}
~~~

PATCH was selected because it allows a partial update.

Example:

~~~json
{
  "age": 24
}
~~~

Only age changes. Name and email remain unchanged.

The supplied fields are extracted using:

~~~python
update_data = user_data.model_dump(
    exclude_unset=True
)
~~~

exclude_unset=True ensures that fields omitted by the client are not included in
the update dictionary.

An empty request:

~~~json
{}
~~~

returns:

~~~text
400 Bad Request
~~~

An explicitly null updated field is rejected so required user data is not erased.

Fields are assigned dynamically:

~~~python
for field, value in update_data.items():
    setattr(user, field, value)
~~~

SQLAlchemy tracks the changed attributes. db.commit() causes PostgreSQL to store
the update.

Duplicate email updates are handled using IntegrityError, rollback, and a
409 Conflict response.

---

## 24. User deletion

Endpoint:

~~~text
DELETE /users/{user_id}
~~~

Important operations:

~~~python
db.delete(user)
db.commit()
~~~

Conceptual SQL:

~~~sql
DELETE FROM users
WHERE id = <user_id>;
~~~

Successful deletion returns:

~~~text
204 No Content
~~~

The empty response body is intentional because the operation succeeded but
there is no resource body to return.

A nonexistent user returns:

~~~text
404 Not Found
~~~

---

## 25. Router registration in main.py

File:

~~~text
backend/app/main.py
~~~

The main application imports and registers the router:

~~~python
from app.routers import users

app.include_router(users.router)
~~~

Flow:

~~~text
users.py creates router
        ↓
main.py imports users
        ↓
app.include_router(users.router)
        ↓
FastAPI exposes all user endpoints
~~~

main.py remains responsible for application-level setup and simple platform
endpoints such as:

~~~text
GET /
GET /health
~~~

User-specific endpoint logic now belongs in users.py.

---

## 26. Starting the server

Run from:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI\backend>
~~~

Command:

~~~powershell
uv run uvicorn app.main:app --reload
~~~

### Command explanation

| Part | Meaning |
| --- | --- |
| uv run | Runs the command inside the uv-managed project environment |
| uvicorn | Starts the ASGI server |
| app.main | Imports the app/main.py module |
| :app | Uses the FastAPI object named app |
| --reload | Restarts the development server when source files change |

Swagger UI:

~~~text
http://127.0.0.1:8000/docs
~~~

The development server can be stopped using:

~~~text
Ctrl+C
~~~

---

## 27. Day 4 testing completed

The Day 4 implementation was tested successfully.

The test flow covered:

1. GET /health returned 200.
2. POST /users created a valid user and returned 201.
3. Invalid email input returned 422.
4. Invalid age input returned 422.
5. GET /users returned a user list.
6. skip and limit pagination worked.
7. GET /users/{user_id} returned an existing user.
8. A nonexistent user ID returned 404.
9. PATCH updated one selected field.
10. PATCH updated multiple selected fields.
11. An empty PATCH request returned 400.
12. A null or invalid update was rejected.
13. Updating to an existing email returned 409.
14. DELETE removed a selected test user and returned 204.
15. Retrieving the deleted user returned 404.
16. Restarting the server confirmed persistent creates, updates, and deletes.

No additional unresolved Day 4 error was reported after the final test suite.

---

## 28. HTTP status codes used

| Status | Meaning | Used when |
| --- | --- | --- |
| 200 OK | Request succeeded | Reading or updating users |
| 201 Created | Resource created | Creating a user |
| 204 No Content | Successful request with no body | Deleting a user |
| 400 Bad Request | Request has no meaningful update | Empty PATCH request |
| 404 Not Found | Requested resource does not exist | User ID is missing |
| 409 Conflict | Request conflicts with existing data | Duplicate email |
| 422 Unprocessable Entity | Input validation failed | Invalid email, age, name, or null update |

---

## 29. Final project structure after Day 4

~~~text
NEXUS_AI/
│
├── backend/
│   ├── .env
│   ├── .venv/
│   ├── pyproject.toml
│   ├── uv.lock
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       │
│       └── routers/
│           ├── __init__.py
│           └── users.py
│
├── frontend/
│
├── docs/
│   └── learning-log/
│       ├── day-01-02-project-setup-fastapi.md
│       └── day-03-04-postgresql-sqlalchemy-user-crud-routing.md
│
└── .gitignore
~~~

---

## 30. Final backend capability after Days 3–4

~~~text
NEXUS AI Backend
│
├── FastAPI application
│   ├── GET /
│   └── GET /health
│
├── User router
│   ├── POST /users
│   ├── GET /users
│   ├── GET /users/{user_id}
│   ├── PATCH /users/{user_id}
│   └── DELETE /users/{user_id}
│
├── Pydantic validation
│   ├── UserBase
│   ├── UserCreate
│   ├── UserUpdate
│   └── UserResponse
│
├── SQLAlchemy ORM
│   ├── engine
│   ├── sessions
│   ├── Base
│   └── User model
│
├── PostgreSQL
│   ├── nexus_ai database
│   ├── users table
│   ├── permanent storage
│   └── unique email constraint
│
└── Error handling
    ├── validation failure → 422
    ├── missing user → 404
    ├── duplicate email → 409
    ├── empty update → 400
    └── deletion success → 204
~~~

---

## 31. Concepts learned

### Day 3

- PostgreSQL
- SQL versus PostgreSQL
- database persistence
- SQLAlchemy
- ORM
- psycopg
- python-dotenv
- environment variables
- database URL
- engine
- session
- session factory
- DeclarativeBase
- ORM models
- tables and columns
- primary keys
- nullable constraints
- unique constraints
- indexes
- Depends(get_db)
- db.add()
- db.commit()
- db.rollback()
- db.refresh()
- db.get()
- IntegrityError
- database transactions
- HTTP 404
- HTTP 409

### Day 4

- CRUD
- APIRouter
- router prefixes
- Swagger tags
- modular-monolith organization
- EmailStr
- Field validation
- schema inheritance
- optional update fields
- query parameters
- pagination
- select()
- offset()
- limit()
- db.scalars()
- list response models
- PATCH versus PUT
- model_dump(exclude_unset=True)
- setattr()
- db.delete()
- HTTP 201
- HTTP 204
- HTTP 400
- HTTP 422

---

## 32. Important engineering decisions

### Continue with a modular monolith

NEXUS AI remains one backend application with logically separated modules.
Microservices are not currently necessary.

### Keep PostgreSQL as the primary database

It supports current relational needs and future JSON, analytics, search, and
pgvector requirements.

### Keep create_all temporarily

Base.metadata.create_all() remains acceptable for the present learning stage.
Alembic will be introduced when controlled database-schema evolution becomes a
real requirement.

### Delay AI features

RAG, embeddings, LangChain, LangGraph, agents, MCP, and multimodal AI were not
introduced during this block. The Nexus Core backend foundation must be reliable
before AI layers depend on it.

### Keep secrets outside Git

Database credentials remain in backend/.env, and .env remains ignored by Git.

---

## 33. Git checkpoint after documentation

Before staging, run from the NEXUS_AI project root:

~~~text
C:\MY DATA\GITHUB DATA\NEXUS_AI>
~~~

Check the working tree:

~~~powershell
git status
~~~

Confirm that backend/.env is not listed for commit.

Stage the Days 3–4 work:

~~~powershell
git add .
~~~

Review the staged files:

~~~powershell
git status
~~~

Create the local Git snapshot:

~~~powershell
git commit -m "feat: add PostgreSQL user CRUD and modular routing"
~~~

git commit creates a local snapshot. It does not upload the code to GitHub.

If the private GitHub remote is already configured and the branch is ready to
upload, the separate command is:

~~~powershell
git push
~~~

Never commit or push:

- .env
- database passwords
- API keys
- JWT secrets
- certificates
- private access tokens

---

## 34. Completion state

Days 3 and 4 are complete.

NEXUS AI now has a persistent, validated, modular user-management foundation.
The next development block should begin with Day 5 and should continue building
the Nexus Core foundation before adding RAG, agents, or other AI technologies.

