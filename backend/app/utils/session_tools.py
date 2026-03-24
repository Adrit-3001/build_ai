from typing import List

from app.schemas import SessionBlock, StudySession
from app.utils.text_tools import summarize_text, adapt_for_learner
from app.utils.study_tools import (
    extract_key_terms,
    generate_flashcards,
    generate_quiz,
    build_study_guide,
)


def build_session(
    text: str,
    learner_type: str = "general",
    difficulty: str = "medium",
    estimated_minutes: int = 5,
) -> StudySession:
    if estimated_minutes <= 0:
        estimated_minutes = 5

    overview_base = summarize_text(text, max_sentences=3)
    overview = adapt_for_learner(overview_base, learner_type, difficulty)

    key_terms = extract_key_terms(text, max_terms=4)
    flashcards = generate_flashcards(text, max_cards=3)
    quiz = generate_quiz(text, max_questions=3)
    guide = build_study_guide(text)

    blocks: List[SessionBlock] = []

    blocks.append(
        SessionBlock(
            block_type="overview",
            title="Quick Overview",
            content=[overview]
        )
    )

    if key_terms:
        blocks.append(
            SessionBlock(
                block_type="key_terms",
                title="Key Terms to Know",
                content=[f"{item.term}: {item.definition}" for item in key_terms]
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
                    content=review_section.bullets
                )
            )

    if flashcards:
        blocks.append(
            SessionBlock(
                block_type="flashcards",
                title="Practice Flashcards",
                content=[card.question for card in flashcards]
            )
        )

    if quiz:
        blocks.append(
            SessionBlock(
                block_type="quiz",
                title="Quick Check Quiz",
                content=[q.question for q in quiz]
            )
        )

    return StudySession(
        title=f"{estimated_minutes}-Minute Study Session",
        learner_type=learner_type,
        difficulty=difficulty,
        estimated_minutes=estimated_minutes,
        overview=overview,
        blocks=blocks,
        flashcards=flashcards,
        quiz=quiz,
    )