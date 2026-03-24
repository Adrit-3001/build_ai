import requests


BACKEND_URL = "http://127.0.0.1:8000"


def check_backend():
    response = requests.get(f"{BACKEND_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()


def upload_document(file_obj):
    files = {
        "file": (file_obj.name, file_obj.getvalue(), file_obj.type)
    }
    response = requests.post(f"{BACKEND_URL}/study/documents", files=files, timeout=60)
    response.raise_for_status()
    return response.json()


def create_session_from_document(document_id, learner_type, difficulty, estimated_minutes):
    payload = {
        "learner_type": learner_type,
        "difficulty": difficulty,
        "estimated_minutes": estimated_minutes
    }
    response = requests.post(
        f"{BACKEND_URL}/study/documents/{document_id}/session",
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def process_document_mode(document_id, mode, learner_type, difficulty):
    payload = {
        "mode": mode,
        "learner_type": learner_type,
        "difficulty": difficulty
    }
    response = requests.post(
        f"{BACKEND_URL}/study/documents/{document_id}/process",
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    return response.json()