from openforms.payments.constants import PaymentStatus
from openforms.registrations.registry import register
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission


def update_submission_payment_registration(submission: Submission):
    # TODO wrap in celery task
    # TODO logging
    if submission.registration_status != RegistrationStatuses.success:
        return
    if not submission.registration_id:
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
    payments = submission.payments.filter(status=PaymentStatus.completed)
    if not payments:
        return

    # TODO handle errors etc
    plugin.update_payment_status(submission)
    # TODO add locking? we'd flag all completed
    payments.update(status=PaymentStatus.registered)
