from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

SUBMISSIONS_SESSION_KEY = "form-submissions"
UPLOADS_SESSION_KEY = "form-uploads"

IMAGE_COMPONENTS = ["signature"]


class RegistrationStatuses(DjangoChoices):
    pending = ChoiceItem("pending", _("Pending (not registered yet)"))
    in_progress = ChoiceItem("in_progress", _("In Progress (not registered yet)"))
    success = ChoiceItem("success", _("Success"))
    failed = ChoiceItem("failed", _("Failed"))


class RemovalMethods(DjangoChoices):
    delete_permanently = ChoiceItem(
        "delete_permanently", _("Submissions will be deleted")
    )
    make_anonymous = ChoiceItem(
        "make_anonymous", _("Sensitive data within the submissions will be deleted")
    )
