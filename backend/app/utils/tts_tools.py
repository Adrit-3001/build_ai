import asyncio
import hashlib
from pathlib import Path

import edge_tts

from app.config import AUDIO_DIR


DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "+0%"


def _safe_filename(text: str, voice: str, rate: str) -> str:
    digest = hashlib.md5(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()
    return f"{digest}.mp3"


async def _synthesize_async(text: str, voice: str, rate: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(output_path))


def synthesize_to_file(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> Path:
    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty.")

    if len(text) > 3000:
        text = text[:3000]

    filename = _safe_filename(text, voice, rate)
    output_path = AUDIO_DIR / filename

    if output_path.exists():
        return output_path

    asyncio.run(_synthesize_async(text=text, voice=voice, rate=rate, output_path=output_path))
    return output_path