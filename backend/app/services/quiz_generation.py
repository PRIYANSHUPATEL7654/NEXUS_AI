import hashlib
import random
import re
from collections import Counter
from dataclasses import dataclass


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z-]{3,}\b")
STOP_WORDS = {
    "about", "after", "again", "also", "because", "before", "being",
    "between", "could", "every", "first", "from", "have", "into", "more",
    "other", "should", "their", "there", "these", "they", "this", "through",
    "using", "which", "while", "with", "would", "your",
}


class QuizGenerationError(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedQuestion:
    question: str
    options: list[str]
    correct_option_index: int
    explanation: str


@dataclass(frozen=True)
class QuizReadiness:
    ready: bool
    character_count: int
    sentence_count: int
    keyword_count: int
    reason: str


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"---\s*Page\s+\d+\s*---", " ", text, flags=re.IGNORECASE)
    raw_parts = [part.strip(" -•\t") for part in SENTENCE_SPLIT.split(cleaned)]
    sentences: list[str] = []
    for part in raw_parts:
        if len(part) < 25:
            continue
        if len(part) <= 600:
            sentences.append(part)
            continue

        words = part.split()
        for start in range(0, len(words), 60):
            chunk = " ".join(words[start:start + 60]).strip()
            if len(chunk) >= 25:
                sentences.append(chunk)
    return sentences


def _keywords(text: str) -> list[str]:
    words = [word for word in WORD_PATTERN.findall(text) if word.lower() not in STOP_WORDS]
    counts = Counter(word.lower() for word in words)
    display: dict[str, str] = {}
    for word in words:
        display.setdefault(word.lower(), word)
    return [display[word] for word, _ in counts.most_common(80)]


def quiz_readiness(text: str) -> QuizReadiness:
    sentences = _sentences(text)
    keywords = _keywords(text)
    ready = bool(sentences) and len(keywords) >= 4
    if not sentences:
        reason = "No sentence with at least 25 readable characters was found."
    elif len(keywords) < 4:
        reason = (
            "At least four meaningful words are required to create one answer "
            "and three distractors."
        )
    else:
        reason = "The document is ready for local quiz generation."
    return QuizReadiness(
        ready=ready,
        character_count=len(text.strip()),
        sentence_count=len(sentences),
        keyword_count=len(keywords),
        reason=reason,
    )


def generate_quiz(text: str, question_count: int) -> list[GeneratedQuestion]:
    """Generate deterministic cloze questions from an owned Knowledge document."""
    sentences = _sentences(text)
    keywords = _keywords(text)
    readiness = quiz_readiness(text)
    if not readiness.ready:
        raise QuizGenerationError(
            f"Knowledge document is not quiz-ready: {readiness.reason} "
            f"Characters={readiness.character_count}, "
            f"sentences={readiness.sentence_count}, "
            f"keywords={readiness.keyword_count}."
        )

    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    used_answers: set[str] = set()

    for sentence in sentences:
        candidates = [word for word in keywords if word.lower() in sentence.lower() and word.lower() not in used_answers]
        if not candidates:
            continue
        for answer in sorted(candidates, key=len, reverse=True):
            distractors = [word for word in keywords if word.lower() != answer.lower()]
            rng.shuffle(distractors)
            selected_distractors = []
            for word in distractors:
                if word.lower() not in {item.lower() for item in selected_distractors}:
                    selected_distractors.append(word)
                if len(selected_distractors) == 3:
                    break
            if len(selected_distractors) < 3:
                continue

            blanked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1, flags=re.IGNORECASE)
            options = selected_distractors + [answer]
            rng.shuffle(options)
            correct_index = next(index for index, option in enumerate(options) if option.lower() == answer.lower())
            questions.append(GeneratedQuestion(
                question=f"Complete the statement: {blanked}",
                options=options,
                correct_option_index=correct_index,
                explanation=f'The source document states: "{sentence}"',
            ))
            used_answers.add(answer.lower())
            if len(questions) >= question_count:
                return questions

    if not questions:
        raise QuizGenerationError("No reliable quiz questions could be generated from this document")
    return questions
