# NEXUS AI — Days 11–12: Learn Tracking, Knowledge Quizzes and Secure Money Text Imports

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 11–12 |
| Day 11 | Nexus Learn foundation and Knowledge-linked quizzes |
| Day 12 | Nexus Money manual and pasted-text transaction workflow |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT bearer token |
| Day 11 status | Completed after Learn recovery |
| Day 12 status | Completed and confirmed by the user |
| Current migration target | `20260908_08 (head)` |
| Documentation status | Complete |

---

## 1. Purpose of this block

Days 11–12 add the first domain workflows built on the shared NEXUS AI platform.

Day 11 connects Nexus Learn to approved Knowledge documents:

```text
Learning goal
    ↓
Learning topics
    ↓
Progress history
    ↓
Skill-gap ranking
    ↓
Knowledge-linked quiz
    ↓
Attempts and score
```

Day 12 creates a privacy-first Money workflow without requesting access to a
bank, SMS inbox or payment application:

```text
Manual entry or pasted text
        ↓
Proposed transaction drafts
        ↓
User review/correction
        ↓
Explicit approval
        ↓
Permanent transactions
        ↓
Raw pasted text deleted by default
```

---

# Shared Reference — Why IDs Appear in Swagger

## 2. Database IDs are required but should not be memorized

Each record needs a stable identifier. Names are not reliable because multiple
records can share the same title.

```text
Goal 4 → Topic 7 → Question 15 → Attempt 22
```

IDs connect relational data accurately. They are not intended as a finished
user interface.

Swagger exposes path parameters because it is an engineering/testing tool. The
React frontend beginning on Day 16 loads records, shows human-readable cards or
dropdowns and keeps IDs inside application state.

## 3. Ownership changes the meaning of “not found”

Learn queries use both:

```text
requested record ID
authenticated user ID from JWT
```

Conceptually:

```sql
SELECT * FROM learning_goals
WHERE id = :goal_id
AND user_id = :current_user_id;
```

Therefore, a record returns 404 when:

- the ID does not exist
- it was deleted
- it belongs to another account
- Swagger is authorized as a different account

An ID alone never grants access.

## 4. Permanent ID lookup map

| Needed ID | Retrieve it from |
| --- | --- |
| Current account | `GET /auth/me` |
| Profile | No ID needed; use `/profile/me` |
| File | `GET /files` |
| Import job | `GET /imports` |
| Knowledge document | `GET /knowledge/documents` or `GET /learn/quiz-ready-documents` |
| Summary | `GET /knowledge/documents/{document_id}/summaries` |
| Learning goal | `GET /learn/goals` |
| Learning topic | `GET /learn/topics` |
| Quiz question | `GET /learn/topics/{topic_id}/quiz` |
| Money import batch | `GET /money/imports` |
| Money draft | `GET /money/imports/{batch_id}` |
| Approved transaction | `GET /money/transactions` |

Always follow:

```text
List records
    ↓
Find record by visible title/description
    ↓
Copy its returned ID
    ↓
Use it in the next request
```

Never type ID 1 merely because it is the example.

---

# Day 11 — Nexus Learn

## 5. Day 11 goals

Day 11 implements:

- learning goals
- goal status and priority
- learning topics
- optional Knowledge-document link
- current and target levels
- progress/study-time history
- explainable skill-gap ranking
- local Knowledge-based quiz generation
- protected correct answers
- quiz attempts
- topic quiz score
- ID-discovery routes
- quiz-readiness diagnostics

## 6. Learn database tables

### `learning_goals`

| Field | Purpose |
| --- | --- |
| `id` | Goal identifier |
| `user_id` | Authenticated owner |
| `title` | Visible goal name |
| `description` | Detailed outcome |
| `target_date` | Optional target |
| `status` | `active`, `paused`, `completed` |
| `priority` | 1–5; 1 is highest |
| timestamps | Creation/update history |

### `learning_topics`

| Field | Purpose |
| --- | --- |
| `id` | Topic identifier |
| `user_id` | Owner |
| `goal_id` | Parent learning goal |
| `source_document_id` | Optional owned Knowledge source |
| `title` | Topic name |
| `description` | Topic scope |
| `current_level` | 0–100 |
| `target_level` | 1–100 |
| `status` | `not_started`, `in_progress`, `mastered` |

The combination of `goal_id + title` is unique to prevent duplicate topic names
inside the same goal.

### `learning_progress_entries`

Each update creates history instead of overwriting every earlier measurement.

| Field | Purpose |
| --- | --- |
| `topic_id` | Topic being measured |
| `progress_percent` | New current level |
| `study_minutes` | Study effort |
| `notes` | Evidence/context |
| `recorded_at` | Measurement time |

### `quiz_questions`

Stores:

- generated question
- four options
- correct option index
- source explanation
- generation method

The public question response excludes the correct index and explanation until
the learner attempts the question.

### `quiz_attempts`

Stores:

- selected option index
- correctness
- attempt time
- authenticated owner

## 7. Learn migration

```text
backend/alembic/versions/20260907_07_add_nexus_learn.py
```

```python
revision = "20260907_07"
down_revision = "20260906_06"
```

## 8. Learn routes

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/learn/goals` | Create a goal |
| GET | `/learn/goals` | List owned goals |
| GET | `/learn/goals/{id}` | Read one goal |
| PATCH | `/learn/goals/{id}` | Update goal |
| DELETE | `/learn/goals/{id}` | Delete goal and dependent Learn data |
| POST | `/learn/goals/{id}/topics` | Create topic under a goal |
| GET | `/learn/goals/{id}/topics` | List topics for one goal |
| GET | `/learn/topics` | List every owned topic without guessing IDs |
| PATCH | `/learn/topics/{id}` | Update/link topic |
| POST | `/learn/topics/{id}/progress` | Record progress |
| GET | `/learn/topics/{id}/progress` | Read progress history |
| GET | `/learn/goals/{id}/skill-gaps` | Rank topic gaps |
| GET | `/learn/quiz-ready-documents` | Inspect Knowledge quiz readiness |
| GET | `/learn/topics/{id}/quiz/readiness` | Validate topic/document before generation |
| POST | `/learn/topics/{id}/quiz/generate` | Generate local questions |
| GET | `/learn/topics/{id}/quiz` | List questions without answers |
| POST | `/learn/quiz/questions/{id}/answer` | Submit one answer |
| GET | `/learn/topics/{id}/quiz/score` | Calculate attempt score |

## 9. Progress status rules

```text
current_level = 0
    → not_started

0 < current_level < target_level
    → in_progress

current_level >= target_level
    → mastered
```

## 10. Skill-gap baseline

```text
gap = max(0, target_level - current_level)
```

Topics are sorted largest gap first.

| Gap | Recommendation |
| --- | --- |
| 0 | Maintain with periodic revision |
| 1–39 | Continue practice and review |
| 40+ | Prioritize focused study and a quiz |

This is intentionally explainable rules logic. It is not falsely presented as a
trained recommendation model.

## 11. Local quiz algorithm

Method:

```text
local_cloze_v1
```

Flow:

1. remove PDF page markers
2. split text into readable sentences
3. break very long paragraphs into manageable chunks
4. find meaningful words with at least four letters
5. remove common stop words
6. rank frequent terms
7. choose a source term as the answer
8. replace it with a blank
9. choose three other meaningful terms as distractors
10. deterministically shuffle four options
11. store the source sentence as explanation

No paid model/API is required.

## 12. Quiz-readiness rules after recovery

A Knowledge document is ready when:

- at least one readable sentence has 25+ characters
- at least four meaningful words exist
- one answer plus three distractors can be formed

The readiness response reports:

- `character_count`
- `sentence_count`
- `keyword_count`
- `quiz_ready`
- `reason`

This replaced the earlier generic “content is too little” failure.

## 13. Original Learn failure and diagnosis

The failed topic request used:

```text
POST /learn/goals/1/topics
```

and returned:

```json
{"detail": "Learning goal not found"}
```

Quiz attempts then guessed topic IDs 1 and 2 and returned:

```json
{"detail": "Learning topic not found"}
```

Because topic creation failed, no dependent topic was created. The correct fix
was not trying more numbers. It was:

```text
GET /learn/goals
GET /learn/topics
```

and using actual owned IDs.

## 14. Learn recovery patch

Corrected files:

```text
backend/app/services/quiz_generation.py
backend/app/learn_schemas.py
backend/app/routers/learn.py
```

No migration or dependency was required.

New endpoints:

```text
GET /learn/topics
GET /learn/quiz-ready-documents
GET /learn/topics/{topic_id}/quiz/readiness
```

## 15. Complete Learn execution reference

### 15.1 Authenticate

Authorize in Swagger, then call:

```text
GET /auth/me
```

Confirm the account email and keep the same account throughout the flow.

### 15.2 Inspect existing Learn records

```text
GET /learn/goals
GET /learn/topics
```

An empty list means the account owns no records of that type. A 404 for an ID
that exists in another account is expected ownership protection.

### 15.3 Find a suitable Knowledge document

```text
GET /learn/quiz-ready-documents
```

Use only a document returning:

```json
{"quiz_ready": true}
```

If none is ready, use the Knowledge creation sequence in section 16.

### 15.4 Create a goal

```text
POST /learn/goals
```

```json
{
  "title": "NEXUS AI Learn Recovery",
  "description": "Verify goals, topics, progress and quizzes",
  "target_date": "2026-09-22",
  "priority": 1
}
```

Expected: 201. Retrieve it again with `GET /learn/goals`; use its real ID.

### 15.5 Create a topic

```text
POST /learn/goals/{real_goal_id}/topics
```

```json
{
  "title": "NEXUS AI Architecture Recovery",
  "description": "Understand the modular platform and Knowledge pipeline",
  "source_document_id": 3,
  "current_level": 35,
  "target_level": 85
}
```

Replace 3 with the actual ready Knowledge document ID.

Expected: 201. Retrieve the real topic with:

```text
GET /learn/topics
```

### 15.6 Check linked-topic readiness

```text
GET /learn/topics/{real_topic_id}/quiz/readiness
```

Do not generate until it returns:

```json
{"quiz_ready": true}
```

If the topic has no source link, use:

```text
PATCH /learn/topics/{real_topic_id}
```

```json
{"source_document_id": 3}
```

using the real document ID.

### 15.7 Generate questions

```text
POST /learn/topics/{real_topic_id}/quiz/generate
```

```json
{"question_count": 5}
```

Expected: 201 and up to five questions with four options each.

### 15.8 Retrieve actual question IDs

```text
GET /learn/topics/{real_topic_id}/quiz
```

### 15.9 Answer

```text
POST /learn/quiz/questions/{real_question_id}/answer
```

```json
{"selected_option_index": 0}
```

Indexes are 0, 1, 2 and 3. A wrong answer remains a successful API request and
returns `is_correct: false`.

### 15.10 Score

```text
GET /learn/topics/{real_topic_id}/quiz/score
```

### 15.11 Progress

```text
POST /learn/topics/{real_topic_id}/progress
```

```json
{
  "progress_percent": 55,
  "study_minutes": 90,
  "notes": "Completed the Knowledge-linked quiz recovery"
}
```

Then:

```text
GET /learn/topics/{real_topic_id}/progress
GET /learn/goals/{real_goal_id}/skill-gaps
```

Expected gap for target 85/current 55:

```text
30
```

## 16. Creating a quiz-ready Knowledge source when needed

### Upload

```text
POST /files/upload
```

Use a meaningful multi-paragraph TXT/PDF and keep its returned actual file ID.

### Import

```text
POST /imports
```

```json
{
  "file_id": 6,
  "target_module": "knowledge"
}
```

Replace 6 with the real file ID.

### Poll and inspect

```text
GET /imports/{real_import_job_id}
GET /imports/{real_import_job_id}/text
```

Wait for `awaiting_review`; confirm extracted text is readable.

### Approve

```text
POST /knowledge/documents/from-import/{real_import_job_id}
```

```json
{
  "title": "NEXUS AI Learn Quiz Source",
  "description": "Reliable Knowledge source for Nexus Learn",
  "tags": ["nexus-ai", "learning", "quiz"]
}
```

Then recheck `GET /learn/quiz-ready-documents`.

## 17. Day 11 completion state

The user confirmed the corrected Learn flow was completed. Day 11 is therefore
considered complete, including Knowledge readiness, actual-ID retrieval, topic
creation, quiz generation, attempt/score and progress testing.

---

# Day 12 — Nexus Money Manual and Pasted-Text Imports

## 18. Privacy-first Money scope

The MVP does not request:

- bank credentials
- bank API access
- UPI/payment-app access
- SMS permission
- notification-reading permission
- automatic account synchronization

Users provide only data they intentionally enter, paste or upload.

## 19. Day 12 functionality

- direct manual transaction creation
- transaction listing and filtering
- transaction deletion
- long pasted-message parsing
- proposed transaction drafts
- automatic expense/income inference
- rule-based category proposal
- explicit-date parsing
- missing-date warnings and safe default
- parser confidence
- draft editing/deletion
- batch approval
- raw-text deletion by default
- batch cancellation
- user isolation

## 20. Money database tables

### `money_import_batches`

Stores:

- user owner
- source type (`pasted_text` now; `file` prepared for Day 13)
- review status
- temporarily retained raw text
- default currency
- parser warnings
- approval time

Statuses:

```text
awaiting_review
approved
cancelled
```

### `money_transaction_drafts`

Drafts are proposals, not permanent financial records.

Fields:

- date
- description
- positive amount
- expense/income type
- category
- confidence
- warnings
- parent batch and owner

### `money_transactions`

Approved/manual normalized records store:

- date
- description
- amount
- type
- category
- currency
- source (`manual`, `pasted_text`, later `file`)
- optional source batch
- user ownership

## 21. Day 12 migration

```text
backend/alembic/versions/20260908_08_add_nexus_money_manual_imports.py
```

```python
revision = "20260908_08"
down_revision = "20260907_07"
```

## 22. Money categories

```text
Food
Transport
Shopping
Bills
Health
Education
Entertainment
Housing
Salary
Transfer
Other
```

## 23. Parser logic

Each newline or semicolon is treated as a proposed entry.

The parser:

1. finds a currency-prefixed or plain amount
2. recognizes explicit dates, `today` and `yesterday`
3. identifies income words such as `received`, `credited` or `salary`
4. otherwise proposes expense
5. matches category keywords
6. calculates confidence
7. records warnings for missing date/category
8. skips lines without a recognizable amount and adds a batch warning

This is an explainable rules baseline. Later corrected drafts can become a real
training/evaluation dataset for an ML category classifier.

## 24. Money routes

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/money/transactions` | Create manual transaction |
| GET | `/money/transactions` | List/filter owned transactions |
| DELETE | `/money/transactions/{id}` | Delete owned transaction |
| POST | `/money/imports/pasted-text` | Create batch and proposed drafts |
| GET | `/money/imports` | List owned batches |
| GET | `/money/imports/{id}` | Read batch and drafts |
| PATCH | `/money/imports/drafts/{id}` | Correct awaiting-review draft |
| DELETE | `/money/imports/drafts/{id}` | Remove unwanted draft |
| POST | `/money/imports/{id}/approve` | Approve drafts into transactions |
| POST | `/money/imports/{id}/cancel` | Cancel and clear sensitive source |

## 25. Complete Day 12 execution reference

### 25.1 Confirm account

Authorize and call:

```text
GET /auth/me
```

Keep the same account for every Money request.

### 25.2 Create a manual transaction

```text
POST /money/transactions
```

```json
{
  "transaction_date": "2026-09-06",
  "description": "Lunch",
  "amount": 250,
  "transaction_type": "expense",
  "category": "Food",
  "currency": "INR"
}
```

Expected: 201, `source = manual`.

Verify:

```text
GET /money/transactions
```

### 25.3 Create a pasted-text batch

```text
POST /money/imports/pasted-text
```

```json
{
  "text": "Paid ₹250 for lunch on 6 September 2026\nUber ride Rs 320 on 05/09/2026\nReceived salary INR 50000 on 01/09/2026\nElectricity bill 1450 on 4 Sep 2026\nBought a Python course for 799 on 03-09-2026\nThis line has no amount and should become a batch warning",
  "default_currency": "INR"
}
```

Expected:

- 201
- batch `awaiting_review`
- five drafts
- one skipped-line warning
- categories Food, Transport, Salary, Bills and Education
- no permanent transactions from this batch yet

### 25.4 Retrieve real batch/draft IDs

```text
GET /money/imports
GET /money/imports/{real_batch_id}
```

Do not guess batch or draft IDs.

### 25.5 Correct one draft

```text
PATCH /money/imports/drafts/{real_draft_id}
```

```json
{
  "description": "Team lunch",
  "amount": 250,
  "transaction_type": "expense",
  "category": "Food",
  "transaction_date": "2026-09-06"
}
```

Expected:

```text
confidence = 1.000
warnings = []
```

### 25.6 Approve the batch

```text
POST /money/imports/{real_batch_id}/approve
```

```json
{"delete_raw_text": true}
```

Expected:

```text
status = approved
transactions_created = 5
raw_text_deleted = true
```

Verify permanent records:

```text
GET /money/transactions
```

The list should contain the manual record plus five imported records.

### 25.7 Test cancellation with a second batch

Create:

```json
{
  "text": "Paid 100 for tea today; Uber 200 yesterday",
  "default_currency": "INR"
}
```

Then:

```text
POST /money/imports/{second_real_batch_id}/cancel
```

Expected:

- status `cancelled`
- raw text removed
- drafts removed
- no permanent transactions created

## 26. Required Day 12 negative/security tests

1. Text containing no amount returns 422.
2. Manual amount zero or negative returns 422.
3. Invalid category/type returns 422.
4. Another user cannot read the first user's batch; returns 404.
5. Another user cannot edit the first user's draft; returns 404.
6. Another user cannot approve the first user's batch; returns 404.
7. An approved batch cannot be approved twice; returns 409.
8. An approved draft cannot be changed; returns 409.
9. A cancelled batch creates no transactions.
10. Default approval no longer retains raw pasted text.

## 27. Day 12 completion state

Completed and confirmed by the user. The manual, pasted-text, correction,
approval, raw-text deletion, cancellation and ownership workflow is accepted as
the stable base for Day 13 file imports and analytics.

### Duplicate-entry behavior at the Day 12 boundary

Day 12 intentionally allows a separately created batch to contain values that
match an earlier approved batch. Two genuine transactions can have the same
date, amount and description, so a database uniqueness constraint would risk
deleting valid financial history.

At this stage, approving a second identical batch can therefore create separate
transactions with different transaction and batch IDs. Day 13 adds safer
behavior: likely duplicates are flagged for review, approval is blocked by
default, and the user must either delete/correct the draft or explicitly confirm
that the matching transaction is genuine.

---

# Combined Environment and Validation

## 28. Dependency

```powershell
uv add python-dateutil
```

It is used for flexible explicit date parsing. No paid service is involved.

## 29. Final migration commands

From the backend directory:

```powershell
uv run alembic current
uv run alembic history
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Expected:

```text
20260908_08 (head)
No new upgrade operations detected.
```

## 30. Start command

```powershell
uv run uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Expected API version:

```text
0.8.0
```

## 31. Validation completed before delivery

- Python compilation
- SQLAlchemy mapper configuration
- FastAPI OpenAPI schema generation
- migration-chain inspection
- transaction parser with five expected records
- correct example dates/amounts/types/categories
- skipped-line warning
- short-content quiz generation
- long-content five-question generation
- four options per question
- Learn discovery/readiness route registration
- ZIP integrity

These development checks do not replace testing against the user's actual
Windows/PostgreSQL environment.

## 32. Files added/updated

```text
backend/alembic/versions/20260907_07_add_nexus_learn.py
backend/alembic/versions/20260908_08_add_nexus_money_manual_imports.py
backend/app/models.py
backend/app/main.py
backend/app/learn_schemas.py
backend/app/money_schemas.py
backend/app/routers/learn.py
backend/app/routers/money.py
backend/app/services/quiz_generation.py
backend/app/services/transaction_parser.py
```

## 33. Security/privacy summary

- JWT identifies the current owner.
- Every goal/topic/question/attempt query applies ownership.
- Knowledge sources must belong to the same user.
- Correct quiz answers remain hidden before an attempt.
- Money uses user-supplied information only.
- Parsed transactions remain drafts until approval.
- Raw pasted text is deleted by default after approval/cancellation.
- Another user's IDs do not grant access.
- No bank/SMS/payment-app permission exists.

## 34. Git checkpoint after Day 12

```powershell
git status
git check-ignore backend/.env
git add .
git status
```

Verify that `.env`, JWT tokens, runtime uploads and private transaction text are
not staged.

Commit:

```powershell
git commit -m "feat: add learn tracking and money text imports"
git push
```

## 35. Completion gate for Days 13–14

This gate has passed:

```text
Alembic current: 20260908_08 (head)
Alembic check: No new upgrade operations detected
Day 11 Learn recovery: passed
Manual Money transaction: passed
Pasted-text five-draft parsing: passed
Draft correction: passed
Batch approval: passed
Raw text deletion: passed
Cancellation: passed
Cross-user Money ownership: passed
```

Day 13 can now safely reuse the Day 12 batches/drafts/approval workflow for PDF,
XLSX and CSV Money imports.

## 36. Next block after the gate

```text
Day 13 — Money PDF/XLSX/CSV imports, category analytics and totals
Day 14 — Work projects/tasks, document-to-work-plan extraction and estimates
```
