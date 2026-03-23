from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def extract_text_from_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_pdf(file_path: Path) -> str:
    text_parts = []
    pdf = fitz.open(file_path)
    try:
        for page in pdf:
            text_parts.append(page.get_text())
    finally:
        pdf.close()
    return "\n".join(text_parts).strip()


def extract_text_from_image(file_path: Path) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image).strip()


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")