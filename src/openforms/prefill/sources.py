from collections import defaultdict

from django.core.exceptions import PermissionDenied

import elasticapm
import structlog
from opentelemetry import trace
from rest_framework.exceptions import ValidationError
from zgw_consumers.concurrent import parallel

from openforms.logging import audit_logger
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable

from .base import BasePlugin
from .constants import IdentifierRoles
from .exceptions import PrefillSkipped
from .registry import Registry

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.prefill.sources")


def fetch_prefill_values_from_attribute(
    submission: Submission,
    register: Registry,
    submission_variables: list[SubmissionValueVariable],
) -> dict[str, JSONEncodable]:
    # grouped_fields is a dict of the following shape:
    # {"plugin_id": {"identifier_role": [{"attr_1":"var1_key", "attr_2":"var2_key"}]}}
    # "identifier_role" is either "main" or "authorizee"

    grouped_fields: defaultdict[str, defaultdict[str, list[dict[str, str]]]] = (
        defaultdict(lambda: defaultdict(list))
    )

    for variable in submission_variables:
        assert variable.form_variable is not None
        plugin_id: str = variable.form_variable.prefill_plugin
        identifier_role = IdentifierRoles(
            variable.form_variable.prefill_identifier_role
        )
        attribute_name: str = variable.form_variable.prefill_attribute

        grouped_fields[plugin_id][identifier_role].append(
            {attribute_name: variable.form_variable.key}
        )

    mappings: dict[str, JSONEncodable] = {}

    @tracer.start_as_current_span(
        name="invoke-plugin", attributes={"span.type": "app", "span.subtype": "prefill"}
    )
    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(
        item: tuple[BasePlugin, IdentifierRoles, list[dict[str, str]]],
    ) -> tuple[list[dict[str, str]], dict[str, JSONEncodable]]:
        plugin, identifier_role, fields = item
        log = logger.bind(
            submission_uuid=str(submission.uuid),
            plugin=plugin,
            for_role=identifier_role,
            fields=fields,
        )
        audit_log = audit_logger.bind(**structlog.get_context(log))

        if not plugin.is_enabled:
            log.debug("plugin_disabled")
            raise PluginNotEnabled()

        if not plugin.verify_auth_plugin_requirement(submission):
            log.info("prefill.plugin.auth_plugin_requirements_not_met")
            return fields, {}

        attributes = [attribute for field in fields for attribute in field]
        audit_log = audit_log.bind(attributes=attributes)
        log.debug("prefill.plugin.lookup_attributes", attributes=attributes)
        try:
            values = plugin.get_prefill_values(submission, attributes, identifier_role)
        except PrefillSkipped:
            log.info("prefill.plugin.skipped")
            values = {}
        except Exception as e:
            audit_log.exception("prefill.plugin.retrieve_failure", exc_info=e)
            values = {}
        else:
            audit_log.info(
                "prefill_retrieve_success" if values else "prefill_retrieve_empty"
            )
        return fields, values

    invoke_plugin_args = []
    for plugin_id, field_groups in grouped_fields.items():
        plugin = register[plugin_id]

        # check if we need to run the plugin when the user is authenticated
        auth_info = getattr(submission, "auth_info", None)
        if auth_info and auth_info.attribute not in plugin.requires_auth:
            continue

        for identifier_role, fields in field_groups.items():
            invoke_plugin_args.append((plugin, identifier_role, fields))

    with parallel() as executor:
        results = executor.map(invoke_plugin, invoke_plugin_args)

    for fields, values in list(results):
        for attribute, value in values.items():
            for field in fields:
                for attr, var_key in field.items():
                    if attribute == attr:
                        mappings[var_key] = value
    return mappings


def fetch_prefill_values_from_options(
    submission: Submission,
    register: Registry,
    variables: list[SubmissionValueVariable],
) -> dict[str, JSONEncodable]:
    values: dict[str, JSONEncodable] = {}
    for variable in variables:
        assert variable.form_variable is not None
        plugin = register[variable.form_variable.prefill_plugin]
        log = logger.bind(plugin=plugin)

        if not plugin.is_enabled:
            log.debug("plugin_disabled")
            continue

        if not plugin.verify_auth_plugin_requirement(submission):
            log.info("prefill.plugin.auth_plugin_requirements_not_met")
            continue

        raw_options = variable.form_variable.prefill_options
        log = logger.bind(
            variable=variable.key, plugin=plugin, submission_uuid=str(submission.uuid)
        )
        audit_log = audit_logger.bind(**structlog.get_context(log))

        # validate the options before processing them
        options_serializer = plugin.options(data=raw_options)
        try:
            options_serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            audit_log.warning(
                "prefill.plugin.retrieve_failure",
                reason="invalid_options",
                exc_info=exc,
            )
            continue

        plugin_options = options_serializer.validated_data

        # If an `initial_data_reference` was passed, we must verify that the
        # authenticated user is the owner of the referenced object
        has_initial_data_reference = bool(submission.initial_data_reference)
        log.debug(
            "prefill.plugin.verify_initial_data_ownership",
            has_initial_data_reference=has_initial_data_reference,
        )
        if has_initial_data_reference:
            try:
                plugin.verify_initial_data_ownership(submission, plugin_options)
            except PermissionDenied as exc:
                audit_log.warning(
                    "prefill.plugin.ownership_check_failure",
                    data_reference=submission.initial_data_reference,
                    exc_info=exc,
                )
                raise exc

        try:
            new_values = plugin.get_prefill_values_from_options(
                submission, plugin_options, variable
            )
        except PrefillSkipped:
            log.info("prefill.plugin.skipped")
            values = {}
        except Exception as exc:
            audit_log.exception("prefill.plugin.retrieve_failure", exc_info=exc)
        else:
            if new_values:
                values.update(**new_values)
            audit_log.info(
                "prefill_retrieve_success" if new_values else "prefill_retrieve_empty",
                attributes=list(values),
            )

    return values
