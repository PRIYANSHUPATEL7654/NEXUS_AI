# Day 20 evaluation fixtures and known limits

## Automated coverage

- API version, OpenAPI route, SQLAlchemy mapper and Alembic-head contracts.
- Money text parser fixtures for dated expenses, income and skipped-line warnings.
- Work-plan parser fixtures for task detection, dates and estimates.
- Summary headings and quiz readiness/generation invariants.
- Ask Nexus intent classification and the eight-tool registry.
- Dedicated-PostgreSQL ownership flow for projects, tasks, notifications and search.
- Notification deduplication, read state, deletion and cross-user 404 behavior.
- Frontend authorization headers, API error propagation, search/profile contracts and reusable UI states.
- TypeScript project compilation and Vite production bundling remain release gates.

## Test-data safety

PostgreSQL integration tests run only when `TEST_DB_NAME` is present. The name must contain `test` and must differ from `DB_NAME`. The suite creates and drops application tables in that dedicated database. Never point `TEST_DB_NAME` at a real or production database.

## Known limits

- Notifications are in-app records. Web Push, email, SMS and background OS delivery are intentionally outside this release.
- Notification synchronization currently covers awaiting-review imports, failed imports and overdue work tasks. It runs when the authenticated shell loads or changes module.
- A read notification is not reopened when the same deduplication key is seen again. A genuinely new import state or a different overdue-date key creates a new record.
- Search is PostgreSQL substring matching with deterministic local ranking, not semantic/vector search. Results are capped by the API limit.
- Search result links open the appropriate module workspace; module pages retain selected record IDs internally after their list loads.
- The browser component tests render reusable components on the server and mock `fetch`. Full browser automation remains a later deployment-stage addition.
- Quiz questions and summaries are deterministic local heuristics. Users should verify generated learning material against its source.
- Money and Work parsers intentionally produce reviewable drafts and warnings. They do not silently approve imported records.
