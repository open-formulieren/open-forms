import logging
from typing import Any

from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission

from ..registry import Registry

logger = logging.getLogger(__name__)


def fetch_prefill_values(
    submission: Submission,
    register: Registry,
    form_variables: list[FormVariable],
) -> dict[str, (dict[str, Any] | dict[str, str])]:
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    values = {}
    for form_var in form_variables:
        plugin = register[form_var.prefill_plugin]

        try:
            values = plugin.get_prefill_values_from_mappings(submission, form_var)
        except Exception as e:
            logger.exception(f"exception in prefill plugin '{plugin.identifier}'")
            logevent.prefill_retrieve_failure(submission, plugin, e)
            values = {}
        else:
            if values:
                logevent.prefill_retrieve_success(submission, plugin, values)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, values)

    return values
