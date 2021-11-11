from django.db import models
from django.utils.translation import gettext_lazy as _


class MSGraphService(models.Model):
    """
    steps to get credentials: https://github.com/Azure-Samples/ms-identity-python-daemon/tree/master/1-Call-MsGraph-WithSecret
    """

    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_("Human readable label to identify services"),
    )
    tenant_id = models.CharField(
        _("tenant ID"),
        max_length=64,
        help_text=_("Tenant ID"),
    )
    client_id = models.CharField(
        _("client ID"),
        max_length=64,
        help_text=_("Client ID (sometimes called App ID or Application ID"),
    )
    secret = models.CharField(
        _("secret"),
        max_length=64,
        help_text=_("Secret for this Client ID"),
    )

    class Meta:
        verbose_name = _("Microsoft Graph Service")

    def __str__(self):
        return self.label
