import re
import uuid
from decimal import Decimal

from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError, models, transaction
from django.db.models import Max, Sum
from django.utils.translation import gettext_lazy as _

from openforms.payments.constants import PaymentStatus
from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.utils.fields import StringUUIDField

RE_INVOICE_NUMBER = re.compile(r"(?P<year>20\d{2})(?P<number>\d+)$")


class SubmissionPaymentManager(models.Manager):
    def create_for(
        self,
        submission: "Submission",
        plugin_id: str,
        plugin_options: dict,
        amount: Decimal,
        form_url: str,
    ):
        assert isinstance(amount, Decimal)

        # first create without order_id
        payment = self.create(
            submission=submission,
            plugin_id=plugin_id,
            plugin_options=plugin_options,
            amount=amount,
            form_url=form_url,
        )
        # then update with a unique order_id
        while True:
            try:
                with transaction.atomic():
                    payment.order_id = self.get_next_order_id(payment)
                    payment.save(update_fields=("order_id",))
                    break
            except IntegrityError:
                # race condition on unique order_id
                continue
        return payment

    def get_next_order_id(self, payment):
        prefix = payment.created.year
        agg = self.aggregate(Max("order_id"))
        max_order_id = str(agg["order_id__max"] or "202000000")
        match = RE_INVOICE_NUMBER.match(max_order_id)
        if not match:
            raise ValueError("Invalid invoice number for invoice %d", payment.pk)
        max_number = int(match.group("number"))
        next_number = "{:05d}".format(max_number + 1)
        return int(f"{prefix}{next_number}")


class SubmissionPaymentQuerySet(models.QuerySet):
    def sum_amount(self) -> Decimal:
        return self.aggregate(sum_amount=Sum("amount"))["sum_amount"] or Decimal("0")


class SubmissionPayment(models.Model):
    uuid = StringUUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

    submission = models.ForeignKey(
        "submissions.Submission", related_name="payments", on_delete=models.CASCADE
    )
    plugin_id = models.CharField(_("Payment backend"), max_length=UNIQUE_ID_MAX_LENGTH)
    plugin_options = JSONField(
        _("Payment options"),
        blank=True,
        null=True,
        help_text=_("Copy of payment options at time of initializing payment."),
    )
    form_url = models.URLField(_("Form URL"), max_length=255)
    order_id = models.BigIntegerField(
        _("Order ID"),
        unique=True,
        null=True,
        help_text=_("Unique tracking across backend"),
    )
    amount = models.DecimalField(
        _("payment amount"),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_("Total payment amount."),
    )
    status = models.CharField(
        _("payment status"),
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.started,
        help_text=_("Status of the payment process in the configured backend."),
    )
    objects = SubmissionPaymentManager.from_queryset(SubmissionPaymentQuerySet)()

    def __str__(self):
        return f"{self.uuid} {self.amount} '{self.get_status_display()}'"

    @property
    def form(self):
        return self.submission.form
