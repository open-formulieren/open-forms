from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from openforms.authentication.service import AuthAttribute, BaseAuth
from openforms.plugins.registry import BaseRegistry
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class Registry(BaseRegistry[BaseStaticVariable]):
    """
    A registry for the Objects API registration variables.
    """

    module = "objects_api"


register = Registry()
"""The Objects API registration variables registry."""


@register("pdf_url")
class PdfUrl(BaseStaticVariable):
    name = _("PDF Url")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        return submission.objects_api_registration_data.pdf_url


@register("csv_url")
class CsvUrl(BaseStaticVariable):
    name = _("CSV Url")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        return submission.objects_api_registration_data.csv_url


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


@register("cosign_data")
class Cosign(BaseStaticVariable):
    name = _("Co-sign data")
    data_type = FormVariableDataTypes.object

    def get_initial_value(
        self, submission: Submission | None = None
    ) -> BaseAuth | None:
        if not submission or not submission.cosign_complete:
            return None

        return submission.co_sign_data


def get_cosign_value(submission: Submission | None, attribute: AuthAttribute) -> str:
    if not submission or not submission.cosign_complete:
        return ""

    if submission.co_sign_data["attribute"] == attribute:
        return submission.co_sign_data["value"]

    return ""


@register("cosign_date")
class CosignDate(BaseStaticVariable):
    name = _("Co-sign date")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(
        self, submission: Submission | None = None
    ) -> datetime | None:
        if not submission or not submission.cosign_complete:
            return None

        if (cosign_date := submission.co_sign_data.get("cosign_date")) is None:
            # Can be the case on existing submissions, at some point we can switch back to
            # `__getitem__` ([...]).
            return None

        return datetime.fromisoformat(cosign_date)


@register("cosign_bsn")
class CosignBSN(BaseStaticVariable):
    name = _("Co-sign BSN")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_cosign_value(submission, AuthAttribute.bsn)


@register("cosign_kvk")
class CosignKvK(BaseStaticVariable):
    name = _("Co-sign KvK")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_cosign_value(submission, AuthAttribute.kvk)


@register("cosign_pseudo")
class CosignPseudo(BaseStaticVariable):
    name = _("Co-sign pseudo")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return get_cosign_value(submission, AuthAttribute.pseudo)
