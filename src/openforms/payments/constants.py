from typing import cast

from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentRequestType(models.TextChoices):
    get = "get"
    post = "post"


# TODO: remove after removal of ogone app
class UserAction(models.TextChoices):
    accept = "accept"
    exception = "exception"
    cancel = "cancel"
    # back = "back"
    # decline = "decline"

    unknown = "unknown"


class PaymentStatus(models.TextChoices):
    # not_required = "not_required", _("Not required")

    # in-progress
    started = "started", _("Started by user")
    processing = "processing", _("Backend is processing")

    # payment finished
    failed = "failed", _("Cancelled or failed")
    completed = "completed", _("Completed by user")

    # flow done
    registered = "registered", _("Completed and registered")

    @classmethod
    def get_label(cls, value: str) -> str:
        return dict(cls.choices)[value]


PAYMENT_STATUS_FINAL = cast(
    set[str],
    {
        PaymentStatus.failed.value,
        PaymentStatus.completed.value,
        PaymentStatus.registered.value,
    },
)
