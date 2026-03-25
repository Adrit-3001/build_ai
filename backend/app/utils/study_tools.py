import re
from collections import Counter
from typing import List, Tuple

from app.schemas import Flashcard, MultipleChoiceQuestion, KeyTerm, StudyGuideSection


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "so", "because",
    "of", "in", "on", "at", "by", "for", "to", "from", "with", "without", "as",
    "is", "are", "was", "were", "be", "being", "been", "it", "this", "that",
    "these", "those", "into", "onto", "about", "over", "under", "through",
    "mainly", "helps", "help", "can", "could", "should", "would", "will",
    "may", "might", "must", "do", "does", "did", "done", "has", "have", "had",
    "their", "there", "them", "they", "he", "she", "we", "you", "your", "our",
    "his", "her", "its", "also", "such", "which", "what", "when", "where",
    "who", "whom", "whose", "while", "during", "after", "before", "more",
    "most", "many", "much", "some", "any", "each", "every", "other", "another",
    "very", "just", "only", "even", "often", "often require", "student", "students",
    "tool", "tools", "need", "needs", "solution", "solutions", "notes", "note",
    "academic", "materials", "information", "processing", "language"
}

WEAK_TERMS = {
    "student", "students", "tool", "tools", "need", "needs", "solution",
    "solutions", "notes", "academic", "materials", "information", "processing",
    "language", "time", "support", "profile", "profiles"
}


def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_chunks(text: str) -> List[str]:
    parts = re.split(r'\n+|[•\-]\s+', text)
    cleaned = [p.strip() for p in parts if len(p.strip()) > 25]
    if not cleaned:
        cleaned = split_into_sentences(text)
    return cleaned


def tokenize_words(text: str) -> List[str]:
    return re.findall(r"\b[A-Za-z][A-Za-z\-]{2,}\b", text)


def normalize_phrase(phrase: str) -> str:
    phrase = phrase.strip(" .,;:!?()[]{}\"'")
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase.strip()


def is_good_term(term: str) -> bool:
    term_l = term.lower().strip()

    if len(term_l) < 4:
        return False
    if term_l in WEAK_TERMS:
        return False
    if term_l in STOPWORDS:
        return False
    if re.fullmatch(r"[0-9\W_]+", term_l):
        return False
    return True


def extract_candidate_phrases(text: str) -> List[str]:
    """
    Prefer multi-word concept phrases from the text.
    """
    candidates: List[str] = []

    # Quoted phrases
    quoted = re.findall(r'"([^"]{4,80})"', text)
    candidates.extend([normalize_phrase(q) for q in quoted])

    # Capitalized multi-word phrases like "Multi-Modal Learner"
    cap_phrases = re.findall(r"\b(?:[A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+){1,3})\b", text)
    candidates.extend([normalize_phrase(p) for p in cap_phrases])

    # Hyphenated / adjective+noun-ish phrases
    phrase_patterns = [
        r"\b([A-Za-z]+-[A-Za-z]+(?:\s+[A-Za-z]+){0,2})\b",
        r"\b((?:[A-Za-z]{4,}\s+){1,3}[A-Za-z]{4,})\b",
    ]
    for pattern in phrase_patterns:
        matches = re.findall(pattern, text)
        candidates.extend([normalize_phrase(m) for m in matches])

    cleaned_candidates = []
    for c in candidates:
        words = c.lower().split()
        if len(words) > 4:
            continue
        if any(w in STOPWORDS for w in words):
            # allow some stopwords inside phrase, but reject if all/mostly weak
            strong_count = sum(1 for w in words if w not in STOPWORDS and len(w) >= 4)
            if strong_count == 0:
                continue
        if any(is_good_term(w) for w in words):
            cleaned_candidates.append(c)

    return cleaned_candidates


def score_phrase(phrase: str, full_text: str) -> int:
    phrase_l = phrase.lower()
    score = 0

    # Prefer multi-word phrases
    word_count = len(phrase_l.split())
    score += min(word_count * 3, 12)

    # Prefer hyphenated concepts
    if "-" in phrase_l:
        score += 3

    # Count frequency
    occurrences = len(re.findall(rf"\b{re.escape(phrase_l)}\b", full_text.lower()))
    score += occurrences * 2

    # Penalize weak endings
    if phrase_l in WEAK_TERMS:
        score -= 8

    weak_word_count = sum(1 for w in phrase_l.split() if w in WEAK_TERMS)
    score -= weak_word_count * 2

    return score


def extract_candidate_terms(text: str, max_terms: int = 8) -> List[str]:
    """
    Hybrid extraction:
    1. Prefer meaningful phrases
    2. Fallback to strong single-word terms
    """
    phrases = extract_candidate_phrases(text)
    ranked_phrases = sorted(
        set(phrases),
        key=lambda p: score_phrase(p, text),
        reverse=True
    )

    final_terms: List[str] = []

    for phrase in ranked_phrases:
        phrase_l = phrase.lower()
        if len(phrase_l) < 4:
            continue
        if phrase_l in final_terms:
            continue

        # reject phrases that are mostly weak
        words = phrase_l.split()
        strong_words = [w for w in words if is_good_term(w)]
        if len(strong_words) == 0:
            continue

        final_terms.append(phrase_l)
        if len(final_terms) >= max_terms:
            return final_terms

    # fallback to good single words
    words = [w.lower() for w in tokenize_words(text)]
    filtered = [w for w in words if w not in STOPWORDS and is_good_term(w)]
    counts = Counter(filtered)

    for word, _ in counts.most_common(max_terms * 3):
        if word not in final_terms and word not in WEAK_TERMS:
            final_terms.append(word)
        if len(final_terms) >= max_terms:
            break

    return final_terms


def sentence_for_term(text: str, term: str) -> str:
    sentences = split_into_sentences(text)
    for sentence in sentences:
        if re.search(rf"\b{re.escape(term)}\b", sentence, flags=re.IGNORECASE):
            return sentence
    return ""


def definition_for_term(text: str, term: str) -> str:
    """
    Try to find the best sentence that defines or explains the term.
    """
    sentences = split_into_sentences(text)
    best_sentence = ""
    best_score = -1

    for sentence in sentences:
        sentence_l = sentence.lower()
        score = 0

        if re.search(rf"\b{re.escape(term)}\b", sentence_l):
            score += 5
        if " is " in sentence_l or " are " in sentence_l:
            score += 2
        if len(sentence) <= 260:
            score += 2
        if len(sentence) < 30:
            score -= 2

        if score > best_score:
            best_score = score
            best_sentence = sentence

    if best_sentence:
        return best_sentence

    return f"{term.title()} is an important concept from the notes."


def extract_key_terms(text: str, max_terms: int = 6) -> List[KeyTerm]:
    terms = extract_candidate_terms(text, max_terms=max_terms)
    key_terms: List[KeyTerm] = []

    seen_terms = set()

    for term in terms:
        title_term = term.title()
        if title_term.lower() in seen_terms:
            continue
        seen_terms.add(title_term.lower())

        definition = definition_for_term(text, term)

        key_terms.append(
            KeyTerm(
                term=title_term,
                definition=definition
            )
        )

    return key_terms


def question_for_term(term: str, definition: str) -> str:
    lower_term = term.lower()

    if "learner" in lower_term:
        return f"What is {term}?"
    if "adhd" in lower_term or "dyslexia" in lower_term or "autism" in lower_term:
        return f"Why is {term} important in these notes?"
    if "audio" in lower_term:
        return f"How is {term} used in the study experience?"
    if "session" in lower_term:
        return f"What role does {term} play?"
    return f"What does {term} refer to?"


def generate_flashcards(text: str, max_cards: int = 6) -> List[Flashcard]:
    key_terms = extract_key_terms(text, max_terms=max_cards)
    cards: List[Flashcard] = []

    for item in key_terms:
        cards.append(
            Flashcard(
                question=question_for_term(item.term, item.definition),
                answer=item.definition
            )
        )

    if cards:
        return cards

    chunks = split_into_chunks(text)
    for chunk in chunks[:max_cards]:
        cards.append(
            Flashcard(
                question="What does this section mean?",
                answer=chunk[:220]
            )
        )
    return cards


def make_distractors(correct: str, key_terms: List[KeyTerm], current_term: str) -> List[str]:
    distractors = []

    for item in key_terms:
        if item.term.lower() == current_term.lower():
            continue
        if item.definition != correct and len(item.definition) > 20:
            distractors.append(item.definition)

    generic = [
        "It is unrelated to the main topic of the notes.",
        "It is a formatting or submission instruction.",
        "It is a general comment that does not define the concept."
    ]

    distractors.extend(generic)

    unique = []
    seen = set()
    for d in distractors:
        if d not in seen:
            seen.add(d)
            unique.append(d)

    return unique[:3]


def generate_quiz(text: str, max_questions: int = 5) -> List[MultipleChoiceQuestion]:
    key_terms = extract_key_terms(text, max_terms=max_questions + 3)
    quiz: List[MultipleChoiceQuestion] = []

    for item in key_terms[:max_questions]:
        correct = item.definition
        distractors = make_distractors(correct, key_terms, item.term)
        options = [correct] + distractors

        if len(options) < 4:
            options += [
                "It is unrelated to the topic.",
                "It is only a formatting instruction."
            ]
            options = options[:4]

        quiz.append(
            MultipleChoiceQuestion(
                question=f"Which option best explains {item.term}?",
                options=options,
                answer=correct
            )
        )

    return quiz


def build_study_guide(text: str) -> List[StudyGuideSection]:
    key_terms = extract_key_terms(text, max_terms=5)
    sentences = split_into_sentences(text)

    overview_bullets = []
    for sentence in sentences[:3]:
        if len(sentence) > 20:
            overview_bullets.append(sentence)

    term_bullets = [f"{item.term}: {item.definition}" for item in key_terms[:5]]

    review_bullets = [
        f"Know what {item.term} means and why it matters." for item in key_terms[:3]
    ]
    if not review_bullets:
        review_bullets = ["Review the main ideas and connections between concepts."]

    guide = [
        StudyGuideSection(
            heading="Overview",
            bullets=overview_bullets if overview_bullets else ["No overview available."]
        ),
        StudyGuideSection(
            heading="Key Terms",
            bullets=term_bullets if term_bullets else ["No key terms found."]
        ),
        StudyGuideSection(
            heading="What to Review",
            bullets=review_bullets
        ),
    ]
    return guide