from django.conf import settings

from celery import Celery

from .setup import setup_env

setup_env()

app = Celery("open-forms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {
        "url": settings.CELERY_BROKER_URL,
        "default_timeout": 60 * 60,  # one hour
    },
}

app.autodiscover_tasks()
