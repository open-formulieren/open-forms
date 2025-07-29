from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH

from ..config.models import GlobalConfiguration
from .constants import PaymentStatus

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class SubmissionPaymentQuerySet(models.QuerySet["SubmissionPayment"]):
    def mark_registered(self):
        qs = self.filter(status=PaymentStatus.completed)
        return qs.update(status=PaymentStatus.registered)

    def paid(self) -> models.QuerySet[SubmissionPayment]:
        return self.filter(
            status__in=(PaymentStatus.registered, PaymentStatus.completed)
        )

    def get_completed_public_order_ids(self) -> list[str]:
        return list(self.paid().values_list("public_order_id", flat=True))

    def get_completed_provider_payment_ids(self) -> list[str]:
        return list(self.paid().values_list("provider_payment_id", flat=True))


class SubmissionPaymentManager(models.Manager.from_queryset(SubmissionPaymentQuerySet)):
    def create_for(
        self,
        submission: Submission,
        plugin_id: str,
        plugin_options: dict,
        amount: Decimal,
    ) -> SubmissionPayment:
        assert isinstance(amount, Decimal)

        # first create without order_id
        payment = self.create(
            submission=submission,
            plugin_id=plugin_id,
            plugin_options=plugin_options,
            amount=amount,
        )
        # then update with a unique order_id

        with transaction.atomic():
            payment.public_order_id = self.create_public_order_id_for(payment)
            payment.save(update_fields=("public_order_id",))

        return payment

    @staticmethod
    def create_public_order_id_for(
        payment: SubmissionPayment, pk: int | None = None
    ) -> str:
        """Create a public order ID to be sent to the payment provider."""

        # TODO it isn't really clear what the required format/max length is
        # for payment providers. Ogone seems to allow up to 40 characters or so,
        # So this might fail at some point.
        assert payment.submission.public_registration_reference

        config = GlobalConfiguration.get_solo()
        template: str = config.payment_order_id_template

        return (
            template.replace("{year}", str(payment.created.year))
            .replace(
                "{public_reference}", payment.submission.public_registration_reference
            )
            .replace("{uid}", str(pk if pk is not None else payment.pk))
        )

    if TYPE_CHECKING:

        def mark_registered(self) -> int: ...

        def paid(self) -> models.QuerySet[SubmissionPayment]: ...

        def get_completed_provider_payment_ids(self) -> list[str]: ...

        def get_completed_public_order_ids(self) -> list[str]: ...


class SubmissionPayment(models.Model):
    id: int | None
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

    submission = models.ForeignKey(
        "submissions.Submission", related_name="payments", on_delete=models.CASCADE
    )
    plugin_id = models.CharField(_("Payment backend"), max_length=UNIQUE_ID_MAX_LENGTH)
    plugin_options = models.JSONField(
        _("Payment options"),
        blank=True,
        null=True,
        help_text=_("Copy of payment options at time of initializing payment."),
    )
    # TODO Django 5.2 Update to a `GeneratedField`
    public_order_id = models.CharField(
        _("Order ID"),
        max_length=32,
        blank=True,
        help_text=_(
            "The order ID to be sent to the payment provider. This ID is built by "
            "concatenating an optional global prefix, the submission public reference "
            "and a unique incrementing ID."
        ),
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
    provider_payment_id = models.CharField(
        _("provider payment ID"),
        # this is a guess, hopefully payment IDs wont be longer than this, but we might
        # have to switch to `TextField` if this is the case for other providers
        max_length=128,
        blank=True,
        help_text=_("The ID assigned to the payment by the payment provider."),
    )

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        SubmissionPaymentManager
    ] = SubmissionPaymentManager()

    class Meta:
        verbose_name = _("submission payment details")
        verbose_name_plural = _("submission payment details")
        constraints = [
            models.UniqueConstraint(
                name="unique_public_order_id",
                fields=("public_order_id",),
                condition=~models.Q(public_order_id=""),
            ),
            models.UniqueConstraint(
                name="unique_plugin_payment",
                fields=(
                    "plugin_id",
                    "provider_payment_id",
                ),
                condition=~models.Q(provider_payment_id=""),
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.public_order_id} '{self.get_status_display()}' {self.amount}"

    if TYPE_CHECKING:

        def get_status_display(self) -> str: ...

    @property
    def form(self):
        return self.submission.form
