import hashlib
import hmac
from base64 import b64encode


def generate_webhook_signature(secret_key: str, data: bytes) -> str:
    _hmac = hmac.new(secret_key.encode("utf-8"), data, hashlib.sha256)
    raw_hmac = _hmac.digest()
    expected_signature = b64encode(raw_hmac)
    return expected_signature.decode("utf-8")
