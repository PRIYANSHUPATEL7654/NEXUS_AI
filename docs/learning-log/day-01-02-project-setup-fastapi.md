# Nexus AI — Phase 0, Days 1–2

## Purpose

The first two days established the basic structure of the Nexus AI ecosystem and created its first working backend API using Python and FastAPI.

The goal was to understand the basic software flow:

```text
Client
  ↓
HTTP Request
  ↓
Web Server
  ↓
FastAPI Backend
  ↓
Python Processing
  ↓
JSON Response
  ↓
Client
```

---

# Day 1 — Project and Architecture Setup

## 1. Create the main project folder

Run from the folder where the Nexus project should be stored:

```powershell
mkdir NEXUS_AI
```

### Meaning

`mkdir` means **make directory**.

It creates:

```text
NEXUS_AI/
```

---

## 2. Enter the project directory

```powershell
cd NEXUS_AI
```

### Meaning

`cd` means **change directory**.

The terminal now operates from inside the Nexus project.

---

## 3. Initialize Git

```powershell
git init
```

### Meaning

Creates a local Git repository.

Git creates a hidden folder:

```text
.git/
```

The `.git` folder stores:

* commit history
* branches
* staging information
* repository configuration

This command does not upload anything to GitHub.

---

## 4. Create the main project sections

```powershell
mkdir backend
mkdir frontend
mkdir docs
```

### Meaning

Creates three directories.

```text
NEXUS_AI/
│
├── backend/
├── frontend/
└── docs/
```

### Purpose

`backend/`

Stores server-side code including FastAPI, databases, ML, AI, RAG and agents.

`frontend/`

Will contain the user interface for laptop and mobile/PWA access.

`docs/`

Stores project documentation, architecture, learning notes and commands.

---

# Day 2 — Python Project and FastAPI

## 5. Enter the backend directory

```powershell
cd backend
```

Terminal location becomes:

```text
NEXUS_AI\backend>
```

---

## 6. Initialize the Python project with uv

```powershell
uv init
```

### What is uv?

`uv` is a Python package and project manager.

We use it to:

* manage our Python environment
* install libraries
* record dependencies
* create/update `.venv`
* run Python applications

### What `uv init` does

Initializes the current directory as a uv-managed Python project.

It may create files such as:

```text
pyproject.toml
.python-version
README.md
main.py
```

`pyproject.toml` stores project information and Python dependencies.

---

## 7. Install FastAPI and Uvicorn

```powershell
uv add fastapi "uvicorn[standard]"
```

### Meaning

`uv add`

Adds libraries to the current project's dependencies.

`fastapi`

Framework used to create the Nexus backend API.

`uvicorn`

Web server used to run the FastAPI application.

The dependencies are recorded by uv instead of being installed randomly into the computer's global Python installation.

---

## 8. Create the application directory

Create:

```text
backend/app/
```

Inside it create:

```text
main.py
```

Result:

```text
backend/
│
├── app/
│   └── main.py
│
├── pyproject.toml
├── uv.lock
└── .venv/
```

---

## 9. Create the FastAPI application

`app/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="Nexus AI API",
    description="Backend API for the Nexus AI ecosystem",
    version="0.1.0"
)


class UserProfile(BaseModel):
    name: str
    email: str
    age: int


@app.get("/")
def root():
    return {
        "message": "Nexus AI backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {
        "user_id": user_id,
        "name": "Test User"
    }


@app.post("/users")
def create_user(user: UserProfile):
    return {
        "message": "User created successfully",
        "user": user
    }
```

---

# 10. Verify uv

```powershell
uv --version
```

### Meaning

Checks whether the `uv` executable is available.

Example output:

```text
uv 0.x.x
```

No project files are changed by this command.

---

# 11. Run the Nexus backend

Run from:

```text
NEXUS_AI\backend>
```

Command:

```powershell
uv run uvicorn app.main:app --reload
```

### Breakdown

`uv`

Use the uv project manager.

`run`

Run a program using the project's managed Python environment.

`uvicorn`

Start the web server.

`app.main`

Import:

```text
app/main.py
```

`:app`

Use the FastAPI object:

```python
app = FastAPI(...)
```

`--reload`

Automatically restart the development server whenever Python source files change.

---

## Development server

The server runs at:

```text
http://127.0.0.1:8000
```

`127.0.0.1`

Means the current computer and is commonly called `localhost`.

`8000`

Is the network port being used by the FastAPI server.

---

# 12. API endpoints created

## Root endpoint

```text
GET /
```

Returns:

```json
{
    "message": "Nexus AI backend is running"
}
```

---

## Health endpoint

```text
GET /health
```

Returns:

```json
{
    "status": "healthy"
}
```

It can later be used by infrastructure to verify that the Nexus backend is running.

---

## Get user endpoint

```text
GET /users/{user_id}
```

Example:

```text
GET /users/5
```

Returns:

```json
{
    "user_id": 5,
    "name": "Test User"
}
```

`user_id` is a path parameter.

Because it is declared as:

```python
user_id: int
```

FastAPI validates that the supplied value is an integer.

---

## Create user endpoint

```text
POST /users
```

Example request:

```json
{
    "name": "Test User",
    "email": "test@example.com",
    "age": 22
}
```

Pydantic validates this against:

```python
class UserProfile(BaseModel):
    name: str
    email: str
    age: int
```

---

# 13. Swagger API documentation

FastAPI automatically creates interactive documentation at:

```text
http://127.0.0.1:8000/docs
```

Swagger UI allows developers to:

* inspect API endpoints
* provide request data
* execute requests
* inspect HTTP responses
* see validation errors

---

# 14. Important HTTP status codes introduced

```text
200 → Successful request
201 → Resource successfully created
400 → Invalid request
401 → Authentication required
403 → Permission denied
404 → Resource not found
422 → Validation error
500 → Server error
```

General rule:

```text
2xx → success
4xx → client/request problem
5xx → backend/server problem
```

---

# 15. Current limitation

Although:

```text
POST /users
```

returns:

```text
User created successfully
```

the user is not yet permanently stored.

Current flow:

```text
Request
  ↓
FastAPI
  ↓
Python
  ↓
Response
```

Future flow:

```text
Request
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
PostgreSQL
  ↓
Permanent storage
  ↓
Response
```

Persistent storage will be introduced on Day 3.

---

# 16. Git ignore configuration

The project root contains:

```text
.gitignore
```

with:

```text
.venv/
__pycache__/
*.pyc
.env
```

### Purpose

`.venv/`

Local Python environment. It can be recreated and should not be committed.

`__pycache__/`

Automatically generated Python cache.

`*.pyc`

Compiled Python files.

`.env`

Environment variables and secrets such as database passwords and API keys.

---

# 17. Check Git state

```powershell
git status
```

### Meaning

Displays:

* modified files
* untracked files
* staged files
* current branch state

It does not modify the project.

---

# 18. Stage changes

```powershell
git add .
```

### Meaning

Prepare all non-ignored changed files under the current directory for the next Git commit.

It does not upload files anywhere.

---

# 19. Commit the project

```powershell
git commit -m "Initialize Nexus AI backend with FastAPI"
```

### Meaning

Creates a local versioned snapshot.

`-m` specifies the commit message.

The commit is stored in the local:

```text
.git/
```

repository.

It is not uploaded to GitHub until `git push` is performed.

---

# Day 2 Result

The Nexus project currently supports:

* Git version control
* uv dependency management
* isolated Python environment
* FastAPI backend
* Uvicorn development server
* GET requests
* POST requests
* path parameters
* JSON responses
* Pydantic validation
* Swagger API documentation
* health endpoint

The next goal is persistent storage using PostgreSQL and SQLAlchemy.
