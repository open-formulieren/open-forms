import os

from sentry_sdk.integrations import DidNotEnable, django, redis

try:
    from sentry_sdk.integrations import celery
except DidNotEnable:  # no celery in this proejct
    celery = None


SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_SDK_INTEGRATIONS = [
    django.DjangoIntegration(),
    redis.RedisIntegration(),
]


if celery is not None:
    SENTRY_SDK_INTEGRATIONS.append(celery.CeleryIntegration())

if SENTRY_DSN:
    import sentry_sdk

    SENTRY_CONFIG = {
        "dsn": SENTRY_DSN,
        "release": os.getenv("VERSION_TAG", "VERSION_TAG not set"),
    }

    sentry_sdk.init(
        **SENTRY_CONFIG, integrations=SENTRY_SDK_INTEGRATIONS, send_default_pii=True
    )
