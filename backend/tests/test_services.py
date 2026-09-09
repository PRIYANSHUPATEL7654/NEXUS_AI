import json
import unittest
from datetime import date
from pathlib import Path

from app.services.intelligence import TOOL_REGISTRY, infer_intent
from app.services.quiz_generation import generate_quiz, quiz_readiness
from app.services.summarization import summarize_text
from app.services.transaction_parser import parse_transaction_text
from app.services.work_plan_parser import parse_work_plan


FIXTURES = Path(__file__).parent / "fixtures"


class ServiceTests(unittest.TestCase):
    def test_transaction_parser_fixtures(self):
        samples = json.loads((FIXTURES / "transaction_samples.json").read_text(encoding="utf-8"))
        for sample in samples:
            with self.subTest(sample=sample["name"]):
                result = parse_transaction_text(sample["text"], date.fromisoformat(sample["today"]))
                expected = sample["expected"]
                self.assertEqual(len(result.transactions), expected["count"])
                item = result.transactions[0]
                self.assertEqual(str(item.amount), expected["amount"])
                self.assertEqual(item.transaction_type, expected["type"])
                self.assertEqual(item.category, expected["category"])
                if "date" in expected:
                    self.assertEqual(item.transaction_date.isoformat(), expected["date"])
                if "warning_count" in expected:
                    self.assertEqual(len(result.warnings), expected["warning_count"])

    def test_work_plan_parser_fixtures(self):
        samples = json.loads((FIXTURES / "work_plan_samples.json").read_text(encoding="utf-8"))
        for sample in samples:
            with self.subTest(sample=sample["name"]):
                result = parse_work_plan(sample["text"])
                self.assertEqual(result.project_title, sample["expected"]["title"])
                self.assertEqual(len(result.tasks), sample["expected"]["task_count"])
                self.assertEqual(result.tasks[0].due_date.isoformat(), sample["expected"]["first_due_date"])

    def test_summary_and_quiz_outputs(self):
        text = (
            "PostgreSQL stores relational data with transactional guarantees. "
            "SQLAlchemy maps Python classes to relational database tables. "
            "FastAPI validates request data with Pydantic schemas. "
            "Alembic records ordered database schema migrations. "
            "React renders component state into accessible user interfaces."
        )
        self.assertTrue(quiz_readiness(text).ready)
        questions = generate_quiz(text, 3)
        self.assertGreaterEqual(len(questions), 1)
        self.assertTrue(all(len(item.options) == 4 for item in questions))
        self.assertTrue(summarize_text(text, "short").startswith("Short Summary"))
        self.assertTrue(summarize_text(text, "revision_notes").startswith("Revision Notes"))

    def test_intelligence_intent_fixtures_and_registry(self):
        samples = json.loads((FIXTURES / "intelligence_intents.json").read_text(encoding="utf-8"))
        for sample in samples:
            with self.subTest(message=sample["message"]):
                self.assertEqual(infer_intent(sample["message"]), sample["intent"])
        self.assertEqual(len(TOOL_REGISTRY), 8)
        self.assertTrue(all(details.get("description") for details in TOOL_REGISTRY.values()))


if __name__ == "__main__":
    unittest.main()
