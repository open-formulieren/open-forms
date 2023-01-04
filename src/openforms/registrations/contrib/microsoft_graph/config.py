from pathlib import Path

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

DEFAULT_BASE_PATH = "/open-forms/"


def is_absolute(value: str) -> None:
    path = Path(value)
    if not path.is_absolute():
        raise serializers.ValidationError(
            _("The path needs to be absolute - i.e. it needs to start with a /")
        )


def is_relative(value: str) -> None:
    path = Path(value)
    if path.is_absolute():
        raise serializers.ValidationError(
            _("The path needs to be relative - i.e. it cannot start with a /")
        )


class MicrosoftGraphOptionsSerializer(
    JsonSchemaSerializerMixin, serializers.Serializer
):
    base_path = serializers.CharField(
        label=_("base path"),
        help_text=_(
            "The path of the folder where folders containing Open-Forms related documents will be created. "
            "It should be an absolute path - i.e. it should start with /"
        ),
        default=DEFAULT_BASE_PATH,
        validators=[is_absolute],
    )
    additional_path = serializers.CharField(
        label=_("additional path"),
        help_text=_(
            "Additional path allowing date-element placeholders, for example {year}-{month}-{day}/. "
            "It should be a relative path - i.e. it should NOT start with /"
        ),
        required=False,
        validators=[is_relative],
    )
    drive_id = serializers.CharField(
        label=_("drive ID"),
        help_text=_(
            "ID of the drive to use. If left empty, the default drive will be used."
        ),
        required=False,
    )
