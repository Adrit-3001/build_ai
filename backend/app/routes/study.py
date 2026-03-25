from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, SMART_MODE
from app.schemas import (
    StudyRequest,
    StudyResponse,
    SavedDocument,
    ProcessSavedDocumentRequest,
    SessionRequest,
    SavedDocumentSessionRequest,
    StudySession,
    Flashcard,
    MultipleChoiceQuestion,
    KeyTerm,
    StudyGuideSection,
)
from app.storage import DOCUMENT_STORE
from app.utils.file_parser import extract_text
from app.utils.text_tools import clean_text, summarize_text, simplify_text, adapt_for_learner
from app.utils.study_tools import (
    generate_flashcards,
    generate_quiz,
    extract_key_terms,
    build_study_guide,
)
from app.utils.session_tools import build_session
from app.utils.llm_tools import smart_generate

router = APIRouter(prefix="/study", tags=["study"])


def safe_study_response(
    cleaned: str,
    mode: str,
    learner_type: str,
    result: str,
    flashcards=None,
    quiz=None,
    key_terms=None,
    study_guide=None,
    session=None,
) -> StudyResponse:
    validated_flashcards = None
    validated_quiz = None
    validated_key_terms = None
    validated_study_guide = None
    validated_session = None

    if flashcards is not None:
        validated_flashcards = [Flashcard(**item) if isinstance(item, dict) else item for item in flashcards]

    if quiz is not None:
        validated_quiz = [MultipleChoiceQuestion(**item) if isinstance(item, dict) else item for item in quiz]

    if key_terms is not None:
        validated_key_terms = [KeyTerm(**item) if isinstance(item, dict) else item for item in key_terms]

    if study_guide is not None:
        validated_study_guide = [StudyGuideSection(**item) if isinstance(item, dict) else item for item in study_guide]

    if session is not None:
        validated_session = StudySession(**session) if isinstance(session, dict) else session

    return StudyResponse(
        original_length=len(cleaned),
        extracted_text_preview=cleaned[:300],
        mode=mode,
        learner_type=learner_type,
        result=result,
        flashcards=validated_flashcards,
        quiz=validated_quiz,
        key_terms=validated_key_terms,
        study_guide=validated_study_guide,
        session=validated_session,
    )


def fallback_response(
    cleaned: str,
    mode: str,
    difficulty: str,
    learner_type: str,
    estimated_minutes: int = 5,
) -> StudyResponse:
    flashcards = None
    quiz = None
    key_terms = None
    study_guide = None
    session = None

    if mode == "summary":
        base = summarize_text(cleaned)
        result = adapt_for_learner(base, learner_type, difficulty)
    elif mode == "simplified":
        result = simplify_text(cleaned, difficulty, learner_type)
    elif mode == "flashcards":
        flashcards = generate_flashcards(cleaned)
        result = "Flashcards generated successfully."
    elif mode == "quiz":
        quiz = generate_quiz(cleaned)
        result = "Quiz generated successfully."
    elif mode == "key_terms":
        key_terms = extract_key_terms(cleaned)
        result = "Key terms extracted successfully."
    elif mode == "study_guide":
        study_guide = build_study_guide(cleaned)
        result = "Study guide generated successfully."
    elif mode == "session":
        session = build_session(
            text=cleaned,
            learner_type=learner_type,
            difficulty=difficulty,
            estimated_minutes=estimated_minutes,
        )
        result = "Study session generated successfully."
    else:
        raise HTTPException(status_code=400, detail="Unsupported mode.")

    return safe_study_response(
        cleaned=cleaned,
        mode=mode,
        learner_type=learner_type,
        result=result,
        flashcards=flashcards,
        quiz=quiz,
        key_terms=key_terms,
        study_guide=study_guide,
        session=session,
    )


def build_response(
    cleaned: str,
    mode: str,
    difficulty: str,
    learner_type: str,
    estimated_minutes: int = 5,
) -> StudyResponse:
    if SMART_MODE == "ollama":
        smart = smart_generate(
            text=cleaned,
            mode=mode,
            learner_type=learner_type,
            difficulty=difficulty,
            estimated_minutes=estimated_minutes,
        )

        if smart is not None:
            try:
                smart_result = smart.get("result", "")
                if mode in {"summary", "simplified"} and (not isinstance(smart_result, str) or not smart_result.strip()):
                    raise ValueError("Empty smart result for summary/simplified.")

                return safe_study_response(
                    cleaned=cleaned,
                    mode=mode,
                    learner_type=learner_type,
                    result=smart_result if isinstance(smart_result, str) and smart_result.strip() else f"{mode} generated successfully.",
                    flashcards=smart.get("flashcards"),
                    quiz=smart.get("quiz"),
                    key_terms=smart.get("key_terms"),
                    study_guide=smart.get("study_guide"),
                    session=smart.get("session"),
                )
            except Exception as e:
                print(f"[SMART_RESPONSE_VALIDATION_ERROR] {type(e).__name__}: {e}")
                print("[SMART_RESPONSE_FALLBACK] Falling back to heuristic pipeline.")

    return fallback_response(
        cleaned=cleaned,
        mode=mode,
        difficulty=difficulty,
        learner_type=learner_type,
        estimated_minutes=estimated_minutes,
    )


@router.post("/process-text", response_model=StudyResponse)
def process_text(payload: StudyRequest):
    cleaned = clean_text(payload.text)

    if not cleaned:
        raise HTTPException(status_code=400, detail="Text is empty after cleaning.")

    return build_response(
        cleaned=cleaned,
        mode=payload.mode,
        difficulty=payload.difficulty,
        learner_type=payload.learner_type,
        estimated_minutes=5,
    )


@router.post("/upload-and-process", response_model=StudyResponse)
async def upload_and_process(
    file: UploadFile = File(...),
    mode: str = "summary",
    difficulty: str = "medium",
    learner_type: str = "general",
):
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    save_name = f"{uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / save_name

    contents = await file.read()
    save_path.write_bytes(contents)

    try:
        extracted = extract_text(save_path)
        cleaned = clean_text(extracted)

        if not cleaned:
            raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

        return build_response(
            cleaned=cleaned,
            mode=mode,
            difficulty=difficulty,
            learner_type=learner_type,
            estimated_minutes=5,
        )

    finally:
        if save_path.exists():
            save_path.unlink(missing_ok=True)


@router.post("/documents", response_model=SavedDocument)
async def create_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    save_name = f"{uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / save_name

    contents = await file.read()
    save_path.write_bytes(contents)

    try:
        extracted = extract_text(save_path)
        cleaned = clean_text(extracted)

        if not cleaned:
            raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

        document_id = uuid4().hex
        DOCUMENT_STORE[document_id] = {
            "filename": file.filename,
            "text": cleaned,
        }

        return SavedDocument(
            document_id=document_id,
            filename=file.filename,
            extracted_text_preview=cleaned[:300],
            original_length=len(cleaned),
        )

    finally:
        if save_path.exists():
            save_path.unlink(missing_ok=True)


@router.get("/documents")
def list_documents():
    return {
        "count": len(DOCUMENT_STORE),
        "documents": [
            {
                "document_id": doc_id,
                "filename": doc["filename"],
                "extracted_text_preview": doc["text"][:150],
                "original_length": len(doc["text"]),
            }
            for doc_id, doc in DOCUMENT_STORE.items()
        ]
    }


@router.get("/documents/{document_id}", response_model=SavedDocument)
def get_document(document_id: str):
    doc = DOCUMENT_STORE.get(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return SavedDocument(
        document_id=document_id,
        filename=doc["filename"],
        extracted_text_preview=doc["text"][:300],
        original_length=len(doc["text"]),
    )


@router.post("/documents/{document_id}/process", response_model=StudyResponse)
def process_saved_document(document_id: str, payload: ProcessSavedDocumentRequest):
    doc = DOCUMENT_STORE.get(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    cleaned = doc["text"]

    return build_response(
        cleaned=cleaned,
        mode=payload.mode,
        difficulty=payload.difficulty,
        learner_type=payload.learner_type,
        estimated_minutes=5,
    )


@router.post("/session", response_model=StudyResponse)
def create_session(payload: SessionRequest):
    cleaned = clean_text(payload.text)

    if not cleaned:
        raise HTTPException(status_code=400, detail="Text is empty after cleaning.")

    return build_response(
        cleaned=cleaned,
        mode="session",
        difficulty=payload.difficulty,
        learner_type=payload.learner_type,
        estimated_minutes=payload.estimated_minutes,
    )


@router.post("/documents/{document_id}/session", response_model=StudyResponse)
def create_session_from_document(document_id: str, payload: SavedDocumentSessionRequest):
    doc = DOCUMENT_STORE.get(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    cleaned = doc["text"]

    return build_response(
        cleaned=cleaned,
        mode="session",
        difficulty=payload.difficulty,
        learner_type=payload.learner_type,
        estimated_minutes=payload.estimated_minutes,
    )


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Document not found.")

    deleted = DOCUMENT_STORE.pop(document_id)

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "filename": deleted["filename"],
    }