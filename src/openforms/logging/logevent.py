import logging
from typing import TYPE_CHECKING

from django.db.models import Model

from openforms.payments.constants import PaymentStatus

if TYPE_CHECKING:
    from openforms.appointments.models import AppointmentInfo
    from openforms.submissions.models import (
        Submission,
        SubmissionPayment,
        SubmissionStep,
    )

logger = logging.getLogger(__name__)


def _create_log(
    object: Model,
    event: str,
    extra_data: dict = None,
    plugin=None,
    error: Exception = None,
    tag_avg: bool = False,
):
    if extra_data is None:
        extra_data = dict()
    extra_data["log_event"] = event

    if plugin:
        extra_data["plugin_id"] = plugin.identifier
        extra_data["plugin_label"] = str(plugin.verbose_name)

    if error:
        extra_data["error"] = str(error)

    # import locally or we'll get "AppRegistryNotReady: Apps aren't loaded yet."
    from openforms.logging.models import TimelineLogProxy

    TimelineLogProxy.objects.create(
        content_object=object,
        template=f"logging/events/{event}.txt",
        extra_data=extra_data,
    )
    # logger.debug('Logged event in %s %s %s', event, object._meta.object_name, object.pk)


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


def prefill_retrieve_success(submission: "Submission", plugin):
    _create_log(
        submission,
        "prefill_retrieve_success",
        plugin=plugin,
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


# - - -


def appointment_register_start(submission: "Submission", plugin):
    # TODO see if we actually have plugin here
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
