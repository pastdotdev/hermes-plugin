"""Settings shared by the provider and its CLI.

Hermes imports cli.py on its own, without running the provider module, to list `hermes past`
commands. Anything cli.py needs therefore lives here, in a sibling module it can import, rather
than in the package's __init__.py.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

VERSION = "0.1.1"
DEFAULT_API_URL = "https://api.past.dev"
# A session is cut into sittings where it went quiet this long, as the other connectors do: past
# dates every memory at its data point's time, so a sitting is dated by its own first turn.
DEFAULT_SITTING_MINUTES = 30
MIN_SITTING_MINUTES = 5


def past_home() -> Path:
    return Path(os.environ.get("PAST_HOME") or Path.home() / ".past")


def write_private(path: Path, value: Any) -> None:
    """Written 600 from the start, in a 700 folder: the folder also holds the key."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".writing")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(value, handle)
    os.replace(temporary, path)


def read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def load_config() -> dict:
    """The environment wins over the file, as in the other connectors."""
    file = read_json(past_home() / "config.json", {})
    sitting = file.get("sittingMinutes")
    return {
        "apiKey": os.environ.get("PAST_API_KEY") or file.get("apiKey") or "",
        "apiUrl": (os.environ.get("PAST_API_URL") or file.get("apiUrl") or DEFAULT_API_URL).rstrip("/"),
        "identity": os.environ.get("PAST_IDENTITY") or file.get("identity") or "",
        "recall": file.get("recall") is not False,
        "ingest": file.get("ingest") is not False,
        "audience": str(file.get("audience") or "").strip(),
        # A messaging gateway can serve several people, and past recalls as one identity.
        "gateway": file.get("gateway") is True or os.environ.get("PAST_GATEWAY") == "1",
        "sittingMinutes": max(MIN_SITTING_MINUTES, int(sitting)) if isinstance(sitting, (int, float)) and sitting > 0
        else DEFAULT_SITTING_MINUTES,
    }
