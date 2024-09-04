from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from openforms.payments.constants import PaymentStatus
from openforms.plugins.registry import BaseRegistry
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class Registry(BaseRegistry[BaseStaticVariable]):
    """
    A registry for the StUF-ZDS (payments) registration variables.
    """

    module = "stuf_zds_payments"


register = Registry()
"""The StUF-ZDS (payments) registration variables registry."""


@register("payment_completed")
class PaymentCompleted(BaseStaticVariable):
    name = _("Payment completed")
    data_type = FormVariableDataTypes.boolean

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        return submission.payment_user_has_paid


@register("payment_amount")
class PaymentAmount(BaseStaticVariable):
    name = _("Payment amount")
    data_type = FormVariableDataTypes.float

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        if submission.price is None:
            return None
        return float(submission.price)


@register("payment_public_order_ids")
class PaymentPublicOrderIds(BaseStaticVariable):
    name = _("Payment public order IDs")
    data_type = FormVariableDataTypes.array

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        return submission.payments.get_completed_public_order_ids()


@register("provider_payment_ids")
class ProviderPaymentIds(BaseStaticVariable):
    name = _("Provider payment IDs")
    data_type = FormVariableDataTypes.array

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None

        return list(
            submission.payments.filter(
                status__in=(PaymentStatus.registered, PaymentStatus.completed)
            ).values_list("provider_payment_id", flat=True)
        )
