from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageOps
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

    # Handle PNG transparency / palette / uncommon modes
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    # Normalize orientation
    image = ImageOps.exif_transpose(image)

    # OCR
    text = pytesseract.image_to_string(image).strip()
    return text


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")