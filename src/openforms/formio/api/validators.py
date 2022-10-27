from typing import Container, Optional

from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

import magic
from rest_framework import serializers


def mimetype_allowed(mime_type: str, allowed_mime_types: Container[str]) -> bool:
    """
    Test if the file mime type passes the allowed_mime_types Formio configuration.
    """
    #  no allowlist specified -> everything is allowed
    if not allowed_mime_types:
        return True

    # wildcard specified -> everything is allowed
    if "*" in allowed_mime_types:
        return True

    return mime_type in allowed_mime_types


class MimeTypeValidator:
    def __init__(self, allowed_mime_types: Optional[Container[str]] = None):
        self._allowed = allowed_mime_types

    def __call__(self, value: UploadedFile) -> None:
        head = value.read(2048)
        ext = value.name.split(".")[-1]
        mime_type = magic.from_buffer(head, mime=True)
        if not (self._allowed is None or mimetype_allowed(mime_type, self._allowed)):
            raise serializers.ValidationError(
                _("The file '{filename}' is not a valid file type.").format(
                    filename=value.name
                ),
            )

        # Contents is allowed. Do extension or submitted content_type agree?

        if value.content_type == "application/octet-stream":
            m = magic.Magic(extension=True)
            extensions = m.from_buffer(head).split("/")
            # magic db doesn't know any more specific extension(s), so accept the
            # file
            if extensions == ["???"]:
                return

            # we did find actual potential extensions, so we can validate the filename
            # by extension.

            # accept the file if the file extension is present in the extensions detected
            # by libmagic - this means the extension (likely) has not been tampered with
            if ext in extensions:
                return

            raise serializers.ValidationError(
                _("The file '{filename}' is not a {file_type}.").format(
                    filename=value.name, file_type=f".{ext}"
                )
            )
        elif mime_type != value.content_type:
            raise serializers.ValidationError(
                _("The file '{filename}' is not a {file_type}.").format(
                    filename=value.name, file_type=f".{ext}"
                )
            )
