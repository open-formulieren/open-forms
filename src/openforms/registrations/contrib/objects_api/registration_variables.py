from __future__ import annotations

from datetime import datetime

from django.utils.translation import gettext_lazy as _

from openforms.authentication.service import AuthAttribute
from openforms.plugins.registry import BaseRegistry
from openforms.submissions.cosigning import CosignV2Data
from openforms.submissions.models import Submission
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes

from .models import ObjectsAPIRegistrationData, ObjectsAPISubmissionAttachment


class Registry(BaseRegistry[BaseStaticVariable]):
    """
    A registry for the Objects API registration variables.
    """

    module = "objects_api"


register = Registry()
"""The Objects API registration variables registry."""


@register("public_reference")
class PublicReference(BaseStaticVariable):
    name = _("Public reference")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        if submission is None:
            return ""
        return submission.public_registration_reference


@register("pdf_url")
class PdfUrl(BaseStaticVariable):
    name = _("PDF Url")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        _data: ObjectsAPIRegistrationData = (
            submission.objects_api_registration_data  # pyright: ignore[reportAttributeAccessIssue]
        )
        return _data.pdf_url


@register("csv_url")
class CsvUrl(BaseStaticVariable):
    name = _("CSV Url")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None):
        if submission is None:
            return None
        _data: ObjectsAPIRegistrationData = (
            submission.objects_api_registration_data  # pyright: ignore[reportAttributeAccessIssue]
        )
        return _data.csv_url


@register("attachment_urls")
class AttachmentUrls(BaseStaticVariable):
    name = _("Attachment URLs")
    data_type = FormVariableDataTypes.array

    def get_initial_value(self, submission: Submission | None = None) -> list[str]:
        attachments = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment__submission_step__submission=submission
        )
        return list(attachments.values_list("document_url", flat=True))


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

        return submission.payments.get_completed_provider_payment_ids()


@register("cosign_data")
class Cosign(BaseStaticVariable):
    name = _("Co-sign data")
    data_type = FormVariableDataTypes.object

    def get_initial_value(
        self, submission: Submission | None = None
    ) -> CosignV2Data | None:
        if not submission or not (cosign := submission.cosign_state).is_signed:
            return None

        return cosign.signing_details


def get_cosign_value(submission: Submission | None, attribute: AuthAttribute) -> str:
    if not submission or not (cosign := submission.cosign_state).is_signed:
        return ""

    details = cosign.signing_details
    if details["attribute"] == attribute:
        return details["value"]

    return ""


@register("cosign_date")
class CosignDate(BaseStaticVariable):
    name = _("Co-sign date")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(
        self, submission: Submission | None = None
    ) -> datetime | None:
        if not submission or not (cosign := submission.cosign_state).is_signed:
            return None
        cosign_date = cosign.signing_details.get("cosign_date")
        return datetime.fromisoformat(cosign_date) if cosign_date else None


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


PAYMENT_VARIABLE_NAMES = [
    "payment_completed",
    "payment_amount",
    "payment_public_order_ids",
    "provider_payment_ids",
]
