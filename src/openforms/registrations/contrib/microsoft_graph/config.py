from pathlib import Path

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

DEFAULT_FOLDER_PATH = "/open-forms/"


def is_absolute(value: str) -> None:
    path = Path(value)
    if not path.is_absolute():
        raise serializers.ValidationError(
            _("The path needs to be absolute - i.e. it needs to start with a /")
        )


class MicrosoftGraphOptionsSerializer(
    JsonSchemaSerializerMixin, serializers.Serializer
):
    folder_path = serializers.CharField(
        label=_("folder path"),
        help_text=_(
            "The path of the folder where folders containing Open-Forms related documents will be created. "
            "It should be an absolute path - i.e. it should start with /"
        ),
        default=DEFAULT_FOLDER_PATH,
        validators=[is_absolute],
    )
    drive_id = serializers.CharField(
        label=_("drive ID"),
        help_text=_(
            "ID of the drive to use. If left empty, the default drive will be used."
        ),
        required=False,
    )
