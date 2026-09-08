# NEXUS AI — Days 9–10: Document Extraction, Knowledge Summaries and PDF Export

## Document information

| Item | Value |
| --- | --- |
| Project | NEXUS AI |
| Development block | Days 9–10 |
| Main areas | Nexus Core imports and Nexus Knowledge |
| Backend | Python and FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT bearer token |
| OCR | Tesseract through `pytesseract` |
| Summary approach | Local extractive NLP baseline |
| PDF generation | ReportLab |
| Completion status | Completed and tested |
| Final migration revision | `20260906_06 (head)` |
| Important correction | PDF timestamps use the user's profile timezone |

---

## 1. Purpose of this block

Days 1–8 gave NEXUS AI shared authentication, user profiles, PostgreSQL data,
Alembic migrations and safe user-owned file storage. A stored file was still
passive: the application could download it, but it could not understand it.

Days 9–10 created the first complete document intelligence workflow:

```text
Authenticated user
        ↓
Upload controlled file
        ↓
Create shared import job
        ↓
Extract text or perform OCR
        ↓
Review extracted content
        ↓
Approve into Nexus Knowledge
        ↓
Generate and store a summary
        ↓
Download summary as PDF
```

The implementation remains free-tier-first. It does not require an LLM API,
paid OCR API, paid worker or paid file-processing service.

---

# Day 9 — Shared Import Jobs and Document Extraction

## 2. Why extraction is a shared platform service

Knowledge, Money and Work all need to understand user-supplied content:

- Knowledge needs document text for summaries, search and later RAG.
- Money needs statement/message text for proposed transactions.
- Work needs assigned-document text for tasks and time estimates.

Creating three independent extractors would duplicate format handling, OCR,
failure states, security and ownership checks. Day 9 therefore introduced the
shared `import_jobs` table and extraction services in Nexus Core.

## 3. Supported formats

| Format | Extraction method | Initial use |
| --- | --- | --- |
| Digital PDF | `pypdf` text layer | Knowledge, Money, Work |
| Scanned PDF page | `pypdfium2` rendering + Tesseract OCR | Knowledge, Money, Work |
| PNG/JPG/JPEG | Pillow + Tesseract OCR | Scans and screenshots |
| DOCX | `python-docx` paragraphs and tables | Knowledge and Work |
| XLSX | `openpyxl` read-only/data-only mode | Money, Work and structured notes |
| CSV | Python `csv` parser | Money and structured imports |
| TXT | UTF-8 text reader | All modules |
| Markdown | UTF-8 Markdown reader | Knowledge notes |

PPTX remains after the September 22 MVP. Old binary Office formats `.doc` and
`.xls` are intentionally unsupported.

## 4. Digital PDF versus scanned PDF

A digital PDF usually contains a selectable text layer. `pypdf` can retrieve
that text directly.

A scanned PDF may contain only page images:

```text
Visible letters to a human
        ≠
Actual encoded PDF text
```

When a PDF page has too little native text, the service:

1. renders the page with `pypdfium2`
2. converts the rendered page to a Pillow image
3. passes it to Tesseract OCR
4. stores the OCR result with a warning showing which pages used OCR

This creates a hybrid extractor: fast native extraction where possible and OCR
only where required.

## 5. Why OCR output requires review

OCR can misread:

- `I` as `1`
- `O` as `0`
- `AI` as `Al`
- punctuation
- poorly scanned numbers
- rotated, handwritten or low-contrast text

The application therefore does not silently treat every extraction as trusted.
Successful extraction stops at `awaiting_review` before module approval.

## 6. Tesseract configuration

`pytesseract` is a Python wrapper. The Tesseract executable is installed on the
machine separately.

Windows `.env` example:

```dotenv
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

This is configuration rather than a secret, but the real `.env` remains outside
Git because it also contains secrets.

## 7. Import-job lifecycle

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

Any extraction/parsing error produces:

```text
failed
  ↓
retry
```

The status exists in both the shared file record and its module import job. The
file shows its broad processing state; the import job stores detailed output.

## 8. `import_jobs` table

| Column | Purpose |
| --- | --- |
| `id` | Import-job primary key |
| `user_id` | Authenticated owner |
| `file_id` | Shared source file |
| `target_module` | `knowledge`, `money` or `work` |
| `status` | Processing lifecycle |
| `extraction_method` | Extractor/OCR used |
| `extracted_text` | Extracted content |
| `extracted_item_count` | Pages, rows or logical items |
| `page_count` | PDF/image page count where relevant |
| `warnings` | Nonfatal processing observations |
| `failure_reason` | Safe error explanation |
| `started_at` | Work start time |
| `completed_at` | Extraction completion time |
| `created_at`, `updated_at` | Audit timestamps |

The unique constraint on `file_id + target_module` prevents accidental duplicate
imports into the same module while allowing a shared file to be reused by a
different module later.

## 9. Background processing

`POST /imports` responds with `202 Accepted` and schedules extraction with
FastAPI `BackgroundTasks`.

The worker opens a new `SessionLocal` instead of reusing the request's database
session. Request-scoped dependencies close after the response, so long-running
code must own its session lifecycle.

MVP limitation:

- the task runs inside the API process
- a restart can interrupt it
- it is not distributed across workers

A durable queue such as a separate Redis/Celery/RQ/ARQ worker is intentionally
postponed until deployment or workload proves it is necessary.

## 10. Import endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/imports` | Create and schedule an import |
| GET | `/imports` | List the current user's imports |
| GET | `/imports/{id}` | Read owned import status/metadata |
| GET | `/imports/{id}/text` | Inspect ready extracted text |
| POST | `/imports/{id}/retry` | Retry an owned failed import |

Every query filters both record ID and authenticated user ID. Another user's
record returns 404 rather than revealing that it exists.

## 11. Day 9 migration

File:

```text
backend/alembic/versions/20260906_05_add_import_jobs.py
```

Revision:

```python
revision = "20260906_05"
down_revision = "20260905_04"
```

## 12. Day 9 tests completed

- dependency imports
- migration upgrade
- migration/model agreement
- TXT extraction
- image OCR through a real Tesseract executable
- status progression to `awaiting_review`
- extracted-text retrieval
- failed-job retry rules
- duplicate job conflict
- nonexistent file rejection
- cross-user ownership rejection

---

# Day 10 — Nexus Knowledge Documents, Summaries and PDF Export

## 13. Why Knowledge has its own document record

`files` answers storage questions:

```text
Where is the upload?
Who owns it?
What type and size is it?
```

`import_jobs` answers processing questions:

```text
Was it extracted?
Which method was used?
Did it fail?
What text was obtained?
```

`knowledge_documents` answers product questions:

```text
What is this document called inside my Knowledge library?
Which tags and description should I use?
What approved text should summaries/search/RAG consume?
```

This separation prevents storage infrastructure from becoming coupled to one
product module.

## 14. Approval boundary

An import becomes a Knowledge document only when:

- it belongs to the authenticated user
- its target module is `knowledge`
- its status is `awaiting_review`
- it contains extracted text

On approval:

```text
Import awaiting_review
        ↓
Create knowledge_document
        ↓
Import completed
        ↓
File completed
```

Deleting only the Knowledge document returns its import to `awaiting_review` so
the source can be approved again. It does not delete the shared physical file.

## 15. `knowledge_documents` table

| Column | Purpose |
| --- | --- |
| `id` | Knowledge document ID |
| `user_id` | Owner |
| `file_id` | Optional shared-file link |
| `import_job_id` | Optional import lineage |
| `title` | User-visible title |
| `description` | Optional context |
| `tags` | Flexible JSONB tag array |
| `extracted_text` | Approved document content |
| `extraction_method` | Lineage/debug information |
| `page_count` | Page metadata |
| timestamps | Audit information |

## 16. `knowledge_summaries` table

One document can have multiple summaries. Storing summaries provides history
and allows different modes without overwriting an earlier result.

| Column | Purpose |
| --- | --- |
| `id` | Summary ID |
| `user_id` | Owner |
| `document_id` | Source Knowledge document |
| `summary_type` | Selected output style |
| `content` | Generated summary text |
| `generation_method` | Algorithm/model provenance |
| `created_at` | Generation time |

## 17. Summary types

| Type | Intended use |
| --- | --- |
| `short` | Quick overview |
| `detailed` | Broader understanding |
| `revision_notes` | Bullet-like study revision |
| `key_insights` | Numbered important findings |

## 18. Local extractive summarization

The baseline method is:

```text
local_extractive_v1
```

Algorithm outline:

1. normalize text
2. split it into sentences
3. tokenize words
4. remove common stop words
5. calculate word frequencies
6. score sentences by important-word frequency
7. apply a small position bonus
8. select top-scoring sentences
9. restore original document order
10. format for the requested summary type

For very long documents, sentences are processed in chunks before a final
selection. This avoids letting one section dominate solely because of length.

## 19. Extractive versus abstractive summary

Extractive summary:

- selects original sentences
- is deterministic and local
- has no API cost
- reduces hallucination risk
- may sound less natural

Abstractive/LLM summary:

- rewrites concepts in new language
- can be smoother and more customized
- can hallucinate or omit details
- requires a model and evaluation
- may introduce API/infrastructure cost

The extractive implementation is a functional baseline. An optional foundation
model can be added later without removing the free path.

## 20. Knowledge endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/knowledge/documents/from-import/{job_id}` | Approve import into Knowledge |
| GET | `/knowledge/documents` | List/search owned documents |
| GET | `/knowledge/documents/{id}` | Read an owned document |
| GET | `/knowledge/documents/{id}/text` | Read extracted content |
| DELETE | `/knowledge/documents/{id}` | Remove Knowledge record/summaries |
| POST | `/knowledge/documents/{id}/summaries` | Create summary |
| GET | `/knowledge/documents/{id}/summaries` | List summary history |
| GET | `/knowledge/summaries/{id}` | Read owned summary |
| GET | `/knowledge/summaries/{id}/pdf` | Download owned summary PDF |

## 21. PDF generation

ReportLab creates the PDF in memory. The server does not create another
permanent upload for each download.

The PDF includes:

- NEXUS AI heading
- source document title
- summary type
- localized generation timestamp
- summary content
- reminder to verify important facts against the original

The API streams bytes with:

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename="...-summary.pdf"
```

## 22. Timezone correction

The first version used:

```python
datetime.now(timezone.utc)
```

This displayed a mathematically valid UTC time but did not respect the user's
Day 7 profile preference. For example:

```text
13:11 UTC = 18:41 IST
```

The corrected flow is:

```text
Authenticated user
      ↓
current_user.profile.timezone
      ↓
ZoneInfo("Asia/Kolkata")
      ↓
Generated: 06:41 PM IST (Asia/Kolkata)
```

If a profile timezone is unexpectedly unavailable, PDF generation safely falls
back to UTC. No database migration was needed because the timezone column
already existed.

## 23. Day 10 migration

File:

```text
backend/alembic/versions/20260906_06_add_knowledge_documents.py
```

Revision:

```python
revision = "20260906_06"
down_revision = "20260906_05"
```

## 24. Day 10 tests completed

- Knowledge-only import approval
- PostgreSQL document persistence
- list/detail/text routes
- title search
- all four summary modes
- saved summary history
- local generation-method provenance
- PDF generation and opening
- profile-localized PDF timestamp
- document/summary/PDF cross-user isolation
- duplicate approval conflict
- document deletion behavior

---

# Combined Technical State

## 25. Dependencies added

```powershell
uv add pypdf pypdfium2 python-docx openpyxl pillow pytesseract reportlab
```

No paid service is involved.

## 26. Final migration chain

```text
20260827_01 — initial users
20260902_02 — authentication
20260904_03 — user profiles
20260905_04 — shared files
20260906_05 — shared import jobs
20260906_06 — Knowledge documents and summaries
```

## 27. Important IDs and relationships

```text
User 1 ─── 1 UserProfile
User 1 ─── * StoredFile
User 1 ─── * ImportJob
StoredFile 1 ─── * ImportJob
ImportJob 0..1 ─── 1 KnowledgeDocument
KnowledgeDocument 1 ─── * KnowledgeSummary
```

IDs are database identifiers, not values users are expected to memorize. They
are temporarily visible in Swagger because the backend is being tested before
the frontend exists.

## 28. Security decisions

- All feature routes require an active JWT-authenticated user.
- IDs alone never authorize access.
- Queries combine requested record ID with `current_user.id`.
- Another user's private record returns 404.
- Internal file paths remain private.
- OCR content requires review.
- Raw uploads remain outside Git.
- No LLM key is required for summaries.
- PDF content is generated from owned summary records.
- PDF timestamps use the user's validated profile timezone.

## 29. Known limitations

- FastAPI background tasks are not a durable job queue.
- OCR quality depends on scan quality and Tesseract language data.
- Tables embedded inside arbitrary PDFs are not reconstructed structurally.
- The summarizer selects source sentences rather than rewriting them.
- No embeddings, semantic search or RAG exists yet.
- Local file storage may be ephemeral on some free hosts.
- The Swagger workflow requires copying IDs until the frontend is built.

## 30. Concepts learned

### Backend architecture

- shared service versus module service
- asynchronous response versus background execution
- request-scoped versus worker-owned DB session
- processing-state machine
- retry flow
- review/approval boundary
- data lineage
- one-to-many relationships
- user ownership filtering

### Document processing

- native PDF text
- image-only scanned PDF
- page rendering
- OCR
- DOCX paragraph/table extraction
- spreadsheet read-only parsing
- UTF-8 text handling
- extraction warnings

### NLP and export

- sentence tokenization
- stop words
- word frequency
- sentence scoring
- extractive summarization
- hierarchical summarization
- generation provenance
- in-memory PDF creation
- streamed file response
- timezone-aware timestamps

## 31. Git checkpoint

Run from the project root:

```powershell
git status
git check-ignore backend/.env
git add .
git status
```

Verify that secrets, tokens, runtime uploads and personal documents are not
staged.

Commit:

```powershell
git commit -m "feat: add shared imports and knowledge summaries"
git push
```

## 32. Completion state

Days 9 and 10 are complete and tested. NEXUS AI now understands supported
documents, handles scanned content through OCR, stores approved Knowledge,
creates four types of no-cost summaries and downloads localized summary PDFs.

The next combined block is:

```text
Day 11 — Nexus Learn goals, topics, progress, skill gaps and quizzes
Day 12 — Nexus Money manual/pasted-text transaction review workflow
```

---

# Permanent Reference — Preparing Knowledge for Nexus Learn

## 33. Why this section was added

During the first Nexus Learn quiz test, a very small Knowledge document was
linked to a learning topic. The first quiz-generator version rejected it with a
generic message that the content was too small. Later attempts used assumed
goal/topic IDs and returned 404.

This did not mean PostgreSQL, authentication or Knowledge had failed. It exposed
two workflow requirements:

1. Knowledge content must be checked before quiz generation.
2. IDs must be retrieved from list responses, never guessed.

Days 9–10 remain complete; this section records how their output is safely
consumed by Day 11.

## 34. Required dependency chain

```text
JWT-authenticated user
        ↓
Owned shared file
        ↓
Owned Knowledge import
        ↓
Successful extracted text
        ↓
Approved Knowledge document
        ↓
Learn topic linked to that document
        ↓
Quiz readiness check
        ↓
Quiz generation
```

Profile, Money and Work records are not required to generate a Learn quiz.
Authentication, files, imports and Knowledge are required.

## 35. ID-safe Knowledge lookup

IDs are relational identifiers. Swagger exposes them because it is a backend
test interface, but users are not expected to remember them.

Use:

| Needed value | Retrieve it from |
| --- | --- |
| Current account | `GET /auth/me` |
| Existing file ID | `GET /files` |
| Existing import-job ID | `GET /imports` |
| Knowledge document ID | `GET /knowledge/documents` |
| Knowledge summary ID | `GET /knowledge/documents/{real_document_id}/summaries` |

Never assume that the first record has ID 1. PostgreSQL sequences do not reset
when records are deleted, and ownership filtering makes another user's record
appear as not found.

## 36. Creating a guaranteed Learn source

If no existing Knowledge document is suitable, use a multi-paragraph TXT or
PDF containing several hundred characters and meaningful sentences.

### Upload

```text
POST /files/upload
```

Keep the returned real `file_id`.

### Create import

```text
POST /imports
```

```json
{
  "file_id": 6,
  "target_module": "knowledge"
}
```

Replace 6 with the actual uploaded file ID.

### Poll

```text
GET /imports/{real_import_job_id}
```

Wait for:

```text
awaiting_review
```

### Inspect text

```text
GET /imports/{real_import_job_id}/text
```

Confirm that extracted text is readable and has substantial content.

### Approve into Knowledge

```text
POST /knowledge/documents/from-import/{real_import_job_id}
```

```json
{
  "title": "NEXUS AI Learn Quiz Source",
  "description": "Knowledge source for learning and quiz testing",
  "tags": ["nexus-ai", "learning", "quiz"]
}
```

Keep the returned real Knowledge `id`.

## 37. Interpreting common responses

| Response | Meaning | Correct action |
| --- | --- | --- |
| File upload 409 | Same bytes were already uploaded by this user | Use `GET /files` and retrieve the existing ID |
| Import creation 409 | An import already exists for that file/module | Use `GET /imports` |
| Import status `failed` | Extraction failed | Read `failure_reason`, correct it and use retry |
| Knowledge approval 409 | Import is not ready or was already approved | Inspect import status and `GET /knowledge/documents` |
| Knowledge route 404 | Record absent or owned by another account | Confirm `GET /auth/me`, then list owned records |

The permanent rule is:

```text
List → select actual record → copy returned ID → call dependent endpoint
```

The React PWA later performs this internally so normal users interact with
cards, buttons and dropdowns rather than IDs.
