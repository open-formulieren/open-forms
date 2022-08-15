import logging
from typing import TYPE_CHECKING, List, Optional, Tuple

from django.db.models import Model

from openforms.forms.constants import LogicActionTypes
from openforms.logging.constants import TimelineLogTags
from openforms.payments.constants import PaymentStatus
from openforms.utils.json_logic import ComponentMeta, introspect_json_logic

if TYPE_CHECKING:  # pragma: nocover
    from openforms.accounts.models import User
    from openforms.analytics_tools.models import AnalyticsToolsConfiguration
    from openforms.appointments.models import AppointmentInfo
    from openforms.forms.models import Form
    from openforms.plugins.plugin import AbstractBasePlugin
    from openforms.submissions.models import (
        Submission,
        SubmissionPayment,
        SubmissionStep,
    )
    from stuf.models import StufService

logger = logging.getLogger(__name__)


def _create_log(
    object: Model,
    event: str,
    extra_data: Optional[dict] = None,
    plugin: Optional["AbstractBasePlugin"] = None,
    error: Optional[Exception] = None,
    tags: Optional[list] = None,
    user: Optional["User"] = None,
):
    # import locally or we'll get "AppRegistryNotReady: Apps aren't loaded yet."
    from openforms.logging.models import TimelineLogProxy

    if extra_data is None:
        extra_data = dict()
    extra_data["log_event"] = event

    if plugin:
        extra_data["plugin_id"] = plugin.identifier
        extra_data["plugin_label"] = str(plugin.verbose_name)

    if error:
        extra_data["error"] = str(error)

    if isinstance(tags, list):
        for tag in tags:
            extra_data[tag] = True

    if user and not user.is_authenticated:
        # If user is not authenticated (eg. AnonymousUser) we can not
        #   save it on the TimelineLogProxy model
        user = None

    TimelineLogProxy.objects.create(
        content_object=object,
        template=f"logging/events/{event}.txt",
        extra_data=extra_data,
        user=user,
    )
    # logger.debug('Logged event in %s %s %s', event, object._meta.object_name, object.pk)


def enabling_analytics_tool(
    analytics_tools_configuration: "AnalyticsToolsConfiguration", analytics_tool: str
):
    _create_log(
        analytics_tools_configuration,
        "analytics_tool_enabled",
        extra_data={"analytics_tool": analytics_tool},
    )


def disabling_analytics_tool(
    analytics_tools_configuration: "AnalyticsToolsConfiguration", analytics_tool: str
):
    _create_log(
        analytics_tools_configuration,
        "analytics_tool_disabled",
        extra_data={"analytics_tool": analytics_tool},
    )


# - - -


def submission_start(submission: "Submission"):
    _create_log(submission, "submission_start")


def submission_step_fill(step: "SubmissionStep"):
    _create_log(
        step.submission,
        "submission_step_fill",
        extra_data={
            "step": str(step.form_step.form_definition.name),
            "step_id": step.id,
        },
    )


def form_submit_success(submission: "Submission"):
    _create_log(submission, "form_submit_success")


# - - -


def pdf_generation_start(submission: "Submission"):
    _create_log(submission, "pdf_generation_start")


def pdf_generation_success(submission: "Submission", submission_report):
    _create_log(
        submission,
        "pdf_generation_success",
        extra_data={
            "report_id": submission_report.id,
        },
    )


def pdf_generation_failure(
    submission: "Submission", submission_report, error: Exception
):
    _create_log(
        submission,
        "pdf_generation_failure",
        error=error,
        extra_data={"report_id": submission_report.id},
    )


def pdf_generation_skip(submission: "Submission", submission_report):
    _create_log(
        submission,
        "pdf_generation_skip",
        extra_data={"report_id": submission_report.id},
    )


# - - -


def prefill_retrieve_success(submission: "Submission", plugin, prefill_fields):
    _create_log(
        submission,
        "prefill_retrieve_success",
        extra_data={"prefill_fields": prefill_fields},
        plugin=plugin,
        tags=[TimelineLogTags.AVG],
    )


def prefill_retrieve_failure(submission: "Submission", plugin, error: Exception):
    _create_log(
        submission,
        "prefill_retrieve_failure",
        plugin=plugin,
        error=error,
    )


# - - -


def registration_start(submission: "Submission"):
    _create_log(submission, "registration_start")


def registration_success(submission: "Submission", plugin):
    _create_log(
        submission,
        "registration_success",
        plugin=plugin,
    )


def registration_failure(submission: "Submission", error: Exception, plugin=None):
    _create_log(
        submission,
        "registration_failure",
        plugin=plugin,
        error=error,
    )


def registration_skip(submission: "Submission"):
    _create_log(
        submission,
        "registration_skip",
    )


def registration_attempts_limited(submission: "Submission"):
    _create_log(
        submission,
        "registration_attempts_limited",
    )


# - - -


def registration_payment_update_start(submission: "Submission", plugin):
    _create_log(submission, "registration_payment_update_start", plugin=plugin)


def registration_payment_update_success(submission: "Submission", plugin):
    _create_log(submission, "registration_payment_update_success", plugin=plugin)


def registration_payment_update_failure(
    submission: "Submission", error: Exception, plugin=None
):
    _create_log(
        submission, "registration_payment_update_failure", plugin=plugin, error=error
    )


def registration_payment_update_skip(submission: "Submission"):
    _create_log(submission, "registration_payment_update_skip")


# - - -


def confirmation_email_start(submission: "Submission"):
    _create_log(submission, "confirmation_email_start")


def confirmation_email_success(submission: "Submission"):
    _create_log(submission, "confirmation_email_success")


def confirmation_email_failure(submission: "Submission", error: Exception):
    _create_log(
        submission,
        "confirmation_email_failure",
        error=error,
    )


def confirmation_email_skip(submission: "Submission"):
    _create_log(submission, "confirmation_email_skip")


# - - -


def payment_flow_start(payment: "SubmissionPayment", plugin):
    _create_log(
        payment.submission,
        "payment_flow_start",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
        },
    )


def payment_flow_failure(payment: "SubmissionPayment", plugin, error: Exception):
    _create_log(
        payment.submission,
        "payment_flow_failure",
        plugin=plugin,
        error=error,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
        },
    )


def payment_flow_return(payment: "SubmissionPayment", plugin):
    _create_log(
        payment.submission,
        "payment_flow_return",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
            "payment_status": payment.status,
            "payment_status_label": str(PaymentStatus.labels[payment.status]),
        },
    )


def payment_flow_webhook(payment: "SubmissionPayment", plugin):
    _create_log(
        payment.submission,
        "payment_flow_webhook",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
            "payment_status": payment.status,
            "payment_status_label": str(PaymentStatus.labels[payment.status]),
        },
    )


# - - -


def payment_register_success(payment: "SubmissionPayment", plugin):
    _create_log(
        payment.submission,
        "payment_register_success",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
        },
    )


def payment_register_failure(payment: "SubmissionPayment", plugin, error: Exception):
    _create_log(
        payment.submission,
        "payment_register_failure",
        plugin=plugin,
        error=error,
        extra_data={
            "payment_order_id": payment.order_id,
            "payment_id": payment.id,
        },
    )


def payment_transfer_to_new_submission(
    submission_payment: "SubmissionPayment",
    old_submission: "Submission",
    new_submission: "Submission",
):
    _create_log(
        object=old_submission,
        event="transfer_payment_to_submission_copy",
        extra_data={
            "payment_uuid": str(submission_payment.uuid),
            "old_submission_id": old_submission.id,
            "new_submission_id": new_submission.id,
        },
    )


# - - -


def appointment_register_start(submission: "Submission", plugin):
    _create_log(
        submission,
        "appointment_register_start",
        plugin=plugin,
    )


def appointment_register_success(appointment: "AppointmentInfo", plugin):
    _create_log(
        appointment.submission,
        "appointment_register_success",
        plugin=plugin,
    )


def appointment_register_failure(appointment: "AppointmentInfo", plugin, error):
    _create_log(
        appointment.submission,
        "appointment_register_failure",
        plugin=plugin,
        error=error,
    )


def appointment_register_skip(submission: "Submission"):
    _create_log(submission, "appointment_register_skip")


# - - -


def appointment_update_start(appointment: "AppointmentInfo", plugin):
    _create_log(
        appointment.submission,
        "appointment_update_start",
        plugin=plugin,
    )


def appointment_update_success(appointment: "AppointmentInfo", plugin):
    _create_log(
        appointment.submission,
        "appointment_update_success",
        plugin=plugin,
    )


def appointment_update_failure(appointment: "AppointmentInfo", plugin, error):
    _create_log(
        appointment.submission,
        "appointment_update_failure",
        plugin=plugin,
        error=error,
    )


# - - -


def appointment_cancel_start(appointment: "AppointmentInfo", plugin):
    _create_log(
        appointment.submission,
        "appointment_cancel_start",
        plugin=plugin,
    )


def appointment_cancel_success(appointment: "AppointmentInfo", plugin):
    _create_log(
        appointment.submission,
        "appointment_cancel_success",
        plugin=plugin,
    )


def appointment_cancel_failure(appointment: "AppointmentInfo", plugin, error):
    _create_log(
        appointment.submission,
        "appointment_cancel_failure",
        plugin=plugin,
        error=error,
    )


def submission_details_view_admin(submission: "Submission", user: "User"):
    _create_log(
        submission,
        "submission_details_view_admin",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def submission_details_view_api(submission: "Submission", user: "User"):
    _create_log(
        submission,
        "submission_details_view_api",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def submission_export_list(form: "Form", user: "User"):
    _create_log(
        form,
        "submission_export_list",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def submission_logic_evaluated(
    submission: "Submission", evaluated_rules, resulting_data
):
    if not evaluated_rules:
        return
    evaluated_rules_list = []

    submission_state = submission.load_execution_state()
    form_steps = submission_state.form_steps

    # Keep a mapping for each component's key for each component in the entire form.
    # The key of the mapping is the component key, the value is a dataclasse composed of
    # form_step and component defintion
    components_map = {}
    for form_step in form_steps:
        for component in form_step.form_definition.iter_components():
            components_map[component["key"]] = ComponentMeta(form_step, component)

    input_data = []
    all_variables = submission.form.formvariable_set.distinct("key").in_bulk(
        field_name="key"
    )
    component_key_lookup = {
        LogicActionTypes.value: "component",
        LogicActionTypes.property: "component",
        LogicActionTypes.variable: "variable",
    }
    for evaluated_rule in evaluated_rules:

        rule = evaluated_rule["rule"]
        rule_introspection = introspect_json_logic(
            rule.json_logic_trigger, components_map, resulting_data
        )

        # Gathering all the input component of each evaluated rule
        input_data.extend(rule_introspection.get_input_components())

        targeted_components = []
        for action in rule.actions:
            action_details = action["action"]
            component_key = action.get(component_key_lookup.get(action_details["type"]))
            component_meta = components_map.get(component_key)
            component = component_meta.component if component_meta else None

            # figure out the best possible label
            # 1. fall back to component label if there is a label, else empty string
            # 2. if there is a variable, use the name if it's set, else fall back to
            # component label
            label = component.get("label", "") if component else ""
            if component_key in all_variables:
                label = all_variables[component_key].name or label

            action_log_data = {
                "key": component_key,
                "type_display": LogicActionTypes.get_choice(
                    action_details["type"]
                ).label,
                "label": label,
                "step_name": component_meta.form_step.form_definition.name
                if component_meta
                else "",
                "value": "",
            }

            # process the value
            if action_details["type"] == LogicActionTypes.value:
                action_log_data["value"] = action_details["value"]
            elif action_details["type"] == LogicActionTypes.property:
                action_log_data.update(
                    {
                        "value": action_details["property"]["value"],
                        "state": action_details["state"],
                    }
                )
            elif action_details["type"] == LogicActionTypes.variable:
                # check if it's a primitive value, which doesn't require introspection
                value_expression = action_details["value"]
                if not isinstance(value_expression, dict):
                    action_log_data["value"] = value_expression
                else:
                    action_logic_introspection = introspect_json_logic(
                        action_details["value"], components_map, resulting_data
                    )
                    action_log_data["value"] = action_logic_introspection.as_string()
            targeted_components.append(action_log_data)

        evaluated_rule_data = {
            "raw_logic_expression": rule_introspection.expression,
            "readable_rule": rule_introspection.as_string(),
            "targeted_components": targeted_components,
            "trigger": evaluated_rule["trigger"],
        }

        evaluated_rules_list.append(evaluated_rule_data)

    # de-duplication of input data
    deduplicated_input_data = {node["key"]: node for node in input_data}

    _create_log(
        submission,
        "submission_logic_evaluated",
        extra_data={
            "evaluated_rules": evaluated_rules_list,
            "input_data": deduplicated_input_data,
        },
    )


# - - -


def stuf_zds_request(service: "StufService", url):
    _create_log(
        service,
        "stuf_zds_request",
        extra_data={"url": url},
    )


def stuf_zds_success_response(service: "StufService", url):
    _create_log(
        service,
        "stuf_zds_success_response",
        extra_data={"url": url},
    )


def stuf_zds_failure_response(service: "StufService", url):
    _create_log(
        service,
        "stuf_zds_failure_response",
        extra_data={"url": url},
    )


def stuf_bg_request(service: "StufService", url):
    _create_log(
        service,
        "stuf_bg_request",
        extra_data={"url": url},
    )


def stuf_bg_response(service: "StufService", url):
    _create_log(
        service,
        "stuf_bg_response",
        extra_data={"url": url},
    )


# - - -


def hijack_started(hijacker, hijacked):
    _create_log(
        hijacked,
        "hijack_started",
        user=hijacker,
        extra_data={
            "hijacker": {
                "id": hijacker.id,
                "full_name": hijacker.get_full_name(),
                "username": hijacker.username,
            },
            "hijacked": {
                "id": hijacked.id,
                "full_name": hijacked.get_full_name(),
                "username": hijacked.username,
            },
        },
        tags=[TimelineLogTags.hijack],
    )


def hijack_ended(hijacker, hijacked):
    _create_log(
        hijacked,
        "hijack_ended",
        user=hijacker,
        extra_data={
            "hijacker": {
                "id": hijacker.id,
                "full_name": hijacker.get_full_name(),
                "username": hijacker.username,
            },
            "hijacked": {
                "id": hijacked.id,
                "full_name": hijacked.get_full_name(),
                "username": hijacked.username,
            },
        },
        tags=[TimelineLogTags.hijack],
    )


# - - -


def forms_bulk_export_downloaded(bulk_export, user):
    _create_log(
        bulk_export,
        "downloaded_bulk_export",
        user=user,
    )


def bulk_forms_imported(user: "User", failed_files: List[Tuple[str, str]]):
    _create_log(
        user,
        "bulk_forms_imported",
        extra_data={"failed_files": failed_files},
        user=user,
    )
