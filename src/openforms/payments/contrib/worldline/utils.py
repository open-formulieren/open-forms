import structlog

from .constants import HostedCheckoutStatus, StatusCategory

logger = structlog.stdlib.get_logger(__name__)


def get_payment_status(worldline_status: str, checkout_status: str = "") -> str:
    # The worldline_status here represents the status of the payment. It could be
    # possible that no payment was created yet for a given checkout and we therefore
    # receive an empty string value here. In order to do have an indication what
    # the payment status is we can derive it from the checkout_status. See the
    # worldline documentation for more information about statuses.
    # https://apireference.connect.worldline-solutions.com/s2sapi/v1/en_US/java/statuses.html?paymentPlatform=ALL
    if not worldline_status and checkout_status:
        return HostedCheckoutStatus.to_of_status(checkout_status)

    try:
        status_category = StatusCategory.from_payment_status(worldline_status)
    except KeyError as exc:
        logger.exception(
            "unknown_payment_status_encountered",
            exc_info=exc,
            status=worldline_status,
            checkout_status=checkout_status,
        )
        raise
    return StatusCategory.to_of_status(status_category)
