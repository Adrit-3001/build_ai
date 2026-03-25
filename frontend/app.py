import time
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


def learner_mode_description(learner_type: str) -> str:
    descriptions = {
        "general": "Balanced layout with a standard study flow.",
        "adhd": "Shorter chunks, faster scanning, and clearer focus points.",
        "dyslexic": "Cleaner spacing, simpler reading flow, and reduced density.",
        "visual": "Grouped information for scanning and section-based review.",
        "auditory": "Spoken-style phrasing for listening and verbal review.",
    }
    return descriptions.get(learner_type, "Adaptive study support.")


def apply_theme(theme: str):
    theme_class = f"theme-{theme}"
    st.markdown(
        f"""
        <script>
        const root = window.parent.document.documentElement;
        root.classList.remove('theme-playful', 'theme-classic');
        root.classList.add('{theme_class}');
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="{theme_class}"></div>', unsafe_allow_html=True)


def render_background_fx(theme: str):
    if theme != "playful":
        return

    st.markdown(
        """
        <div class="bg-fx-wrap" aria-hidden="true">
            <div class="bg-orb orb-1"></div>
            <div class="bg-orb orb-2"></div>
            <div class="bg-orb orb-3"></div>
            <div class="bg-shape shape-triangle"></div>
            <div class="bg-shape shape-square"></div>
            <div class="bg-shape shape-ring"></div>
            <div class="bg-dot-grid"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start_time" not in st.session_state:
    st.session_state.timer_start_time = None
if "timer_duration" not in st.session_state:
    st.session_state.timer_duration = 0
if "time_remaining" not in st.session_state:
    st.session_state.time_remaining = 0
if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False


def reset_timer():
    st.session_state.timer_running = False
    st.session_state.timer_start_time = None
    st.session_state.timer_duration = 0
    st.session_state.time_remaining = 0
    st.session_state.timer_paused = False


def start_timer(minutes: int):
    total_seconds = minutes * 60

    if st.session_state.timer_paused and st.session_state.time_remaining > 0:
        st.session_state.timer_duration = st.session_state.time_remaining
        st.session_state.timer_start_time = time.time()
        st.session_state.timer_running = True
        st.session_state.timer_paused = False
        return

    st.session_state.timer_duration = total_seconds
    st.session_state.time_remaining = total_seconds
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True
    st.session_state.timer_paused = False


def pause_timer():
    if not st.session_state.timer_running or st.session_state.timer_start_time is None:
        return

    elapsed = int(time.time() - st.session_state.timer_start_time)
    remaining = st.session_state.timer_duration - elapsed
    st.session_state.time_remaining = max(0, remaining)
    st.session_state.timer_running = False
    st.session_state.timer_paused = True
    st.session_state.timer_start_time = None


with st.sidebar:
    st.markdown("## Settings")

    theme = st.selectbox(
        "Theme",
        ["playful", "classic"],
        index=0
    )

apply_theme(theme)
render_background_fx(theme)

st.title("📘 Study Buddy")
st.caption("Turn your notes into a cleaner, more adaptive study experience.")

with st.sidebar:
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
        min_value=1,
        max_value=30,
        value=5,
        step=1
    )

    st.markdown("### Active learning mode")
    st.info(learner_mode_description(learner_type))

    st.markdown("---")
    st.markdown("### Backend status")
    try:
        status = check_backend()
        st.success(f"Connected: {status['status']}")
    except RequestException:
        st.error("Backend not reachable")
        st.stop()

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.markdown("## Upload Notes")
    uploaded_file = st.file_uploader(
        "Upload a PDF, TXT, or image",
        type=["pdf", "txt", "png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        if st.button("Save document", use_container_width=True):
            try:
                with st.spinner("Uploading and extracting text..."):
                    result = upload_document(uploaded_file)
                st.session_state.document_id = result["document_id"]
                st.session_state.filename = result["filename"]
                st.session_state.session_data = None
                st.session_state.mode_data = None
                st.session_state.last_mode = None
                reset_timer()
                st.success(f"Saved: {result['filename']}")
            except RequestException as e:
                st.error(f"Upload failed: {e}")

    if st.session_state.document_id:
        st.markdown("### Current document")
        with st.container(border=True):
            st.write(st.session_state.filename)
            st.caption(f"Document ID: {st.session_state.document_id}")

        if st.button("Generate study session", use_container_width=True):
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
                reset_timer()
                st.success("Session generated.")
            except RequestException as e:
                st.error(f"Session generation failed: {e}")

        st.markdown("### Timer Controls")
        timer_col1, timer_col2, timer_col3 = st.columns(3)

        session_ready = st.session_state.session_data is not None and st.session_state.last_mode == "session"

        with timer_col1:
            if st.button("Start", use_container_width=True, disabled=not session_ready):
                start_timer(estimated_minutes)

        with timer_col2:
            if st.button("Pause", use_container_width=True, disabled=not st.session_state.timer_running):
                pause_timer()

        with timer_col3:
            if st.button("Reset", use_container_width=True):
                reset_timer()

        if not session_ready:
            st.caption("Generate a study session before starting the timer.")

        st.markdown("### Quick study modes")
        mode = st.selectbox(
            "Choose a mode",
            ["summary", "simplified", "key_terms", "flashcards", "quiz", "study_guide"]
        )

        if st.button("Run selected mode", use_container_width=True):
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
                reset_timer()
                st.success(f"{mode.replace('_', ' ').title()} ready.")
            except RequestException as e:
                st.error(f"Mode generation failed: {e}")

with right:
    st.markdown("## Output")

    if st.session_state.timer_running and st.session_state.timer_start_time is not None:
        elapsed = int(time.time() - st.session_state.timer_start_time)
        remaining = max(0, st.session_state.timer_duration - elapsed)
        st.session_state.time_remaining = remaining

        st.markdown("## ⏱️ Session Timer")
        minutes = remaining // 60
        seconds = remaining % 60
        st.metric("Time Remaining", f"{minutes:02d}:{seconds:02d}")

        if st.session_state.timer_duration > 0:
            progress = 1 - (remaining / st.session_state.timer_duration)
            st.progress(min(max(progress, 0.0), 1.0))

        if remaining == 0:
            st.session_state.timer_running = False
            st.session_state.timer_paused = False
            st.session_state.timer_start_time = None
            st.error("⏰ Time's up!")

    elif st.session_state.timer_paused:
        st.markdown("## ⏱️ Session Timer")
        minutes = st.session_state.time_remaining // 60
        seconds = st.session_state.time_remaining % 60
        st.metric("Time Remaining", f"{minutes:02d}:{seconds:02d}")
        st.warning("Timer paused.")

        if st.session_state.timer_duration > 0:
            elapsed_fraction = 1 - (st.session_state.time_remaining / st.session_state.timer_duration)
            st.progress(min(max(elapsed_fraction, 0.0), 1.0))

    elif st.session_state.timer_duration > 0 and st.session_state.time_remaining == 0:
        st.markdown("## ⏱️ Session Timer")
        st.metric("Time Remaining", "00:00")
        st.progress(1.0)
        st.success("Session complete 🎉")
        st.info("Nice work. Review your flashcards or try the quiz next.")

    if st.session_state.last_mode == "session" and st.session_state.session_data:
        render_session(st.session_state.session_data, learner_type, theme)
    elif st.session_state.mode_data and st.session_state.last_mode:
        render_mode_output(st.session_state.mode_data, st.session_state.last_mode, learner_type, theme)
    else:
        st.info(
            "Upload notes, save the document, then generate a study session or run a study mode."
        )

if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()