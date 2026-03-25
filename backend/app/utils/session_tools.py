import re
from typing import Any


def _normalize_text(text: str) -> str:
    text = text or ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_probable_junk(line: str) -> bool:
    line = line.strip()
    if not line:
        return True

    # page numbers / isolated numbers
    if re.fullmatch(r"\d{1,3}", line):
        return True

    # common PDF junk
    junk_patterns = [
        r"^page \d+$",
        r"^slide \d+$",
        r"^\d+/\d+$",
        r"^continued$",
        r"^copyright",
        r"^all rights reserved",
    ]
    for pat in junk_patterns:
        if re.match(pat, line, flags=re.I):
            return True

    # too short to be meaningful unless it's clearly a heading
    if len(line) <= 2:
        return True

    return False


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or _is_probable_junk(line):
        return False

    if len(line) > 90:
        return False

    if re.match(r"^(chapter|lecture|week|topic|section)\b", line, flags=re.I):
        return True

    if re.match(r"^\d+(\.\d+)*\s+", line):
        return True

    words = re.findall(r"[A-Za-z]+", line)
    if not words:
        return False

    if len(words) <= 8:
        title_like = sum(1 for w in words if w[:1].isupper()) / len(words)
        if title_like >= 0.6:
            return True

    if line.isupper() and len(words) >= 2:
        return True

    return False


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[\-\*\u2022]+\s*", "", line)
    line = re.sub(r"^\d+[\.\)]\s*", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    raw = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in raw:
        s = s.strip()
        if len(s) < 12:
            continue
        out.append(s)
    return out


def _extract_sections(text: str) -> list[dict[str, Any]]:
    lines = [ln.rstrip() for ln in text.split("\n")]
    sections: list[dict[str, Any]] = []
    current_title = "Overview"
    current_lines: list[str] = []

    def flush():
        nonlocal current_title, current_lines, sections
        cleaned = []
        for x in current_lines:
            c = _clean_line(x)
            if not c or _is_probable_junk(c):
                continue
            cleaned.append(c)

        if cleaned:
            sections.append(
                {
                    "title": current_title.strip(),
                    "lines": cleaned,
                }
            )
        current_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or _is_probable_junk(line):
            continue

        if _is_heading(line):
            flush()
            current_title = _clean_line(line)
        else:
            current_lines.append(line)

    flush()

    if sections:
        return sections

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if paragraphs:
        for i, p in enumerate(paragraphs):
            parts = []
            for x in p.split("\n"):
                c = _clean_line(x)
                if not c or _is_probable_junk(c):
                    continue
                parts.append(c)
            if parts:
                sections.append({"title": f"Section {i + 1}", "lines": parts})
        return sections

    return [{"title": "Overview", "lines": [text]}]


def _explode_section_lines_to_points(lines: list[str]) -> list[str]:
    points: list[str] = []

    for line in lines:
        line = line.strip()
        if not line or _is_probable_junk(line):
            continue

        # keep compact bullets
        if 18 <= len(line) <= 160:
            points.append(line)
            continue

        # split long text into sentences
        sents = _split_sentences(line)
        if sents:
            points.extend(sents)
        else:
            if len(line) > 18:
                points.append(line)

    # dedupe
    seen = set()
    deduped = []
    for p in points:
        key = p.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return deduped


def _merge_tiny_points(points: list[str]) -> list[str]:
    merged = []
    buffer = ""

    for p in points:
        p = p.strip()
        if not p:
            continue

        if len(p) < 45:
            if buffer:
                buffer = f"{buffer} {p}"
            else:
                buffer = p
        else:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(p)

    if buffer:
        merged.append(buffer.strip())

    return merged


def _group_points(points: list[str], chunk_size: int) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []

    for p in points:
        current.append(p)
        if len(current) >= chunk_size:
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)

    return chunks


def _infer_block_type(title: str, content: list[str], learner_type: str) -> str:
    joined = f"{title} {' '.join(content)}".lower()

    if learner_type == "adhd":
        return "focus_step"

    if any(k in joined for k in ["summary", "overview", "main idea"]):
        return "summary"
    if any(k in joined for k in ["quiz", "question", "mcq"]):
        return "quiz"
    if any(k in joined for k in ["flashcard", "remember"]):
        return "flashcard"
    return "concept"


def _make_blocks_from_sections(sections: list[dict[str, Any]], learner_type: str) -> list[dict[str, Any]]:
    all_blocks: list[dict[str, Any]] = []

    for section in sections:
        title = section["title"]
        points = _explode_section_lines_to_points(section["lines"])
        points = _merge_tiny_points(points)

        if not points:
            continue

        if learner_type == "adhd":
            chunk_size = 1 if len(points) <= 8 else 2
        elif learner_type == "dyslexic":
            chunk_size = 2
        else:
            # general mode should be denser, not fragmented
            chunk_size = 3 if len(points) >= 6 else 2

        grouped = _group_points(points, chunk_size=chunk_size)

        for idx, group in enumerate(grouped):
            block_title = title
            if len(grouped) > 1:
                block_title = f"{title} ({idx + 1})"

            all_blocks.append(
                {
                    "title": block_title,
                    "content": group,
                    "block_type": _infer_block_type(block_title, group, learner_type),
                }
            )

    if not all_blocks:
        all_blocks = [
            {
                "title": "Key Concepts",
                "content": ["No structured content could be extracted."],
                "block_type": "concept",
            }
        ]

    # general mode: reduce excessive tiny cards
    if learner_type == "general" and len(all_blocks) > 8:
        compressed = []
        i = 0
        while i < len(all_blocks):
            first = all_blocks[i]
            if i + 1 < len(all_blocks):
                second = all_blocks[i + 1]
                compressed.append(
                    {
                        "title": first["title"],
                        "content": first["content"] + second["content"],
                        "block_type": "concept",
                    }
                )
                i += 2
            else:
                compressed.append(first)
                i += 1
        all_blocks = compressed

    return all_blocks


def _build_overview(blocks: list[dict[str, Any]], max_points: int = 4) -> str:
    snippets: list[str] = []

    for block in blocks:
        for item in block.get("content", []):
            if isinstance(item, str) and item.strip():
                snippets.append(item.strip())
            if len(snippets) >= max_points:
                break
        if len(snippets) >= max_points:
            break

    if not snippets:
        return "This study session summarizes the key ideas from your notes."

    return " ".join(snippets[:max_points])


def _build_flashcards(blocks: list[dict[str, Any]], max_cards: int = 6) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []

    for block in blocks:
        title = block["title"]
        for item in block.get("content", []):
            text = item.strip()
            if len(text) < 18:
                continue

            q = f"What should you remember from {title}?"
            a = text
            cards.append({"question": q, "answer": a})

            if len(cards) >= max_cards:
                return cards

    return cards


def _build_quiz(blocks: list[dict[str, Any]], max_questions: int = 5) -> list[dict[str, Any]]:
    distractors = [
        "It is unrelated to the topic.",
        "It is mainly a formatting instruction.",
        "It focuses on a different concept.",
    ]

    quiz: list[dict[str, Any]] = []

    for block in blocks:
        for item in block.get("content", []):
            text = item.strip()
            if len(text) < 24:
                continue

            quiz.append(
                {
                    "question": f"Which option best matches the notes in {block['title']}?",
                    "options": [text] + distractors,
                    "answer": text,
                }
            )

            if len(quiz) >= max_questions:
                return quiz

    return quiz


def build_session(text: str, learner_type: str, difficulty: str, estimated_minutes: int = 5) -> dict:
    text = _normalize_text(text)

    if not text:
        return {
            "title": "Study Session",
            "learner_type": learner_type,
            "difficulty": difficulty,
            "estimated_minutes": estimated_minutes,
            "overview": "No usable text was found.",
            "blocks": [],
            "flashcards": [],
            "quiz": [],
        }

    sections = _extract_sections(text)
    blocks = _make_blocks_from_sections(sections, learner_type=learner_type)

    cleaned_blocks: list[dict[str, Any]] = []
    for block in blocks:
        content = [c for c in block["content"] if isinstance(c, str) and c.strip()]
        if not content:
            continue
        cleaned_blocks.append(
            {
                "title": block["title"],
                "content": content,
                "block_type": block.get("block_type", _infer_block_type(block["title"], content, learner_type)),
            }
        )

    if not cleaned_blocks:
        cleaned_blocks = [
            {
                "title": "Key Concepts",
                "content": [text[:300]],
                "block_type": "concept",
            }
        ]

    overview = _build_overview(cleaned_blocks)
    flashcards = _build_flashcards(cleaned_blocks)
    quiz = _build_quiz(cleaned_blocks)

    title = sections[0]["title"] if sections and sections[0]["title"] != "Overview" else "Study Session"

    return {
        "title": title,
        "learner_type": learner_type,
        "difficulty": difficulty,
        "estimated_minutes": estimated_minutes,
        "overview": overview,
        "blocks": cleaned_blocks,
        "flashcards": flashcards,
        "quiz": quiz,
    }


def ensure_rich_session(session: dict, text: str, learner_type: str, difficulty: str, estimated_minutes: int = 5) -> dict:
    if not isinstance(session, dict):
        return build_session(text, learner_type, difficulty, estimated_minutes)

    blocks = session.get("blocks")
    if not isinstance(blocks, list):
        return build_session(text, learner_type, difficulty, estimated_minutes)

    repaired_blocks = []
    usable_points = 0

    for block in blocks:
        if not isinstance(block, dict):
            continue

        title = str(block.get("title", "Section")).strip()
        content = block.get("content", [])
        if not isinstance(content, list):
            content = [str(content)] if content else []

        content = [str(x).strip() for x in content if str(x).strip()]
        content = _merge_tiny_points(content)

        if not content:
            continue

        usable_points += len(content)
        repaired_blocks.append(
            {
                "title": title,
                "content": content,
                "block_type": block.get("block_type", _infer_block_type(title, content, learner_type)),
            }
        )

    if len(repaired_blocks) <= 1 or usable_points <= 2:
        return build_session(text, learner_type, difficulty, estimated_minutes)

    session["blocks"] = repaired_blocks
    if not session.get("overview"):
        session["overview"] = _build_overview(repaired_blocks)
    if not session.get("title"):
        session["title"] = "Study Session"

    return session