import dataclasses
import logging
from typing import Any, Iterable, List, TypeVar

from django.core.exceptions import ValidationError as DJ_ValidationError
from django.utils.translation import gettext_lazy as _

import elasticapm
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission

from .base import BasePlugin

logger = logging.getLogger(__name__)


@dataclasses.dataclass()
class ValidationResult:
    is_valid: bool
    messages: List[str] = dataclasses.field(default_factory=list)


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


T = TypeVar("T")


class Registry(BaseRegistry[BasePlugin[T]]):
    """
    A registry for the validations module plugins.
    """

    module = "validations"

    @elasticapm.capture_span("app.validations.validate")
    def validate(
        self, plugin_id: str, value: T, submission: Submission
    ) -> ValidationResult:
        try:
            validator = self._registry[plugin_id]
        except KeyError:
            logger.warning("called unregistered plugin_id %s", plugin_id)
            return ValidationResult(
                False,
                messages=[
                    _("unknown validation plugin_id '{plugin_id}'").format(
                        plugin_id=plugin_id
                    )
                ],
            )

        if not getattr(validator, "is_enabled", True):
            return ValidationResult(
                False,
                messages=[
                    _("plugin '{plugin_id}' not enabled").format(plugin_id=plugin_id)
                ],
            )

        SerializerClass = validator.value_serializer
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

    def check_plugin(self, plugin: BasePlugin):
        if not hasattr(plugin, "value_serializer"):
            raise ValueError(
                f"Validator '{plugin.identifier}' must have a 'value_serializer' attribute."
            )


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
