from django.db import transaction

from openforms.logging import logevent
from openforms.registrations.registry import register
from openforms.submissions.models import Submission

from .constants import PaymentStatus

__all__ = ["update_submission_payment_registration"]


def update_submission_payment_registration(submission: Submission):
    try:
        plugin = register[submission.registration_backend.backend]
    except (AttributeError, KeyError) as e:
        logevent.registration_payment_update_failure(submission, error=e)
        return

    # TODO support partial payments
    with transaction.atomic():
        payments = submission.payments.filter(
            status=PaymentStatus.completed
        ).select_for_update()
        if not payments:
            logevent.registration_payment_update_skip(submission)
            return

        logevent.registration_payment_update_start(submission, plugin=plugin)
        options_serializer = plugin.configuration_options(
            data=(
                submission.registration_backend
                and submission.registration_backend.options
            ),
            context={"validate_business_logic": False},
        )
        options_serializer.is_valid(raise_exception=True)

        try:
            plugin.update_payment_status(submission, options_serializer.validated_data)
            payments.mark_registered()
        except Exception as e:
            logevent.registration_payment_update_failure(
                submission, error=e, plugin=plugin
            )
            for p in payments:
                logevent.payment_register_failure(p, plugin, e)
            raise
        else:
            logevent.registration_payment_update_success(submission, plugin=plugin)
            for p in payments:
                logevent.payment_register_success(p, plugin)
