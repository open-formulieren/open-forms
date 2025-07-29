from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.payments.constants import (
    PaymentStatus as OFPaymentStatus,
)

logger = structlog.stdlib.get_logger(__name__)

# TODO: use TextChoices return type hint where applicable


class WorldlineEndpoints(models.TextChoices):
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

    @classproperty
    def payment_status_mapping(cls) -> dict:
        return {
            cls.created: [PaymentStatus.created],
            cls.unsuccessful: [
                PaymentStatus.cancelled,
                PaymentStatus.rejected,
                PaymentStatus.rejected_capture,
            ],
            cls.pending_payment: [
                PaymentStatus.redirected,
                PaymentStatus.pending_payment,
            ],
            cls.account_verified: [PaymentStatus.account_verified],
            cls.pending_merchant: [
                PaymentStatus.pending_approval,
                PaymentStatus.pending_completion,
                PaymentStatus.pending_capture,
                PaymentStatus.pending_fraud_approval,
            ],
            cls.pending_connect_or_3rd_party: [
                PaymentStatus.authorization_requested,
                PaymentStatus.capture_requested,
            ],
            cls.completed: [
                PaymentStatus.captured,
                PaymentStatus.paid,
                PaymentStatus.chargeback_notification,
            ],
            cls.reversed: [
                PaymentStatus.chargebacked,
                PaymentStatus.reversed,
            ],
            cls.refunded: [
                PaymentStatus.refunded,
            ],
        }

    @classproperty
    def of_status_mapping(cls) -> dict:
        return {
            cls.created: OFPaymentStatus.started,
            cls.unsuccessful: OFPaymentStatus.failed,
            cls.pending_payment: OFPaymentStatus.processing,
            cls.account_verified: OFPaymentStatus.started,
            cls.pending_merchant: OFPaymentStatus.processing,
            cls.pending_connect_or_3rd_party: OFPaymentStatus.processing,
            cls.completed: OFPaymentStatus.completed,
            cls.reversed: OFPaymentStatus.completed,
            cls.refunded: OFPaymentStatus.failed,
        }

    @classmethod
    def from_payment_status(cls, worldline_status: str) -> str:
        try:
            return next(
                category
                for category, items in cls.payment_status_mapping.items()
                if worldline_status in items
            )
        except StopIteration:
            raise KeyError(f"Unknown status {worldline_status} found")

    @classmethod
    def to_of_status(cls, worldine_status_category: str) -> str:
        return cls.of_status_mapping[worldine_status_category]


class HostedCheckoutStatus(models.TextChoices):
    payment_created = "PAYMENT_CREATED"
    in_progress = "IN_PROGRESS"
    cancelled_by_consumer = "CANCELLED_BY_CONSUMER"
    client_not_eligible = "CLIENT_NOT_ELIGIBLE_FOR_SELECTED_PAYMENT_PRODUCT"

    @classproperty
    def of_mapping(cls) -> dict[str, str]:
        return {
            cls.payment_created: OFPaymentStatus.started,
            cls.in_progress: OFPaymentStatus.started,
            cls.cancelled_by_consumer: OFPaymentStatus.failed,
            cls.client_not_eligible: OFPaymentStatus.failed,
        }

    @classmethod
    def to_of_status(cls, value) -> str:
        return cls.of_mapping[value]


def get_payment_status(
    worldline_status: str, checkout_status: str | None = None
) -> str:
    if not worldline_status and checkout_status:
        return HostedCheckoutStatus.to_of_status(checkout_status)

    try:
        status_category = StatusCategory.from_payment_status(worldline_status)
    except KeyError as exc:
        logger.exception(
            "unknown_payment_status_encountered",
            exc_info=exc,
            status=worldline_status,
            checkout_status=checkout_status,
        )
        return ""
    return StatusCategory.to_of_status(status_category)
