import hashlib
import hmac
from base64 import b64encode

import structlog
from onlinepayments.sdk.factory import DefaultMarshaller
from onlinepayments.sdk.webhooks.secret_key_not_available_exception import (
    SecretKeyNotAvailableException,
)
from onlinepayments.sdk.webhooks.secret_key_store import (
    SecretKeyStore as BaseKeyStore,
)
from onlinepayments.sdk.webhooks.webhooks_helper import WebhooksHelper

from .constants import HostedCheckoutStatus, StatusCategory
from .models import WorldlineAccount

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


class SecretKeyStore(BaseKeyStore):
    def get_secret_key(self, key_id: str) -> str:
        try:
            account = WorldlineAccount.objects.get(webhook_key_id=key_id)
        except WorldlineAccount.DoesNotExist as e:
            raise SecretKeyNotAvailableException(key_id) from e

        return account.webhook_key_secret


def get_webhook_helper() -> WebhooksHelper:
    key_store = SecretKeyStore()
    return WebhooksHelper(DefaultMarshaller.instance(), key_store)


def generate_webhook_signature(secret_key: str, data: bytes) -> str:
    _hmac = hmac.new(secret_key.encode("utf-8"), data, hashlib.sha256)
    raw_hmac = _hmac.digest()
    expected_signature = b64encode(raw_hmac)
    return expected_signature.decode("utf-8")
