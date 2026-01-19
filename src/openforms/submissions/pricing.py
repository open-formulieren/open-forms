from __future__ import annotations

import decimal
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

from openforms.logging import logevent
from openforms.typing import JSONValue

if TYPE_CHECKING:
    from .models import Submission

logger = structlog.stdlib.get_logger(__name__)


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
    assert submission.form, (
        "Price cannot be calculated on a submission without the form relation set"
    )
    assert submission.form.product, "Form must have a related product"
    assert submission.form.product.price_options, (
        "get_submission_price' may only be called for forms that require payment"
    )
    with structlog.contextvars.bound_contextvars(
        submission_uuid=str(submission.uuid), action="submissions.get_submission_price"
    ):
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

            logger.warning(
                "price_calculation_variable_error",
                variable=exc.variable,
                value=exc.value,
                exc_info=exc,
            )
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
        logger.debug("fallback_to_product_price")

        def get_price_option_key():
            for step in form.formstep_set.all():
                for component in step.form_definition.configuration["components"]:
                    if component["type"] == "productPrice":
                        return component["key"]
            raise ValueError("Form does not have a productPrice component")

        price_option_key = get_price_option_key()

        data = submission.data
        if not data.get(price_option_key):
            return Decimal("0")

        return form.product.price_options.get(uuid=data[price_option_key]).amount


def _price_from_variable(submission: Submission) -> Decimal | None:
    if not (var_key := submission.form.price_variable_key):
        return None

    values_state = submission.load_submission_value_variables_state()
    data = values_state.get_data(include_unsaved=True)
    if var_key not in data:
        # Discussed with DH - it's better to crash hard than the possibly make them
        # pay the wrong price.
        raise InvalidPrice(
            f"No variable '{var_key}' present in the submission data, refusing the "
            "temptation to guess.",
            variable=var_key,
        )
    value = data[var_key]
    logger.debug("price_taken_from_variable", variable=var_key, value=value)

    invalid_type_error = InvalidPrice(
        f"Got an incompatible value type for the price variable '{var_key}': "
        f"{type(value)}. We require a value that can be cast to a decimal.",
        variable=var_key,
    )
    if not isinstance(value, str | float | int) or isinstance(value, bool):
        raise invalid_type_error
    try:
        return Decimal(value)
    except decimal.InvalidOperation as exc:
        raise invalid_type_error from exc
