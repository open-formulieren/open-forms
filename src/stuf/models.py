from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import EndpointType


class StufServiceManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "soap_service",
            "soap_service__client_certificate",
            "soap_service__server_certificate",
        )


class StufService(models.Model):

    soap_service = models.OneToOneField(
        "soap.SoapService",
        on_delete=models.CASCADE,
        related_name="stuf_service",
        help_text=_("The soap service this stuf service uses"),
    )

    ontvanger_organisatie = models.CharField(
        _("receiving organisation"),
        help_text=_("Field 'ontvanger organisatie' in StUF"),
        max_length=200,
        blank=True,
    )
    ontvanger_applicatie = models.CharField(
        _("receiving application"),
        help_text=_("Field 'ontvanger applicatie' in StUF"),
        max_length=200,
    )
    ontvanger_administratie = models.CharField(
        _("receiving administration"),
        help_text=_("Field 'ontvanger administratie' in StUF"),
        max_length=200,
        blank=True,
    )
    ontvanger_gebruiker = models.CharField(
        _("receiving user"),
        help_text=_("Field 'ontvanger gebruiker' in StUF"),
        max_length=200,
        blank=True,
    )

    zender_organisatie = models.CharField(
        _("sending organisation"),
        help_text=_("Field 'zender organisatie' in StUF"),
        max_length=200,
        blank=True,
    )
    zender_applicatie = models.CharField(
        _("sending application"),
        help_text=_("Field 'zender applicatie' in StUF"),
        max_length=200,
    )
    zender_administratie = models.CharField(
        _("sending administration"),
        help_text=_("Field 'zender administratie' in StUF"),
        max_length=200,
        blank=True,
    )
    zender_gebruiker = models.CharField(
        _("sending user"),
        help_text=_("Field 'zender gebruiker' in StUF"),
        max_length=200,
        blank=True,
    )

    endpoint_beantwoord_vraag = models.URLField(
        _("endpoint BeantwoordVraag"),
        blank=True,
        help_text=_(
            "Endpoint for synchronous request messages, usually '[...]/BeantwoordVraag'"
        ),
    )
    endpoint_vrije_berichten = models.URLField(
        _("endpoint VrijeBerichten"),
        blank=True,
        help_text=_(
            "Endpoint for synchronous free messages, usually '[...]/VerwerkSynchroonVrijBericht' or '[...]/VrijeBerichten'."
        ),
    )
    endpoint_ontvang_asynchroon = models.URLField(
        _("endpoint OntvangAsynchroon"),
        blank=True,
        help_text=_(
            "Endpoint for asynchronous messages, usually '[...]/OntvangAsynchroon'."
        ),
    )

    objects = StufServiceManager()

    class Meta:
        verbose_name = _("StUF service")
        verbose_name_plural = _("StUF services")

    def __str__(self):
        return self.soap_service.label

    def get_endpoint(self, type: EndpointType) -> str:
        attr = f"endpoint_{type}"
        value = getattr(self, attr, None)
        if value is None:
            raise ValueError(f"Endpoint type {type} does not exist.")
        return value or self.soap_service.url

    def get_cert(self) -> None | str | tuple[str, str]:
        return self.soap_service.get_cert()

    def get_verify(self) -> bool | str:
        return self.soap_service.get_verify()

    def get_auth(self) -> tuple[str, str] | None:
        return self.soap_service.get_auth()

    def get_timeout(self) -> int:
        return self.soap_service.timeout
