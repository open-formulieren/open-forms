from collections.abc import Iterable

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers


class ValidateQueryStringParametersMixin:
    validate_params: Iterable[OpenApiParameter] = ()

    def validate_query_parameters(self) -> dict[OpenApiParameter, str | None]:
        errors, extracted = {}, {}

        for param in self.validate_params:
            value = self.request.GET.get(param.name)
            if not value and param.required:
                error_message = _("The '{param}' query parameter is required.").format(
                    param=param.name
                )
                errors[param.name] = serializers.ErrorDetail(
                    error_message, code="required"
                )
            elif value and param.enum and value not in param.enum:
                errors[param.name] = _(
                    "The value '{value}' is not a valid value for the '{param}' query "
                    "parameter. Valid values are: {valid_values}."
                ).format(
                    param=param.name, value=value, valid_values=", ".join(param.enum)
                )
            else:
                extracted[param] = value

        if errors:
            raise serializers.ValidationError(errors)

        return extracted
