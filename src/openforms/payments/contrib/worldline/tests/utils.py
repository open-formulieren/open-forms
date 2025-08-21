import hashlib
import hmac
import json
from base64 import b64encode

from .data import WebhookEventRequest


def generate_webhook_signature(
    secret_key: str, webhook_event_request: WebhookEventRequest
) -> str:
    raw_data = json.dumps(webhook_event_request)
    _hmac = hmac.new(secret_key.encode("utf-8"), raw_data.encode(), hashlib.sha256)
    raw_hmac = _hmac.digest()
    expected_signature = b64encode(raw_hmac)
    return expected_signature.decode("utf-8")
