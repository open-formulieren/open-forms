from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.payments.constants import PaymentStatus as OFPaymentStatus


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

    @classmethod
    def from_payment_status(cls, worldline_status: PaymentStatus) -> "StatusCategory":
        return next(
            category
            for category, items in CATEGORY_TO_STATUS.items()
            if worldline_status in items
        )

    @classmethod
    def to_of_status(
        cls, worldline_status_category: "StatusCategory"
    ) -> OFPaymentStatus:
        return CATEGORY_TO_OF_STATUS[worldline_status_category]


class HostedCheckoutStatus(models.TextChoices):
    payment_created = "PAYMENT_CREATED"
    in_progress = "IN_PROGRESS"
    cancelled_by_consumer = "CANCELLED_BY_CONSUMER"
    client_not_eligible = "CLIENT_NOT_ELIGIBLE_FOR_SELECTED_PAYMENT_PRODUCT"

    @classmethod
    def to_payment_status(cls, value: "HostedCheckoutStatus") -> PaymentStatus:
        return CHECKOUT_STATUS_TO_STATUS[value]


CATEGORY_TO_STATUS = {
    StatusCategory.created: [PaymentStatus.created],
    StatusCategory.unsuccessful: [
        PaymentStatus.cancelled,
        PaymentStatus.rejected,
        PaymentStatus.rejected_capture,
    ],
    StatusCategory.pending_payment: [
        PaymentStatus.redirected,
        PaymentStatus.pending_payment,
    ],
    StatusCategory.account_verified: [PaymentStatus.account_verified],
    StatusCategory.pending_merchant: [
        PaymentStatus.pending_approval,
        PaymentStatus.pending_completion,
        PaymentStatus.pending_capture,
        PaymentStatus.pending_fraud_approval,
    ],
    StatusCategory.pending_connect_or_3rd_party: [
        PaymentStatus.authorization_requested,
        PaymentStatus.capture_requested,
    ],
    StatusCategory.completed: [
        PaymentStatus.captured,
        PaymentStatus.paid,
        PaymentStatus.chargeback_notification,
    ],
    StatusCategory.reversed: [
        PaymentStatus.chargebacked,
        PaymentStatus.reversed,
    ],
    StatusCategory.refunded: [
        PaymentStatus.refunded,
    ],
}

CATEGORY_TO_OF_STATUS = {
    StatusCategory.created: OFPaymentStatus.started,
    StatusCategory.unsuccessful: OFPaymentStatus.failed,
    StatusCategory.pending_payment: OFPaymentStatus.processing,
    StatusCategory.account_verified: OFPaymentStatus.started,
    StatusCategory.pending_merchant: OFPaymentStatus.processing,
    StatusCategory.pending_connect_or_3rd_party: OFPaymentStatus.processing,
    StatusCategory.completed: OFPaymentStatus.completed,
    StatusCategory.reversed: OFPaymentStatus.completed,
    StatusCategory.refunded: OFPaymentStatus.failed,
}

CHECKOUT_STATUS_TO_STATUS = {
    HostedCheckoutStatus.payment_created: PaymentStatus.created,
    HostedCheckoutStatus.in_progress: PaymentStatus.created,
    HostedCheckoutStatus.cancelled_by_consumer: PaymentStatus.cancelled,
    HostedCheckoutStatus.client_not_eligible: PaymentStatus.rejected,
}


assert all(
    any(status in values for values in CATEGORY_TO_STATUS.values())
    for status in PaymentStatus.values
), "Not all payment statuses are present in the CATEGORY_TO_STATUS mapping!"

assert all(value in CATEGORY_TO_OF_STATUS for value in StatusCategory.values), (
    "Not all status categories are present in the CATEGORY_TO_OF_STATUS mapping!"
)

assert all(
    value in CHECKOUT_STATUS_TO_STATUS for value in HostedCheckoutStatus.values
), (
    "Not all HostedCheckoutStatus's are present in the CHECKOUT_STATUS_TO_STATUS mapping!"
)
