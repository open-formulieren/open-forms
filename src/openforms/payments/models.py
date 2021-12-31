import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List

from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError, models, transaction
from django.db.models import Max, Sum
from django.utils.translation import gettext_lazy as _

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH

from ..config.models import GlobalConfiguration
from .constants import PaymentStatus

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission

ORDER_ID_START = 100
ORDER_ID_PAD_LENGTH = 6


class SubmissionPaymentManager(models.Manager):
    def create_for(
        self,
        submission: "Submission",
        plugin_id: str,
        plugin_options: dict,
        amount: Decimal,
    ):
        assert isinstance(amount, Decimal)

        # first create without order_id
        payment = self.create(
            submission=submission,
            plugin_id=plugin_id,
            plugin_options=plugin_options,
            amount=amount,
        )
        # then update with a unique order_id
        while True:
            try:
                with transaction.atomic():
                    payment.order_id = self.get_next_order_id()
                    payment.public_order_id = self.create_public_order_id_for(payment)
                    payment.save(update_fields=("order_id", "public_order_id"))
                    break
            except IntegrityError:
                # race condition on unique order_id
                continue
        return payment

    def get_next_order_id(self) -> int:
        agg = self.aggregate(Max("order_id"))
        max_order_id = agg["order_id__max"] or ORDER_ID_START
        return max_order_id + 1

    @staticmethod
    def create_public_order_id_for(payment: "SubmissionPayment") -> str:
        config = GlobalConfiguration.get_solo()
        prefix = config.payment_order_id_prefix
        prefix = prefix.replace("{year}", str(payment.created.year))
        order_id = str(payment.order_id).rjust(ORDER_ID_PAD_LENGTH, "0")
        return prefix + order_id


class SubmissionPaymentQuerySet(models.QuerySet):
    def sum_amount(self) -> Decimal:
        return self.aggregate(sum_amount=Sum("amount"))["sum_amount"] or Decimal("0")

    def get_completed_public_order_ids(self) -> List[int]:
        return list(
            self.filter(
                status__in=(PaymentStatus.registered, PaymentStatus.completed)
            ).values_list("public_order_id", flat=True)
        )


class SubmissionPayment(models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
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
    order_id = models.BigIntegerField(
        _("Order ID (internal)"),
        unique=True,
        null=True,
        help_text=_("Unique tracking across backend"),
    )
    public_order_id = models.CharField(
        _("Order ID"),
        max_length=32,
        blank=True,
        help_text=_("Order ID stored with payment provider."),
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

    class Meta:
        verbose_name = _("submission payment details")
        verbose_name_plural = _("submission payment details")
        constraints = [
            models.UniqueConstraint(
                name="unique_public_order_id",
                fields=("public_order_id",),
                condition=~models.Q(public_order_id=""),
            )
        ]

    def __str__(self):
        return f"#{self.order_id} '{self.get_status_display()}' {self.amount}"

    @property
    def form(self):
        return self.submission.form
