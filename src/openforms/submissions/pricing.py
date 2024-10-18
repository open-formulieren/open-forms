from __future__ import annotations

import decimal
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from json_logic import jsonLogic

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
    # 2. Check if there are any logic rules defined that match.
    #
    data = submission.data
    # test the rules one by one, if relevant
    price_rules = form.formpricelogic_set.all()
    for rule in price_rules:
        # logic does not match, no point in bothering
        if not jsonLogic(rule.json_logic_trigger, data):
            continue
        logger.debug(
            "Price for submission %s calculated using logic trigger %d: %r",
            submission.uuid,
            rule.id,
            rule.json_logic_trigger,
        )
        # first logic match wins
        # TODO: validate on API/backend/frontend that logic triggers must be unique for
        # a form
        return rule.price

    #
    # 3. More specific modes didn't produce anything, fall back to the linked product
    #    price.
    #
    logger.debug(
        "Falling back to product price for submission %s after trying %d price rules.",
        submission.uuid,
        len(price_rules),
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
