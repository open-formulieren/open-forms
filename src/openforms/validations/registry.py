import dataclasses
from collections.abc import Iterable

from django.core.exceptions import ValidationError as DJ_ValidationError
from django.utils.translation import gettext_lazy as _

import elasticapm
import structlog
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from .base import BasePlugin

logger = structlog.stdlib.get_logger(__name__)

type StrOrIterable = str | Iterable["StrOrIterable"]


@dataclasses.dataclass()
class ValidationResult:
    is_valid: bool
    messages: list[str] = dataclasses.field(default_factory=list)


def _flat(it: StrOrIterable):
    if isinstance(it, str):
        yield it
    else:
        for v in it:
            if isinstance(v, Iterable):
                yield from _flat(v)
            else:
                yield v


def flatten(iterables: Iterable[StrOrIterable]) -> list[str]:
    return list(_flat(iterables))


class Registry(BaseRegistry[BasePlugin[JSONValue]]):
    """
    A registry for the validations module plugins.

    The plugins can be any Django or DRF style validator;
        eg: a function or callable class (or instance thereof) that raises either a Django or DRF ValidationError
    The validation plugin must be relevant to the component(s);
        eg: the KvKNumberValidator is relevant for textfields but not phoneNumber fields
    """

    module = "validations"

    @elasticapm.capture_span("app.validations.validate")
    def validate(
        self, plugin_id: str, value: JSONValue, submission: Submission
    ) -> ValidationResult:
        log = logger.bind(plugin_id=plugin_id, submission_id=submission.uuid)
        try:
            validator = self._registry[plugin_id]
        except KeyError as exc:
            log.warning("validations.unknown_plugin_called", exc_info=exc)
            return ValidationResult(
                False,
                messages=[
                    _("unknown validation plugin_id '{plugin_id}'").format(
                        plugin_id=plugin_id
                    )
                ],
            )

        if not validator.is_enabled:
            log.info("validations.plugin_not_enabled")
            return ValidationResult(
                False,
                messages=[
                    _("plugin '{plugin_id}' not enabled").format(plugin_id=plugin_id)
                ],
            )

        SerializerClass = validator.value_serializer
        serializer = SerializerClass(data={"value": value})

        # first, run the cheap validation to check that the data actually conforms to the expected schema.
        # only if that succeeds we may invoke the actual validator which potentially performs expensive
        # (network) checks.
        # TODO this will raise a 400 and will not have the same structure as below. This should only
        # raise here if someone's playing with the API directly. Otherwise, the SDK should perform the
        # necessary checks before making a call.
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
