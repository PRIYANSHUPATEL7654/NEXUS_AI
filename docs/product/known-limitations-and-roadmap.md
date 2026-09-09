# Known limitations and post-MVP roadmap

## Accepted MVP limitations

- Free backend/database services may cold-start after idle time.
- Hosted backend file storage is temporary; PostgreSQL metadata can outlive the
  corresponding uploaded bytes after a host replacement or restart.
- Search is substring matching with local ranking, not embeddings/vector RAG.
- Summaries and quizzes are deterministic heuristics and require user review.
- Money parsing supports explicit user input but is not a bank-grade statement
  ingestion engine.
- Work estimates are low/high planning aids, not delivery guarantees.
- Notifications are in-app only and synchronize while the PWA is active.
- Access tokens do not yet use refresh-token rotation.
- The deployment smoke script is unauthenticated; full flows remain part of the
  manual final QA and automated isolated ownership tests.
- PWA offline behavior caches the application shell, not complete private data
  workflows.

## Immediate post-MVP priorities

1. Durable object storage for private uploads and generated exports.
2. Backup, restore and disaster-recovery drills.
3. Refresh tokens, session revocation, email verification and account recovery.
4. Rate limiting, abuse controls and improved security monitoring.
5. Structured production telemetry and alerting.
6. PostgreSQL full-text search, then evaluated vector/RAG retrieval if needed.
7. Optional free/local model integration behind explicit privacy controls.
8. Browser end-to-end automation against an isolated deployment.
9. Web Push only after permission UX, privacy and delivery value are designed.
10. React Native/Expo client after the responsive PWA is stable.

## Longer-term ecosystem

- shared memory with provenance and deletion controls;
- anomaly detection and forecasting for reviewed Money data;
- richer learning paths and career preparation;
- customers, sales and support workflows for Work;
- external tools through least-privilege connectors;
- multimodal document/audio/video processing;
- team/organization roles only after single-user ownership remains reliable.

These items must not be pulled into the September 22, 2026 deadline build at
the cost of deployment stability, privacy or the final test gate.
