from __future__ import annotations

import decimal
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from openforms.logging import logevent
from openforms.typing import JSONValue

if TYPE_CHECKING:
    from .models import Submission


logger = logging.getLogger(__name__)


class InvalidPrice(Exception):
    def __init__(
        self, message: str, variable: str, value: JSONValue = None, *args, **kwargs
    ):
        self.message = message
        self.variable = variable
        self.value = value
        super().__init__(message, *args, **kwargs)


def get_submission_price(submission: Submission) -> Decimal:
    """
    Calculate the price for a given submission.

    If payment is required, the price logic rules are evaluated if present. If no
    pricing logic rules exist or there is no match, the linked product price is
    returned.

    :param submission: the :class:`openforms.submissions.models.Submission: instance
      to calculate the price for.
    :return: the calculated price.
    """
    assert (
        submission.form
    ), "Price cannot be calculated on a submission without the form relation set"
    assert submission.form.product, "Form must have a related product"
    assert (
        submission.form.product.price
    ), "get_submission_price' may only be called for forms that require payment"

    form = submission.form

    #
    # 1. If a variable key is configured, try that.
    #
    try:
        price = _price_from_variable(submission)
    except InvalidPrice as exc:
        # Dirty, dirty hack - don't create new log records when viewing this in the
        # admin.
        if getattr(submission, "_in_admin_display", False):  # pragma: no cover
            raise
        logevent.price_calculation_variable_error(
            submission=submission,
            variable=exc.variable,
            error=exc,
            value=exc.value,
        )
        raise
    else:
        if price is not None:
            return price

    #
    # 2. No price stored in a variable, fall back to the linked product price.
    #
    assert price is None
    logger.debug(
        "Falling back to product price for submission %s, there is no price variable.",
        submission.uuid,
    )
    return form.product.price


def _price_from_variable(submission: Submission) -> Decimal | None:
    if not (var_key := submission.form.price_variable_key):
        return None

    values_state = submission.load_submission_value_variables_state()
    # user defined variables don't show up in `values_state.get_data()` :( so we
    # need to access them differently.
    # XXX these data structures can be cleaned up - Victorien did an attempt already
    # and it revealed it's not easy.
    if var_key not in values_state.variables:
        # Discussed with DH - it's better to crash hard than the possibly make them
        # pay the wrong price.
        raise InvalidPrice(
            f"No variable '{var_key}' present in the submission data, refusing the "
            "temptation to guess.",
            variable=var_key,
        )
    value = values_state.get_variable(var_key).value
    logger.debug(
        "Price for submission %s obtained from variable with key '%s'. Value: %r",
        submission.uuid,
        var_key,
        value,
    )

    invalid_type_error = InvalidPrice(
        f"Got an incompatible value type for the price variable '{var_key}': "
        f"{type(value)}. We require a value that can be cast to a decimal.",
        variable=var_key,
    )
    if not isinstance(value, (str, float, int)) or isinstance(value, bool):
        raise invalid_type_error
    try:
        return Decimal(value)
    except decimal.InvalidOperation as exc:
        raise invalid_type_error from exc
