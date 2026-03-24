import streamlit as st
from requests.exceptions import RequestException

from api import (
    check_backend,
    upload_document,
    create_session_from_document,
    process_document_mode,
)
from components import render_session, render_mode_output


st.set_page_config(
    page_title="Study Buddy",
    page_icon="📘",
    layout="wide"
)


def load_css():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


load_css()

if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "session_data" not in st.session_state:
    st.session_state.session_data = None
if "mode_data" not in st.session_state:
    st.session_state.mode_data = None
if "last_mode" not in st.session_state:
    st.session_state.last_mode = None


st.title("📘 Study Buddy")
st.caption("Turn your notes into a cleaner, more adaptive study experience.")

with st.sidebar:
    st.markdown("## Settings")

    learner_type = st.selectbox(
        "Learner type",
        ["general", "adhd", "dyslexic", "visual", "auditory"],
        index=0
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["easy", "medium", "hard"],
        index=1
    )

    estimated_minutes = st.slider(
        "Session length (minutes)",
        min_value=5,
        max_value=20,
        value=5,
        step=5
    )

    st.markdown("---")
    st.markdown("### Backend status")
    try:
        status = check_backend()
        st.success(f"Connected: {status['status']}")
    except RequestException:
        st.error("Backend not reachable")
        st.stop()

left, right = st.columns([1, 1.3], gap="large")

with left:
    st.markdown("## Upload Notes")
    uploaded_file = st.file_uploader(
        "Upload a PDF, TXT, or image",
        type=["pdf", "txt", "png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        if st.button("Save document"):
            try:
                with st.spinner("Uploading and extracting text..."):
                    result = upload_document(uploaded_file)
                st.session_state.document_id = result["document_id"]
                st.session_state.filename = result["filename"]
                st.session_state.session_data = None
                st.session_state.mode_data = None
                st.session_state.last_mode = None
                st.success(f"Saved: {result['filename']}")
            except RequestException as e:
                st.error(f"Upload failed: {e}")

    if st.session_state.document_id:
        st.markdown("### Current document")
        st.write(st.session_state.filename)
        st.caption(f"Document ID: {st.session_state.document_id}")

        if st.button("Generate study session"):
            try:
                with st.spinner("Building session..."):
                    data = create_session_from_document(
                        st.session_state.document_id,
                        learner_type,
                        difficulty,
                        estimated_minutes
                    )
                st.session_state.session_data = data["session"]
                st.session_state.mode_data = None
                st.session_state.last_mode = "session"
                st.success("Session generated.")
            except RequestException as e:
                st.error(f"Session generation failed: {e}")

        st.markdown("### Quick study modes")
        mode = st.selectbox(
            "Choose a mode",
            ["summary", "simplified", "key_terms", "flashcards", "quiz", "study_guide"]
        )

        if st.button("Run selected mode"):
            try:
                with st.spinner(f"Generating {mode}..."):
                    data = process_document_mode(
                        st.session_state.document_id,
                        mode,
                        learner_type,
                        difficulty
                    )
                st.session_state.mode_data = data
                st.session_state.session_data = None
                st.session_state.last_mode = mode
                st.success(f"{mode.replace('_', ' ').title()} ready.")
            except RequestException as e:
                st.error(f"Mode generation failed: {e}")

with right:
    st.markdown("## Output")

    if st.session_state.last_mode == "session" and st.session_state.session_data:
        render_session(st.session_state.session_data)
    elif st.session_state.mode_data and st.session_state.last_mode:
        render_mode_output(st.session_state.mode_data, st.session_state.last_mode)
    else:
        st.info(
            "Upload notes, save the document, then generate a study session or run a study mode."
        )