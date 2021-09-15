from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

SUBMISSIONS_SESSION_KEY = "form-submissions"
UPLOADS_SESSION_KEY = "form-uploads"

IMAGE_COMPONENTS = ["signature"]


class RegistrationStatuses(DjangoChoices):
    pending = ChoiceItem("pending", _("Pending (not registered yet)"))
    in_progress = ChoiceItem("in_progress", _("In progress (not registered yet)"))
    success = ChoiceItem("success", _("Success"))
    failed = ChoiceItem("failed", _("Failed"))


class ProcessingStatuses(DjangoChoices):
    """
    Translation of interal Celery states to public states.
    """

    in_progress = ChoiceItem("in_progress", _("In progress"))
    done = ChoiceItem("done", _("Done"))


class ProcessingResults(DjangoChoices):
    """
    Possible background processing outcomes (once it's 'done')
    """

    retry = ChoiceItem("retry", _("Retry needed, re-submit from summary page."))
    failed = ChoiceItem("failed", _("Failed, should return to the start of the form."))
    success = ChoiceItem("success", _("Success, proceed to confirmation page."))
