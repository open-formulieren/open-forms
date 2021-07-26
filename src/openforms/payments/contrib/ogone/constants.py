from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


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


class OgoneStatus(DjangoChoices):
    invalid_or_incomplete = ChoiceItem(0, "Invalid or incomplete")
    cancelled_by_customer = ChoiceItem(1, "Cancelled by customer")
    authorisation_declined = ChoiceItem(2, "Authorisation declined")
    waiting_for_client_payment = ChoiceItem(41, "Waiting for client payment")
    waiting_authentication = ChoiceItem(46, "Waiting authentication")
    authorised = ChoiceItem(5, "Authorised")
    authorised_waiting_external_result = ChoiceItem(
        50, "Authorised waiting external result"
    )
    authorisation_waiting = ChoiceItem(51, "Authorisation waiting")
    authorisation_not_known = ChoiceItem(52, "Authorisation not known")
    standby = ChoiceItem(55, "Standby")
    ok_with_scheduled_payments = ChoiceItem(56, "Ok with scheduled payments")
    not_ok_with_scheduled_payments = ChoiceItem(57, "Not OK with scheduled payments")
    authorised_and_cancelled = ChoiceItem(6, "Authorised and cancelled")
    author_deletion_waiting = ChoiceItem(61, "Author. deletion waiting")
    author_deletion_uncertain = ChoiceItem(62, "Author. deletion uncertain")
    author_deletion_refused = ChoiceItem(63, "Author. deletion refused")
    payment_deleted = ChoiceItem(7, "Payment deleted")
    payment_deletion_pending = ChoiceItem(71, "Payment deletion pending")
    payment_deletion_uncertain = ChoiceItem(72, "Payment deletion uncertain")
    payment_deletion_refused = ChoiceItem(73, "Payment deletion refused")
    payment_deleted2 = ChoiceItem(74, "Payment deleted")  # double?
    refund = ChoiceItem(8, "Refund")
    refund_pending = ChoiceItem(81, "Refund pending")
    refund_uncertain = ChoiceItem(82, "Refund uncertain")
    refund_refused = ChoiceItem(83, "Refund refused")
    payment_declined_by_the_acquirer = ChoiceItem(
        84, "Payment declined by the acquirer"
    )
    refund_processed_by_merchant = ChoiceItem(85, "Refund processed by merchant")
    payment_requested = ChoiceItem(9, "Payment requested")
    payment_processing = ChoiceItem(91, "Payment processing")
    payment_uncertain = ChoiceItem(92, "Payment uncertain")
    payment_refused = ChoiceItem(93, "Payment refused")
    refund_declined_by_the_acquirer = ChoiceItem(94, "Refund declined by the acquirer")
    payment_processed_by_merchant = ChoiceItem(95, "Payment processed by merchant")
    being_processed = ChoiceItem(99, "Being processed")
