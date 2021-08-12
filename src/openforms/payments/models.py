import uuid
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.payments.constants import PaymentStatus
from openforms.utils.fields import StringUUIDField


class SubmissionPaymentManager(models.Manager):
    def create_for(
        self, submission: "Submission", plugin_id: str, amount: Decimal, form_url: str
    ):
        assert isinstance(amount, Decimal)

        # TODO use expression to grab number on database without race-condition
        count = self.filter(submission=submission, plugin_id=plugin_id).count()
        order_id = f"{str(submission.uuid)}-{count}"

        return self.create(
            submission=submission,
            plugin_id=plugin_id,
            amount=amount,
            form_url=form_url,
            order_id=order_id,
        )


class SubmissionQuerySet(models.QuerySet):
    pass


class SubmissionPayment(models.Model):
    uuid = StringUUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

    submission = models.ForeignKey(
        "submissions.Submission", related_name="payments", on_delete=models.CASCADE
    )
    plugin_id = models.CharField(_("Payment backend"), max_length=64)
    form_url = models.URLField(_("Form URL"), max_length=255)
    order_id = models.CharField(
        _("Order ID"), max_length=255, help_text=_("Unique tracking across backend")
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

    objects = SubmissionPaymentManager.from_queryset(SubmissionQuerySet)()

    class Meta:
        unique_together = (("submission", "plugin_id", "order_id"),)

    def __str__(self):
        return f"{self.uuid} {self.amount} '{self.get_status_display()}'"

    @property
    def options(self):
        # TODO we should store a copy of this
        return self.submission.form.payment_backend_options

    @property
    def form(self):
        return self.submission.form
