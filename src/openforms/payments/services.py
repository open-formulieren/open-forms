from django.db import transaction

from openforms.registrations.registry import register
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .constants import PaymentStatus


def update_submission_payment_registration(submission: Submission):
    # TODO wrap in celery task
    # TODO logging
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

        # TODO handle errors etc
        plugin.update_payment_status(submission)
        # TODO add locking? we'd flag all completed
        payments.update(status=PaymentStatus.registered)
