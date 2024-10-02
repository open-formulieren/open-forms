import logging
from collections import defaultdict
from typing import Any

import elasticapm
from glom import Path, assign
from zgw_consumers.concurrent import parallel

from openforms.forms.models import FormVariable
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.models import Submission

from ..registry import Registry

logger = logging.getLogger(__name__)


def fetch_prefill_values(
    submission: Submission, register: Registry, form_variables: list[FormVariable]
) -> dict[str, dict[str, Any]]:
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    # grouped_fields is a dict of the following shape:
    # {"plugin_id": {"identifier_role": ["attr_1", "attr_2"]}}
    # "identifier_role" is either "main" or "authorizee"
    grouped_fields: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for form_variable in form_variables:
        plugin_id = form_variable.prefill_plugin
        identifier_role = form_variable.prefill_identifier_role
        attribute_name = form_variable.prefill_attribute

        grouped_fields[plugin_id][identifier_role].append(attribute_name)

    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(
        item: tuple[str, str, list[str]]
    ) -> tuple[str, str, dict[str, Any]]:
        plugin_id, identifier_role, fields = item
        plugin = register[plugin_id]
        if not plugin.is_enabled:
            raise PluginNotEnabled()

        try:
            values = plugin.get_prefill_values(submission, fields, identifier_role)
        except Exception as e:
            logger.exception(f"exception in prefill plugin '{plugin_id}'")
            logevent.prefill_retrieve_failure(submission, plugin, e)
            values = {}
        else:
            if values:
                logevent.prefill_retrieve_success(submission, plugin, fields)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, fields)

        return plugin_id, identifier_role, values

    invoke_plugin_args = []
    for plugin_id, field_groups in grouped_fields.items():
        for identifier_role, fields in field_groups.items():
            invoke_plugin_args.append((plugin_id, identifier_role, fields))

    with parallel() as executor:
        results = executor.map(invoke_plugin, invoke_plugin_args)

    collected_results = {}
    for plugin_id, identifier_role, values_dict in list(results):
        assign(
            collected_results,
            Path(plugin_id, identifier_role),
            values_dict,
            missing=dict,
        )

    return collected_results
