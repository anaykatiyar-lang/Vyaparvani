"""Load optional development-only app settings from .env.local."""

import os
from pathlib import Path


def load_local_env():
    env_path = Path(__file__).resolve().parent.parent / ".env.local"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or name not in {"DOCTR_OCR_URL", "DOCTR_OCR_TOKEN"}:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)
