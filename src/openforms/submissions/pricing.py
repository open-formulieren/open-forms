import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from json_logic import jsonLogic

if TYPE_CHECKING:
    from .models import Submission


logger = logging.getLogger(__name__)


def get_submission_price(submission: "Submission") -> Optional[Decimal]:
    """
    Calculate the price for a given submission.

    If payment is required, the price logic rules are evaluated if present. If no
    pricing logic rules exist or there is no match, the linked product price is
    returned.

    :param submission: the :class:`openforms.submissions.models.Submission: instance
      to calculate the price for.
    :return: the calculated price, or ``None`` if no payment is required.
    """
    logger.debug("Calculating submission %s price", submission.uuid)
    if not submission.payment_required:
        logger.debug(
            "Submission %s does not require payment, skipping price calculation",
            submission.uuid,
        )
        return None

    assert (
        submission.form
    ), "Price cannot be calculated on a submission without the form relation set"
    assert submission.form.product, "Form must have a related product"

    form = submission.form
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

    # no price rules or no match found -> use linked product
    logger.debug(
        "Falling back to product price for submission %s after trying %d price rules",
        submission.uuid,
        len(price_rules),
    )
    return form.product.price
