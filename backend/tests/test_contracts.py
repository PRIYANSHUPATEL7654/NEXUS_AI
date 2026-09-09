import unittest

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.orm import configure_mappers

from app.main import app
from app.models import Notification


class ContractTests(unittest.TestCase):
    def test_models_openapi_and_migration_head(self):
        configure_mappers()
        self.assertEqual(app.version, "0.12.0")
        self.assertEqual(ScriptDirectory.from_config(Config("alembic.ini")).get_heads(), ["20260912_12"])
        self.assertEqual(
            {column.name for column in Notification.__table__.columns},
            {"id", "user_id", "kind", "module", "title", "message", "severity", "route", "is_read", "dedupe_key", "created_at", "read_at"},
        )

    def test_day_19_routes_are_in_openapi(self):
        paths = app.openapi()["paths"]
        expected = {
            "/profile/me", "/intelligence/search", "/notifications/sync",
            "/notifications", "/notifications/unread-count",
            "/notifications/{notification_id}/read", "/notifications/read-all",
            "/notifications/{notification_id}",
        }
        self.assertTrue(expected.issubset(paths))
        self.assertIn("patch", paths["/profile/me"])
        self.assertIn("get", paths["/intelligence/search"])

    def test_every_frontend_api_operation_matches_openapi(self):
        paths = app.openapi()["paths"]
        operations = {
            ("get", "/health"), ("post", "/auth/login"), ("post", "/auth/register"), ("get", "/auth/me"),
            ("get", "/intelligence/daily-brief"), ("get", "/intelligence/recommendations"),
            ("post", "/intelligence/ask"), ("get", "/intelligence/search"),
            ("get", "/profile/me"), ("patch", "/profile/me"), ("post", "/files/upload"),
            ("post", "/imports"), ("get", "/imports"), ("get", "/imports/{import_job_id}"),
            ("post", "/imports/{import_job_id}/retry"),
            ("get", "/knowledge/documents"), ("get", "/knowledge/documents/{document_id}"),
            ("get", "/knowledge/documents/{document_id}/text"), ("post", "/knowledge/documents/from-import/{import_job_id}"),
            ("delete", "/knowledge/documents/{document_id}"), ("get", "/knowledge/documents/{document_id}/summaries"),
            ("post", "/knowledge/documents/{document_id}/summaries"), ("get", "/knowledge/summaries/{summary_id}/pdf"),
            ("get", "/learn/goals"), ("post", "/learn/goals"), ("patch", "/learn/goals/{goal_id}"),
            ("delete", "/learn/goals/{goal_id}"), ("get", "/learn/topics"), ("post", "/learn/goals/{goal_id}/topics"),
            ("patch", "/learn/topics/{topic_id}"), ("get", "/learn/topics/{topic_id}/progress"),
            ("post", "/learn/topics/{topic_id}/progress"), ("get", "/learn/goals/{goal_id}/skill-gaps"),
            ("get", "/learn/quiz-ready-documents"), ("get", "/learn/topics/{topic_id}/quiz/readiness"),
            ("post", "/learn/topics/{topic_id}/quiz/generate"), ("get", "/learn/topics/{topic_id}/quiz"),
            ("post", "/learn/quiz/questions/{question_id}/answer"), ("get", "/learn/topics/{topic_id}/quiz/score"),
            ("get", "/money/transactions"), ("post", "/money/transactions"), ("delete", "/money/transactions/{transaction_id}"),
            ("post", "/money/imports/pasted-text"), ("post", "/money/imports/from-job/{import_job_id}"),
            ("get", "/money/imports"), ("get", "/money/imports/{batch_id}"),
            ("patch", "/money/imports/drafts/{draft_id}"), ("delete", "/money/imports/drafts/{draft_id}"),
            ("post", "/money/imports/{batch_id}/approve"), ("post", "/money/imports/{batch_id}/cancel"),
            ("get", "/money/analytics/summary"), ("get", "/money/transactions/export.csv"),
            ("get", "/work/dashboard"), ("get", "/work/projects"), ("post", "/work/projects"),
            ("patch", "/work/projects/{project_id}"), ("get", "/work/tasks"), ("post", "/work/projects/{project_id}/tasks"),
            ("patch", "/work/tasks/{task_id}"), ("delete", "/work/tasks/{task_id}"),
            ("get", "/work/projects/{project_id}/estimate"), ("get", "/work/imports"),
            ("get", "/work/imports/{plan_id}"), ("post", "/work/imports/from-job/{import_job_id}"),
            ("patch", "/work/imports/drafts/{draft_id}"), ("delete", "/work/imports/drafts/{draft_id}"),
            ("post", "/work/imports/{plan_id}/approve"), ("post", "/work/imports/{plan_id}/cancel"),
            ("post", "/notifications/sync"), ("get", "/notifications"), ("get", "/notifications/unread-count"),
            ("patch", "/notifications/{notification_id}/read"), ("post", "/notifications/read-all"),
            ("delete", "/notifications/{notification_id}"),
        }
        missing = sorted((method, path) for method, path in operations if path not in paths or method not in paths[path])
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
