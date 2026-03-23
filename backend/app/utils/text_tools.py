import re


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def summarize_text(text: str, max_sentences: int = 5) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return " ".join(sentences[:max_sentences])


def adapt_for_learner(summary: str, learner_type: str, difficulty: str) -> str:
    learner_type = learner_type.lower()

    if learner_type == "auditory":
        prefix = "Audio-friendly study version:\n- Short spoken-style explanation:\n"
    elif learner_type == "visual":
        prefix = "Visual-friendly study version:\n- Key ideas grouped for scanning:\n"
    elif learner_type == "dyslexic":
        prefix = "Dyslexia-friendly study version:\n- Shorter, clearer chunks:\n"
    elif learner_type == "adhd":
        prefix = "Focus-friendly study version:\n- Fast, important points first:\n"
    else:
        prefix = "General study version:\n"

    if difficulty == "easy":
        level = "\nDifficulty level: easy to understand.\n"
    elif difficulty == "hard":
        level = "\nDifficulty level: more detailed.\n"
    else:
        level = "\nDifficulty level: balanced.\n"

    return f"{prefix}{level}{summary}"


def simplify_text(text: str, difficulty: str = "easy", learner_type: str = "general") -> str:
    if difficulty == "easy":
        max_sentences = 4
    elif difficulty == "hard":
        max_sentences = 7
    else:
        max_sentences = 5

    summary = summarize_text(text, max_sentences=max_sentences)
    return adapt_for_learner(summary, learner_type, difficulty)