import logging
from typing import Any

from rest_framework.exceptions import ValidationError

from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission

from ..registry import Registry

logger = logging.getLogger(__name__)


def check_if_prefill_plugin_mapping_needed(form_variable: FormVariable):
    """
    This is used for user_defined variables which have the mappings for pre-filling
    component variables. These are not aware of the prefill_plugin so we have to update them.
    """
    mappings = form_variable.prefill_options["variables_mapping"]
    form_variable_keys = [item["variable_key"] for item in mappings]
    form_variables_for_update = FormVariable.objects.filter(key__in=form_variable_keys)
    for variable in form_variables_for_update:
        variable.prefill_plugin = form_variable.prefill_plugin

    FormVariable.objects.bulk_update(form_variables_for_update, ["prefill_plugin"])


def fetch_prefill_values(
    submission: Submission,
    register: Registry,
    form_variables: list[FormVariable],
) -> dict[str, (dict[str, Any] | dict[str, str])]:
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    values = {}
    for form_var in form_variables:
        check_if_prefill_plugin_mapping_needed(form_var)

        plugin = register[form_var.prefill_plugin]
        options_serializer = plugin.options(data=form_var.prefill_options)

        try:
            options_serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            logevent.prefill_retrieve_failure(submission, plugin, exc)
            values = {}

        try:
            values = plugin.get_prefill_values_from_options(
                submission, options_serializer.validated_data
            )
        except Exception as exc:
            logger.exception(f"exception in prefill plugin '{plugin.identifier}'")
            logevent.prefill_retrieve_failure(submission, plugin, exc)
            values = {}
        else:
            if values:
                logevent.prefill_retrieve_success(submission, plugin, values)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, values)

    return values
