from typing import Any

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.utils import underscore_to_camel


class DummySerializer(serializers.Serializer):
    """
    Defines a valid-name-having empty serializer.

    drf-spectacular does serializer name validation, and using plain
    :class:`serializers.Serializer` in some places throws warnings because the schema
    component name resolves to an empty string.

    In some places we need to map something to an empty serializer (we can't just say
    there is _no_ serializer), so there we can use the DummySerializer to avoid schema
    generation warnings.
    """


class FieldValidationErrorSerializer(serializers.Serializer):
    """
    Validation error format, following the NL API Strategy.

    See https://docs.geostandaarden.nl/api/API-Strategie/ and
    https://docs.geostandaarden.nl/api/API-Strategie-ext/#error-handling-0
    """

    name = serializers.CharField(help_text=_("Name of the field with invalid data"))
    code = serializers.CharField(help_text=_("System code of the type of error"))
    reason = serializers.CharField(
        help_text=_("Explanation of what went wrong with the data")
    )


class ExceptionSerializer(serializers.Serializer):
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


class ValidationErrorSerializer(ExceptionSerializer):
    invalid_params = FieldValidationErrorSerializer(many=True)


class ListWithChildSerializer(serializers.ListSerializer):
    child_serializer_class = None  # class or dotted import path
    bulk_create_kwargs: dict[str, Any] | None = None

    def __init__(self, *args, **kwargs):
        child_serializer_class = self.get_child_serializer_class()
        kwargs.setdefault("child", child_serializer_class())
        super().__init__(*args, **kwargs)

    def get_child_serializer_class(self):
        if isinstance(self.child_serializer_class, str):
            self.child_serializer_class = import_string(self.child_serializer_class)
        return self.child_serializer_class

    def process_object(self, obj):
        return obj

    def preprocess_validated_data(self, validated_data):
        return validated_data

    def create(self, validated_data):
        validated_data = self.preprocess_validated_data(validated_data)
        model = self.get_child_serializer_class().Meta.model
        objects_to_create = []
        for data_dict in validated_data:
            obj = model(**data_dict)
            objects_to_create.append(self.process_object(obj))

        kwargs = self.bulk_create_kwargs or {}
        return model._default_manager.bulk_create(objects_to_create, **kwargs)


class PublicFieldsSerializerMixin:
    # Mixin to distinguish between public and private serializer fields
    # Public fields are displayed for all users and private fields are (by default) only
    # displayed for staff users.

    # Example usage:

    #     class PersonSerializer(PublicFieldsSerializerMixin, serializers.ModelSerializer):
    #         class Meta:
    #             fields = (
    #                 "first_name",
    #                 "family_name",
    #                 "phone_number",
    #             )
    #             public_fields = (
    #                 "first_name",
    #                 "family_name",
    #             )

    @classmethod
    def _get_admin_field_names(cls, camelize=True) -> list[str]:
        formatter = underscore_to_camel if camelize else lambda x: x
        return [
            formatter(name)
            for name in cls.Meta.fields
            if name not in cls.Meta.public_fields
        ]

    def get_fields(self):
        fields = super().get_fields()

        request = self.context.get("request")
        view = self.context.get("view")
        is_api_schema_generation = (
            getattr(view, "swagger_fake_view", False) if view else False
        )
        is_mock_request = request and getattr(
            request, "is_mock_request", is_api_schema_generation
        )

        admin_only_fields = self._get_admin_field_names(camelize=False)

        # filter public fields if not staff and not exporting or schema generating
        # request.is_mock_request is set by the export serializers (possibly from management command etc)
        # also this can be called from schema generator without request
        if request and not is_mock_request:
            if not request.user.is_staff:
                for admin_field in admin_only_fields:
                    del fields[admin_field]

        return fields
