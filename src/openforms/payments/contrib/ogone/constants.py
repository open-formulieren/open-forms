from django.db import models
from django.utils.translation import gettext_lazy as _

from ...constants import PaymentStatus


class HashAlgorithm(models.TextChoices):
    sha1 = "sha1", "SHA-1"
    sha256 = "sha256", "SHA-256"
    sha512 = "sha512", "SHA-512"


class OgoneEndpoints(models.TextChoices):
    test = "https://ogone.test.v-psp.com/ncol/test/orderstandard_utf8.asp", _(
        "Ogone Test"
    )
    live = "https://secure.ogone.com/ncol/prod/orderstandard_utf8.asp", _("Ogone Live")


class OgoneStatus(models.TextChoices):
    invalid_or_incomplete = "0", "Invalid or incomplete"
    cancelled_by_customer = "1", "Cancelled by customer"
    authorisation_declined = "2", "Authorisation declined"
    waiting_for_client_payment = "41", "Waiting for client payment"
    waiting_authentication = "46", "Waiting authentication"
    authorised = "5", "Authorised"
    authorised_waiting_external_result = "50", "Authorised waiting external result"
    authorisation_waiting = "51", "Authorisation waiting"
    authorisation_not_known = "52", "Authorisation not known"
    standby = "55", "Standby"
    ok_with_scheduled_payments = "56", "Ok with scheduled payments"
    not_ok_with_scheduled_payments = "57", "Not OK with scheduled payments"
    authorised_and_cancelled = "6", "Authorised and cancelled"
    author_deletion_waiting = "61", "Author. deletion waiting"
    author_deletion_uncertain = "62", "Author. deletion uncertain"
    author_deletion_refused = "63", "Author. deletion refused"
    payment_deleted = "7", "Payment deleted"
    payment_deletion_pending = "71", "Payment deletion pending"
    payment_deletion_uncertain = "72", "Payment deletion uncertain"
    payment_deletion_refused = "73", "Payment deletion refused"
    payment_deleted2 = "74", "Payment deleted"  # double
    refund = "8", "Refund"
    refund_pending = "81", "Refund pending"
    refund_uncertain = "82", "Refund uncertain"
    refund_refused = "83", "Refund refused"
    payment_declined_by_the_acquirer = "84", "Payment declined by the acquirer"
    refund_processed_by_merchant = "85", "Refund processed by merchant"
    payment_requested = "9", "Payment requested"
    payment_processing = "91", "Payment processing"
    payment_uncertain = "92", "Payment uncertain"
    payment_refused = "93", "Payment refused"
    refund_declined_by_the_acquirer = "94", "Refund declined by the acquirer"
    payment_processed_by_merchant = "95", "Payment processed by merchant"
    being_processed = "99", "Being processed"

    @classmethod
    def as_payment_status(cls, ogone_status: str) -> str:
        return OGONE_TO_PAYMENT_STATUS[ogone_status]


OGONE_TO_PAYMENT_STATUS: dict[str, str] = {
    OgoneStatus.invalid_or_incomplete.value: PaymentStatus.failed.value,
    OgoneStatus.cancelled_by_customer.value: PaymentStatus.failed.value,
    OgoneStatus.authorisation_declined.value: PaymentStatus.failed.value,
    OgoneStatus.waiting_for_client_payment.value: PaymentStatus.processing.value,
    OgoneStatus.waiting_authentication.value: PaymentStatus.processing.value,
    OgoneStatus.authorised.value: PaymentStatus.processing.value,
    OgoneStatus.authorised_waiting_external_result.value: PaymentStatus.processing.value,
    OgoneStatus.authorisation_waiting.value: PaymentStatus.processing.value,
    OgoneStatus.authorisation_not_known.value: PaymentStatus.processing.value,
    OgoneStatus.standby.value: PaymentStatus.processing.value,
    OgoneStatus.ok_with_scheduled_payments.value: PaymentStatus.processing.value,
    OgoneStatus.not_ok_with_scheduled_payments.value: PaymentStatus.failed.value,
    OgoneStatus.authorised_and_cancelled.value: PaymentStatus.failed.value,
    OgoneStatus.author_deletion_waiting.value: PaymentStatus.failed.value,
    OgoneStatus.author_deletion_uncertain.value: PaymentStatus.failed.value,
    OgoneStatus.author_deletion_refused.value: PaymentStatus.failed.value,
    OgoneStatus.payment_deleted.value: PaymentStatus.failed.value,
    OgoneStatus.payment_deletion_pending.value: PaymentStatus.failed.value,
    OgoneStatus.payment_deletion_uncertain.value: PaymentStatus.failed.value,
    OgoneStatus.payment_deletion_refused.value: PaymentStatus.failed.value,
    OgoneStatus.payment_deleted2.value: PaymentStatus.failed,  # doubl.valuee
    OgoneStatus.refund.value: PaymentStatus.failed.value,
    OgoneStatus.refund_pending.value: PaymentStatus.failed.value,
    OgoneStatus.refund_uncertain.value: PaymentStatus.failed.value,
    OgoneStatus.refund_refused.value: PaymentStatus.failed.value,
    OgoneStatus.payment_declined_by_the_acquirer.value: PaymentStatus.failed.value,
    OgoneStatus.refund_processed_by_merchant.value: PaymentStatus.failed.value,
    OgoneStatus.payment_requested.value: PaymentStatus.completed.value,
    OgoneStatus.payment_processing.value: PaymentStatus.processing.value,
    OgoneStatus.payment_uncertain.value: PaymentStatus.processing.value,
    OgoneStatus.payment_refused.value: PaymentStatus.failed.value,
    OgoneStatus.refund_declined_by_the_acquirer.value: PaymentStatus.failed.value,
    OgoneStatus.payment_processed_by_merchant.value: PaymentStatus.failed.value,
    OgoneStatus.being_processed.value: PaymentStatus.processing.value,
}

assert set(OgoneStatus.values) == set(
    OGONE_TO_PAYMENT_STATUS.keys()
), "Not all Ogone statuses are mapped to a generic payment status"
