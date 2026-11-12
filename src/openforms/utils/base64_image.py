import base64
import binascii
import mimetypes

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import magic


def decode_base64_image(value: str) -> tuple[bytes, str, str]:
    """
    Decode a Base64 encoded image and return it as a DecodedBase64Image object.

    :param value: Base64 encoded image content.
    :return: Tuple of decoded content bytes, extension and mime_type.
    """
    # decode as base64 - note that this loads the entire file into memory so
    # appropriate memory constraints limits should be set.
    try:
        file_data: bytes = base64.b64decode(value, validate=True)
    except (TypeError, binascii.Error, ValueError):
        raise ValidationError(
            _("Failed to decode the (image) file data."),
            code="invalid",
        )

    # guess the mime type from the first 2KiB & validate
    mime_type: str = magic.from_buffer(file_data[:2048], mime=True)
    if not mime_type:  # pragma: no cover / I don't know how to test this
        raise ValidationError(
            _("Could not detect the file content type."), code="invalid"
        )
    assert isinstance(mime_type, str)

    # get the extension from the mime type
    extension = mimetypes.guess_extension(mime_type)
    if extension is None:  # pragma: no cover / I don't know how to test this
        raise ValidationError(
            _(
                "Could not determine an extension for the content type {mime_type}."
            ).format(mime_type=mime_type),
            code="invalid",
        )
    assert isinstance(extension, str)

    assert extension.startswith(".")
    extension = extension.lower()

    return file_data, extension, mime_type
