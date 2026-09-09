# Final MVP quality-assurance gate

Record the deployed URLs and pass/fail outcome locally. Do not write secrets or
real private data into this document.

## 1. CI and build

- [ ] GitHub `NEXUS CI` is green for the deployed commit.
- [ ] Backend compilation passed.
- [ ] All nine backend tests passed without skips.
- [ ] Alembic upgrade and consistency check passed.
- [ ] Frontend tests and typecheck passed.
- [ ] Frontend production build artifact exists.
- [ ] Backend and frontend container builds passed.

## 2. Platform startup

- [ ] PostgreSQL is reachable only through its protected connection string.
- [ ] Backend startup log shows successful Alembic upgrade.
- [ ] Backend `/health` returns `200` and `{"status":"healthy"}`.
- [ ] Backend `/docs` shows API `0.12.0`.
- [ ] Frontend loads through HTTPS.
- [ ] Browser console has no blocking CORS or mixed-content error.

## 3. Authentication and ownership

- [ ] A new demonstration user can register and sign in.
- [ ] Refreshing keeps the current session until token expiry.
- [ ] Invalid credentials show a safe error.
- [ ] Automated cross-user project, notification and search tests passed.
- [ ] The browser never asks for a raw database ID.

## 4. Knowledge and Learn

- [ ] Upload a synthetic TXT/PDF document.
- [ ] Import reaches awaiting review.
- [ ] Save the document with title and tags.
- [ ] Generate a summary and download its PDF.
- [ ] Create a named learning goal and topic.
- [ ] Link the owned document through the readable picker.
- [ ] Record progress and generate/answer a quiz.

## 5. Money

- [ ] Add a synthetic manual transaction.
- [ ] Parse synthetic pasted text into drafts.
- [ ] Edit and approve the drafts.
- [ ] Verify income/expense totals and category analytics.
- [ ] Export a CSV using synthetic data only.

## 6. Work

- [ ] Create a project and task through readable choices.
- [ ] Update task status and actual minutes.
- [ ] Import a synthetic work plan.
- [ ] Review assumptions, warnings, confidence and estimate range.
- [ ] Approve the plan and verify the project estimate.

## 7. Intelligence and notifications

- [ ] Today brief loads all four module sections.
- [ ] Ask Nexus answers a Money, Work or Learning question.
- [ ] Unified search returns only the signed-in user's records.
- [ ] An awaiting-review import creates a notification.
- [ ] An overdue task creates a notification.
- [ ] Opening/marking notifications updates the unread count.

## 8. Responsive PWA

- [ ] Desktop sidebar works at laptop width.
- [ ] Six-module bottom dock works at phone width.
- [ ] Search and Profile remain available on mobile.
- [ ] Forms do not overflow at 360-430 px widths.
- [ ] Keyboard focus and Skip to main content work.
- [ ] PWA installs from the HTTPS production URL.
- [ ] Home-screen launch uses standalone display.

## 9. Operations

- [ ] Deployment smoke script passes.
- [ ] Backend, database and frontend logs were inspected.
- [ ] One cold-start request was observed and recovered.
- [ ] Rollback procedure was read and the last green commit is identifiable.
- [ ] No payment method, paid plan or automatic billing was enabled.

## Final decision

The MVP is release-ready only when every required checkbox passes or the exact
known limitation is accepted and recorded.
