from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

SUBMISSIONS_SESSION_KEY = "form-submissions"

IMAGE_COMPONENTS = ["signature"]


class RegistrationStatuses(DjangoChoices):
    pending = ChoiceItem("pending", _("Pending (not registered yet)"))
    success = ChoiceItem("success", _("Success"))
    failed = ChoiceItem("failed", _("Failed"))
