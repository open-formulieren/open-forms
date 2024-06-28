import logging
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import groupby
from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_yubin.models import Message
from furl import furl
from rest_framework import serializers
from simple_certmanager.models import Certificate

from openforms.contrib.brk.service import check_brk_config_for_addressNL
from openforms.contrib.kadaster.service import check_bag_config_for_address_fields
from openforms.dmn.registry import BasePlugin as DMNPlugin, register as dmn_register
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import Form, FormLogic, FormRegistrationBackend
from openforms.logging.models import TimelineLogProxy
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.registry import register
from openforms.submissions.logic.actions import ActionDict, EvaluateDMNAction
from openforms.submissions.models.submission import Submission
from openforms.submissions.utils import get_filtered_submission_admin_url
from openforms.typing import StrOrPromise
from openforms.utils.json_logic.datastructures import InputVar
from openforms.utils.json_logic.introspection import introspect_json_logic
from openforms.utils.urls import build_absolute_uri
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.service import get_static_variables

logger = logging.getLogger(__name__)


@dataclass
class FailedEmail:
    submission_uuid: uuid.UUID
    event: str


@dataclass
class FailedRegistration:
    form_name: str
    failed_submissions_counter: int
    initial_failure_at: datetime
    last_failure_at: datetime
    admin_link: str
    has_errors: bool


@dataclass
class FailedPrefill:
    plugin_label: str
    form_names: list[str]
    submission_ids: list[str]
    initial_failure_at: datetime
    last_failure_at: datetime
    # whether an uncaught exception has happened or empty data was returned
    has_errors: bool

    @property
    def admin_link(self) -> str:
        content_type = ContentType.objects.get_for_model(Submission).id

        query_params = {
            "content_type": content_type,
            "object_id__in": ",".join(self.submission_ids),
            "extra_data__log_event__in": "prefill_retrieve_empty,prefill_retrieve_failure",
        }
        submissions_relative_admin_url = furl(
            reverse("admin:logging_timelinelogproxy_changelist")
        )
        submissions_relative_admin_url.add(query_params)

        return build_absolute_uri(submissions_relative_admin_url.url)

    @property
    def failed_submissions_counter(self) -> int:
        return len(self.submission_ids)


@dataclass
class BrokenConfiguration:
    config_name: StrOrPromise
    exception_message: str


@dataclass
class InvalidCertificate:
    id: int
    label: str
    error_message: str
    is_valid_pair: bool
    expiry_date: datetime | None = None

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:simple_certmanager_certificate_change",
            kwargs={"object_id": self.id},
        )

        return build_absolute_uri(form_relative_admin_url)


@dataclass
class InvalidRegistrationBackend:
    config_name: StrOrPromise
    exception_message: str
    form_name: str
    form_id: int

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )
        return build_absolute_uri(form_relative_admin_url)


@dataclass
class InvalidLogicVariable:
    variable: str
    form_name: str
    form_id: int

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )

        return build_absolute_uri(form_relative_admin_url)


def collect_failed_emails(since: datetime) -> Iterable[FailedEmail]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__status=Message.STATUS_FAILED,
        extra_data__include_in_daily_digest=True,
    ).distinct("content_type", "extra_data__status", "extra_data__event")

    if not logs:
        return []

    failed_emails = [
        FailedEmail(
            submission_uuid=log.content_object.uuid, event=log.extra_data["event"]
        )
        for log in logs
    ]

    return failed_emails


def collect_failed_registrations(
    since: datetime,
) -> list[FailedRegistration]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event="registration_failure",
    ).order_by("timestamp")

    form_sorted_logs = sorted(logs, key=lambda x: x.content_object.form.admin_name)

    grouped_logs = groupby(form_sorted_logs, key=lambda log: log.content_object.form)

    failed_registrations = []
    for form, submission_logs in grouped_logs:
        logs = list(submission_logs)
        timestamps = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_registrations.append(
            FailedRegistration(
                form_name=form.name,
                failed_submissions_counter=len(logs),
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                admin_link=get_filtered_submission_admin_url(
                    form.id, filter_retry=True, registration_time="24hAgo"
                ),
                has_errors=has_errors,
            )
        )

    return failed_registrations


def collect_failed_prefill_plugins(since: datetime) -> list[FailedPrefill]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event__in=[
            "prefill_retrieve_empty",
            "prefill_retrieve_failure",
        ],
    ).order_by("extra_data__plugin_label")

    grouped_logs = groupby(logs, key=lambda x: x.extra_data["plugin_label"])

    failed_prefill_plugins = []
    for prefill_plugin, submission_logs in grouped_logs:
        logs = list(submission_logs)

        timestamps = []
        forms = set()
        submission_ids = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            forms.add(log.content_object.form.admin_name)
            submission_ids.append(log.object_id)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_prefill_plugins.append(
            FailedPrefill(
                plugin_label=prefill_plugin,
                form_names=sorted(forms),
                submission_ids=submission_ids,
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                has_errors=has_errors,
            )
        )

    return failed_prefill_plugins


# TODO: check DMN config
def collect_broken_configurations() -> list[BrokenConfiguration]:
    check_brk_configuration = check_brk_config_for_addressNL()
    check_bag_configuration = check_bag_config_for_address_fields()

    broken_configurations = []
    if check_brk_configuration:
        broken_configurations.append(
            BrokenConfiguration(
                config_name=_("BRK Client"), exception_message=check_brk_configuration
            )
        )

    if check_bag_configuration:
        broken_configurations.append(
            BrokenConfiguration(
                config_name=_("BAG Client"), exception_message=check_bag_configuration
            )
        )

    # check DMN usage for each plugin and if used, validate the plugin config
    for plugin in dmn_register.iter_enabled_plugins():
        has_forms = _get_forms_with_dmn_action(plugin.identifier).exists()
        if not has_forms:
            continue

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            broken_configurations.append(
                BrokenConfiguration(
                    config_name=_("{plugin} (DMN)").format(plugin=plugin.verbose_name),
                    exception_message=exc.message,
                )
            )

    return broken_configurations


def collect_invalid_certificates() -> list[InvalidCertificate]:
    today = timezone.now()
    error_messages = {
        "expiring": _("will expire soon"),
        "invalid": _("has invalid keypair"),
        "invalid_expiring": _("invalid keypair, will expire soon"),
    }

    invalid_certs = []
    # filter only on the certificates that are used by services
    configured_certificates = Certificate.objects.filter(
        Q(soap_services_client__isnull=False)
        | Q(soap_services_server__isnull=False)
        | Q(service_client__isnull=False)
        | Q(service_server__isnull=False)
    )
    for cert in configured_certificates:
        time_until_expiry = cert.expiry_date - today
        error_message = ""
        is_valid_pair = False

        match (time_until_expiry <= timedelta(days=14), cert.is_valid_key_pair()):

            case (True, True) | (True, None):
                error_message = error_messages["expiring"]
                is_valid_pair = True

            case (False, False):
                error_message = error_messages["invalid"]
                is_valid_pair = False

            case (True, False):
                error_message = error_messages["invalid_expiring"]
                is_valid_pair = False

        if error_message:
            invalid_certs.append(
                InvalidCertificate(
                    id=cert.id,
                    label=str(cert),
                    error_message=error_message,
                    is_valid_pair=is_valid_pair,
                    expiry_date=cert.expiry_date,
                )
            )

    return invalid_certs


def collect_invalid_registration_backends() -> list[InvalidRegistrationBackend]:
    registration_backends = (
        backend
        for backend in FormRegistrationBackend.objects.select_related("form").iterator()
        if backend.form.is_available
    )

    checked_plugins = set()
    invalid_registration_backends = []
    for registration_backend in registration_backends:
        form_name = registration_backend.form.admin_name
        form = registration_backend.form
        backend_options = registration_backend.options
        backend_type = registration_backend.backend
        plugin = register[backend_type]

        # errors in general configuration are more straightforward for the user,
        # so we show the exact ones
        plugin_cls = type(plugin)
        if plugin_cls not in checked_plugins:
            try:
                plugin.check_config()
            # we always raise an InvalidPluginConfiguration exception even when we have
            # errors like HTTPError
            except InvalidPluginConfiguration as e:
                invalid_registration_backends.append(
                    InvalidRegistrationBackend(
                        config_name=plugin.verbose_name,
                        exception_message=e.args[0],
                        form_name=form_name,
                        form_id=form.id,
                    )
                )
            checked_plugins.add(plugin_cls)

        # errors in the form level can be more detailed so here we want to show
        # a more general error and the link to the broken form to investigate
        serializer = plugin.configuration_options(
            data=backend_options,
            context={"validate_business_logic": True},
        )

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            invalid_registration_backends.append(
                InvalidRegistrationBackend(
                    config_name=plugin.verbose_name,
                    exception_message=_(
                        "Invalid registration backend configuration detected"
                    ),
                    form_name=form_name,
                    form_id=form.id,
                )
            )

    return invalid_registration_backends


def collect_invalid_logic_variables() -> list[InvalidLogicVariable]:
    forms = Form.objects.live().iterator()
    static_variables = {
        var.key: {"source": var.source, "type": var.data_type}
        for var in get_static_variables()
    }

    invalid_logic_rules = []
    for form in forms:
        form_variables = {
            form_variable.key: {
                "source": form_variable.source,
                "type": form_variable.data_type,
            }
            for form_variable in form.formvariable_set.all()
        }

        all_keys = list(static_variables) + list(form_variables)

        form_logics = FormLogic.objects.filter(form=form)

        form_logics_vars = []
        for logic in form_logics:
            form_logics_vars += introspect_json_logic(
                logic.json_logic_trigger
            ).get_input_keys()
            for action in logic.actions:
                if action["action"]["type"] == LogicActionTypes.variable:
                    form_logics_vars.append(InputVar(key=action["variable"]))
                    expression = action["action"]["value"]
                    form_logics_vars += introspect_json_logic(
                        expression
                    ).get_input_keys()

        for var in set(form_logics_vars):
            # there is a variable with this exact key, it is a valid reference
            if var.key in all_keys:
                continue

            outer, *nested = var.key.split(".")

            def _report():
                invalid_logic_rules.append(
                    InvalidLogicVariable(
                        variable=var.key,
                        form_name=form.admin_name,
                        form_id=form.id,
                    )
                )

            # Before checking the type of the parent/outer bit, check if it exists in
            # the first place. It could also be that it's not a parent at all (nested is
            # empty), so that's a guaranteed broken reference too.
            if outer not in all_keys:
                _report()
                continue

            # Nested cannot be empty now - if it were, either the key exists as a var,
            # which is the first thing we checked above, or it doesn't exist as a var,
            # which is the second thing we checked above and errored out.
            assert nested

            # We can only check the outer bit of the variable, which must be a suitable
            # container type to be valid. Container types are objects and arrays, but
            # we only consider arrays as a valid type if the first bit of the nested
            # key is numeric, as this must refer to an array index.
            # E.g. foo.bar -> only objects are possible, but foo.3 -> objects and arrays
            # are possible (you could have a dict with the string "3" as key").
            expected_container_types = {FormVariableDataTypes.object}
            if nested[0].isnumeric():
                expected_container_types.add(FormVariableDataTypes.array)

            # Now, check that the type of the container variable is as expected. If the
            # variable does *not* have any of the container types, then it's a
            # guaranteed error since lookups inside primitives are not possible.
            parent_var = form_variables.get(outer) or static_variables.get(outer)
            if parent_var["type"] not in expected_container_types:
                _report()
                continue

            # all the other situations - we cannot (yet) conclude anything meaningful,
            # so instead, log information for our own insight into (typical) usage/
            # constructions.
            logger.info(
                "possible invalid variable reference (%s) in logic of form %s",
                var.key,
                form.admin_name,
            )

    return invalid_logic_rules


def _get_forms_with_dmn_action(plugin_id: str):
    # actions is a JSONField - the top-level is an array of actions. Each action is
    # an object with the shape openforms.submissions.logic.actions.ActionDict. The
    # JSONField query does not fully specify all properties because it performs
    # structural matching (and we only process the rest of the config after establishing
    # that it is indeed the expected action type).
    lookup_value = [
        {
            "action": {
                "type": LogicActionTypes.evaluate_dmn,
                # if a plugin ID is provided, filter actions for that plugin, otherwise
                # return any DMN evaluation action plugin
                "config": {"plugin_id": plugin_id} if plugin_id else {},
            }
        }
    ]
    base_qs = Form.objects.live().distinct()
    return base_qs.filter(formlogic__actions__contains=lookup_value)


@dataclass
class InvalidDMNAction:
    form_id: int
    form_name: str
    # definition: DecisionDefinition
    message: StrOrPromise

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )

        return build_absolute_uri(form_relative_admin_url)


def _iter_dmn_actions(form_qs) -> Iterator[tuple[Form, ActionDict]]:
    for form in form_qs.iterator():
        logic_rules = form.formlogic_set.filter(
            actions__contains=[{"action": {"type": LogicActionTypes.evaluate_dmn}}]
        )
        for rule in logic_rules.iterator():
            for action in rule.actions:
                match action:
                    case {"action": {"type": LogicActionTypes.evaluate_dmn}}:
                        yield (form, action)


def collect_invalid_dmn_actions() -> list[InvalidDMNAction]:
    """
    Introspect forms using the DMN action in their logic rules.

    Checks whether:

    1. The decision definition can be introspected
    2. The input/output variables exist
    """
    invalid_actions = []
    # track available definitions to present human readable names
    available_definitions: dict[str, dict[str, str]] = {}

    static_variables = [var.key for var in get_static_variables()]

    def _populate_definitions(plugin: DMNPlugin) -> None:
        if (key := plugin.identifier) in available_definitions:
            return
        try:
            definitions = plugin.get_available_decision_definitions()
        except Exception:
            definitions = []
        available_definitions[key] = {
            definition.identifier: definition.label for definition in definitions
        }

    forms = _get_forms_with_dmn_action(plugin_id="")
    for form, _action in _iter_dmn_actions(forms):

        def _report(msg: StrOrPromise):
            invalid_actions.append(
                InvalidDMNAction(
                    form_id=form.id, form_name=form.admin_name, message=msg
                )
            )

        try:
            action = EvaluateDMNAction.from_action(_action)
        except Exception:
            _report(_("Could not parse configuration"))
            continue

        try:
            plugin = dmn_register[action.plugin_id]
        except KeyError:
            _report(
                _("Unknown DMN plugin: {plugin_id}").format(plugin_id=action.plugin_id)
            )
            continue

        definition_id = action.decision_definition_id
        definition_version = action.decision_definition_version

        # introspect the definition - if this fails, there's likely some permission issue
        # or the definition was removed
        try:
            parameters = plugin.get_decision_definition_parameters(
                definition_id=definition_id,
                version=definition_version,
            )
        except Exception:
            _populate_definitions(plugin)
            name = available_definitions[action.plugin_id].get(
                definition_id, definition_id
            )
            _report(
                _(
                    "Definition {name} does not exist or Open Forms has no access"
                ).format(name=name)
            )
            continue

        form_variable_keys = list(form.formvariable_set.values_list("key", flat=True))
        all_keys = static_variables + form_variable_keys
        output_names = [param.name for param in parameters.outputs]

        invalid_form_vars = []
        invalid_input_vars = []
        invalid_output_vars = []

        for input_mapping in action.input_mapping:
            if (form_var := input_mapping["form_variable"]) not in all_keys:
                invalid_form_vars.append(form_var)

            dmn_var = input_mapping["dmn_variable"]
            # there could be false negatives here, since we don't parse the FEEL
            # expressions and just do string containment checks.
            if not any(dmn_var in param.expression for param in parameters.inputs):
                invalid_input_vars.append(dmn_var)

        for output_mapping in action.output_mapping:
            # exclude static vars, since you cannot assign to them
            if (form_var := output_mapping["form_variable"]) not in form_variable_keys:
                invalid_form_vars.append(form_var)
            if (dmn_var := output_mapping["dmn_variable"]) not in output_names:
                invalid_output_vars.append(dmn_var)

        if any([invalid_form_vars, invalid_input_vars, invalid_output_vars]):
            _populate_definitions(plugin)
            name = available_definitions[action.plugin_id].get(
                definition_id, definition_id
            )

            if invalid_form_vars:
                msg = _(
                    "The '{name}' definition configuration points to invalid form variables: {form_vars}"
                ).format(
                    name=name,
                    form_vars=", ".join(invalid_form_vars),
                )
                _report(msg)

            if invalid_input_vars:
                msg = _(
                    "Definition '{name}' does not appear to have the input variable(s): {input_vars}"
                ).format(
                    name=name,
                    input_vars=", ".join(invalid_input_vars),
                )
                _report(msg)

            if invalid_output_vars:
                msg = _(
                    "Definition '{name}' does not appear to have the output variable(s): {output_vars}"
                ).format(
                    name=name,
                    output_vars=", ".join(invalid_output_vars),
                )
                _report(msg)

    return invalid_actions
