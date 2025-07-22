from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from onlinepayments.sdk.client import IMerchantClient
from onlinepayments.sdk.communicator_configuration import CommunicatorConfiguration
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.merchant_client import IHostedCheckoutClient

from .constants import WorldlineEndpoints


class WorldlineMerchant(models.Model):
    label = models.CharField(
        _("Label"),
        max_length=255,
        help_text=_("Human readable label"),
    )
    pspid = models.CharField(
        _("PSPID"), max_length=255, help_text=_("Worldline PSPID"), unique=True
    )

    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        help_text=_("API Key created for the specified PSPID"),
    )
    api_secret = models.CharField(
        _("API Secret"),
        max_length=255,
        help_text=_("API Secret created for the specified PSPID"),
    )

    endpoint = models.URLField(
        _("Preset endpoint"),
        choices=WorldlineEndpoints.choices,
        default=WorldlineEndpoints.test,
        help_text=_("Select a common preset endpoint"),
    )

    def __str__(self):
        return self.label

    def get_merchant_client(self) -> IMerchantClient:
        configuration = CommunicatorConfiguration(
            api_endpoint=self.endpoint,
            api_key_id=self.api_key,
            secret_api_key=self.api_secret,
            authorization_type="v1HMAC",
            integrator="openforms",  #  TODO: is this the correct value?
            connect_timeout=settings.DEFAULT_TIMEOUT_REQUESTS,
            socket_timeout=settings.DEFAULT_TIMEOUT_REQUESTS * 2,
            max_connections=10,
        )

        communicator = Factory.create_communicator_from_configuration(configuration)
        client = Factory.create_client_from_communicator(communicator)
        return client.merchant(self.pspid)

    def get_checkout_client(self) -> IHostedCheckoutClient:
        merchant_client = self.get_merchant_client()
        return merchant_client.hosted_checkout()
