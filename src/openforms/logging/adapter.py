"""
Adapt structlog log records to django-timeline-logger compatible properties.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import models

from structlog.typing import EventDict
from timeline_logger.typing import EventDetailsProtocol

from .constants import (
    FORM_SUBMIT_SUCCESS_EVENT,
    REGISTRATION_SUCCESS_EVENT,
    TimelineLogTags,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from openforms.accounts.models import User
    from openforms.plugins.plugin import AbstractBasePlugin
    from openforms.submissions.models import Submission


@dataclass(slots=True, frozen=True, kw_only=True)
class EventDetails(EventDetailsProtocol["User"]):
    event: str
    """
    Canonical event name of the thing that happened.
    """
    instance: models.Model
    """
    Main database object this log event is about.
    """
    extra_data: Mapping[str, object] | None = None
    """
    Additional data to store in the extra_data JSON field.

    Must be JSON-serializable!
    """
    plugin: AbstractBasePlugin | None = None
    """
    The relevant plugin used, if available.
    """
    error: Exception | str = ""
    """
    Any relevant Python exception to include in the log record.

    Note that the exception may already have been formatted to a string.
    """
    tags: Collection[TimelineLogTags] = frozenset()
    """
    Tags/markers to query/filter log records on.
    """
    user: User | AnonymousUser | None = None
    """
    The current user that triggerd the log event.
    """

    def get_template_name(self) -> str:
        return f"logging/events/{self.event}.txt"

    def get_user(self) -> User | None:
        from openforms.accounts.models import User

        # If user is not authenticated (eg. AnonymousUser) we can not
        # save it on the TimelineLog model
        if self.user and self.user.is_authenticated:
            assert isinstance(self.user, User)
            return self.user
        return None

    def get_extra_data(self) -> Mapping[str, object]:
        extra_data: dict[str, object] = {"log_event": self.event}
        if self.extra_data:
            extra_data |= self.extra_data
        if self.plugin:
            extra_data |= {
                "plugin_id": self.plugin.identifier,
                "plugin_label": str(self.plugin.verbose_name),
            }
        if self.error:
            extra_data["error"] = str(self.error)

        for tag in self.tags:
            extra_data[tag] = True

        return extra_data


def from_structlog(event_dict: EventDict) -> EventDetails:
    """
    Transform structlog events into django-timeline-logger parameters.
    """
    from log_outgoing_requests.models import OutgoingRequestsLog

    from openforms.accounts.models import User
    from openforms.analytics_tools.models import AnalyticsToolsConfiguration
    from openforms.appointments.base import BasePlugin as AppointmentBasePlugin
    from openforms.forms.models import Form, FormsExport
    from openforms.payments.base import BasePlugin as PaymentBasePlugin
    from openforms.payments.models import SubmissionPayment
    from openforms.prefill.base import BasePlugin as PrefillBasePlugin
    from openforms.registrations.base import BasePlugin as RegistrationBasePlugin
    from openforms.submissions.models import Submission, SubmissionStep

    assert "event" in event_dict

    # always try to grab the submission by PK first - we can create an in-memory
    # instance to pass to the Generic Foreign Key instance without it actually having
    # to exist in the database this way (due to pending DB transactions!)
    submission: Submission | None = None
    if submission_pk := event_dict.get("submission_pk"):
        submission = Submission(pk=submission_pk)

    # in uncommitted transactions, we can't look up the submission by UUID since the
    # adapter typically runs in an separate database transaction and will trigger
    # Submission.DoesNotExist on the lookups.
    match event_dict:
        case {
            "submission_committed": False,
            "submission_uuid": str(submission_uuid),
        } if submission is None:  # pragma: no cover
            raise RuntimeError(
                "Cannot query uncommitted submission by UUID! Put 'submission_pk' "
                "in the event dict instead."
            )

    # now do the real event matching to enrich the log context/event details.
    match event_dict:
        #
        # Accounts
        #
        case {
            "event": "hijack_started" | "hijack_ended" as event,
            "hijacked": str(hijacked_username),
            "hijacker": str(hijacker_username),
        }:
            users: dict[str, User] = User.objects.filter(
                username__in=(hijacked_username, hijacker_username)
            ).in_bulk(field_name="username")
            hijacked_user = users[hijacked_username]
            hijacker = users[hijacker_username]
            extra_data = {
                "hijacker": {
                    "id": hijacker.pk,
                    "full_name": hijacker.get_full_name(),
                    "username": hijacker.username,
                },
                "hijacked": {
                    "id": hijacked_user.pk,
                    "full_name": hijacked_user.get_full_name(),
                    "username": hijacked_user.username,
                },
            }
            return EventDetails(
                event=event,
                instance=hijacked_user,
                user=hijacker,
                tags=[TimelineLogTags.hijack],
                extra_data=extra_data,
            )

        #
        # Outgoing requests logs
        #
        case {
            "event": "outgoing_request_log_details_view_admin" as event,
            "object_id": str(object_id),
            "user": str(username),
        }:
            user = User.objects.get(username=username)
            outgoing_request_log = OutgoingRequestsLog.objects.get(pk=object_id)
            return EventDetails(
                event=event,
                instance=outgoing_request_log,
                user=user,
                tags=[TimelineLogTags.AVG],
            )

        #
        # Emails (django-yubin)
        #
        case {
            "event": "email_status_change" as event,
            "submission_uuid": str(submission_uuid),
            "new_status": int(status),
            "status_label": str(status_label),
            "email_event": str(email_event),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={
                    "event": email_event,
                    "status": status,
                    "status_label": status_label,
                    "include_in_daily_digest": True,
                },
            )
        #
        # Analytics
        #
        case {
            "event": "analytics_tool_enabled" | "analytics_tool_disabled" as event,
            "analytics_tool": str(tool),
        }:
            config = AnalyticsToolsConfiguration.get_solo()
            return EventDetails(
                event=event,
                instance=config,
                extra_data={"analytics_tool": tool},
            )

        #
        # Forms
        #
        case {
            "event": "downloaded_bulk_export" as event,
            "user": str(username),
            "export_id": int(export_id),
        }:
            export = FormsExport.objects.get(pk=export_id)
            user = User.objects.get(username=username)
            return EventDetails(
                event=event,
                instance=export,
                user=user,
            )

        case {
            "event": "bulk_forms_imported" as event,
            "user_id": int(user_id),
            "failed_files": [*failed_files],
        }:
            user = User.objects.get(id=user_id)
            assert user
            return EventDetails(
                event=event,
                instance=user,
                user=user,
                extra_data={"failed_files": failed_files},
            )

        case {
            "event": "form_activated" | "form_deactivated" as event,
            "form_id": int(form_id),
        }:
            form = Form.objects.get(pk=form_id)
            return EventDetails(event=event, instance=form)

        case {
            "event": "form_configuration_error"
            | "reference_lists_failure_response" as event,
            "form_id": int(form_id),
            "component": dict() as component,
            "error_message": str(error_message),
        }:
            form = Form.objects.get(pk=form_id)
            return EventDetails(
                event=event,
                instance=form,
                error=error_message,
                extra_data={"component": component},
            )

        #
        # Submissions
        #
        case {
            "event": "submission_start" as event,
            "submission_uuid": str(submission_uuid),
        }:
            assert submission is not None  # expected to be populated via submission_pk
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "authentication.submission_auth",
            "submission_uuid": str(submission_uuid),
            "is_delegated": bool(is_delegated),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            user = (
                User.objects.get(username=username)
                if (username := event_dict.get("username"))
                else None
            )
            return EventDetails(
                event="submission_auth",
                instance=submission,
                user=user,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={"delegated": is_delegated},
            )

        case {
            "event": "submission_step_fill" as event,
            "step_id": int(step_pk),
        }:
            step = SubmissionStep.objects.select_related(
                "submission", "form_step__form_definition"
            ).get(pk=step_pk)
            assert step.form_step is not None
            return EventDetails(
                event=event,
                instance=step.submission,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={
                    "step": str(step.form_step.form_definition.name),
                    "step_id": step_pk,
                },
            )

        case {
            "event": str(event),
            "submission_uuid": str(submission_uuid),
        } if event == FORM_SUBMIT_SUCCESS_EVENT:
            submission = Submission.objects.select_related("form").get(
                uuid=submission_uuid
            )
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data=_snapshot_submission_statistics(submission),
            )

        case {
            "event": "cosigner_email_queuing_failure"
            | "cosigner_email_queuing_success" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "submission_details_view_admin"
            | "submission_details_view_api" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)

            user: User | None = None
            if username := event_dict.get("user"):
                assert isinstance(username, str)
                user = User.objects.get(username=username)

            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.AVG],
                user=user,
            )

        case {
            "event": "submission_export_list" as event,
            "form_id": int(form_id),
            "user": str(username),
        }:
            form = Form.objects.get(pk=form_id)
            user = User.objects.get(username=username)
            return EventDetails(
                event=event,
                instance=form,
                user=user,
                tags=[TimelineLogTags.AVG],
            )

        #
        # Prefil
        #
        case {
            "event": "prefill_retrieve_success" | "prefill_retrieve_empty" as event,
            "submission_uuid": str(submission_uuid),
            "plugin": PrefillBasePlugin() as plugin,
            "attributes": [*prefill_fields],
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            extra_tags: set[TimelineLogTags] = set()
            if event == "prefill_retrieve_success":
                extra_tags.add(TimelineLogTags.AVG)
            return EventDetails(
                event=event,
                instance=submission,
                plugin=plugin,
                tags=[TimelineLogTags.submission_lifecycle, *extra_tags],
                extra_data={"prefill_fields": prefill_fields},
            )

        case {
            "event": "prefill.plugin.retrieve_failure"
            | "prefill.plugin.ownership_check_failure",
            "submission_uuid": str(submission_uuid),
            "plugin": PrefillBasePlugin() as plugin,
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event="prefill_retrieve_failure",
                instance=submission,
                plugin=plugin,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        #
        # Appointments
        #
        case {
            "event": "appointment_register_start"
            | "appointment_register_skip"
            | "appointment_register_success"
            | "appointment_register_failure" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            appointment_plugin: AppointmentBasePlugin | None = event_dict.get("plugin")
            return EventDetails(
                event=event,
                instance=submission,
                plugin=appointment_plugin,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "appointment_cancel_start"
            | "appointment_cancel_success"
            | "appointment_cancel_failure" as event,
            "submission_uuid": str(submission_uuid),
            "plugin": AppointmentBasePlugin() as plugin,
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                plugin=plugin,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        #
        # Registrations
        #
        case {
            "event": "max_registration_attempts_exceeded",
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event="registration_attempts_limited",
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "skipped_registration",
            "submission_uuid": str(submission_uuid),
            "reason": str(reason),
        }:
            REASON_TO_EVENT_MAP = {
                "payment_not_received": "registration_skipped_not_yet_paid",
                "cosign_required": "skipped_registration_cosign_required",
            }
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=REASON_TO_EVENT_MAP[reason],
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "registration_start" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "registration_debug" as event,
            "submission_uuid": str(submission_uuid),
            "message": str(message),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            extra_data: dict[str, object] = {"message": message}
            # dict with key `key` and optionally a key `name`
            if backend := event_dict.get("backend"):
                extra_data["backend"] = backend
            return EventDetails(
                event=event,
                instance=submission,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data=extra_data,
            )

        case {
            "event": str(event),
            "submission_uuid": str(submission_uuid),
            "plugin": RegistrationBasePlugin() as plugin,
        } if event == REGISTRATION_SUCCESS_EVENT:
            submission = Submission.objects.select_related("form").get(
                uuid=submission_uuid
            )
            return EventDetails(
                event=event,
                instance=submission,
                plugin=plugin,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data=_snapshot_submission_statistics(submission),
            )

        case {
            "event": "registration_failure" as event,
            "submission_uuid": str(submission_uuid),
            "plugin": RegistrationBasePlugin() as plugin,
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                plugin=plugin,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "registration_completed",
            "reason": "no_registration_plugin_configured",
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event="registration_skip",
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "update_registration_with_confirmation_email_completed"
            | "update_registration_with_confirmation_email_failed"
            | "update_registration_with_confirmation_email_done" as _event,
            "submission_uuid": str(submission_uuid),
        }:
            EVENT_MAP = {
                "update_registration_with_confirmation_email_failed": "registration_update_with_confirmation_email_failure",
                "update_registration_with_confirmation_email_completed": "registration_update_with_confirmation_email_skip",
                "update_registration_with_confirmation_email_done": "registration_update_with_confirmation_email_success",
            }
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=EVENT_MAP[_event],
                instance=submission,
                plugin=event_dict.get("plugin"),
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={"reason": event_dict.get("reason")},
            )

        case {
            "event": "registration_payment_update_skip"
            | "registration_payment_update_start"
            | "registration_payment_update_success"
            | "registration_payment_update_failure" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                plugin=event_dict.get("plugin"),
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "component_pre_registration_start"
            | "component_pre_registration_success"
            | "component_pre_registration_failure"
            | "component_pre_registration_skip" as event,
            "submission_uuid": str(submission_uuid),
            "component_key": str(component_key),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={"component": component_key},
            )

        #
        # PDF generation
        #
        case {
            "event": (
                "pdf_generation_start"
                | "pdf_generation_success"
                | "pdf_generation_failure"
                | "pdf_generation_skip"
            ) as event,
            "submission_id": int(submission_id),
            "report_id": int(report_id),
        }:
            submission = Submission.objects.get(pk=submission_id)
            return EventDetails(
                event=event,
                instance=submission,
                tags=[TimelineLogTags.submission_lifecycle],
                error=event_dict.get("exception", ""),
                extra_data={"report_id": report_id},
            )

        #
        # Payments
        #
        case {
            "event": "price_calculation_variable_error" as event,
            "submission_uuid": str(submission_uuid),
            "variable": str(variable),
            # JSONValue type, but we can't pattern match that
            "value": object() as value,
            "exception": str(error),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            return EventDetails(
                event=event,
                instance=submission,
                error=error,
                extra_data={"variable": variable, "value": value},
                tags=[TimelineLogTags.submission_lifecycle],
            )

        case {
            "event": "payment_flow_start"
            | "payment_flow_failure"
            | "payment_flow_return"
            | "payment_register_success"
            | "payment_register_failure"
            | "payment_flow_webhook" as event,
            "submission_uuid": str(submission_uuid),
            "plugin": PaymentBasePlugin() | RegistrationBasePlugin() as plugin,
            "payment_uuid": str(payment_uuid),
        }:
            payment = SubmissionPayment.objects.select_related("submission").get(
                uuid=payment_uuid
            )
            assert str(payment.submission.uuid) == submission_uuid

            extra_data: dict[str, object] = {
                "payment_order_id": payment.public_order_id,
                "payment_id": payment.id,
            }
            match event:
                case "payment_flow_start":
                    extra_data["from_email"] = event_dict.get("from_email", False)
                case "payment_flow_return":
                    extra_data.update(
                        {
                            "payment_status": payment.status,
                            "payment_status_label": payment.get_status_display(),
                        }
                    )

            return EventDetails(
                event=event,
                instance=payment.submission,
                plugin=plugin,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data=extra_data,
            )

        #
        # Confirmation emails
        #
        case {
            "event": "confirmation_email_start"
            | "confirmation_email_skip"
            | "confirmation_email_scheduled"
            | "confirmation_email_success"
            | "confirmation_email_failure" as event,
            "submission_uuid": str(submission_uuid),
        }:
            submission = Submission.objects.get(uuid=submission_uuid)
            extra_data: dict[str, object] = {}
            if sched_opts := event_dict.get("scheduling_options"):
                extra_data["scheduling_options"] = sched_opts
            if reason := event_dict.get("reason"):
                extra_data["reason"] = reason
            return EventDetails(
                event=event,
                instance=submission,
                error=event_dict.get("exception", ""),
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data=extra_data or None,
            )

        #
        # Contrib - Objects API
        #
        case {
            "event": "object_ownership_passed" | "object_ownership_failure" as event,
            "submission_uuid": str(submission_uuid),
        }:
            EVENT_MAP = {
                "object_ownership_passed": "object_ownership_check_success",
                "object_ownership_failure": "object_ownership_check_failure",
            }

            submission = Submission.objects.get(uuid=submission_uuid)
            _plugin: PrefillBasePlugin | RegistrationBasePlugin | None = event_dict.get(
                "plugin"
            )

            _event = EVENT_MAP[event]
            if (
                _event == "object_ownership_check_failure"
                and not submission.is_authenticated
            ):
                _event = "object_ownership_check_anonymous_user"

            return EventDetails(
                event=_event,
                instance=submission,
                plugin=_plugin,
                tags=[TimelineLogTags.submission_lifecycle],
                extra_data={
                    "object_reference": event_dict.get("object_reference"),
                },
            )

        case _:  # pragma: no cover
            raise AssertionError(f"Unhandled event '{event_dict['event']}'!")


def _snapshot_submission_statistics(submission: Submission):
    return {
        # note: these keys are used in the form statistics admin view!
        "public_reference": submission.public_registration_reference,
        "form_id": submission.form.pk,
        "form_name": submission.form.name,
        "internal_form_name": submission.form.internal_name,
        "submitted_on": submission.completed_on,
    }
