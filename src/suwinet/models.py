from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from soap.models import SoapService

from .constants import SERVICES, Service


class SuwinetManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "service",
            "service__client_certificate",
            "service__server_certificate",
        )


class SuwinetConfig(SingletonModel):
    service = models.OneToOneField(
        SoapService,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    bijstandsregelingen_binding_address = models.URLField(
        _("Bijstandsregelingen Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/Bijstandsregelingen/v0500}BijstandsregelingenBinding"
        ),
        blank=True,
    )

    brpdossierpersoongsd_binding_address = models.URLField(
        _("BRPDossierPersoonGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/BRPDossierPersoonGSD/v0200}BRPBinding"
        ),
        blank=True,
    )
    duodossierpersoongsd_binding_address = models.URLField(
        _("DUODossierPersoonGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/DUODossierPersoonGSD/v0300}DUOBinding"
        ),
        blank=True,
    )
    duodossierstudiefinancieringgsd_binding_address = models.URLField(
        _("DUODossierStudiefinancieringGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/DUODossierStudiefinancieringGSD/v0200}DUOBinding"
        ),
        blank=True,
    )
    gsddossierreintegratie_binding_address = models.URLField(
        _("GSDDossierReintegratie Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/GSDDossierReintegratie/v0200}GSDReintegratieBinding"
        ),
        blank=True,
    )
    ibverwijsindex_binding_address = models.URLField(
        _("IBVerwijsindex Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/IBVerwijsindex/v0300}IBVerwijsindexBinding"
        ),
        blank=True,
    )
    kadasterdossiergsd_binding_address = models.URLField(
        _("KadasterDossierGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/KadasterDossierGSD/v0300}KadasterBinding"
        ),
        blank=True,
    )
    rdwdossierdigitalediensten_binding_address = models.URLField(
        _("RDWDossierDigitaleDiensten Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/RDWDossierDigitaleDiensten/v0200}RDWBinding"
        ),
        blank=True,
    )
    rdwdossiergsd_binding_address = models.URLField(
        _("RDWDossierGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/RDWDossierGSD/v0200}RDWBinding"
        ),
        blank=True,
    )
    svbdossierpersoongsd_binding_address = models.URLField(
        _("SVBDossierPersoonGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/SVBDossierPersoonGSD/v0200}SVBBinding"
        ),
        blank=True,
    )
    uwvdossieraanvraaguitkeringstatusgsd_binding_address = models.URLField(
        _("UWVDossierAanvraagUitkeringStatusGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierAanvraagUitkeringStatusGSD/v0200}UWVAanvraagUitkeringStatusBinding"
        ),
        blank=True,
    )
    uwvdossierinkomstengsddigitalediensten_binding_address = models.URLField(
        _("UWVDossierInkomstenGSDDigitaleDiensten Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierInkomstenGSDDigitaleDiensten/v0200}UWVIkvBinding"
        ),
        blank=True,
    )
    uwvdossierinkomstengsd_binding_address = models.URLField(
        _("UWVDossierInkomstenGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierInkomstenGSD/v0200}UWVIkvBinding"
        ),
        blank=True,
    )
    uwvdossierquotumarbeidsbeperktengsd_binding_address = models.URLField(
        _("UWVDossierQuotumArbeidsbeperktenGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierQuotumArbeidsbeperktenGSD/v0300}UWVArbeidsbeperktenBinding"
        ),
        blank=True,
    )
    uwvdossierwerknemersverzekeringengsddigitalediensten_binding_address = models.URLField(
        _("UWVDossierWerknemersverzekeringenGSDDigitaleDiensten Binding Address"),
        db_column="ba_baracus",  # I ain't gettin' in no plane, fool! — postgres
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierWerknemersverzekeringenGSDDigitaleDiensten/v0200}UWVBinding"
        ),
        blank=True,
    )
    uwvdossierwerknemersverzekeringengsd_binding_address = models.URLField(
        _("UWVDossierWerknemersverzekeringenGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierWerknemersverzekeringenGSD/v0200}UWVBinding"
        ),
        blank=True,
    )
    uwvwbdossierpersoongsd_binding_address = models.URLField(
        _("UWVWbDossierPersoonGSD Binding Address"),
        help_text=_(
            "Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVWbDossierPersoonGSD/v0200}UwvWbBinding"
        ),
        blank=True,
    )
    objects = SuwinetManager()

    class Meta:
        verbose_name = _("Suwinet configuration")

    def clean(self):
        super().clean()
        errors = []
        if self.service and self.service.url:
            errors.append(
                _("Using a wsdl to describe all of Suwinet is not implemented.")
            )
        if not any(self.get_binding_address(service) for service in SERVICES.values()):
            errors.append(
                _("Without any binding addresses, no Suwinet service can be used.")
            )
        if errors:
            raise ValidationError(errors)

    def get_binding_address(self, service: Service) -> str:
        return getattr(self, f"{service.name.lower()}_binding_address", "")
