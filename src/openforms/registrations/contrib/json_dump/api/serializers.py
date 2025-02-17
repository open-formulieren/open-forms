from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.formio.api.fields import FormioVariableKeyField


class FixedMetadataVariableSerializer(serializers.Serializer):
    variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Fixed metadata variable key list"),
        help_text=_(
            "A list of fixed variables to use in the metadata. These include the "
            "registration variables of the JSON dump plugin."
        ),
        default=[
            "public_reference",
            "form_name",
            "form_version",
            "form_id",
            "registration_timestamp",
            "auth_type",
        ],
        read_only=True,
    )
