from typing import List, Optional
from pydantic import BaseModel


class StudyRequest(BaseModel):
    text: str
    mode: str = "summary"   # summary, simplified, flashcards, quiz
    difficulty: str = "medium"  # easy, medium, hard
    learner_type: str = "general"  # general, visual, auditory, dyslexic, adhd


class Flashcard(BaseModel):
    question: str
    answer: str


class MultipleChoiceQuestion(BaseModel):
    question: str
    options: List[str]
    answer: str


class StudyResponse(BaseModel):
    original_length: int
    extracted_text_preview: str
    mode: str
    learner_type: str
    result: str
    flashcards: Optional[List[Flashcard]] = None
    quiz: Optional[List[MultipleChoiceQuestion]] = None