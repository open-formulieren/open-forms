import dataclasses
import logging
from typing import Any, Callable, Iterable, List, Type, Union

from django.core.exceptions import ValidationError as DJ_ValidationError
from django.utils.translation import gettext_lazy as _

import elasticapm
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)

ValidatorType = Callable[[Any, Submission], bool]


class StringValueSerializer(serializers.Serializer):
    """A default serializer that accepts ``value`` as a string."""

    value = serializers.CharField()


@dataclasses.dataclass()
class ValidationResult:
    is_valid: bool
    messages: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass()
class RegisteredValidator:
    identifier: str
    verbose_name: str
    callable: ValidatorType
    for_components: tuple[str]
    is_demo_plugin: bool = False
    # TODO always enabled for now, see: https://github.com/open-formulieren/open-forms/issues/1149
    is_enabled: bool = True

    def __call__(self, *args, **kwargs) -> bool:
        return self.callable(*args, **kwargs)


def flatten(iterables: Iterable) -> List[str]:
    def _flat(it):
        if isinstance(it, str):
            yield it
        else:
            for v in it:
                if isinstance(v, Iterable):
                    yield from _flat(v)
                else:
                    yield v

    return list(_flat(iterables))


def filter_empty_values(value: Any) -> Any:
    if not isinstance(value, dict):
        # Let the serializer raise a the validation error
        return value
    return {k: v for k, v in value.items() if v}


class Registry(BaseRegistry[RegisteredValidator]):
    """
    A registry for the validations module plugins.

    The plugins can be any Django or DRF style validator;
        eg: a function or callable class (or instance thereof) that raises either a Django or DRF ValidationError
    The validation plugin must be relevant to the component(s);
        eg: the KvKNumberValidator is relevant for textfields but not phoneNumber fields
    """

    module = "validations"

    def __call__(
        self,
        identifier: str,
        verbose_name: str,
        is_demo_plugin: bool = False,
        for_components: tuple[str] = tuple(),
        *args,
        **kwargs,
    ) -> Callable:
        def decorator(validator: Union[Type, ValidatorType]):
            if identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{identifier}' is already present "
                    "in the registry."
                )

            call = validator
            if not hasattr(call, "value_serializer"):
                raise ValueError(
                    f"Validator '{identifier}' doesn't have a 'value_serializer' attribute."
                )
            if isinstance(call, type):
                call = validator()
            if not callable(call):
                raise ValueError(f"Validator '{identifier}' is not callable.")

            self._registry[identifier] = RegisteredValidator(
                identifier=identifier,
                verbose_name=verbose_name,
                callable=call,
                for_components=for_components,
                is_demo_plugin=is_demo_plugin,
            )
            return validator

        return decorator

    @elasticapm.capture_span("app.validations.validate")
    def validate(
        self, plugin_id: str, value: Any, submission: Submission
    ) -> ValidationResult:
        try:
            validator = self._registry[plugin_id]
        except KeyError:
            logger.warning(f"called unregistered plugin_id '{plugin_id}'")
            return ValidationResult(
                False,
                messages=[
                    _("unknown validation plugin_id '{plugin_id}'").format(
                        plugin_id=plugin_id
                    )
                ],
            )

        if not getattr(validator.callable, "is_enabled", True):
            return ValidationResult(
                False,
                messages=[
                    _("plugin '{plugin_id}' not enabled").format(plugin_id=plugin_id)
                ],
            )

        SerializerClass = validator.callable.value_serializer
        serializer = SerializerClass(data={"value": filter_empty_values(value)})
        serializer.is_valid(raise_exception=True)

        try:
            validator(serializer.data["value"], submission)
        except (DJ_ValidationError, DRF_ValidationError) as e:
            errors = serializers.as_serializer_error(e)
            messages = flatten(errors.values())
            return ValidationResult(False, messages=messages)
        else:
            return ValidationResult(True)


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
