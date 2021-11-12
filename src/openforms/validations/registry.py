import dataclasses
import logging
from typing import Callable, Iterable, List, Type, Union

from django.core.exceptions import ValidationError as DJ_ValidationError

from rest_framework.exceptions import ValidationError as DRF_ValidationError
from rest_framework.serializers import as_serializer_error

from openforms.plugins.registry import BaseRegistry

logger = logging.getLogger(__name__)

ValidatorType = Callable[[str], None]


@dataclasses.dataclass()
class ValidationResult:
    is_valid: bool
    messages: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass()
class RegisteredValidator:
    identifier: str
    verbose_name: str
    callable: ValidatorType
    is_demo_plugin: bool = False

    def __call__(self, value):
        return self.callable(value)


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


class Registry(BaseRegistry):
    """
    A registry for the validations module plugins.

    The plugins can be any Django or DRF style validator;
        eg: a function or callable class (or instance thereof) that raises either a Django or DRF ValidationError
    """

    def __call__(
        self,
        identifier: str,
        verbose_name: str,
        is_demo_plugin: bool = False,
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
            if isinstance(call, type):
                call = validator()
            if not callable(call):
                raise ValueError(f"Validator '{identifier}' is not callable.")

            self._registry[identifier] = RegisteredValidator(
                identifier=identifier,
                verbose_name=verbose_name,
                callable=call,
                is_demo_plugin=is_demo_plugin,
            )
            return validator

        return decorator

    def validate(self, plugin_id: str, value: str) -> ValidationResult:
        try:
            validator = self._registry[plugin_id]
        except KeyError:
            logger.warning(f"called unregistered plugin_id '{plugin_id}'")
            return ValidationResult(
                False, messages=[f"unknown validation plugin_id '{plugin_id}'"]
            )

        try:
            validator(value)
        except (DJ_ValidationError, DRF_ValidationError) as e:
            errors = as_serializer_error(e)
            messages = flatten(errors.values())
            return ValidationResult(False, messages=messages)
        else:
            return ValidationResult(True)


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
