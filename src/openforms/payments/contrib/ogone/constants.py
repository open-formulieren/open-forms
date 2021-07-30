from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

from openforms.payments.constants import PaymentStatus


class HashAlgorithm(DjangoChoices):
    sha1 = ChoiceItem("sha1", "SHA-1")
    sha256 = ChoiceItem("sha256", "SHA-256")
    sha512 = ChoiceItem("sha512", "SHA-512")


class OgoneEndpoints(DjangoChoices):
    test = ChoiceItem(
        "https://ogone.test.v-psp.com/ncol/test/orderstandard_utf8.asp",
        _("Ogone Test"),
    )
    live = ChoiceItem(
        "https://secure.ogone.com/ncol/prod/orderstandard_utf8.asp",
        _("Ogone Live"),
    )


def StatusChoice(value, label, status):
    # wrapper to keep code dry-er
    return ChoiceItem(value, label, payment_status=status)


class OgoneStatus(DjangoChoices):
    invalid_or_incomplete = StatusChoice(
        "0", "Invalid or incomplete", PaymentStatus.failed
    )
    cancelled_by_customer = StatusChoice(
        "1", "Cancelled by customer", PaymentStatus.failed
    )
    authorisation_declined = StatusChoice(
        "2", "Authorisation declined", PaymentStatus.failed
    )
    waiting_for_client_payment = StatusChoice(
        "41", "Waiting for client payment", PaymentStatus.processing
    )
    waiting_authentication = StatusChoice(
        "46", "Waiting authentication", PaymentStatus.processing
    )
    authorised = StatusChoice("5", "Authorised", PaymentStatus.processing)
    authorised_waiting_external_result = StatusChoice(
        "50", "Authorised waiting external result", PaymentStatus.processing
    )
    authorisation_waiting = StatusChoice(
        "51", "Authorisation waiting", PaymentStatus.processing
    )
    authorisation_not_known = StatusChoice(
        "52", "Authorisation not known", PaymentStatus.processing
    )
    standby = StatusChoice("55", "Standby", PaymentStatus.processing)
    ok_with_scheduled_payments = StatusChoice(
        "56", "Ok with scheduled payments", PaymentStatus.processing
    )
    not_ok_with_scheduled_payments = StatusChoice(
        "57", "Not OK with scheduled payments", PaymentStatus.failed
    )
    authorised_and_cancelled = StatusChoice(
        "6", "Authorised and cancelled", PaymentStatus.failed
    )
    author_deletion_waiting = StatusChoice(
        "61", "Author. deletion waiting", PaymentStatus.failed
    )
    author_deletion_uncertain = StatusChoice(
        "62", "Author. deletion uncertain", PaymentStatus.failed
    )
    author_deletion_refused = StatusChoice(
        "63", "Author. deletion refused", PaymentStatus.failed
    )
    payment_deleted = StatusChoice("7", "Payment deleted", PaymentStatus.failed)
    payment_deletion_pending = StatusChoice(
        "71", "Payment deletion pending", PaymentStatus.failed
    )
    payment_deletion_uncertain = StatusChoice(
        "72", "Payment deletion uncertain", PaymentStatus.failed
    )
    payment_deletion_refused = StatusChoice(
        "73", "Payment deletion refused", PaymentStatus.failed
    )
    payment_deleted2 = StatusChoice(
        "74", "Payment deleted", PaymentStatus.failed
    )  # double?
    refund = StatusChoice("8", "Refund", PaymentStatus.failed)
    refund_pending = StatusChoice("81", "Refund pending", PaymentStatus.failed)
    refund_uncertain = StatusChoice("82", "Refund uncertain", PaymentStatus.failed)
    refund_refused = StatusChoice("83", "Refund refused", PaymentStatus.failed)
    payment_declined_by_the_acquirer = StatusChoice(
        "84", "Payment declined by the acquirer", PaymentStatus.failed
    )
    refund_processed_by_merchant = StatusChoice(
        "85", "Refund processed by merchant", PaymentStatus.failed
    )
    payment_requested = StatusChoice("9", "Payment requested", PaymentStatus.completed)
    payment_processing = StatusChoice(
        "91", "Payment processing", PaymentStatus.processing
    )
    payment_uncertain = StatusChoice(
        "92", "Payment uncertain", PaymentStatus.processing
    )
    payment_refused = StatusChoice("93", "Payment refused", PaymentStatus.failed)
    refund_declined_by_the_acquirer = StatusChoice(
        "94", "Refund declined by the acquirer", PaymentStatus.failed
    )
    payment_processed_by_merchant = StatusChoice(
        "95", "Payment processed by merchant", PaymentStatus.failed
    )
    being_processed = StatusChoice("99", "Being processed", PaymentStatus.processing)

    @classmethod
    def as_payment_status(cls, ogone_status):
        choice = cls.get_choice(str(ogone_status))
        return choice.payment_status
