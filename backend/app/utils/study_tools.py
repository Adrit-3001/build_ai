import re
from typing import List
from app.schemas import Flashcard, MultipleChoiceQuestion


def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_chunks(text: str) -> List[str]:
    parts = re.split(r'\n+|[•\-]\s+', text)
    cleaned = [p.strip() for p in parts if len(p.strip()) > 25]
    if not cleaned:
        cleaned = split_into_sentences(text)
    return cleaned


def generate_flashcards(text: str, max_cards: int = 5) -> List[Flashcard]:
    chunks = split_into_chunks(text)
    cards: List[Flashcard] = []

    for chunk in chunks[:max_cards]:
        short = chunk.strip()
        if len(short) > 180:
            short = short[:180].rsplit(" ", 1)[0] + "..."

        cards.append(
            Flashcard(
                question="What does this mean?",
                answer=short
            )
        )

    return cards


def generate_quiz(text: str, max_questions: int = 4) -> List[MultipleChoiceQuestion]:
    sentences = split_into_sentences(text)
    quiz: List[MultipleChoiceQuestion] = []

    fallback_options = [
        "It describes a key concept from the notes.",
        "It is unrelated to the topic.",
        "It is only an opinion with no factual basis.",
        "It is a formatting instruction."
    ]

    for sentence in sentences[:max_questions]:
        cleaned = sentence.strip()
        if len(cleaned) < 20:
            continue

        question_text = f"Which option best matches this note?"
        correct = cleaned

        options = [
            correct,
            fallback_options[1],
            fallback_options[2],
            fallback_options[3],
        ]

        quiz.append(
            MultipleChoiceQuestion(
                question=question_text,
                options=options,
                answer=correct
            )
        )

    return quiz