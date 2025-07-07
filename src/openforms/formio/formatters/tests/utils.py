import json
from pathlib import Path
from typing import Any

FILES_DIR = Path(__file__).parent / "files"


def load_json(filename: str) -> dict[str, Any]:
    with open(FILES_DIR / filename) as infile:
        return json.load(infile)
