from django.db import models
from django.utils.translation import gettext_lazy as _


class WordlineEndpoints(models.TextChoices):
    test = (
        "https://payment.preprod.direct.worldline-solutions.com/v2/",
        _("Worldline Test"),
    )
    live = "https://payment.direct.worldline-solutions.com/v2/", _("Worldline Live")


class WordlineStatus(models.TextChoices):
    created = "CREATED"
    cancelled = "CANCELLED"
    rejected = "REJECTED"
    rejected_capture = "REJECTED_CAPTURE"
    redirected = "REDIRECTED"
    pending_payment = "PENDING_PAYMENT"
    pending_completion = "PENDING_COMPLETION"
    pending_capture = "PENDING_CAPTURE"
    authorization_requested = "AUTHORIZATION_REQUESTED"
    capture_requested = "CAPTURE_REQUESTED"
    captured = "CAPTURED"
    reversed = "REVERSED"
    refund_requested = "REFUND_REQUESTED"
    refunded = "REFUNDED"
