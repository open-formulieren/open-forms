import json
import os
from io import BytesIO
from pathlib import Path
from typing import Union

from O365 import Account

from openforms.contrib.microsoft.constants import ConflictHandling
from openforms.contrib.microsoft.exceptions import MSAuthenticationError
from openforms.contrib.microsoft.models import MSGraphService


class MSGraphClient:
    """
    wrapper to setup O365 graph client from a MSGraphService
    """

    # .default works fine for our credentials use
    scopes = [
        "https://graph.microsoft.com/.default",
    ]

    def __init__(self, service: MSGraphService):
        self.service = service

        self.account = Account(
            (self.service.client_id, self.service.secret),
            auth_flow_type="credentials",
            tenant_id=self.service.tenant_id,
        )
        if not self.account.is_authenticated:
            if not self.account.authenticate(scopes=self.scopes):
                raise MSAuthenticationError("cannot authenticate")

    @property
    def is_authenticated(self):
        return self.account.is_authenticated


class MSGraphUploadHelper:
    """
    helper for uploading
    - navigate to our folder in the account
    - upload various objects in stream mode to support large files
    """

    # TODO wrap upload_()-variations in single function and auto-detect object type

    def __init__(self, client: MSGraphClient):
        self.client = client

        self.storage = self.client.account.storage()
        self.drive = self.storage.get_default_drive()
        self.root_folder = self.drive.get_root_folder()

        # lets start from root and use subfolders in the remote_path so we don't have to manage folders
        self.target_folder = self.root_folder

    def upload_disk_file(self, input_path: str, remote_path: Union[str, Path]):
        stream_size = os.path.getsize(input_path)
        with open(input_path, "rb") as stream:
            return self.upload_stream(stream, stream_size, remote_path)

    def upload_django_file(self, input_field, remote_path: Union[str, Path]):
        stream_size = input_field.size
        stream = input_field.open("rb")
        return self.upload_stream(stream, stream_size, remote_path)

    def upload_json(self, json_data: dict, remote_path: Union[str, Path]):
        json_str = json.dumps(json_data)
        return self.upload_string(json_str, remote_path)

    def upload_string(self, string: str, remote_path: Union[str, Path]):
        bytes_str = string.encode("utf8")
        return self.upload_bytes(bytes_str, remote_path)

    def upload_bytes(self, bytes_: bytes, remote_path: Union[str, Path]):
        stream_size = len(bytes_)
        stream = BytesIO(bytes_)
        return self.upload_stream(stream, stream_size, remote_path)

    def upload_stream(self, stream, stream_size: int, remote_path: Union[str, Path]):
        return self.target_folder.upload_file(
            None,
            remote_path,
            stream=stream,
            stream_size=stream_size,
            conflict_handling=ConflictHandling.replace,
        )
