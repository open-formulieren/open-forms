import structlog
from onlinepayments.sdk.factory import DefaultMarshaller
from onlinepayments.sdk.webhooks.secret_key_not_available_exception import (
    SecretKeyNotAvailableException,
)
from onlinepayments.sdk.webhooks.secret_key_store import (
    SecretKeyStore as BaseKeyStore,
)
from onlinepayments.sdk.webhooks.webhooks_helper import WebhooksHelper

from .models import WorldlineWebhookConfiguration

logger = structlog.stdlib.get_logger(__name__)


class SecretKeyStore(BaseKeyStore):
    def get_secret_key(self, key_id: str) -> str:
        configuration = WorldlineWebhookConfiguration.get_solo()

        if not configuration.webhook_key_id == key_id:
            raise SecretKeyNotAvailableException(
                key_id, "No secret key found for given value"
            )

        return configuration.webhook_key_secret


def get_webhook_helper() -> WebhooksHelper:
    key_store = SecretKeyStore()
    return WebhooksHelper(DefaultMarshaller.instance(), key_store)
