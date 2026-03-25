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


def render_key_value(label, value):
    st.markdown(f"**{label}:** {value}")


def adapt_text_for_display(text: str, learner_type: str) -> str:
    if not isinstance(text, str):
        return ""

    if learner_type == "adhd":
        if len(text) > 220:
            return text[:220].rsplit(" ", 1)[0] + "..."
        return text

    if learner_type == "dyslexic":
        text = text.replace("; ", ". ")
        if len(text) > 240:
            text = text[:240].rsplit(" ", 1)[0] + "..."
        return text

    if learner_type == "auditory":
        return f"Say this out loud: {text}"

    return text


def render_mode_banner(learner_type: str):
    st.markdown(
        f"""
        <div class="mode-banner">
            <div class="mode-banner-title">{learner_badge(learner_type)}</div>
            <div class="mode-banner-subtitle">This view is adapted for the selected learning style.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_result_panel(text: str, learner_type: str):
    display_text = adapt_text_for_display(text, learner_type)
    st.markdown(
        f"""
        <div class="reading-panel general-panel">
            {display_text}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_session(session, learner_type: str):
    render_mode_banner(learner_type)

    st.subheader(session["title"])
    col1, col2, col3 = st.columns(3)
    with col1:
        render_key_value("Learner Type", session["learner_type"].title())
    with col2:
        render_key_value("Difficulty", session["difficulty"].title())
    with col3:
        render_key_value("Estimated Time", f"{session['estimated_minutes']} min")

    st.markdown("### Overview")

    overview = session["overview"]
    if learner_type == "dyslexic":
        st.markdown(f'<div class="reading-panel dyslexic-panel">{adapt_text_for_display(overview, learner_type)}</div>', unsafe_allow_html=True)
    elif learner_type == "adhd":
        st.markdown(f'<div class="reading-panel adhd-panel">{adapt_text_for_display(overview, learner_type)}</div>', unsafe_allow_html=True)
    elif learner_type == "auditory":
        st.markdown(f'<div class="reading-panel auditory-panel">{adapt_text_for_display(overview, learner_type)}</div>', unsafe_allow_html=True)
    elif learner_type == "visual":
        st.markdown(f'<div class="reading-panel visual-panel">{overview}</div>', unsafe_allow_html=True)
    else:
        st.info(overview)

    if session.get("blocks"):
        st.markdown("### Session Flow")
        for block in session["blocks"]:
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

    if session.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(session["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {adapt_text_for_display(option, learner_type)}")
                st.caption(f"Answer: {adapt_text_for_display(q['answer'], learner_type)}")


def render_mode_output(data, mode, learner_type: str):
    render_mode_banner(learner_type)

    st.markdown(f"## {mode.replace('_', ' ').title()}")

    result = data.get("result")
    if isinstance(result, str) and result.strip():
        if mode in {"summary", "simplified"}:
            render_result_panel(result, learner_type)
        else:
            st.write(adapt_text_for_display(result, learner_type))

    if data.get("key_terms"):
        st.markdown("### Key Terms")
        for item in data["key_terms"]:
            with st.container(border=True):
                st.markdown(f"**{item['term']}**")
                st.write(adapt_text_for_display(item["definition"], learner_type))

    if data.get("flashcards"):
        st.markdown("### Flashcards")
        for i, card in enumerate(data["flashcards"], start=1):
            with st.expander(f"Flashcard {i}: {card['question']}"):
                st.write(adapt_text_for_display(card["answer"], learner_type))

    if data.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(data["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {adapt_text_for_display(option, learner_type)}")
                st.caption(f"Answer: {adapt_text_for_display(q['answer'], learner_type)}")

    if data.get("study_guide"):
        st.markdown("### Study Guide")
        for section in data["study_guide"]:
            with st.container(border=True):
                st.markdown(f"**{section['heading']}**")
                for bullet in section["bullets"]:
                    st.markdown(f"- {adapt_text_for_display(bullet, learner_type)}")