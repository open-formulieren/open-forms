"""
Helpers for the template based Objects API registration handler.
"""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypedDict

from django.conf import settings

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.formio.service import FormioData
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.models import Submission
from openforms.typing import JSONObject, VariableValue
from openforms.variables.service import get_static_variables

from ..registration_variables import get_cosign_value
from ..utils import recursively_escape_html_strings


class PaymentContextData(TypedDict):
    completed: bool
    amount: str  # stringified decimal with a decimal precision of 2 digits
    public_order_ids: Sequence[str]
    provider_payment_ids: Sequence[str]


def get_payment_context_data(submission: Submission) -> PaymentContextData:
    price = submission.price
    amount = Decimal(price).quantize(Decimal("0.01")) if price is not None else 0
    return {
        "completed": submission.payment_user_has_paid,
        "amount": str(amount),
        "public_order_ids": submission.payments.get_completed_public_order_ids(),
        "provider_payment_ids": submission.payments.get_completed_provider_payment_ids(),
    }


class CosignContextData(TypedDict):
    bsn: str
    kvk: str
    pseudo: str
    date: datetime | Literal[""]


def get_cosign_context_data(submission: Submission) -> CosignContextData | None:
    if not (cosign := submission.cosign_state).is_signed:
        return None

    cosign_date = cosign.signing_details.get("cosign_date")
    return {
        "bsn": get_cosign_value(submission, AuthAttribute.bsn),
        "kvk": get_cosign_value(submission, AuthAttribute.kvk),
        "pseudo": get_cosign_value(submission, AuthAttribute.pseudo),
        "date": datetime.fromisoformat(cosign_date) if cosign_date else "",
    }


class SubmissionContext(TypedDict):
    """
    `submission` context variable shape.
    """

    public_reference: str
    kenmerk: str
    language_code: str
    uploaded_attachment_urls: Sequence[str]
    pdf_url: str
    csv_url: str


class JSONTemplateContext(TypedDict):
    _submission: Submission
    productaanvraag_type: str
    payment: PaymentContextData
    cosign_data: CosignContextData | None
    variables: dict[str, VariableValue]
    submission: SubmissionContext


def _get_variables_for_context(submission: Submission) -> dict[str, VariableValue]:
    """
    Return the key/value pairs of data in the state (static, user-defined, and component
    variables). If specified in the settings, strings will be escaped for HTML.

    Note that this is a custom override of ``variables.utils.get_variables_for_context``
    that returns JSON values instead (for the submission data). The static variables
    are still date-related objects.
    """
    state = submission.load_submission_value_variables_state()

    data = FormioData()
    # Loop over the saved variables here to mimic the exact behaviour of the original
    # ``get_variables_for_context``
    for variable in state.saved_variables.values():
        if variable.source != SubmissionValueVariableSources.sensitive_data_cleaner:
            data[variable.key] = variable.to_json()
    data.update(
        {
            variable.key: variable.initial_value
            for variable in get_static_variables(submission=submission)
        }
    )

    data = data.data
    if settings.ESCAPE_REGISTRATION_OUTPUT:
        data = recursively_escape_html_strings(data)

    return data


def render_template(
    *,
    submission: Submission,
    template: str,
    product_request_type: str,
    uploaded_attachment_urls: Sequence[str],
    pdf_url: str,
    csv_url: str,
) -> JSONObject:
    context: JSONTemplateContext = {
        "_submission": submission,
        "productaanvraag_type": product_request_type,
        "payment": get_payment_context_data(submission),
        "cosign_data": get_cosign_context_data(submission),
        "variables": _get_variables_for_context(submission),
        # Github issue #661, nested for namespacing note: other templates and context expose all submission
        # variables in the top level namespace, but that is due for refactor
        "submission": {
            "public_reference": submission.public_registration_reference,
            "kenmerk": str(submission.uuid),
            "language_code": submission.language_code,
            "uploaded_attachment_urls": uploaded_attachment_urls,
            "pdf_url": pdf_url,
            "csv_url": csv_url,
        },
    }

    result = render_to_json(template, context)
    # the template must produce a top-level object, primitives are not valid
    assert isinstance(result, dict)
    return result
