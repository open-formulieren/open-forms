import json
import os


def load_json_mock(name: str):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "r") as f:
        return json.load(f)


def load_binary_mock(name: str, file_path: str = ""):
    path = os.path.join(file_path or os.path.dirname(__file__), "files", name)
    with open(path, "rb") as f:
        return f.read()
