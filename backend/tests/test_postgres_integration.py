import os
import unittest
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base, DATABASE_URL, DB_NAME
from app.models import KnowledgeDocument, User, UserProfile
from app.routers.notifications import delete_notification, list_notifications, mark_notification_read
from app.routers.work import owned_project
from app.services.intelligence import cross_module_search
from app.services.notifications import sync_notifications, unread_count
from app.work_schemas import WorkProjectCreate, WorkTaskCreate
from app.routers.work import create_project, create_task


TEST_DB_NAME = os.getenv("TEST_DB_NAME", "")


@unittest.skipUnless(TEST_DB_NAME, "Set TEST_DB_NAME to run dedicated PostgreSQL integration tests")
class PostgreSQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TEST_DB_NAME == DB_NAME or "test" not in TEST_DB_NAME.lower():
            raise RuntimeError("TEST_DB_NAME must differ from DB_NAME and contain the word 'test'")
        cls.engine = create_engine(DATABASE_URL.set(database=TEST_DB_NAME), echo=False)
        Base.metadata.drop_all(cls.engine)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.db = Session(self.engine, expire_on_commit=False)
        self.user_a = User(name="Owner A", email="owner-a@nexus.test", age=30, is_active=True, profile=UserProfile())
        self.user_b = User(name="Owner B", email="owner-b@nexus.test", age=31, is_active=True, profile=UserProfile())
        self.db.add_all([self.user_a, self.user_b]); self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_representative_work_notification_and_ownership_flow(self):
        project = create_project(WorkProjectCreate(title="Private launch"), db=self.db, current_user=self.user_a)
        create_task(project.id, WorkTaskCreate(
            title="Review launch", due_date=date.today()-timedelta(days=1),
            estimated_minutes_low=30, estimated_minutes_high=60,
        ), db=self.db, current_user=self.user_a)
        self.assertEqual(sync_notifications(self.db, self.user_a), 1)
        self.assertEqual(sync_notifications(self.db, self.user_a), 0)
        self.assertEqual(unread_count(self.db, self.user_a.id), 1)
        items = list_notifications(False, 30, db=self.db, current_user=self.user_a)
        self.assertEqual(items[0].kind, "task_overdue")
        with self.assertRaises(HTTPException) as context:
            mark_notification_read(items[0].id, db=self.db, current_user=self.user_b)
        self.assertEqual(context.exception.status_code, 404)
        mark_notification_read(items[0].id, db=self.db, current_user=self.user_a)
        self.assertEqual(unread_count(self.db, self.user_a.id), 0)
        delete_notification(items[0].id, db=self.db, current_user=self.user_a)
        with self.assertRaises(HTTPException):
            owned_project(project.id, self.user_b.id, self.db)

    def test_search_returns_only_owned_records(self):
        self.db.add_all([
            KnowledgeDocument(user_id=self.user_a.id, title="Atlas notes", extracted_text="Private owner A content", extraction_method="test"),
            KnowledgeDocument(user_id=self.user_b.id, title="Atlas secret", extracted_text="Private owner B content", extraction_method="test"),
        ]); self.db.commit()
        result = cross_module_search(self.db, self.user_a.id, "Atlas")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["results"][0]["title"], "Atlas notes")


if __name__ == "__main__":
    unittest.main()
