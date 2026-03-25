import requests

BASE_URL = "http://127.0.0.1:8000"


def check_backend():
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()


def upload_document(uploaded_file):
    files = {
        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
    }
    response = requests.post(f"{BASE_URL}/study/documents", files=files, timeout=120)
    response.raise_for_status()
    return response.json()


def create_session_from_document(document_id, learner_type, difficulty, estimated_minutes):
    payload = {
        "learner_type": learner_type,
        "difficulty": difficulty,
        "estimated_minutes": estimated_minutes,
    }
    response = requests.post(
        f"{BASE_URL}/study/documents/{document_id}/session",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def process_document_mode(document_id, mode, learner_type, difficulty):
    payload = {
        "mode": mode,
        "learner_type": learner_type,
        "difficulty": difficulty,
    }
    response = requests.post(
        f"{BASE_URL}/study/documents/{document_id}/process",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def synthesize_speech(text, voice="en-US-AriaNeural", rate="+0%"):
    payload = {
        "text": text,
        "voice": voice,
        "rate": rate,
    }
    response = requests.post(
        f"{BASE_URL}/study/tts",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()
    return response.content