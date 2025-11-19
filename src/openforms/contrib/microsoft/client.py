"""
Microsoft (graph) API client.

This client implementation wraps around the API client/integration implemented in the
O365 package. While it uses requests-oauth2client under the hood, we opt to *not*
use our own :module:`api_client` implementation here, as the typical Dutch API/service
requirements such as mTLS are not relevant. The service model definition also does not
allow configuring any of those aspects.
"""

import json
import os
from io import BytesIO
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Literal, TypedDict

from django.core.serializers.json import DjangoJSONEncoder

from O365 import Account
from O365.drive import Folder

from .exceptions import MSAuthenticationError
from .models import MSGraphService


class MSGraphClient:
    """
    wrapper to setup O365 graph client from a MSGraphService
    """

    # .default works fine for our credentials use
    scopes = [
        "https://graph.microsoft.com/.default",
    ]

    def __init__(self, service: MSGraphService, force_auth=False):
        self.service = service

        self.account = Account(
            (self.service.client_id, self.service.secret),
            auth_flow_type="credentials",
            tenant_id=self.service.tenant_id,
            # We are passing timeout through the Account instance and then to the
            # Connection instance which handles the timeout parameter in the __init__
            timeout=self.service.timeout,
        )
        if force_auth or not self.account.is_authenticated:
            if not self.account.authenticate(scopes=self.scopes):
                raise MSAuthenticationError("cannot authenticate: check credentials")

    @property
    def is_authenticated(self):
        return self.account.is_authenticated


class UploadHelperOptions(TypedDict):
    folder_path: str
    drive_id: str


type ConflictHandling = Literal["fail", "replace", "rename"]


class MSGraphUploadHelper:
    """
    helper for uploading
    - navigate to our folder in the account
    - upload various objects in stream mode to support large files
    """

    conflict_handling: ConflictHandling = "replace"

    # TODO wrap upload_()-variations in single function and auto-detect object type

    def __init__(self, client: MSGraphClient, options: UploadHelperOptions):
        self.client = client

        self.storage = self.client.account.storage()

        if drive_id := options["drive_id"]:
            self.drive = self.storage.get_drive(drive_id)
        else:
            self.drive = self.storage.get_default_drive()

        assert self.drive is not None
        root_folder = self.drive.get_root_folder()
        # lets start from root and use subfolders in the remote_path so we don't have to manage folders
        self.target_folder = root_folder

    def upload_disk_file(self, input_path: str, remote_path: PurePosixPath | None):
        stream_size = os.path.getsize(input_path)
        with open(input_path, "rb") as stream:
            return self.upload_stream(stream, stream_size, remote_path)

    def upload_django_file(self, input_field, remote_path: PurePosixPath | None):
        stream_size = input_field.size
        with input_field.open("rb") as stream:
            return self.upload_stream(stream, stream_size, remote_path)

    def upload_data_as_json(self, data: dict, remote_path: PurePosixPath | None):
        json_str = json.dumps(data, cls=DjangoJSONEncoder)
        return self.upload_string(json_str, remote_path)

    def upload_string(self, string: str, remote_path: PurePosixPath | None):
        bytes_str = string.encode("utf8")
        return self.upload_bytes(bytes_str, remote_path)

    def upload_bytes(self, bytes_: bytes, remote_path: PurePosixPath | None):
        stream_size = len(bytes_)
        stream = BytesIO(bytes_)
        return self.upload_stream(stream, stream_size, remote_path)

    def upload_stream(
        self, stream, stream_size: int, remote_path: PurePosixPath | None
    ):
        if TYPE_CHECKING:
            assert isinstance(self.target_folder, Folder)
        return self.target_folder.upload_file(
            None,
            # upload_file says it accepts strings or Path objects
            # (https://github.com/O365/python-o365/blob/master/O365/drive.py#L1239), but Path objects give errors
            str(remote_path),
            stream=stream,
            stream_size=stream_size,
            conflict_handling=self.conflict_handling,
        )
