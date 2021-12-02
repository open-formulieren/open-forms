import warnings

from django.dispatch import receiver

from rest_framework.request import Request

from openforms.submissions.models import Submission
from openforms.submissions.signals import submission_start


@receiver(submission_start, dispatch_uid="auth.eherkenning.set_submission_kvk")
def set_kvk_from_session(sender, instance: Submission, request: Request, **kwargs):
    kvk = request.session.get("kvk")
    if not kvk:
        return

    warnings.warn(
        "The bare 'kvk' session key is deprecated in favour of the generic 'form_auth' "
        "session key.",
        DeprecationWarning,
    )

    instance.kvk = kvk
    instance.save(update_fields=["kvk"])
