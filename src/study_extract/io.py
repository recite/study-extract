"""Local JSON I/O and immutable document fingerprints."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as f:
        temp = Path(f.name)
        f.write(data)
    os.replace(temp, path)
