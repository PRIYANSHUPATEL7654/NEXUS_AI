from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, false, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    age: Mapped[int] = mapped_column(nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=false(), nullable=False)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True, uselist=False)
    files: Mapped[list["StoredFile"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    import_jobs: Mapped[list["ImportJob"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    knowledge_summaries: Mapped[list["KnowledgeSummary"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    learning_goals: Mapped[list["LearningGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    learning_topics: Mapped[list["LearningTopic"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    learning_progress_entries: Mapped[list["LearningProgressEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    money_import_batches: Mapped[list["MoneyImportBatch"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    money_transaction_drafts: Mapped[list["MoneyTransactionDraft"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    money_transactions: Mapped[list["MoneyTransaction"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    work_projects: Mapped[list["WorkProject"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    work_tasks: Mapped[list["WorkTask"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    work_plan_imports: Mapped[list["WorkPlanImport"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    work_task_drafts: Mapped[list["WorkTaskDraft"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    intelligence_runs: Mapped[list["IntelligenceRun"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", server_default="UTC", nullable=False)
    preferred_currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    learning_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    privacy_preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    notification_preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")


class StoredFile(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("processing_status IN ('uploaded', 'extracting', 'parsing', 'awaiting_review', 'completed', 'failed')", name="ck_files_processing_status"),
        UniqueConstraint("user_id", "sha256_hash", name="uq_files_user_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(30), default="uploaded", server_default="uploaded", nullable=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="files")
    import_jobs: Mapped[list["ImportJob"]] = relationship(back_populates="file", cascade="all, delete-orphan", passive_deletes=True)
    knowledge_document: Mapped["KnowledgeDocument | None"] = relationship(back_populates="file", uselist=False)


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint("target_module IN ('knowledge', 'money', 'work')", name="ck_import_jobs_target_module"),
        CheckConstraint("status IN ('uploaded', 'extracting', 'parsing', 'awaiting_review', 'completed', 'failed')", name="ck_import_jobs_status"),
        UniqueConstraint("file_id", "target_module", name="uq_import_jobs_file_module"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    target_module: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", server_default="uploaded", nullable=False, index=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_item_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="import_jobs")
    file: Mapped[StoredFile] = relationship(back_populates="import_jobs")
    knowledge_document: Mapped["KnowledgeDocument | None"] = relationship(back_populates="import_job", uselist=False)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"), unique=True, nullable=True)
    import_job_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id", ondelete="SET NULL"), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="knowledge_documents")
    file: Mapped[StoredFile | None] = relationship(back_populates="knowledge_document")
    import_job: Mapped[ImportJob | None] = relationship(back_populates="knowledge_document")
    summaries: Mapped[list["KnowledgeSummary"]] = relationship(back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    learning_topics: Mapped[list["LearningTopic"]] = relationship(back_populates="source_document")


class KnowledgeSummary(Base):
    __tablename__ = "knowledge_summaries"
    __table_args__ = (CheckConstraint("summary_type IN ('short', 'detailed', 'revision_notes', 'key_insights')", name="ck_knowledge_summaries_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generation_method: Mapped[str] = mapped_column(String(50), default="local_extractive_v1", server_default="local_extractive_v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="knowledge_summaries")
    document: Mapped[KnowledgeDocument] = relationship(back_populates="summaries")


class LearningGoal(Base):
    __tablename__ = "learning_goals"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'completed')", name="ck_learning_goals_status"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_learning_goals_priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="learning_goals")
    topics: Mapped[list["LearningTopic"]] = relationship(back_populates="goal", cascade="all, delete-orphan", passive_deletes=True)


class LearningTopic(Base):
    __tablename__ = "learning_topics"
    __table_args__ = (
        CheckConstraint("current_level BETWEEN 0 AND 100", name="ck_learning_topics_current_level"),
        CheckConstraint("target_level BETWEEN 1 AND 100", name="ck_learning_topics_target_level"),
        CheckConstraint("status IN ('not_started', 'in_progress', 'mastered')", name="ck_learning_topics_status"),
        UniqueConstraint("goal_id", "title", name="uq_learning_topics_goal_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("learning_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_level: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, default=80, server_default="80", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="not_started", server_default="not_started", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="learning_topics")
    goal: Mapped[LearningGoal] = relationship(back_populates="topics")
    source_document: Mapped[KnowledgeDocument | None] = relationship(back_populates="learning_topics")
    progress_entries: Mapped[list["LearningProgressEntry"]] = relationship(back_populates="topic", cascade="all, delete-orphan", passive_deletes=True)
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="topic", cascade="all, delete-orphan", passive_deletes=True)


class LearningProgressEntry(Base):
    __tablename__ = "learning_progress_entries"
    __table_args__ = (
        CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_learning_progress_percent"),
        CheckConstraint("study_minutes BETWEEN 0 AND 1440", name="ck_learning_progress_study_minutes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("learning_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    study_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="learning_progress_entries")
    topic: Mapped[LearningTopic] = relationship(back_populates="progress_entries")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (CheckConstraint("correct_option_index BETWEEN 0 AND 3", name="ck_quiz_questions_correct_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("learning_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    generation_method: Mapped[str] = mapped_column(String(50), default="local_cloze_v1", server_default="local_cloze_v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="quiz_questions")
    topic: Mapped[LearningTopic] = relationship(back_populates="quiz_questions")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="question", cascade="all, delete-orphan", passive_deletes=True)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (CheckConstraint("selected_option_index BETWEEN 0 AND 3", name="ck_quiz_attempts_selected_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="quiz_attempts")
    question: Mapped[QuizQuestion] = relationship(back_populates="attempts")


class MoneyImportBatch(Base):
    __tablename__ = "money_import_batches"
    __table_args__ = (
        CheckConstraint("source_type IN ('pasted_text', 'file')", name="ck_money_import_batches_source"),
        CheckConstraint("status IN ('awaiting_review', 'approved', 'cancelled')", name="ck_money_import_batches_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    import_job_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id", ondelete="SET NULL"), unique=True, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="pasted_text", server_default="pasted_text", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="awaiting_review", server_default="awaiting_review", nullable=False, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="money_import_batches")
    drafts: Mapped[list["MoneyTransactionDraft"]] = relationship(back_populates="batch", cascade="all, delete-orphan", passive_deletes=True)
    transactions: Mapped[list["MoneyTransaction"]] = relationship(back_populates="batch")


class MoneyTransactionDraft(Base):
    __tablename__ = "money_transaction_drafts"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_money_drafts_positive_amount"),
        CheckConstraint("transaction_type IN ('expense', 'income')", name="ck_money_drafts_type"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_money_drafts_confidence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("money_import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    source_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    possible_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    duplicate_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("money_transactions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="money_transaction_drafts")
    batch: Mapped[MoneyImportBatch] = relationship(back_populates="drafts")


class MoneyTransaction(Base):
    __tablename__ = "money_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_money_transactions_positive_amount"),
        CheckConstraint("transaction_type IN ('expense', 'income')", name="ck_money_transactions_type"),
        CheckConstraint("source IN ('manual', 'pasted_text', 'file')", name="ck_money_transactions_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("money_import_batches.id", ondelete="SET NULL"), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", server_default="manual", nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="money_transactions")
    batch: Mapped[MoneyImportBatch | None] = relationship(back_populates="transactions")


class WorkProject(Base):
    __tablename__ = "work_projects"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'in_progress', 'blocked', 'completed', 'cancelled')",
            name="ck_work_projects_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned", server_default="planned", nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="work_projects")
    tasks: Mapped[list["WorkTask"]] = relationship(back_populates="project", cascade="all, delete-orphan", passive_deletes=True)
    plan_imports: Mapped[list["WorkPlanImport"]] = relationship(back_populates="project")


class WorkPlanImport(Base):
    __tablename__ = "work_plan_imports"
    __table_args__ = (
        CheckConstraint("status IN ('awaiting_review', 'approved', 'cancelled')", name="ck_work_plan_imports_status"),
        CheckConstraint("estimate_confidence IN ('low', 'medium', 'high')", name="ck_work_plan_imports_confidence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("work_projects.id", ondelete="SET NULL"), nullable=True, index=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    import_job_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id", ondelete="SET NULL"), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="awaiting_review", server_default="awaiting_review", nullable=False, index=True)
    proposed_project_title: Mapped[str] = mapped_column(String(200), nullable=False)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_minutes_low: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes_high: Mapped[int] = mapped_column(Integer, nullable=False)
    estimate_confidence: Mapped[str] = mapped_column(String(10), nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="work_plan_imports")
    project: Mapped[WorkProject | None] = relationship(back_populates="plan_imports")
    drafts: Mapped[list["WorkTaskDraft"]] = relationship(back_populates="plan_import", cascade="all, delete-orphan", passive_deletes=True)
    tasks: Mapped[list["WorkTask"]] = relationship(back_populates="source_plan")


class WorkTask(Base):
    __tablename__ = "work_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('backlog', 'planned', 'in_progress', 'blocked', 'completed', 'cancelled')",
            name="ck_work_tasks_status",
        ),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_work_tasks_priority"),
        CheckConstraint("complexity BETWEEN 1 AND 5", name="ck_work_tasks_complexity"),
        CheckConstraint("estimated_minutes_low > 0", name="ck_work_tasks_estimate_low"),
        CheckConstraint("estimated_minutes_high >= estimated_minutes_low", name="ck_work_tasks_estimate_range"),
        CheckConstraint("actual_minutes IS NULL OR actual_minutes >= 0", name="ck_work_tasks_actual_minutes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("work_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_task_id: Mapped[int | None] = mapped_column(ForeignKey("work_tasks.id", ondelete="SET NULL"), nullable=True)
    source_plan_id: Mapped[int | None] = mapped_column(ForeignKey("work_plan_imports.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned", server_default="planned", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    complexity: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_minutes_low: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes_high: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dependencies: Mapped[list[int]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="work_tasks")
    project: Mapped[WorkProject] = relationship(back_populates="tasks")
    source_plan: Mapped[WorkPlanImport | None] = relationship(back_populates="tasks")
    parent: Mapped["WorkTask | None"] = relationship(remote_side="WorkTask.id", back_populates="subtasks")
    subtasks: Mapped[list["WorkTask"]] = relationship(back_populates="parent")


class WorkTaskDraft(Base):
    __tablename__ = "work_task_drafts"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_work_task_drafts_priority"),
        CheckConstraint("complexity BETWEEN 1 AND 5", name="ck_work_task_drafts_complexity"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_work_task_drafts_confidence"),
        CheckConstraint("estimated_minutes_low > 0", name="ck_work_task_drafts_estimate_low"),
        CheckConstraint("estimated_minutes_high >= estimated_minutes_low", name="ck_work_task_drafts_estimate_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_import_id: Mapped[int] = mapped_column(ForeignKey("work_plan_imports.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    complexity: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_minutes_low: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes_high: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    source_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="work_task_drafts")
    plan_import: Mapped[WorkPlanImport] = relationship(back_populates="drafts")


class IntelligenceRun(Base):
    __tablename__ = "intelligence_runs"
    __table_args__ = (
        CheckConstraint("status IN ('completed', 'failed')", name="ck_intelligence_runs_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tool_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="intelligence_runs")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "module IN ('knowledge', 'learn', 'money', 'work', 'system')",
            name="ck_notifications_module",
        ),
        CheckConstraint(
            "severity IN ('info', 'success', 'warning', 'urgent')",
            name="ck_notifications_severity",
        ),
        UniqueConstraint("user_id", "dedupe_key", name="uq_notifications_user_dedupe"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", server_default="info", nullable=False)
    route: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="notifications")
