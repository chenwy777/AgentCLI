from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

IMAGE_PATTERN = re.compile(r"@image:([^\s]+)")


def parse_image_references(message: str, cwd: str) -> str | list[dict]:
    matches = list(IMAGE_PATTERN.finditer(message))
    if not matches:
        return message

    parts: list[dict] = []
    cursor = 0
    for match in matches:
        before = message[cursor : match.start()]
        if before:
            parts.append({"type": "text", "text": before})
        reference = match.group(1)
        parts.append(_image_part(reference, cwd))
        cursor = match.end()
    tail = message[cursor:]
    if tail:
        parts.append({"type": "text", "text": tail})
    return parts


def _image_part(reference: str, cwd: str) -> dict:
    if reference.startswith(("http://", "https://")):
        return {"type": "image_url", "image_url": {"url": reference}}
    path = _resolve_image_path(reference, cwd)
    data_url, width, height = _encode_image(path)
    return {
        "type": "image_url",
        "image_url": {"url": data_url},
        "metadata": {"source": str(path), "width": width, "height": height},
    }


def _resolve_image_path(reference: str, cwd: str) -> Path:
    if reference.startswith("file://"):
        parsed = urlparse(reference)
        path = Path(unquote(parsed.path))
    else:
        path = Path(reference)
    if not path.is_absolute():
        path = Path(cwd).resolve() / path
    path = path.resolve()
    path.relative_to(Path(cwd).resolve())
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _encode_image(path: Path, max_side: int = 1568) -> tuple[str, int, int]:
    with Image.open(path) as image:
        image.thumbnail((max_side, max_side))
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}", image.width, image.height
