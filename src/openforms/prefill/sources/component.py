import logging
from collections import defaultdict

import elasticapm
from zgw_consumers.concurrent import parallel

from openforms.plugins.exceptions import PluginNotEnabled
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
    submission_variables: list[SubmissionValueVariable],
) -> dict[str, JSONEncodable]:
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    # grouped_fields is a dict of the following shape:
    # {"plugin_id": {"identifier_role": [{"attr_1":"var1_key", "attr_2":"var2_key"}]}}
    # "identifier_role" is either "main" or "authorizee"

    grouped_fields: defaultdict[str, defaultdict[str, list[dict[str, str]]]] = (
        defaultdict(lambda: defaultdict(list))
    )

    for variable in submission_variables:
        plugin_id = variable.form_variable.prefill_plugin
        identifier_role = variable.form_variable.prefill_identifier_role
        attribute_name = variable.form_variable.prefill_attribute

        grouped_fields[plugin_id][identifier_role].append(
            {attribute_name: variable.form_variable.key}
        )

    mappings: dict[str, JSONEncodable] = {}

    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(
        item: tuple[str, str, list[dict[str, str]]]
    ) -> tuple[list[dict[str, str]], dict[str, JSONEncodable]]:
        plugin_id, identifier_role, fields = item
        plugin = register[plugin_id]

        if not plugin.is_enabled:
            raise PluginNotEnabled()

        attributes = [attribute for field in fields for attribute in field]
        try:
            values = plugin.get_prefill_values(submission, attributes, identifier_role)
        except Exception as e:
            logger.exception(f"exception in prefill plugin '{plugin_id}'")
            logevent.prefill_retrieve_failure(submission, plugin, e)
            values = {}
        else:
            if values:
                logevent.prefill_retrieve_success(submission, plugin, fields)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, fields)
        return fields, values

    invoke_plugin_args = []
    for plugin_id, field_groups in grouped_fields.items():
        for identifier_role, fields in field_groups.items():
            invoke_plugin_args.append((plugin_id, identifier_role, fields))

    with parallel() as executor:
        results = executor.map(invoke_plugin, invoke_plugin_args)

    for fields, values in list(results):
        for attribute, value in values.items():
            for field in fields:
                for attr, var_key in field.items():
                    if attribute == attr:
                        mappings[var_key] = value
    return mappings
