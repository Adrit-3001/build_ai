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
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_css():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def force_sidebar_collapsed():
    st.markdown(
        """
        <script>
        (function () {
            const tryClose = () => {
                const rootDoc = window.parent.document;
                const closeBtn = rootDoc.querySelector('button[aria-label="Close sidebar"]');
                if (closeBtn) closeBtn.click();
            };
            setTimeout(tryClose, 50);
            setTimeout(tryClose, 250);
            setTimeout(tryClose, 700);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def learner_mode_description(learner_type: str) -> str:
    descriptions = {
        "general": "Balanced layout with a standard study flow.",
        "adhd": "Focus mode with one clear task at a time, reduced overload, and visible progress.",
        "dyslexic": "Reader mode with spacing controls, softer reading presets, and cleaner text presentation.",
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


def apply_accessibility_settings(reading_cfg: dict, learner_type: str):
    dyslexic_font_mode = "1" if reading_cfg.get("dyslexic_font_mode", False) else "0"

    st.markdown(
        f"""
        <style>
        :root {{
            --reader-text-size: {reading_cfg["text_size_px"]}px;
            --reader-line-height: {reading_cfg["line_height"]};
            --reader-paragraph-gap: {reading_cfg["paragraph_gap_rem"]}rem;
            --reader-max-width: {reading_cfg["max_width_px"]}px;
        }}
        </style>
        <script>
        const root = window.parent.document.documentElement;
        root.classList.remove('mode-general', 'mode-adhd', 'mode-dyslexic', 'mode-visual', 'mode-auditory');
        root.classList.add('mode-{learner_type}');

        if ({dyslexic_font_mode}) {{
            root.classList.add('dyslexic-font-mode');
        }} else {{
            root.classList.remove('dyslexic-font-mode');
        }}
        </script>
        """,
        unsafe_allow_html=True,
    )


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
force_sidebar_collapsed()

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
if "adhd_step_index" not in st.session_state:
    st.session_state.adhd_step_index = 0

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


def reset_workspace():
    st.session_state.document_id = None
    st.session_state.filename = None
    st.session_state.session_data = None
    st.session_state.mode_data = None
    st.session_state.last_mode = None
    st.session_state.adhd_step_index = 0
    reset_timer()


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

    st.markdown("### Learning mode description")
    st.info(learner_mode_description(learner_type))

    focus_view = False
    if learner_type == "adhd":
        focus_view = st.toggle("Use focus view", value=True)
        st.caption("Keeps the focus on the current content while leaving controls available.")

    st.markdown("### Reading controls")

    default_text_size = 20 if learner_type == "dyslexic" else 17
    default_line_height = 2.0 if learner_type == "dyslexic" else 1.75
    default_paragraph_gap = 1.25 if learner_type == "dyslexic" else 0.85
    default_width = 760 if learner_type == "dyslexic" else 860

    text_size_px = st.slider("Text size", 15, 28, default_text_size, 1)
    line_height = st.slider("Line spacing", 1.4, 2.4, default_line_height, 0.05)
    paragraph_gap_rem = st.slider("Paragraph spacing", 0.4, 2.0, default_paragraph_gap, 0.05)
    max_width_px = st.slider("Reading width", 560, 1000, default_width, 20)

    reader_tint = "default"
    dyslexic_font_mode = False
    if learner_type == "dyslexic":
        st.markdown("### Dyslexia-friendly options")
        reader_preset = st.selectbox(
            "Reading preset",
            ["Comfort", "Soft Cream", "Cool Paper", "Dark Reader"],
            index=0
        )

        preset_map = {
            "Comfort": "default",
            "Soft Cream": "warm",
            "Cool Paper": "cool",
            "Dark Reader": "soft-dark",
        }
        reader_tint = preset_map[reader_preset]
        dyslexic_font_mode = st.toggle("Use dyslexia-friendly font style", value=True)

    st.markdown("### Read aloud")
    read_aloud_enabled = st.toggle("Enable generated audio", value=True)
    tts_voice = st.selectbox(
        "Voice",
        ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural"],
        index=0
    )

    # st.markdown("---")
    # st.markdown("### Backend status")
    # try:
    #     status = check_backend()
    #     st.success(f"Connected: {status['status']}")
    # except RequestException:
    #     st.error("Backend not reachable")
    #     st.stop()

    reading_cfg = {
        "text_size_px": text_size_px,
        "line_height": line_height,
        "paragraph_gap_rem": paragraph_gap_rem,
        "max_width_px": max_width_px,
        "reader_tint": reader_tint,
        "focus_view": focus_view,
        "dyslexic_font_mode": dyslexic_font_mode,
        "read_aloud_enabled": read_aloud_enabled,
        "tts_voice": tts_voice,
    }

apply_accessibility_settings(reading_cfg, learner_type)


if st.session_state.document_id is None:
    _, center_col, _ = st.columns([1, 2.2, 1])

    with center_col:
        st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="landing-badge">📘 Study Buddy</div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="landing-title">Hey, let’s start by uploading your study document.</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="landing-subtitle">Upload your notes first. Open the sidebar anytime if you want to adjust learner type, difficulty, theme, session length, audio, or reading controls.</p>',
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload a PDF, TXT, or image",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
            label_visibility="collapsed",
        )

        st.markdown(
            '<div class="landing-helper">Need to customize things first? Use the top-left arrow to open settings.</div>',
            unsafe_allow_html=True,
        )

        if uploaded_file is not None:
            if st.button("Upload study document", use_container_width=True):
                try:
                    with st.spinner("Uploading and extracting text..."):
                        result = upload_document(uploaded_file)
                    st.session_state.document_id = result["document_id"]
                    st.session_state.filename = result["filename"]
                    st.session_state.session_data = None
                    st.session_state.mode_data = None
                    st.session_state.last_mode = None
                    st.session_state.adhd_step_index = 0
                    reset_timer()
                    st.rerun()
                except RequestException as e:
                    st.error(f"Upload failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


_, main_col, _ = st.columns([0.8, 2.5, 0.8])

with main_col:
    st.markdown('<div class="workspace-shell">', unsafe_allow_html=True)

    header_left, header_right = st.columns([1.4, 0.8])

    with header_left:
        st.markdown("## Study Companion")
        if st.session_state.filename:
            st.caption(f"Working on: {st.session_state.filename}")

    with header_right:
        st.markdown('<div class="top-actions-space"></div>', unsafe_allow_html=True)
        if st.button("← Back to upload", use_container_width=True):
            reset_workspace()
            st.rerun()

    def render_study_tools():
        action_col1, action_col2 = st.columns([1.1, 1])

        with action_col1:
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
                    st.session_state.adhd_step_index = 0
                    reset_timer()
                    st.success("Session generated.")
                except RequestException as e:
                    st.error(f"Session generation failed: {e}")

        with action_col2:
            mode = st.selectbox(
                "Quick mode",
                ["summary", "simplified", "key_terms", "flashcards", "quiz", "study_guide"],
                label_visibility="collapsed",
                key="main_quick_mode"
            )

        if st.button(f"Run {mode.replace('_', ' ')}", use_container_width=True, key="run_quick_mode_btn"):
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
                st.session_state.adhd_step_index = 0
                reset_timer()
                # st.success(f"{mode.replace('_', ' ').title()} ready.")
            except RequestException as e:
                st.error(f"Mode generation failed: {e}")

    # if learner_type == "adhd":
    with st.expander("Study tools", expanded=True):
        render_study_tools()
    # else:
    #     st.markdown("### Study tools")
    #     render_study_tools()

    timer_open = st.session_state.timer_running or st.session_state.timer_paused or (
        st.session_state.timer_duration > 0 and st.session_state.time_remaining == 0
    )

    with st.expander("⏱︎ Timer", expanded=timer_open):
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

        if st.session_state.timer_running and st.session_state.timer_start_time is not None:
            elapsed = int(time.time() - st.session_state.timer_start_time)
            remaining = max(0, st.session_state.timer_duration - elapsed)
            st.session_state.time_remaining = remaining

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
                st.error("Time's up!")

        elif st.session_state.timer_paused:
            minutes = st.session_state.time_remaining // 60
            seconds = st.session_state.time_remaining % 60
            st.metric("Time Remaining", f"{minutes:02d}:{seconds:02d}")
            st.warning("Timer paused.")

            if st.session_state.timer_duration > 0:
                elapsed_fraction = 1 - (st.session_state.time_remaining / st.session_state.timer_duration)
                st.progress(min(max(elapsed_fraction, 0.0), 1.0))

        elif st.session_state.timer_duration > 0 and st.session_state.time_remaining == 0:
            st.metric("Time Remaining", "00:00")
            st.progress(1.0)
            st.success("Session complete – great job!")
            st.info("Nice work. Review your flashcards or try the quiz next.")

    # st.markdown("### Output")

    if st.session_state.last_mode == "session" and st.session_state.session_data:
        render_session(
            st.session_state.session_data,
            learner_type,
            theme,
            reading_cfg,
            st.session_state.adhd_step_index
        )
    elif st.session_state.mode_data and st.session_state.last_mode:
        render_mode_output(
            st.session_state.mode_data,
            st.session_state.last_mode,
            learner_type,
            theme,
            reading_cfg
        )
    else:
        st.info("Generate a study session or run a study mode to see your output here.")

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()