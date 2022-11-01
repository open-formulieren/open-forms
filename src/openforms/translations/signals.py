from django.dispatch import receiver
from django.utils import translation

from rest_framework.request import Request

from openforms.submissions.models import Submission
from openforms.submissions.signals import submission_start


@receiver(submission_start, dispatch_uid="translation.set_submission_language")
def set_submission_language(sender, instance: Submission, request: Request, **kwargs):
    instance.language_code = translation.get_language()
    instance.save()
