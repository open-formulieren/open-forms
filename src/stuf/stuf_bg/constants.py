from django.db import models
from django.utils.translation import gettext_lazy as _

# Namespacing in the XML we want to remove
# Note:  This could cause a collision if two of the same elements
#   are present in different namespaces
NAMESPACE_REPLACEMENTS = {
    "http://www.w3.org/2003/05/soap-envelope": None,  # SOAP 1.2
    "http://schemas.xmlsoap.org/soap/envelope/": None,  # SOAP 1.1
    "http://www.egem.nl/StUF/sector/bg/0310": None,
    "http://www.egem.nl/StUF/StUF0301": None,
    "http://www.w3.org/1999/xlink": None,
    "http://www.opengis.net/gml": None,
}

# StUF-BG requires some expiry time to be given so we just give it 5 minutes.
STUF_BG_EXPIRY_MINUTES = 5


class FieldChoices(models.TextChoices):
    bsn = "bsn", _("BSN")

    voornamen = "voornamen", _("First name")
    voorletters = "voorletters", _("Initials")
    geslachtsnaam = "geslachtsnaam", _("Last name")
    voorvoegselGeslachtsnaam = "voorvoegselGeslachtsnaam", _("Last name prefix")

    straatnaam = "straatnaam", _("Street Name")
    huisnummer = "huisnummer", _("House number")
    huisletter = "huisletter", _("House letter")
    huisnummertoevoeging = "huisnummertoevoeging", _("House number addition")
    postcode = "postcode", _("Postal code")
    woonplaatsNaam = "woonplaatsNaam", _("Residence name")
    gemeenteVanInschrijving = "gemeenteVanInschrijving", _(
        "Municipality where registered"
    )

    landAdresBuitenland = "landAdresBuitenland", _("Foreign address country")
    adresBuitenland1 = "adresBuitenland1", _("Foreign address line 1")
    adresBuitenland2 = "adresBuitenland2", _("Foreign address line 2")
    adresBuitenland3 = "adresBuitenland3", _("Foreign address line 3")

    geboorteplaats = "geboorteplaats", _("Place of birth")
    geboortedatum = "geboortedatum", _("Date of birth")
    geboorteland = "geboorteland", _("Country of birth")
    geslachtsaanduiding = "geslachtsaanduiding", _("Gender indication")

    overlijdensdatum = "overlijdensdatum", _("Date of death")
