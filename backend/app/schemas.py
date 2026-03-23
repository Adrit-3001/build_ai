from typing import List, Optional
from pydantic import BaseModel


class StudyRequest(BaseModel):
    text: str
    mode: str = "summary"
    difficulty: str = "medium"
    learner_type: str = "general"


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


class SavedDocument(BaseModel):
    document_id: str
    filename: str
    extracted_text_preview: str
    original_length: int


class ProcessSavedDocumentRequest(BaseModel):
    mode: str = "summary"
    difficulty: str = "medium"
    learner_type: str = "general"