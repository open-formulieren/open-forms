from pathlib import PurePath

from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

import magic
from rest_framework import serializers


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


def mime_type_validator(value: UploadedFile) -> UploadedFile:
    """
    Validate whether value has the mime-type it says it has.
    """
    if value.content_type == "application/octet-stream":
        ext = PurePath(value.name).suffix
        m = magic.Magic(extension=True)
        extensions = m.from_buffer(value.read(2048)).split("/")
        if extensions == ["???"]:
            pass  # magic db doesn't know extensions; let form validation decide on mime-type
        elif ext not in extensions:
            raise serializers.ValidationError(
                _("The file %(filename)s is not a %(file_type)s.")
                % {"filename": value.name, "file_type": ext}
            )
    elif magic.from_buffer(value.read(2048), mime=True) != value.content_type:
        raise serializers.ValidationError(
            _("The file %(filename)s is not a %(file_type)s.")
            % {"filename": value.name, "file_type": value.content_type}
        )
    return value
