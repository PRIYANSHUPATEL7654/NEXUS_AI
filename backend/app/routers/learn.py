from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..learn_schemas import (
    LearningGoalCreate, LearningGoalResponse, LearningGoalUpdate,
    LearningProgressCreate, LearningProgressResponse, LearningTopicCreate,
    LearningTopicResponse, LearningTopicUpdate, QuizAnswerCreate,
    QuizAnswerResponse, QuizGenerateRequest, QuizQuestionResponse,
    QuizReadyDocumentResponse, QuizScoreResponse, SkillGapResponse,
    TopicQuizReadinessResponse,
)
from ..models import (
    KnowledgeDocument, LearningGoal, LearningProgressEntry, LearningTopic,
    QuizAttempt, QuizQuestion, User,
)
from ..security import get_current_active_user
from ..services.quiz_generation import QuizGenerationError, generate_quiz, quiz_readiness


router = APIRouter(prefix="/learn", tags=["Learn"])


def owned_goal(goal_id: int, user_id: int, db: Session) -> LearningGoal:
    goal = db.scalar(select(LearningGoal).where(LearningGoal.id == goal_id, LearningGoal.user_id == user_id))
    if goal is None:
        raise HTTPException(status_code=404, detail="Learning goal not found")
    return goal


def owned_topic(topic_id: int, user_id: int, db: Session) -> LearningTopic:
    topic = db.scalar(select(LearningTopic).where(LearningTopic.id == topic_id, LearningTopic.user_id == user_id))
    if topic is None:
        raise HTTPException(status_code=404, detail="Learning topic not found")
    return topic


def owned_question(question_id: int, user_id: int, db: Session) -> QuizQuestion:
    question = db.scalar(select(QuizQuestion).where(QuizQuestion.id == question_id, QuizQuestion.user_id == user_id))
    if question is None:
        raise HTTPException(status_code=404, detail="Quiz question not found")
    return question


def validate_owned_document(document_id: int | None, user_id: int, db: Session) -> None:
    if document_id is None:
        return
    exists = db.scalar(select(KnowledgeDocument.id).where(KnowledgeDocument.id == document_id, KnowledgeDocument.user_id == user_id))
    if exists is None:
        raise HTTPException(status_code=404, detail="Source Knowledge document not found")


@router.post("/goals", response_model=LearningGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(payload: LearningGoalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    goal = LearningGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/goals", response_model=list[LearningGoalResponse])
def list_goals(goal_status: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    statement = select(LearningGoal).where(LearningGoal.user_id == current_user.id)
    if goal_status:
        if goal_status not in {"active", "paused", "completed"}:
            raise HTTPException(status_code=422, detail="Invalid goal status")
        statement = statement.where(LearningGoal.status == goal_status)
    return list(db.scalars(statement.order_by(LearningGoal.priority, LearningGoal.created_at.desc())).all())


@router.get("/goals/{goal_id}", response_model=LearningGoalResponse)
def read_goal(goal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return owned_goal(goal_id, current_user.id, db)


@router.patch("/goals/{goal_id}", response_model=LearningGoalResponse)
def update_goal(goal_id: int, payload: LearningGoalUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    goal = owned_goal(goal_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db.delete(owned_goal(goal_id, current_user.id, db))
    db.commit()
    return Response(status_code=204)


@router.post("/goals/{goal_id}/topics", response_model=LearningTopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(goal_id: int, payload: LearningTopicCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_goal(goal_id, current_user.id, db)
    validate_owned_document(payload.source_document_id, current_user.id, db)
    topic_status = "not_started" if payload.current_level == 0 else "in_progress"
    if payload.current_level >= payload.target_level:
        topic_status = "mastered"
    topic = LearningTopic(user_id=current_user.id, goal_id=goal_id, status=topic_status, **payload.model_dump())
    db.add(topic)
    try:
        db.commit()
        db.refresh(topic)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="This goal already has a topic with that title") from error
    return topic


@router.get("/goals/{goal_id}/topics", response_model=list[LearningTopicResponse])
def list_topics(goal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_goal(goal_id, current_user.id, db)
    return list(db.scalars(select(LearningTopic).where(LearningTopic.goal_id == goal_id, LearningTopic.user_id == current_user.id).order_by(LearningTopic.created_at)).all())


@router.get("/topics", response_model=list[LearningTopicResponse])
def list_all_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """List every topic owned by the current user so IDs never need guessing."""
    return list(db.scalars(select(LearningTopic).where(LearningTopic.user_id == current_user.id).order_by(LearningTopic.created_at.desc())).all())


@router.patch("/topics/{topic_id}", response_model=LearningTopicResponse)
def update_topic(topic_id: int, payload: LearningTopicUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    topic = owned_topic(topic_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)
    if "source_document_id" in updates:
        validate_owned_document(updates["source_document_id"], current_user.id, db)
    for field, value in updates.items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    return topic


@router.post("/topics/{topic_id}/progress", response_model=LearningProgressResponse, status_code=status.HTTP_201_CREATED)
def record_progress(topic_id: int, payload: LearningProgressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    topic = owned_topic(topic_id, current_user.id, db)
    entry = LearningProgressEntry(user_id=current_user.id, topic_id=topic.id, **payload.model_dump())
    topic.current_level = payload.progress_percent
    topic.status = "mastered" if topic.current_level >= topic.target_level else ("not_started" if topic.current_level == 0 else "in_progress")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/topics/{topic_id}/progress", response_model=list[LearningProgressResponse])
def progress_history(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_topic(topic_id, current_user.id, db)
    return list(db.scalars(select(LearningProgressEntry).where(LearningProgressEntry.topic_id == topic_id, LearningProgressEntry.user_id == current_user.id).order_by(LearningProgressEntry.recorded_at.desc())).all())


@router.get("/goals/{goal_id}/skill-gaps", response_model=list[SkillGapResponse])
def skill_gaps(goal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_goal(goal_id, current_user.id, db)
    topics = db.scalars(select(LearningTopic).where(LearningTopic.goal_id == goal_id, LearningTopic.user_id == current_user.id)).all()
    results = []
    for topic in topics:
        gap = max(0, topic.target_level - topic.current_level)
        action = "Maintain with periodic revision" if gap == 0 else ("Prioritize focused study and a quiz" if gap >= 40 else "Continue practice and review")
        results.append(SkillGapResponse(topic_id=topic.id, topic_title=topic.title, current_level=topic.current_level, target_level=topic.target_level, gap=gap, recommended_action=action))
    return sorted(results, key=lambda item: item.gap, reverse=True)


@router.get("/quiz-ready-documents", response_model=list[QuizReadyDocumentResponse])
def list_quiz_ready_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    documents = db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.user_id == current_user.id).order_by(KnowledgeDocument.created_at.desc())).all()
    results = []
    for document in documents:
        readiness = quiz_readiness(document.extracted_text)
        results.append(QuizReadyDocumentResponse(
            document_id=document.id,
            title=document.title,
            character_count=readiness.character_count,
            sentence_count=readiness.sentence_count,
            keyword_count=readiness.keyword_count,
            quiz_ready=readiness.ready,
            reason=readiness.reason,
        ))
    return results


@router.get("/topics/{topic_id}/quiz/readiness", response_model=TopicQuizReadinessResponse)
def topic_quiz_readiness(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    topic = owned_topic(topic_id, current_user.id, db)
    if topic.source_document is None:
        raise HTTPException(status_code=409, detail="This topic is not linked to a Knowledge document")
    readiness = quiz_readiness(topic.source_document.extracted_text)
    return TopicQuizReadinessResponse(
        topic_id=topic.id,
        topic_title=topic.title,
        document_id=topic.source_document.id,
        title=topic.source_document.title,
        character_count=readiness.character_count,
        sentence_count=readiness.sentence_count,
        keyword_count=readiness.keyword_count,
        quiz_ready=readiness.ready,
        reason=readiness.reason,
    )


@router.post("/topics/{topic_id}/quiz/generate", response_model=list[QuizQuestionResponse], status_code=status.HTTP_201_CREATED)
def create_quiz(topic_id: int, payload: QuizGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    topic = owned_topic(topic_id, current_user.id, db)
    if topic.source_document is None:
        raise HTTPException(status_code=409, detail="Link an owned Knowledge document to this topic before generating a quiz")
    try:
        generated = generate_quiz(topic.source_document.extracted_text, payload.question_count)
    except QuizGenerationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    questions = [QuizQuestion(user_id=current_user.id, topic_id=topic.id, question=item.question, options=item.options, correct_option_index=item.correct_option_index, explanation=item.explanation) for item in generated]
    db.add_all(questions)
    db.commit()
    for question in questions:
        db.refresh(question)
    return questions


@router.get("/topics/{topic_id}/quiz", response_model=list[QuizQuestionResponse])
def list_quiz(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_topic(topic_id, current_user.id, db)
    return list(db.scalars(select(QuizQuestion).where(QuizQuestion.topic_id == topic_id, QuizQuestion.user_id == current_user.id).order_by(QuizQuestion.created_at.desc())).all())


@router.post("/quiz/questions/{question_id}/answer", response_model=QuizAnswerResponse, status_code=status.HTTP_201_CREATED)
def answer_question(question_id: int, payload: QuizAnswerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    question = owned_question(question_id, current_user.id, db)
    is_correct = payload.selected_option_index == question.correct_option_index
    attempt = QuizAttempt(user_id=current_user.id, question_id=question.id, selected_option_index=payload.selected_option_index, is_correct=is_correct)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return QuizAnswerResponse(attempt_id=attempt.id, question_id=question.id, selected_option_index=attempt.selected_option_index, correct_option_index=question.correct_option_index, is_correct=attempt.is_correct, explanation=question.explanation, attempted_at=attempt.attempted_at)


@router.get("/topics/{topic_id}/quiz/score", response_model=QuizScoreResponse)
def quiz_score(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_topic(topic_id, current_user.id, db)
    attempts, correct = db.execute(select(func.count(QuizAttempt.id), func.count(QuizAttempt.id).filter(QuizAttempt.is_correct.is_(True))).join(QuizQuestion).where(QuizQuestion.topic_id == topic_id, QuizAttempt.user_id == current_user.id)).one()
    score = round((correct / attempts) * 100, 2) if attempts else 0.0
    return QuizScoreResponse(topic_id=topic_id, attempts=attempts, correct_answers=correct, score_percent=score)
