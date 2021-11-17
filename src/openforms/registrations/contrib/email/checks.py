from django.conf import settings
from django.core.mail import get_connection
from django.utils.translation import gettext_lazy as _

from django_yubin import settings as yubin_settings

from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_config():
    if settings.EMAIL_BACKEND == "django_yubin.smtp_queue.EmailBackend":
        backend = yubin_settings.USE_BACKEND
    else:
        backend = settings.EMAIL_BACKEND

    try:
        connection = get_connection(backend, fail_silently=False)
        result = connection.open()
        if result:
            connection.close()
    except Exception as e:
        raise InvalidPluginConfiguration(
            _("Could not connect to mail service: {exception}").format(exception=e)
        )
