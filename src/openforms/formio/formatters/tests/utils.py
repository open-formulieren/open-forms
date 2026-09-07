import json
from pathlib import Path

from openforms.typing import JSONValue

FILES_DIR = Path(__file__).parent / "files"


def load_json(filename: str) -> JSONValue:
    with open(FILES_DIR / filename) as infile:
        return json.load(infile)
