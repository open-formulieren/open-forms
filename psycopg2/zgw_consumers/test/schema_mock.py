import os

from requests_mock import Mocker

from ..settings import get_setting

_cache = {}


def read_schema(service: str, extension=".yaml"):
    schema_dirs = get_setting("ZGW_CONSUMERS_TEST_SCHEMA_DIRS")

    if service not in _cache:
        file_name = f"{service}{extension}"
        for directory in schema_dirs:
            filepath = os.path.join(directory, file_name)
            if os.path.exists(filepath):
                break
        else:
            raise IOError(
                f"File '{file_name}' not found, searched directories: {', '.join(schema_dirs)}. "
                "Consider adding the containing directory to the ZGW_CONSUMERS_TEST_SCHEMA_DIRS setting."
            )

        with open(filepath, "rb") as api_spec:
            _cache[service] = api_spec.read()

    return _cache[service]


def _clear_cache():
    for key in list(_cache.keys()):
        del _cache[key]


def mock_service_oas_get(m: Mocker, url: str, service: str, oas_url: str = "") -> None:
    if not oas_url:
        oas_url = f"{url}schema/openapi.yaml?v=3"
    content = read_schema(service)
    m.get(oas_url, content=content)
