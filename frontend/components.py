import streamlit as st


def render_key_value(label, value):
    st.markdown(f"**{label}:** {value}")


def render_session(session):
    st.subheader(session["title"])
    render_key_value("Learner Type", session["learner_type"].title())
    render_key_value("Difficulty", session["difficulty"].title())
    render_key_value("Estimated Time", f'{session["estimated_minutes"]} min')

    st.markdown("### Overview")
    st.info(session["overview"])

    if session.get("blocks"):
        st.markdown("### Session Flow")
        for block in session["blocks"]:
            with st.container(border=True):
                st.markdown(f"#### {block['title']}")
                for item in block["content"]:
                    st.markdown(f"- {item}")

    if session.get("flashcards"):
        st.markdown("### Flashcards")
        for i, card in enumerate(session["flashcards"], start=1):
            with st.expander(f"Flashcard {i}: {card['question']}"):
                st.write(card["answer"])

    if session.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(session["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {option}")
                st.caption(f"Answer: {q['answer']}")


def render_mode_output(data, mode):
    st.markdown(f"## {mode.replace('_', ' ').title()}")

    if data.get("result"):
        st.write(data["result"])

    if data.get("key_terms"):
        st.markdown("### Key Terms")
        for item in data["key_terms"]:
            with st.container(border=True):
                st.markdown(f"**{item['term']}**")
                st.write(item["definition"])

    if data.get("flashcards"):
        st.markdown("### Flashcards")
        for i, card in enumerate(data["flashcards"], start=1):
            with st.expander(f"Flashcard {i}: {card['question']}"):
                st.write(card["answer"])

    if data.get("quiz"):
        st.markdown("### Quiz")
        for i, q in enumerate(data["quiz"], start=1):
            with st.container(border=True):
                st.markdown(f"**Q{i}. {q['question']}**")
                for option in q["options"]:
                    st.markdown(f"- {option}")
                st.caption(f"Answer: {q['answer']}")

    if data.get("study_guide"):
        st.markdown("### Study Guide")
        for section in data["study_guide"]:
            with st.container(border=True):
                st.markdown(f"**{section['heading']}**")
                for bullet in section["bullets"]:
                    st.markdown(f"- {bullet}")