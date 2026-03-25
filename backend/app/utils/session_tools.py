from typing import List

from app.schemas import SessionBlock, StudySession
from app.utils.text_tools import summarize_text, adapt_for_learner
from app.utils.study_tools import (
    extract_key_terms,
    generate_flashcards,
    generate_quiz,
    build_study_guide,
)


def session_config(estimated_minutes: int) -> dict:
    if estimated_minutes <= 5:
        return {
            "summary_sentences": 2,
            "key_terms": 2,
            "flashcards": 2,
            "quiz": 2,
        }
    if estimated_minutes <= 10:
        return {
            "summary_sentences": 3,
            "key_terms": 4,
            "flashcards": 3,
            "quiz": 3,
        }
    return {
        "summary_sentences": 4,
        "key_terms": 5,
        "flashcards": 4,
        "quiz": 4,
    }


def learner_title(learner_type: str) -> str:
    mapping = {
        "general": "General Study Plan",
        "adhd": "Focus-Friendly Study Plan",
        "dyslexic": "Readable Study Plan",
        "visual": "Scan-Friendly Study Plan",
        "auditory": "Listen-First Study Plan",
    }
    return mapping.get(learner_type.lower(), "Study Plan")


def adapt_block_content(items: List[str], learner_type: str) -> List[str]:
    learner = learner_type.lower()

    if learner == "adhd":
        return [item if len(item) <= 140 else item[:140].rsplit(" ", 1)[0] + "..." for item in items]

    if learner == "dyslexic":
        simplified = []
        for item in items:
            short = item.replace(";", ".")
            if len(short) > 160:
                short = short[:160].rsplit(" ", 1)[0] + "..."
            simplified.append(short)
        return simplified

    if learner == "visual":
        return [f"• {item}" for item in items]

    if learner == "auditory":
        return [f"Say it like this: {item}" for item in items]

    return items


def build_session(
    text: str,
    learner_type: str = "general",
    difficulty: str = "medium",
    estimated_minutes: int = 5,
) -> StudySession:
    if estimated_minutes <= 0:
        estimated_minutes = 5

    cfg = session_config(estimated_minutes)

    overview_base = summarize_text(text, max_sentences=cfg["summary_sentences"])
    overview = adapt_for_learner(overview_base, learner_type, difficulty)

    key_terms = extract_key_terms(text, max_terms=cfg["key_terms"])
    flashcards = generate_flashcards(text, max_cards=cfg["flashcards"])
    quiz = generate_quiz(text, max_questions=cfg["quiz"])
    guide = build_study_guide(text)

    blocks: List[SessionBlock] = []

    blocks.append(
        SessionBlock(
            block_type="overview",
            title="Quick Overview",
            content=adapt_block_content([overview], learner_type)
        )
    )

    if key_terms:
        blocks.append(
            SessionBlock(
                block_type="key_terms",
                title="Key Terms to Know",
                content=adapt_block_content(
                    [f"{item.term}: {item.definition}" for item in key_terms],
                    learner_type
                )
            )
        )

    if guide:
        review_section = next(
            (section for section in guide if section.heading.lower() == "what to review"),
            None
        )
        if review_section:
            blocks.append(
                SessionBlock(
                    block_type="review",
                    title="Focus Review Points",
                    content=adapt_block_content(review_section.bullets, learner_type)
                )
            )

    if flashcards:
        blocks.append(
            SessionBlock(
                block_type="flashcards",
                title="Practice Flashcards",
                content=adapt_block_content(
                    [card.question for card in flashcards],
                    learner_type
                )
            )
        )

    if quiz:
        blocks.append(
            SessionBlock(
                block_type="quiz",
                title="Quick Check Quiz",
                content=adapt_block_content(
                    [q.question for q in quiz],
                    learner_type
                )
            )
        )

    return StudySession(
        title=f"{estimated_minutes}-Minute {learner_title(learner_type)}",
        learner_type=learner_type,
        difficulty=difficulty,
        estimated_minutes=estimated_minutes,
        overview=overview,
        blocks=blocks,
        flashcards=flashcards,
        quiz=quiz,
    )