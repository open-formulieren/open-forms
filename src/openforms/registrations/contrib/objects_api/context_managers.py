import json
from contextlib import contextmanager


@contextmanager
def catch_json_decode_errors(*args, **kwargs):
    try:
        yield
    except json.decoder.JSONDecodeError as err:
        raise RuntimeError("Template evaluation did not result in valid JSON") from err
