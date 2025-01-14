import logging
from collections import defaultdict

from django.core.exceptions import PermissionDenied

import elasticapm
from rest_framework.exceptions import ValidationError
from zgw_consumers.concurrent import parallel

from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable

from .base import BasePlugin
from .constants import IdentifierRoles
from .registry import Registry

logger = logging.getLogger(__name__)


def fetch_prefill_values_from_attribute(
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
        identifier_role = IdentifierRoles(
            variable.form_variable.prefill_identifier_role
        )
        attribute_name = variable.form_variable.prefill_attribute

        grouped_fields[plugin_id][identifier_role].append(
            {attribute_name: variable.form_variable.key}
        )

    mappings: dict[str, JSONEncodable] = {}

    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(
        item: tuple[BasePlugin, IdentifierRoles, list[dict[str, str]]]
    ) -> tuple[list[dict[str, str]], dict[str, JSONEncodable]]:
        plugin, identifier_role, fields = item

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
    # local import to prevent AppRegistryNotReady:
    from openforms.logging import logevent

    values: dict[str, JSONEncodable] = {}
    for variable in variables:
        plugin = register[variable.form_variable.prefill_plugin]
        raw_options = variable.form_variable.prefill_options

        # validate the options before processing them
        options_serializer = plugin.options(data=raw_options)
        try:
            options_serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            logevent.prefill_retrieve_failure(submission, plugin, exc)
            continue

        plugin_options = options_serializer.validated_data

        # If an `initial_data_reference` was passed, we must verify that the
        # authenticated user is the owner of the referenced object
        if submission.initial_data_reference:
            try:
                plugin.verify_initial_data_ownership(submission, plugin_options)
            except PermissionDenied as exc:
                # XXX: these log records will typically not be created in the DB because
                # the transaction is rolled back as part of DRFs exception handler
                logger.warning(
                    "Submission %s attempted to prefill the initial_data_reference %s "
                    "using the %r plugin, but the ownership check failed.",
                    submission.uuid,
                    submission.initial_data_reference,
                    plugin,
                    exc_info=exc,
                    extra={
                        "submission": submission.uuid,
                        "plugin_cls": type(plugin),
                        "initial_data_reference": submission.initial_data_reference,
                    },
                )
                logevent.prefill_retrieve_failure(submission, plugin, exc)
                raise exc

        try:
            new_values = plugin.get_prefill_values_from_options(
                submission, plugin_options
            )
        except Exception as exc:
            logger.exception(f"exception in prefill plugin '{plugin.identifier}'")
            logevent.prefill_retrieve_failure(submission, plugin, exc)
        else:
            if new_values:
                values.update(**new_values)
                logevent.prefill_retrieve_success(submission, plugin, values)
            else:
                logevent.prefill_retrieve_empty(submission, plugin, values)

    return values
