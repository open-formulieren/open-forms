from typing import Any, Callable, Generic, TypeVar, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import get_error_detail

from .utils import get_model_serializer_instance


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


MT = TypeVar("MT", bound=models.Model)


class ModelValidator(Generic[MT]):
    """
    Turn a Django validator of model instances into a DRF validator.

    For example:

    >>> from django.core.exceptions import ValidationError
    >>>
    >>> def validate_service_has_oas(service: Service):
    ...     "Check the service has an OAS file or OAS url"
    ...     if not service.oas and not service.oas_file:
    ...         raise ValidationError({
    ...             "oas": _("Set either oas or oas_file"),
    ...             "oas_file": _("Set either oas or oas_file"),
    ...         })
    ...

    Then `ModelValidator(validate_service_has_oas)` will be validator you can use on a
    Serializer.

    You can annotate `ModelValidator` with a type:
    `ModelValidator[Service](validate_service_has_oas)` should typecheck whether the validator
    function that is passed takes the right type of Model instance.
    """

    requires_context = True

    def __init__(self, validator_func: Callable[[MT], None]):
        self.validator_func = validator_func

    def __call__(
        self, attrs: dict[str, Any], serializer: serializers.ModelSerializer
    ) -> dict[str, Any]:
        model_fields = [f.name for f in serializer.Meta.model._meta.get_fields()]

        # Assign the serializer data to the model instance as the model serializer would
        # do for a create or update when all the data is valid - this allows validator
        # functions to operate on model instances and shared logic between serializers
        # and Django model.clean() methods.
        instance = cast(MT, get_model_serializer_instance(serializer))
        for key, value in attrs.items():
            if key not in model_fields:
                continue
            setattr(instance, key, value)

        try:
            self.validator_func(instance)
        except DjangoValidationError as exc:
            detail = get_error_detail(exc)
            raise serializers.ValidationError(detail)
        return attrs
