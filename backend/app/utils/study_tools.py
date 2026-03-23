import re
from collections import Counter
from typing import List

from app.schemas import Flashcard, MultipleChoiceQuestion, KeyTerm, StudyGuideSection


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "so", "because",
    "of", "in", "on", "at", "by", "for", "to", "from", "with", "without", "as",
    "is", "are", "was", "were", "be", "being", "been", "it", "this", "that",
    "these", "those", "into", "onto", "about", "over", "under", "through",
    "mainly", "helps", "help", "can", "could", "should", "would", "will",
    "may", "might", "must", "do", "does", "did", "done", "has", "have", "had",
    "their", "there", "them", "they", "he", "she", "we", "you", "your", "our",
    "his", "her", "its", "also", "such", "than", "which", "what", "when", "where"
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


def extract_candidate_terms(text: str, max_terms: int = 8) -> List[str]:
    words = [w.lower() for w in tokenize_words(text)]
    filtered = [w for w in words if w not in STOPWORDS and len(w) >= 4]
    counts = Counter(filtered)

    ranked = [word for word, _ in counts.most_common(max_terms * 3)]

    seen = set()
    final_terms = []
    for word in ranked:
        if word not in seen:
            seen.add(word)
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


def extract_key_terms(text: str, max_terms: int = 6) -> List[KeyTerm]:
    terms = extract_candidate_terms(text, max_terms=max_terms)
    key_terms: List[KeyTerm] = []

    for term in terms:
        source_sentence = sentence_for_term(text, term)
        definition = source_sentence if source_sentence else f"{term.title()} is an important concept from the notes."
        key_terms.append(
            KeyTerm(
                term=term.title(),
                definition=definition
            )
        )

    return key_terms


def generate_flashcards(text: str, max_cards: int = 6) -> List[Flashcard]:
    key_terms = extract_key_terms(text, max_terms=max_cards)
    cards: List[Flashcard] = []

    for item in key_terms:
        cards.append(
            Flashcard(
                question=f"What is {item.term}?",
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


def make_distractors(correct: str, key_terms: List[KeyTerm]) -> List[str]:
    distractors = []

    for item in key_terms:
        if item.definition != correct and len(item.definition) > 15:
            distractors.append(item.definition)

    generic = [
        "It is unrelated to the main topic of the notes.",
        "It is a procedural instruction rather than a concept.",
        "It is an opinion with no study relevance."
    ]

    for g in generic:
        if g != correct:
            distractors.append(g)

    unique = []
    seen = set()
    for d in distractors:
        if d not in seen:
            seen.add(d)
            unique.append(d)

    return unique[:3]


def generate_quiz(text: str, max_questions: int = 5) -> List[MultipleChoiceQuestion]:
    key_terms = extract_key_terms(text, max_terms=max_questions + 2)
    quiz: List[MultipleChoiceQuestion] = []

    for item in key_terms[:max_questions]:
        correct = item.definition
        distractors = make_distractors(correct, key_terms)
        options = [correct] + distractors

        if len(options) < 4:
            options += [
                "It is unrelated to the topic.",
                "It is only a formatting instruction."
            ]
            options = options[:4]

        quiz.append(
            MultipleChoiceQuestion(
                question=f"Which option best describes {item.term}?",
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
        overview_bullets.append(sentence)

    term_bullets = [f"{item.term}: {item.definition}" for item in key_terms[:5]]

    review_bullets = [
        f"Know the meaning of {item.term}." for item in key_terms[:3]
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