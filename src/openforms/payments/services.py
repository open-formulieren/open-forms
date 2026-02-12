from django.db import transaction

from openforms.logging import audit_logger
from openforms.registrations.registry import register
from openforms.submissions.models import Submission

from .constants import PaymentStatus

__all__ = ["update_submission_payment_registration"]


def update_submission_payment_registration(submission: Submission):
    audit_log = audit_logger.bind(submission_uuid=str(submission.uuid))

    if (registration_backend := submission.registration_backend) is None:
        audit_log.info(
            "registration_payment_update_failure", reason="no_registration_backend"
        )
        return

    try:
        plugin = register[registration_backend.backend]
    except KeyError as exc:
        audit_log.warning("registration_payment_update_failure", exc_info=exc)
        return

    audit_log = audit_log.bind(plugin=plugin)

    # TODO support partial payments
    with transaction.atomic():
        payments = submission.payments.filter(
            status=PaymentStatus.completed
        ).select_for_update()
        if not payments:
            audit_log.info("registration_payment_update_skip")
            return

        audit_log.info("registration_payment_update_start")
        options_serializer = plugin.configuration_options(
            data=registration_backend and registration_backend.options,
            context={"validate_business_logic": False},
        )
        options_serializer.is_valid(raise_exception=True)

        try:
            plugin.update_payment_status(submission, options_serializer.validated_data)
            # FIXME: pyright + custom querysets...
            payments.mark_registered()  # pyright: ignore[reportAttributeAccessIssue]
        except Exception as exc:
            audit_log = audit_log.bind(exc_info=exc)
            audit_log.warning("registration_payment_update_failure")
            for p in payments:
                audit_log.warning("payment_register_failure", payment_uuid=str(p.uuid))
            raise
        else:
            audit_log.info("registration_payment_update_success")
            for p in payments:
                audit_log.info("payment_register_success", payment_uuid=str(p.uuid))
