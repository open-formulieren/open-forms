from typing import Dict, Iterable, Optional

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers


class ValidateQueryStringParametersMixin:
    validate_params: Iterable[OpenApiParameter] = ()

    def validate_query_parameters(self) -> Dict[OpenApiParameter, Optional[str]]:
        errors, extracted = {}, {}

        for param in self.validate_params:
            value = self.request.GET.get(param.name)
            if not value and param.required:
                errors[param.name] = _(
                    "The '{param}' query parameter is required."
                ).format(param=param.name)
            else:
                extracted[param] = value

        if errors:
            raise serializers.ValidationError(errors)

        return extracted
