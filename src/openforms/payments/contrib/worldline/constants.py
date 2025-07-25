from django.db import models
from django.utils.translation import gettext_lazy as _


class WordlineEndpoints(models.TextChoices):
    test = (
        "https://payment.preprod.direct.worldline-solutions.com",
        _("Worldline Test"),
    )
    live = "https://payment.direct.worldline-solutions.com", _("Worldline Live")


# see https://apireference.connect.worldline-solutions.com/s2sapi/v1/en_US/python/statuses.html?paymentPlatform=ALL#statuses
class PaymentStatus(models.TextChoices):
    # CREATED category
    created = "CREATED"

    # UNSUCCESSFUL category
    cancelled = "CANCELLED"
    rejected = "REJECTED"
    rejected_capture = "REJECTED_CAPTURE"

    # PENDING_PAYMENT category
    pending_payment = "PENDING_PAYMENT"
    redirected = "REDIRECTED"

    # ACCOUNT_VERIFIED category
    account_verified = "ACCOUNT_VERIFIED"

    # PENDING_MERCHANT category
    pending_approval = "PENDING_APPROVAL"
    pending_completion = "PENDING_COMPLETION"
    pending_capture = "PENDING_CAPTURE"
    pending_fraud_approval = "PENDING_FRAUD_APPROVAL"

    # PENDING_CONNECT_OR_3RD_PARTY category
    authorization_requested = "AUTHORIZATION_REQUESTED"
    capture_requested = "CAPTURE_REQUESTED"

    # COMPLETED category
    captured = "CAPTURED"
    paid = "PAID"
    chargeback_notification = "CHARGEBACK_NOTIFICATION"

    # REVERSED category
    chargebacked = "CHARGEBACKED"
    reversed = "REVERSED"

    # REFUNDED category
    refunded = "REFUNDED"

    # TODO: map to PaymentStatus from payments app


class PaymentStatusCategory(models.TextChoices):
    rejected = "REJECTED"
    status_unknown = "STATUS_UNKNOWN"
    successful = "SUCCESFUL"

    payment_status_mapping = {
        rejected: [
            PaymentStatus.created,
            PaymentStatus.cancelled,
            PaymentStatus.rejected,
            PaymentStatus.rejected_capture,
        ],
        status_unknown: [PaymentStatus.redirected],
        successful: [PaymentStatus.redirected],
    }

    @classmethod
    def from_payment_status(cls, value):
        return next(
            category for category, items in cls.payment_status_mapping if value in items
        )


class StatusCategory(models.TextChoices):
    created = "CREATED"
    unsuccessful = "UNSUCCESSFUL"
    pending_payment = "PENDING_PAYMENT"
    account_verified = "ACCOUNT_VERIFIED"
    pending_merchant = "PENDING_MERCHANT"
    pending_connect_or_3rd_party = "PENDING_CONNECT_OR_3RD_PARTY"
    completed = "COMPLETED"
    reversed = "REVERSED"
    refunded = "REFUNDED"

    payment_status_mapping = {
        created: [PaymentStatus.created],
        unsuccessful: [
            PaymentStatus.cancelled,
            PaymentStatus.rejected,
            PaymentStatus.rejected_capture,
        ],
        pending_payment: [
            PaymentStatus.redirected,
            PaymentStatus.pending_payment,
        ],
        account_verified: [PaymentStatus.account_verified],
        pending_merchant: [
            PaymentStatus.pending_approval,
            PaymentStatus.pending_completion,
            PaymentStatus.pending_capture,
            PaymentStatus.pending_fraud_approval,
        ],
        pending_connect_or_3rd_party: [
            PaymentStatus.authorization_requested,
            PaymentStatus.capture_requested,
        ],
        completed: [
            PaymentStatus.captured,
            PaymentStatus.paid,
            PaymentStatus.chargeback_notification,
        ],
        reversed: [
            PaymentStatus.chargebacked,
            PaymentStatus.reversed,
        ],
        refunded: [
            PaymentStatus.refunded,
        ],
    }

    @classmethod
    def from_payment_status(cls, value):
        return next(
            category for category, items in cls.payment_status_mapping if value in items
        )
