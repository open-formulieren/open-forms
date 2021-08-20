from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

import requests
from djchoices.choices import ChoiceItem, DjangoChoices

from .compat import jwt_encode

JWT_ALG = "HS256"


class AuthTypes(DjangoChoices):
    no_auth = ChoiceItem("no_auth", _("No authentication"))
    basic_auth = ChoiceItem("basic_auth", _("Basic authentication"))
    api_key = ChoiceItem("api_key", _("API key"))
    jwt = ChoiceItem("jwt", _("JWT"))
    custom_header = ChoiceItem("custom_header", _("Custom header"))


class RestAPI(models.Model):
    """
    Basic API configuration.
    """

    label = models.CharField(_("label"), max_length=100)
    api_root = models.CharField(_("api root url"), max_length=255, unique=True)

    # credentials for the API
    auth_type = models.CharField(
        _("authorization type"),
        max_length=20,
        choices=AuthTypes.choices,
        default=AuthTypes.no_auth,
    )

    basic_auth_username = models.CharField(_("username"), max_length=255, blank=True)
    basic_auth_password = models.CharField(_("password"), max_length=255, blank=True)

    api_key = models.CharField(_("API key"), max_length=255, blank=True)

    jwt_payload = JSONField(_("payload"), blank=True, default=dict)
    jwt_secret = models.CharField(_("secret"), max_length=255, blank=True)

    custom_header_key = models.CharField(_("header key"), max_length=100, blank=True)
    custom_header_value = models.CharField(
        _("header value"), max_length=255, blank=True
    )

    class Meta:
        verbose_name = _("Rest API")
        verbose_name_plural = _("Rest APIs")

    def __str__(self):
        return f"[{self.get_api_type_display()}] {self.label}"

    def save(self, *args, **kwargs):
        if not self.api_root.endswith("/"):
            self.api_root = f"{self.api_root}/"

        super().save(*args, **kwargs)

    def build_client(self, **claims):
        """
        Build an API client from the service configuration.
        """
        session = requests.Session()
        session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if self.auth_type == AuthTypes.api_key:
            session.headers.update({"Authorization": f"Token {self.api_key}"})
        elif self.auth_type == AuthTypes.basic_auth:
            session.auth = (self.basic_auth_username, self.basic_auth_password)
        elif self.auth_type == AuthTypes.jwt:
            encoded = jwt_encode(self.jwt_payload, self.jwt_secret, algorithm=JWT_ALG)
            session.headers.update({"Authorization": f"Bearer {encoded}"})
        elif self.auth_type == AuthTypes.custom_header:
            session.headers.update({self.custom_header_key: self.custom_header_value})

        return session
