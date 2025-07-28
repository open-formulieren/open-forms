from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from openforms.payments.constants import (
    PAYMENT_STATUS_FINAL,
    PaymentStatus as OFPaymentStatus,
    UserAction,
)

# TODO: use TextChoices return type hint where applicable


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


class PaymentStatusCategory(models.TextChoices):
    rejected = "REJECTED"
    status_unknown = "STATUS_UNKNOWN"
    successful = "SUCCESFUL"

    @classproperty
    def payment_status_mapping(cls) -> dict:
        return {
            cls.rejected: [
                PaymentStatus.created,
                PaymentStatus.cancelled,
                PaymentStatus.rejected,
                PaymentStatus.rejected_capture,
            ],
            cls.status_unknown: [PaymentStatus.redirected],
            cls.successful: [
                PaymentStatus.pending_payment,
                PaymentStatus.account_verified,
                PaymentStatus.pending_approval,
                PaymentStatus.pending_completion,
                PaymentStatus.pending_capture,
                PaymentStatus.pending_fraud_approval,
                PaymentStatus.authorization_requested,
                PaymentStatus.capture_requested,
                PaymentStatus.captured,
                PaymentStatus.paid,
                PaymentStatus.chargeback_notification,
                PaymentStatus.chargebacked,
                PaymentStatus.reversed,
                PaymentStatus.refunded,
            ],
        }

    @classmethod
    def from_payment_status(cls, worldline_status: str) -> str:
        return next(
            category
            for category, items in cls.payment_status_mapping
            if worldline_status in items
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
            cls.pending_payment: OFPaymentStatus.started,
            cls.account_verified: OFPaymentStatus.started,
            cls.pending_merchant: OFPaymentStatus.processing,
            cls.pending_connect_or_3rd_party: OFPaymentStatus.processing,
            cls.completed: OFPaymentStatus.completed,
            cls.reversed: OFPaymentStatus.completed,
            cls.refunded: OFPaymentStatus.completed,
        }

    @classproperty
    def of_action_mapping(cls) -> dict:
        return {
            cls.created: UserAction.unknown,
            cls.unsuccessful: UserAction.exception,
            cls.pending_payment: UserAction.unknown,
            cls.account_verified: UserAction.unknown,
            cls.pending_merchant: UserAction.unknown,
            cls.pending_connect_or_3rd_party: UserAction.unknown,
            cls.completed: UserAction.accept,
            cls.reversed: UserAction.accept,
            cls.refunded: UserAction.accept,
        }

    @classmethod
    def from_payment_status(cls, worldline_status: str) -> str:
        return next(
            category
            for category, items in cls.payment_status_mapping.items()
            if worldline_status in items
        )

    @classmethod
    def to_of_status(cls, worldine_status_category: str) -> str:
        return cls.of_status_mapping[worldine_status_category]

    @classmethod
    def to_of_action(cls, worldine_status_category: str) -> str:
        return cls.of_action_mapping[worldine_status_category]


def is_final_status(worldline_status: str) -> bool:
    status_category = StatusCategory.from_payment_status(worldline_status)
    return StatusCategory.to_of_status(status_category) in PAYMENT_STATUS_FINAL


def get_user_action(worldline_status: str) -> str:
    status_category = StatusCategory.from_payment_status(worldline_status)
    return StatusCategory.to_of_action(status_category)
