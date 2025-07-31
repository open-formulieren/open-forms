import structlog

from .constants import HostedCheckoutStatus, StatusCategory

logger = structlog.stdlib.get_logger(__name__)


def get_payment_status(worldline_status: str, checkout_status: str = "") -> str:
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
        return ""
    return StatusCategory.to_of_status(status_category)
