import json
from pathlib import Path

TEST_FILES = Path(__file__).parent.resolve() / "files"


def load_json_mock(name: str):
    with (TEST_FILES / name).open("r") as f:
        return json.load(f)
