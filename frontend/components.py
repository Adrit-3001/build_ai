import base64
import hashlib
import html
import re
import streamlit as st


def learner_badge(learner_type: str) -> str:
    mapping = {
        "general": "General Mode",
        "adhd": "ADHD Focus Mode",
        "dyslexic": "Dyslexia-Friendly Mode",
        "visual": "Visual Scan Mode",
        "auditory": "Auditory Review Mode",
    }
    return mapping.get(learner_type, "Study Mode")


def theme_badge(theme: str) -> str:
    return "Playful Theme" if theme == "playful" else "Classic Theme"


def render_key_value(label, value):
    st.markdown(f"**{label}:** {value}")


def split_into_short_paragraphs(text: str, max_sentences_per_paragraph: int = 2) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return text

    groups = []
    for i in range(0, len(sentences), max_sentences_per_paragraph):
        groups.append(" ".join(sentences[i:i + max_sentences_per_paragraph]))

    return "\n\n".join(groups)


def adapt_text_for_display(text: str, learner_type: str) -> str:
    if not isinstance(text, str):
        return ""

    if learner_type == "adhd":
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return "\n".join(sentences[:3])

    if learner_type == "dyslexic":
        text = text.replace("; ", ". ")
        return split_into_short_paragraphs(text, max_sentences_per_paragraph=1)

    if learner_type == "auditory":
        return f"Say this out loud: {text}"

    return text


def render_mode_banner(learner_type: str, theme: str):
    theme_class = "mode-banner-playful" if theme == "playful" else "mode-banner-classic"
    st.markdown(
        f"""
        <div class="mode-banner {theme_class}">
            <div class="mode-banner-title">{learner_badge(learner_type)} • {theme_badge(theme)}</div>
            <div class="mode-banner-subtitle">This view is adapted for the selected learning style.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_read_aloud_button(text: str, label: str = "🔊 Read aloud"):
    if not text or not isinstance(text, str):
        return

    button_id = "speak_" + hashlib.md5((label + text[:120]).encode("utf-8")).hexdigest()
    encoded_text = base64.b64encode(text.encode("utf-8")).decode("ascii")
    safe_label = html.escape(label)

    st.markdown(
        f"""
        <div class="read-aloud-wrap">
            <button id="{button_id}" class="read-aloud-btn" type="button">{safe_label}</button>
        </div>
        <script>
        (function() {{
            const btn = document.getElementById("{button_id}");
            if (!btn || btn.dataset.bound === "1") return;
            btn.dataset.bound = "1";

            const decodeText = () => {{
                try {{
                    return atob("{encoded_text}");
                }} catch (e) {{
                    return "";
                }}
            }};

            const pickVoice = () => {{
                const voices = window.speechSynthesis.getVoices() || [];
                if (!voices.length) return null;

                const preferred =
                    voices.find(v => /en/i.test(v.lang) && /female|samantha|ava|zira|aria|natural/i.test(v.name)) ||
                    voices.find(v => /en/i.test(v.lang)) ||
                    voices[0];

                return preferred || null;
            }};

            const speak = () => {{
                try {{
                    const text = decodeText();
                    if (!text) return;

                    window.speechSynthesis.cancel();

                    const utterance = new SpeechSynthesisUtterance(text);
                    const voice = pickVoice();
                    if (voice) utterance.voice = voice;

                    utterance.rate = 0.95;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;

                    window.speechSynthesis.speak(utterance);
                }} catch (e) {{
                    console.log("Read aloud failed:", e);
                }}
            }};

            btn.addEventListener("click", speak);

            if (window.speechSynthesis && window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = function() {{}};
            }}
        }})();
        </script>
        """,
        unsafe_allow_html=True
    )


def render_result_panel(text: str, learner_type: str, theme: str, reading_cfg: dict):
    display_text = adapt_text_for_display(text, learner_type)
    panel_theme = "general-panel-playful" if theme == "playful" else "general-panel-classic"

    if learner_type == "dyslexic":
        panel_theme = "dyslexic-panel-playful" if theme == "playful" else "dyslexic-panel-classic"
    elif learner_type == "adhd":
        panel_theme = "adhd-panel-playful" if theme == "playful" else "adhd-panel-classic"
    elif learner_type == "auditory":
        panel_theme = "auditory-panel-playful" if theme == "playful" else "auditory-panel-classic"
    elif learner_type == "visual":
        panel_theme = "visual-panel-playful" if theme == "playful" else "visual-panel-classic"

    tint_class = ""
    if learner_type == "dyslexic":
        tint = reading_cfg.get("reader_tint", "default")
        tint_class = f" reader-tint-{tint}"

    html_text = html.escape(display_text).replace("\n\n", "</p><p>").replace("\n", "<br>")
    html_text = f"<p>{html_text}</p>"

    st.markdown(
        f"""
        <div class="reading-panel reader-panel {panel_theme}{tint_class}">
            {html_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    if reading_cfg.get("read_aloud_enabled", False):
        render_read_aloud_button(display_text)


def render_focus_block(block: dict, learner_type: str, theme: str, reading_cfg: dict):
    block_title = html.escape(block.get("title", "Step"))
    content = block.get("content", [])
    panel_theme = "adhd-panel-playful" if theme == "playful" else "adhd-panel-classic"

    st.markdown(
        f"""
        <div class="focus-step-card {panel_theme}">
            <div class="focus-step-title">{block_title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if content:
        for item in content[:3]:
            display = adapt_text_for_display(item, learner_type)
            st.markdown(
                f"""
                <div class="focus-item-card">
                    {html.escape(display)}
                </div>
                """,
                unsafe_allow_html=True
            )
            if reading_cfg.get("read_aloud_enabled", False):
                render_read_aloud_button(display, "🔊 Read this step")


def render_session(session, learner_type: str, theme: str, reading_cfg: dict, adhd_step_index: int = 0):
    render_mode_banner(learner_type, theme)

    st.subheader(session["title"])
    col1, col2, col3 = st.columns(3)
    with col1:
        render_key_value("Learner Type", session["learner_type"].title())
    with col2:
        render_key_value("Difficulty", session["difficulty"].title())
    with col3:
        render_key_value("Estimated Time", f"{session['estimated_minutes']} min")

    overview = session.get("overview", "")
    blocks = session.get("blocks", [])

    if learner_type == "adhd" and reading_cfg.get("focus_view", False):
        st.markdown("### Main Idea")
        render_result_panel(overview, learner_type, theme, reading_cfg)

        if blocks:
            safe_index = min(max(adhd_step_index, 0), len(blocks) - 1)
            current_block = blocks[safe_index]

            st.markdown(
                f'<div class="focus-banner">Focus mode: one step at a time • Step {safe_index + 1} of {len(blocks)}</div>',
                unsafe_allow_html=True
            )

            nav_col1, nav_col2, nav_col3 = st.columns(3)
            with nav_col1:
                if st.button("← Previous step", use_container_width=True, disabled=safe_index == 0):
                    st.session_state.adhd_step_index -= 1
                    st.rerun()
            with nav_col2:
                if st.button("Restart flow", use_container_width=True):
                    st.session_state.adhd_step_index = 0
                    st.rerun()
            with nav_col3:
                if st.button("Next step →", use_container_width=True, disabled=safe_index >= len(blocks) - 1):
                    st.session_state.adhd_step_index += 1
                    st.rerun()

            st.markdown("### Current Step")
            render_focus_block(current_block, learner_type, theme, reading_cfg)

        st.markdown("### Quick Practice")
        flashcards = session.get("flashcards", [])
        quiz = session.get("quiz", [])

        practice_col1, practice_col2 = st.columns(2)
        with practice_col1:
            if flashcards:
                idx = min(adhd_step_index, len(flashcards) - 1)
                with st.expander("Flashcard prompt"):
                    st.write(flashcards[idx]["question"])
                    st.caption(flashcards[idx]["answer"])
                    if reading_cfg.get("read_aloud_enabled", False):
                        render_read_aloud_button(
                            flashcards[idx]["question"] + ". " + flashcards[idx]["answer"],
                            "🔊 Read flashcard"
                        )

        with practice_col2:
            if quiz:
                idx = min(adhd_step_index, len(quiz) - 1)
                with st.expander("Quick check"):
                    q = quiz[idx]
                    st.write(q["question"])
                    for option in q["options"]:
                        st.markdown(f"- {option}")
                    st.caption(f"Answer: {q['answer']}")
                    if reading_cfg.get("read_aloud_enabled", False):
                        render_read_aloud_button(
                            q["question"] + ". " + " ".join(q["options"]),
                            "🔊 Read quiz"
                        )
        return

    st.markdown("### Overview")
    render_result_panel(overview, learner_type, theme, reading_cfg)

    if blocks:
        st.markdown("### Session Flow")
        for block in blocks:
            with st.container(border=True):
                st.markdown(f"#### {block['title']}")
                if learner_type == "visual":
                    cols = st.columns(2)
                    for idx, item in enumerate(block["content"]):
                        with cols[idx % 2]:
                            st.markdown(f"- {adapt_text_for_display(item, learner_type)}")
                else:
                    for item in block["content"]:
                        st.markdown(f"- {adapt_text_for_display(item, learner_type)}")

    if session.get("flashcards"):
        st.markdown("### Flashcards")
        for i, card in enumerate(session["flashcards"], start=1):
            with st.expander(f"Flashcard {i}: {card['question']}"):
                st.write(adapt_text_for_display(card["answer"], learner_type))
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(card["question"] + ". " + card["answer"], "🔊 Read flashcard")

    if session.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(session["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {adapt_text_for_display(option, learner_type)}")
                st.caption(f"Answer: {adapt_text_for_display(q['answer'], learner_type)}")
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(q["question"] + ". " + " ".join(q["options"]), "🔊 Read quiz")


def render_mode_output(data, mode, learner_type: str, theme: str, reading_cfg: dict):
    render_mode_banner(learner_type, theme)

    st.markdown(f"## {mode.replace('_', ' ').title()}")

    result = data.get("result")
    if isinstance(result, str) and result.strip():
        if mode in {"summary", "simplified"}:
            render_result_panel(result, learner_type, theme, reading_cfg)
        else:
            st.write(adapt_text_for_display(result, learner_type))
            if reading_cfg.get("read_aloud_enabled", False):
                render_read_aloud_button(adapt_text_for_display(result, learner_type))

    if data.get("key_terms"):
        st.markdown("### Key Terms")
        for item in data["key_terms"]:
            with st.container(border=True):
                st.markdown(f"**{item['term']}**")
                st.write(adapt_text_for_display(item["definition"], learner_type))
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(item["term"] + ". " + item["definition"], "🔊 Read key term")

    if data.get("flashcards"):
        st.markdown("### Flashcards")
        for i, card in enumerate(data["flashcards"], start=1):
            with st.expander(f"Flashcard {i}: {card['question']}"):
                st.write(adapt_text_for_display(card["answer"], learner_type))
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(card["question"] + ". " + card["answer"], "🔊 Read flashcard")

    if data.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(data["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {adapt_text_for_display(option, learner_type)}")
                st.caption(f"Answer: {adapt_text_for_display(q['answer'], learner_type)}")
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(q["question"] + ". " + " ".join(q["options"]), "🔊 Read quiz")

    if data.get("study_guide"):
        st.markdown("### Study Guide")
        for section in data["study_guide"]:
            with st.container(border=True):
                st.markdown(f"**{section['heading']}**")
                bullets_text = []
                for bullet in section["bullets"]:
                    display = adapt_text_for_display(bullet, learner_type)
                    st.markdown(f"- {display}")
                    bullets_text.append(display)
                if reading_cfg.get("read_aloud_enabled", False):
                    render_read_aloud_button(section["heading"] + ". " + " ".join(bullets_text), "🔊 Read section")