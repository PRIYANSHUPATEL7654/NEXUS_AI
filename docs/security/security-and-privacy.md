# Security and privacy

## Implemented controls

- Argon2 password hashing through `pwdlib`.
- Signed JWT bearer access tokens with configured expiration.
- Active-user check for protected APIs.
- Owner-filtered SQLAlchemy queries for user records.
- Cross-user lookups return `404` rather than revealing another owner.
- Pydantic request validation and bounded list/upload limits.
- File extension, MIME type and content-signature checks.
- Draft-review-approval boundaries for Money and Work imports.
- Allow-listed read-only Intelligence tools and run auditing.
- Owned, deduplicated in-app notification records.
- Exact production CORS origins.
- HTTPS frontend/API transport supplied by deployment platforms.
- Secrets excluded from Git, containers and frontend build output.
- Static security headers for the PWA host.

## Secret locations

| Secret | Correct location |
| --- | --- |
| Local PostgreSQL password | `backend/.env` only |
| Local JWT secret | `backend/.env` only |
| Docker learning secrets | ignored `deploy/compose.env` |
| Hosted database URL | Render secret environment field |
| Hosted JWT secret | Render secret environment field |
| CI deployment credentials, if later added | GitHub encrypted secrets |

`VITE_API_BASE_URL` is not a secret. It becomes visible in the browser bundle.
Never place a database URL, JWT secret or private token in a `VITE_` variable.

## Financial privacy boundary

NEXUS Money does not request bank, UPI, SMS inbox, payment-app, brokerage or
payment-initiation access. A user must explicitly enter, paste or upload data.
Imported items remain drafts until review and approval.

## AI privacy boundary

Current summaries, quizzes, parsers, estimates, search ranking,
recommendations and intent routing are deterministic local services. No owned
record content is automatically sent to a paid or external model.

## Production checks

- Keep the GitHub repository private.
- Do not use wildcard production CORS.
- Use unique production and local JWT secrets.
- Do not reuse database passwords.
- Review provider access permissions.
- Rotate a secret immediately if it appears in Git history, logs or a
  screenshot.
- Do not upload real financial statements during a public portfolio demo.
- Use a dedicated demonstration account with synthetic data.

## Remaining hardening

Refresh-token rotation, rate limiting, account recovery, email verification,
malware scanning, durable object storage, managed backups, disaster recovery,
advanced monitoring and formal security review remain post-MVP work.
