from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Model

from openforms.accounts.models import User
from openforms.analytics_tools.models import AnalyticsToolsConfiguration
from openforms.appointments.models import AppointmentInfo
from openforms.forms.models import Form
from openforms.logging.constants import TimelineLogTags
from openforms.payments.constants import PaymentStatus
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import JSONObject, JSONValue

if TYPE_CHECKING:
    from log_outgoing_requests.models import OutgoingRequestsLog

    from openforms.payments.models import SubmissionPayment
    from openforms.prefill.base import BasePlugin as PrefillPlugin
    from openforms.submissions.models import Submission, SubmissionStep
    from stuf.models import StufService

    from .models import TimelineLogProxy


def _create_log(
    object: Model,
    event: str,
    extra_data: dict | None = None,
    plugin: AbstractBasePlugin | None = None,
    error: Exception | None = None,
    tags: list | None = None,
    user: User | None = None,
) -> TimelineLogProxy | None:
    if getattr(settings, "AUDITLOG_DISABLED", False):
        return

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

    log_entry = TimelineLogProxy.objects.create(
        content_object=object,
        template=f"logging/events/{event}.txt",
        extra_data=extra_data,
        user=user,
    )
    return log_entry


def outgoing_request_log_details_view_admin(
    outgoing_request_log: OutgoingRequestsLog, user: User
) -> None:
    _create_log(
        outgoing_request_log,
        "outgoing_request_log_details_view_admin",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


# - - -


def enabling_analytics_tool(
    analytics_tools_configuration: AnalyticsToolsConfiguration, analytics_tool: str
):
    _create_log(
        analytics_tools_configuration,
        "analytics_tool_enabled",
        extra_data={"analytics_tool": analytics_tool},
    )


def disabling_analytics_tool(
    analytics_tools_configuration: AnalyticsToolsConfiguration, analytics_tool: str
):
    _create_log(
        analytics_tools_configuration,
        "analytics_tool_disabled",
        extra_data={"analytics_tool": analytics_tool},
    )


# - - -


def submission_start(submission: Submission):
    _create_log(
        submission,
        "submission_start",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def submission_auth(
    submission: Submission, delegated: bool = False, user: User | None = None
):
    _create_log(
        submission,
        "submission_auth",
        user=user,
        extra_data={"delegated": delegated},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def submission_step_fill(step: SubmissionStep):
    from openforms.forms.models import FormStep

    assert isinstance(step.form_step, FormStep)
    _create_log(
        step.submission,
        "submission_step_fill",
        extra_data={
            "step": str(step.form_step.form_definition.name),
            "step_id": step.pk,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def _snapshot_submission_statistics(submission: Submission):
    return {
        # note: these keys are used in the form statistics admin view!
        "public_reference": submission.public_registration_reference,
        "form_id": submission.form.pk,
        "form_name": submission.form.name,
        "internal_form_name": submission.form.internal_name,
        "submitted_on": submission.completed_on,
    }


FORM_SUBMIT_SUCCESS_EVENT = "form_submit_success"


def form_submit_success(submission: Submission):
    _create_log(
        submission,
        FORM_SUBMIT_SUCCESS_EVENT,
        extra_data=_snapshot_submission_statistics(submission),
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def pdf_generation_start(submission: Submission):
    _create_log(
        submission,
        "pdf_generation_start",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def pdf_generation_success(submission: Submission, submission_report):
    _create_log(
        submission,
        "pdf_generation_success",
        extra_data={
            "report_id": submission_report.id,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def pdf_generation_failure(submission: Submission, submission_report, error: Exception):
    _create_log(
        submission,
        "pdf_generation_failure",
        error=error,
        extra_data={"report_id": submission_report.id},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def pdf_generation_skip(submission: Submission, submission_report):
    _create_log(
        submission,
        "pdf_generation_skip",
        extra_data={"report_id": submission_report.id},
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def prefill_retrieve_success(
    submission: Submission,
    plugin: PrefillPlugin,
    prefill_fields: Sequence[str],
):
    _create_log(
        submission,
        "prefill_retrieve_success",
        extra_data={"prefill_fields": prefill_fields},
        plugin=plugin,
        tags=[TimelineLogTags.AVG, TimelineLogTags.submission_lifecycle],
    )


def prefill_retrieve_empty(
    submission: Submission,
    plugin: PrefillPlugin,
    prefill_fields: Sequence[str],
):
    _create_log(
        submission,
        "prefill_retrieve_empty",
        extra_data={"prefill_fields": prefill_fields},
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def prefill_retrieve_failure(submission: Submission, plugin, error: Exception):
    _create_log(
        submission,
        "prefill_retrieve_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def registration_start(submission: Submission):
    _create_log(
        submission,
        "registration_start",
        tags=[TimelineLogTags.submission_lifecycle],
    )


registration_debug = partial(
    _create_log,
    event="registration_debug",
    tags=[TimelineLogTags.submission_lifecycle],
)
registration_debug.__doc__ = (
    """Log debugging info. `model` parameter ought to be the submission."""
)


REGISTRATION_SUCCESS_EVENT = "registration_success"


def registration_success(submission: Submission, plugin):
    _create_log(
        submission,
        REGISTRATION_SUCCESS_EVENT,
        extra_data=_snapshot_submission_statistics(submission),
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_failure(submission: Submission, error: Exception, plugin=None):
    _create_log(
        submission,
        "registration_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_skip(submission: Submission):
    _create_log(
        submission,
        "registration_skip",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_attempts_limited(submission: Submission):
    _create_log(
        submission,
        "registration_attempts_limited",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def object_ownership_check_failure(submission: Submission, plugin=None):
    _create_log(
        submission,
        "object_ownership_check_failure",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def object_ownership_check_success(submission: Submission, plugin=None):
    _create_log(
        submission,
        "object_ownership_check_success",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def object_ownership_check_anonymous_user(submission: Submission, plugin=None):
    _create_log(
        submission,
        "object_ownership_check_anonymous_user",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def registration_payment_update_start(submission: Submission, plugin):
    _create_log(
        submission,
        "registration_payment_update_start",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_payment_update_success(submission: Submission, plugin):
    _create_log(
        submission,
        "registration_payment_update_success",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_payment_update_failure(
    submission: Submission, error: Exception, plugin=None
):
    _create_log(
        submission,
        "registration_payment_update_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_payment_update_skip(submission: Submission):
    _create_log(
        submission,
        "registration_payment_update_skip",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_skipped_not_yet_paid(submission: Submission):
    _create_log(
        submission,
        "registration_skipped_not_yet_paid",
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def registration_update_with_confirmation_email_failure(
    submission: Submission, error: Exception, plugin=None
):
    _create_log(
        submission,
        "registration_update_with_confirmation_email_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_update_with_confirmation_email_skip(submission: Submission):
    _create_log(
        submission,
        "registration_update_with_confirmation_email_skip",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def registration_update_with_confirmation_email_success(submission: Submission, plugin):
    _create_log(
        submission,
        "registration_update_with_confirmation_email_success",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def confirmation_email_scheduled(
    submission: Submission, scheduling_options: dict
) -> None:
    _create_log(
        submission,
        "confirmation_email_scheduled",
        extra_data=scheduling_options,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def confirmation_email_start(submission: Submission):
    _create_log(
        submission,
        "confirmation_email_start",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def confirmation_email_success(submission: Submission):
    _create_log(
        submission,
        "confirmation_email_success",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def confirmation_email_failure(submission: Submission, error: Exception):
    _create_log(
        submission,
        "confirmation_email_failure",
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def confirmation_email_skip(submission: Submission):
    _create_log(
        submission,
        "confirmation_email_skip",
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def price_calculation_variable_error(
    submission: Submission,
    variable: str,
    error: Exception,
    value: JSONValue = None,
):
    _create_log(
        submission,
        "price_calculation_variable_error",
        extra_data={"variable": variable, "value": value},
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def payment_flow_start(payment: SubmissionPayment, plugin, from_email: bool = False):
    _create_log(
        payment.submission,
        "payment_flow_start",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
            "from_email": from_email,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def payment_flow_failure(payment: SubmissionPayment, plugin, error: Exception):
    _create_log(
        payment.submission,
        "payment_flow_failure",
        plugin=plugin,
        error=error,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def payment_flow_return(payment: SubmissionPayment, plugin):
    _create_log(
        payment.submission,
        "payment_flow_return",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
            "payment_status": payment.status,
            "payment_status_label": PaymentStatus.get_label(payment.status),
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def payment_flow_webhook(payment: SubmissionPayment, plugin):
    _create_log(
        payment.submission,
        "payment_flow_webhook",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
            "payment_status": payment.status,
            "payment_status_label": PaymentStatus.get_label(payment.status),
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def payment_register_success(payment: SubmissionPayment, plugin):
    _create_log(
        payment.submission,
        "payment_register_success",
        plugin=plugin,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


def payment_register_failure(payment: SubmissionPayment, plugin, error: Exception):
    _create_log(
        payment.submission,
        "payment_register_failure",
        plugin=plugin,
        error=error,
        extra_data={
            "payment_order_id": payment.public_order_id,
            "payment_id": payment.id,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def appointment_register_start(submission: Submission, plugin):
    _create_log(
        submission,
        "appointment_register_start",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def appointment_register_success(appointment: AppointmentInfo, plugin):
    _create_log(
        appointment.submission,
        "appointment_register_success",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def appointment_register_failure(appointment: AppointmentInfo, plugin, error):
    _create_log(
        appointment.submission,
        "appointment_register_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def appointment_register_skip(submission: Submission):
    _create_log(
        submission,
        "appointment_register_skip",
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def appointment_cancel_start(appointment: AppointmentInfo, plugin):
    _create_log(
        appointment.submission,
        "appointment_cancel_start",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def appointment_cancel_success(appointment: AppointmentInfo, plugin):
    _create_log(
        appointment.submission,
        "appointment_cancel_success",
        plugin=plugin,
        tags=[TimelineLogTags.submission_lifecycle],
    )


def appointment_cancel_failure(appointment: AppointmentInfo, plugin, error):
    _create_log(
        appointment.submission,
        "appointment_cancel_failure",
        plugin=plugin,
        error=error,
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def submission_details_view_admin(submission: Submission, user: User):
    _create_log(
        submission,
        "submission_details_view_admin",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def submission_details_view_api(submission: Submission, user: User):
    _create_log(
        submission,
        "submission_details_view_api",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def submission_export_list(form: Form, user: User):
    _create_log(
        form,
        "submission_export_list",
        tags=[TimelineLogTags.AVG],
        user=user,
    )


def form_configuration_error(
    form: Form,
    component: JSONObject,
    error_message: str,
):
    _create_log(
        form,
        "form_configuration_error",
        extra_data={"component": component, "error": error_message},
    )


# - - -


def stuf_zds_request(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_request",
        extra_data={"url": url},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def stuf_zds_success_response(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_success_response",
        extra_data={"url": url},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def stuf_zds_failure_response(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_failure_response",
        extra_data={"url": url},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def stuf_bg_request(service: StufService, url):
    _create_log(
        service,
        "stuf_bg_request",
        extra_data={"url": url},
        tags=[TimelineLogTags.submission_lifecycle],
    )


def stuf_bg_response(service: StufService, url):
    _create_log(
        service,
        "stuf_bg_response",
        extra_data={"url": url},
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def reference_lists_failure_response(
    form: Form, component: JSONObject, error_message: str
):
    _create_log(
        form,
        "reference_lists_failure_response",
        extra_data={"component": component, "error": error_message},
        tags=[TimelineLogTags.submission_lifecycle],
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


def bulk_forms_imported(user: User, failed_files: list[tuple[str, str]]):
    _create_log(
        user,
        "bulk_forms_imported",
        extra_data={"failed_files": failed_files},
        user=user,
    )


# - - -


def cosigner_email_queuing_failure(submission: Submission):
    _create_log(
        submission,
        "cosigner_email_queuing_failure",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def cosigner_email_queuing_success(submission: Submission):
    _create_log(
        submission,
        "cosigner_email_queuing_success",
        tags=[TimelineLogTags.submission_lifecycle],
    )


def skipped_registration_cosign_required(submission: Submission):
    _create_log(
        submission,
        "skipped_registration_cosign_required",
        tags=[TimelineLogTags.submission_lifecycle],
    )


# - - -


def form_activated(form: Form):
    _create_log(form, "form_activated")


def form_deactivated(form: Form):
    _create_log(form, "form_deactivated")


# - - -
def email_status_change(
    submission: Submission,
    event: str,
    status: int,
    status_label: str,
    include_in_daily_digest: bool,
):
    _create_log(
        submission,
        "email_status_change",
        extra_data={
            "event": event,
            "status": status,
            "status_label": status_label,
            "include_in_daily_digest": include_in_daily_digest,
        },
        tags=[TimelineLogTags.submission_lifecycle],
    )
