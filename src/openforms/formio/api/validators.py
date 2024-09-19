import logging
from typing import Iterable

from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

import clamd
import magic
from rest_framework import serializers

from openforms.config.models import GlobalConfiguration

logger = logging.getLogger(__name__)


def mimetype_allowed(
    mime_type: str,
    allowed_regular_mime_types: Iterable[str],
    allowed_wildcard_mime_types: Iterable[str],
) -> bool:
    """
    Test if the file mime type passes the allowed_mime_types Formio configuration.

    The test for `allowed_regular_mime_types` is list inclusion. The test for
    `allowed_wildcard_mime_types` is string inclusion (is my string in
    `allowed_regular_mime_types` a substring of `mime_type`?).
    """
    #  no allowlist specified -> everything is allowed
    if not (allowed_regular_mime_types or allowed_wildcard_mime_types):
        return True

    # wildcard specified -> everything is allowed
    if "*" in allowed_wildcard_mime_types:
        return True

    # check1: is mimetype included in regular types?
    if mime_type in allowed_regular_mime_types:
        return True

    # check2: is the string mimetype a substring of any string in wildcard_mime_types?
    return any(
        mime_type.startswith(pattern[:-1]) for pattern in allowed_wildcard_mime_types
    )


class MimeTypeValidator:
    def __init__(self, allowed_mime_types: Iterable[str] | None = None):
        self.any_allowed = allowed_mime_types is None

        allowed_mime_types = allowed_mime_types or []
        normalized = [
            item for string in allowed_mime_types for item in string.split(",")
        ]
        self._regular_mimes = [item for item in normalized if not item.endswith("*")]
        self._wildcard_mimes = [item for item in normalized if item.endswith("*")]

    def __call__(self, value: UploadedFile) -> None:
        head = value.read(2048)
        ext = value.name.split(".")[-1]
        mime_type = magic.from_buffer(head, mime=True)

        # gh #2520
        # application/x-ole-storage on Arch with shared-mime-info 2.0+155+gf4e7cbc-1
        if mime_type in ["application/CDFV2", "application/x-ole-storage"]:
            whole_file = head + value.read()
            mime_type = magic.from_buffer(whole_file, mime=True)

        # gh #4658
        # Windows use application/x-zip-compressed as a mimetype for .zip files, which
        # is deprecated but still we need to support it. Instead, the common case for
        # zip files is application/zip or application/zip-compressed mimetype.
        if (
            value.content_type
            in ["application/x-zip-compressed", "application/zip-compressed"]
            and mime_type == "application/zip"
        ):
            value.content_type = "application/zip"

        if mime_type == "image/heif":
            mime_type = "image/heic"

        if not (
            self.any_allowed
            or mimetype_allowed(mime_type, self._regular_mimes, self._wildcard_mimes)
        ):
            raise serializers.ValidationError(
                _("The provided file is not a valid file type.")
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
                _("The provided file is not a {file_type}.").format(file_type=f".{ext}")
            )
        elif mime_type == "image/heic" and value.content_type in (
            "image/heic",
            "image/heif",
        ):
            return
        elif mime_type != value.content_type:
            raise serializers.ValidationError(
                _("The provided file is not a {file_type}.").format(
                    filename=value.name, file_type=f".{ext}"
                )
            )


class NoVirusValidator:
    def __call__(self, uploaded_file: UploadedFile) -> None:
        config = GlobalConfiguration.get_solo()
        if not config.enable_virus_scan:
            return

        scanner = clamd.ClamdNetworkSocket(
            host=config.clamav_host,
            port=config.clamav_port,
            timeout=config.clamav_timeout,
        )

        uploaded_file.file.seek(0)

        try:
            result = scanner.instream(uploaded_file.file)
        except Exception as exc:
            logger.error("ClamAV error", exc_info=exc)
            raise serializers.ValidationError(
                _(
                    "The virus scan could not be performed at this time. Please retry later."
                )
            )

        # Possible results FOUND|OK|ERROR
        match result["stream"]:
            case ("FOUND", virus_name):
                raise serializers.ValidationError(
                    _(
                        "File did not pass the virus scan. It was found to contain '{virus_name}'."
                    ).format(virus_name=virus_name)
                )
            case ("ERROR", error_message):
                logger.error("ClamAV error: %s", error_message)
                raise serializers.ValidationError(
                    _("The virus scan on this file returned an error.")
                )
            case ("OK", _):
                return

            case (status, message):
                logger.error(
                    "ClamAV returned an unexpected status for a scan: %s, %s",
                    status,
                    message,
                )
                raise serializers.ValidationError(
                    _("The virus scan returned an unexpected status.")
                )
