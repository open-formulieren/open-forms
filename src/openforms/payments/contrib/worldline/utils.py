import hashlib
import hmac
from base64 import b64encode

import structlog
from onlinepayments.sdk.domain.payment_response import PaymentResponse
from onlinepayments.sdk.factory import DefaultMarshaller
from onlinepayments.sdk.webhooks.secret_key_not_available_exception import (
    SecretKeyNotAvailableException,
)
from onlinepayments.sdk.webhooks.secret_key_store import (
    SecretKeyStore as BaseKeyStore,
)
from onlinepayments.sdk.webhooks.webhooks_helper import WebhooksHelper

from .models import WorldlineWebhookEntry

logger = structlog.stdlib.get_logger(__name__)


class SecretKeyStore(BaseKeyStore):
    def get_secret_key(self, key_id: str) -> str:
        try:
            entry = WorldlineWebhookEntry.objects.get(webhook_key_id=key_id)
        except WorldlineWebhookEntry.DoesNotExist as e:
            raise SecretKeyNotAvailableException(
                key_id, "No secret key found for given value"
            ) from e

        return entry.webhook_key_secret


def get_webhook_helper() -> WebhooksHelper:
    key_store = SecretKeyStore()
    return WebhooksHelper(DefaultMarshaller.instance(), key_store)


def generate_webhook_signature(secret_key: str, data: bytes) -> str:
    _hmac = hmac.new(secret_key.encode("utf-8"), data, hashlib.sha256)
    raw_hmac = _hmac.digest()
    expected_signature = b64encode(raw_hmac)
    return expected_signature.decode("utf-8")


def get_merchant_reference(payment_response: PaymentResponse) -> str:
    merchant_reference = (
        payment_response.payment_output.references.merchant_reference
        if payment_response.payment_output
        and payment_response.payment_output.references
        else None
    )

    assert merchant_reference, "Merchant reference not found"
    return merchant_reference
