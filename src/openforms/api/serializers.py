from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class FieldValidationErrorSerializer(serializers.Serializer):
    """
    Validation error format, following the NL API Strategy.

    See https://docs.geostandaarden.nl/api/API-Strategie/ and
    https://docs.geostandaarden.nl/api/API-Strategie-ext/#error-handling-0
    """

    name = serializers.CharField(help_text=_("Name of the field with invalid data"))
    code = serializers.CharField(help_text=_("System code of the type of error"))
    reason = serializers.CharField(
        help_text=_("Explanation of what when wrong with the data")
    )


class FoutSerializer(serializers.Serializer):
    """
    Error format for HTTP 4xx and 5xx errors.

    See https://docs.geostandaarden.nl/api/API-Strategie-ext/#error-handling-0 for the NL API strategy guidelines.
    """

    type = serializers.CharField(
        help_text=_("URI reference to the error type, intended for developers"),
        required=False,
        allow_blank=True,
    )
    code = serializers.CharField(
        help_text=_("System code indicating the type of error")
    )
    title = serializers.CharField(help_text=_("Generic title for the type of error"))
    status = serializers.IntegerField(help_text=_("The HTTP status code"))
    detail = serializers.CharField(
        help_text=_("Extra information about the error, if available")
    )
    instance = serializers.CharField(
        help_text=_(
            "URI with reference to this specific occurrence of the error. "
            "This can be used in conjunction with server logs, for example."
        )
    )


class ValidatieFoutSerializer(FoutSerializer):
    invalid_params = FieldValidationErrorSerializer(many=True)
