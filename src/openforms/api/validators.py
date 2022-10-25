from pathlib import PurePath
from typing import Callable, Container, Optional

from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

import magic
from rest_framework import serializers

from openforms.formio.service import mimetype_allowed


class AllOrNoneRequiredFieldsValidator:
    """
    Validate that the set of fields is present as soon as one field is provided.

    Field values are checked to be truthy to determine if they are provided or not.
    """

    message = _("The fields {fields} must all be provided if one of them is provided.")
    code = "required"
    requires_context = True

    def __init__(self, *fields: str):
        self.fields = fields

    def __call__(self, data: dict, serializer: serializers.Serializer):
        values = [data.get(field) for field in self.fields]
        if any(values) and not all(values):
            err = self.message.format(fields=", ".join(self.fields))
            raise serializers.ValidationError(err, code=self.code)


class MimeTypeValidator:
    def __init__(self, allowed_mime_types: Optional[Container[str]] = None):
        self._allowed = allowed_mime_types

    def __call__(self, value: UploadedFile) -> None:
        head = value.read(2048)
        ext = PurePath(value.name).suffix
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
            if extensions == ["???"]:
                pass  # magic db doesn't know correct extensions
            elif ext not in extensions:
                raise serializers.ValidationError(
                    _("The file '{filename}' is not a {file_type}.").format(
                        filename=value.name, file_type=ext
                    )
                )
        elif mime_type != value.content_type:
            raise serializers.ValidationError(
                _("The file '{filename}' is not a {file_type}.").format(
                    filename=value.name, file_type=ext
                )
            )
