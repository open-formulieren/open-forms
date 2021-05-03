from django_yubin.smtp_queue import EmailBackend

from .models import SMTPServerConfig


class CustomYubinEmailBackend(EmailBackend):
    def __init__(self, *args, **kwargs):
        config = SMTPServerConfig.get_solo()
        for key in ["host", "port", "username", "password", "default_from_email"]:
            kwargs[key] = getattr(config, key, kwargs.get(key))

        super().__init__(*args, **kwargs)
