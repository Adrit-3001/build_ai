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


class KeyTerm(BaseModel):
    term: str
    definition: str


class StudyGuideSection(BaseModel):
    heading: str
    bullets: List[str]


class SessionBlock(BaseModel):
    block_type: str
    title: str
    content: List[str]


class StudySession(BaseModel):
    title: str
    learner_type: str
    difficulty: str
    estimated_minutes: int
    overview: str
    blocks: List[SessionBlock]
    flashcards: List[Flashcard]
    quiz: List[MultipleChoiceQuestion]


class StudyResponse(BaseModel):
    original_length: int
    extracted_text_preview: str
    mode: str
    learner_type: str
    result: str
    flashcards: Optional[List[Flashcard]] = None
    quiz: Optional[List[MultipleChoiceQuestion]] = None
    key_terms: Optional[List[KeyTerm]] = None
    study_guide: Optional[List[StudyGuideSection]] = None
    session: Optional[StudySession] = None


class SavedDocument(BaseModel):
    document_id: str
    filename: str
    extracted_text_preview: str
    original_length: int


class ProcessSavedDocumentRequest(BaseModel):
    mode: str = "summary"
    difficulty: str = "medium"
    learner_type: str = "general"


class SessionRequest(BaseModel):
    text: str
    learner_type: str = "general"
    difficulty: str = "medium"
    estimated_minutes: int = 5


class SavedDocumentSessionRequest(BaseModel):
    learner_type: str = "general"
    difficulty: str = "medium"
    estimated_minutes: int = 5