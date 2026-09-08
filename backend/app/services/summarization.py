import math
import re
from collections import Counter


SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n{2,}")
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'-]{1,}")

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "can", "could", "did", "do", "does", "for", "from", "had", "has",
    "have", "he", "her", "here", "hers", "him", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "may", "more", "most",
    "not", "of", "on", "or", "our", "ours", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them",
    "then", "there", "these", "they", "this", "those", "to", "too",
    "up", "us", "was", "we", "were", "what", "when", "where", "which",
    "who", "why", "will", "with", "would", "you", "your", "yours",
}

SUMMARY_SENTENCE_TARGETS = {
    "short": 5,
    "detailed": 12,
    "revision_notes": 14,
    "key_insights": 8,
}


class SummarizationError(ValueError):
    """Raised when meaningful summary input is unavailable."""


def _sentences(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))
    return [
        sentence.strip(" \n-•")
        for sentence in SENTENCE_PATTERN.split(normalized)
        if len(sentence.strip()) >= 25
    ]


def _tokens(sentence: str) -> list[str]:
    return [
        word.lower()
        for word in WORD_PATTERN.findall(sentence)
        if word.lower() not in STOP_WORDS
    ]


def _select_sentences(sentences: list[str], target: int) -> list[str]:
    if len(sentences) <= target:
        return sentences

    frequencies = Counter(
        token for sentence in sentences for token in _tokens(sentence)
    )
    if not frequencies:
        return sentences[:target]

    max_frequency = max(frequencies.values())
    normalized_frequencies = {
        word: frequency / max_frequency
        for word, frequency in frequencies.items()
    }

    scored: list[tuple[float, int]] = []
    for index, sentence in enumerate(sentences):
        tokens = _tokens(sentence)
        if not tokens:
            continue
        frequency_score = sum(normalized_frequencies[token] for token in tokens)
        length_penalty = math.sqrt(max(len(tokens), 1))
        position_bonus = 1.15 if index < max(2, len(sentences) // 10) else 1.0
        scored.append(((frequency_score / length_penalty) * position_bonus, index))

    selected_indexes = sorted(
        index for _, index in sorted(scored, reverse=True)[:target]
    )
    return [sentences[index] for index in selected_indexes]


def _hierarchical_selection(sentences: list[str], target: int) -> list[str]:
    if len(sentences) <= 120:
        return _select_sentences(sentences, target)

    candidates: list[str] = []
    for start in range(0, len(sentences), 60):
        chunk = sentences[start:start + 60]
        candidates.extend(_select_sentences(chunk, min(8, len(chunk))))
    return _select_sentences(candidates, target)


def _format_summary(selected: list[str], summary_type: str) -> str:
    if summary_type == "revision_notes":
        return "Revision Notes\n\n" + "\n".join(
            f"• {sentence}" for sentence in selected
        )
    if summary_type == "key_insights":
        return "Key Insights\n\n" + "\n".join(
            f"{index}. {sentence}" for index, sentence in enumerate(selected, start=1)
        )
    heading = "Short Summary" if summary_type == "short" else "Detailed Summary"
    return heading + "\n\n" + " ".join(selected)


def summarize_text(text: str, summary_type: str) -> str:
    """Create a deterministic, no-cost extractive summary."""
    if summary_type not in SUMMARY_SENTENCE_TARGETS:
        raise SummarizationError("Unsupported summary type")

    sentences = _sentences(text)
    if not sentences:
        raise SummarizationError("The document has too little readable text to summarize")

    selected = _hierarchical_selection(
        sentences,
        SUMMARY_SENTENCE_TARGETS[summary_type],
    )
    return _format_summary(selected, summary_type)
