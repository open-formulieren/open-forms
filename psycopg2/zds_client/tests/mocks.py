import contextlib
import hashlib
import json
import sys
from urllib.parse import urljoin

from ..client import Client


class MockClientMeta(type):
    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)
        if dct["responses"] is not None:
            # register the client class as a module-importable thing
            setattr(sys.modules[__name__], name, klass)
        return klass


class MockClient(Client, metaclass=MockClientMeta):

    responses = None

    def fetch_schema(self) -> None:
        raise NotImplementedError
        self._schema = {}

    def request(self, path: str, operation: str, method="GET", *args, **kwargs):
        url = urljoin(self.base_url, path)

        # temprorary solution for testing requests with notifications
        if operation == "notificaties":
            assert method == "POST", "For notifications only POST method is supported"
            return self.responses.get(url, {})

        assert method == "GET", "Methods other than GET are currently not supported"
        return self.responses[url]


@contextlib.contextmanager
def mock_client(responses: dict):
    try:
        from django.test import override_settings
    except ImportError as exc:
        raise ImportError("You can only use this in a django context") from exc

    try:
        json_string = json.dumps(responses).encode("utf-8")
        md5 = hashlib.md5(json_string).hexdigest()
        name = f"MockClient{md5}"
        # create the class
        type(name, (MockClient,), {"responses": responses})
        dotted_path = f"{__name__}.{name}"
        with override_settings(ZDS_CLIENT_CLASS=dotted_path):
            yield

        # clean up
        delattr(sys.modules[__name__], name)
    finally:
        pass
