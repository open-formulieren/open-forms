import logging

from rest_framework.exceptions import ValidationError

from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable

from ..registry import Registry

logger = logging.getLogger(__name__)


def fetch_prefill_values(
    submission: Submission,
    register: Registry,
    variables: list[SubmissionValueVariable],
) -> dict[str, JSONEncodable]:
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    values: dict[str, JSONEncodable] = {}
    for variable in variables:
        plugin = register[variable.form_variable.prefill_plugin]
        options_serializer = plugin.options(data=variable.form_variable.prefill_options)

        try:
            options_serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            logevent.prefill_retrieve_failure(submission, plugin, exc)

        try:
            values = plugin.get_prefill_values_from_options(
                submission, options_serializer.validated_data
            )
        except Exception as exc:
            logger.exception(f"exception in prefill plugin '{plugin.identifier}'")
            logevent.prefill_retrieve_failure(submission, plugin, exc)
        else:
            if values:
                logevent.prefill_retrieve_success(submission, plugin, values)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, values)

    return values
