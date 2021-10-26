from django.db import transaction

from openforms.logging import logevent
from openforms.registrations.registry import register
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .constants import PaymentStatus

__all__ = ["update_submission_payment_registration"]


def update_submission_payment_registration(submission: Submission):
    if submission.registration_status != RegistrationStatuses.success:
        return
    if not submission.payment_required:
        return
    if submission.payment_registered:
        return

    try:
        plugin = register[submission.form.registration_backend]
    except KeyError:
        return

    # TODO support partial payments
    with transaction.atomic():
        payments = submission.payments.filter(
            status=PaymentStatus.completed
        ).select_for_update()
        if not payments:
            return

        options_serializer = plugin.configuration_options(
            data=submission.form.registration_backend_options
        )
        options_serializer.is_valid(raise_exception=True)

        try:
            plugin.update_payment_status(submission, options_serializer.validated_data)
            payments.update(status=PaymentStatus.registered)
        except Exception as e:
            for p in payments:
                logevent.payment_register_failure(p, plugin, e)
            raise
        else:
            for p in payments:
                logevent.payment_register_success(p, plugin)
