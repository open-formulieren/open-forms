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


class PaymentStatuses(DjangoChoices):
    not_required = ChoiceItem("not_required", _("Not required"))
    waiting = ChoiceItem("waiting", _("Awaiting user action"))

    started = ChoiceItem("started", _("Process started by user"))
    cancelled = ChoiceItem("cancelled", _("Process cancelled by user"))
    completed = ChoiceItem("completed", _("Payment completed by user"))
    registered = ChoiceItem("registered", _("Payment completed and registered"))
