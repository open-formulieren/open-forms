import json
from pathlib import Path
from typing import Any, Dict

FILES_DIR = Path(__file__).parent / "files"


def load_json(filename: str) -> Dict[str, Any]:
    with open(FILES_DIR / filename, "r") as infile:
        return json.load(infile)
