from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class PaymentRequestType(DjangoChoices):
    get = ChoiceItem("get")
    post = ChoiceItem("post")


class UserAction(DjangoChoices):
    accept = ChoiceItem("accept")
    exception = ChoiceItem("exception")
    cancel = ChoiceItem("cancel")
    # back = ChoiceItem("back")
    # decline = ChoiceItem("decline")

    unknown = ChoiceItem("unknown")


class PaymentStatus(DjangoChoices):
    # not_required = ChoiceItem("not_required", _("Not required"))

    # in-progress
    started = ChoiceItem("started", _("Started by user"))
    processing = ChoiceItem("processing", _("Backend is processing"))

    # payment finished
    failed = ChoiceItem("failed", _("Cancelled or failed"))
    completed = ChoiceItem("completed", _("Completed by user"))

    # flow done
    registered = ChoiceItem("registered", _("Completed and registered"))

    is_final = {
        failed.value,
        completed.value,
        registered.value,
    }
