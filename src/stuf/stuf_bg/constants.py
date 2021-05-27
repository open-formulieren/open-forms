from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

# Namespacing in the XML we want to remove
# Note:  This could cause a collision if two of the same elements
#   are present in different namespaces
NAMESPACE_REPLACEMENTS = {
    "http://schemas.xmlsoap.org/soap/envelope/": None,
    "http://www.egem.nl/StUF/sector/bg/0310": None,
    "http://www.egem.nl/StUF/StUF0301": None,
    "http://www.w3.org/1999/xlink": None,
    "http://www.opengis.net/gml": None,
}

# StUF-BG requires some expiry time to be given so we just give it 5 minutes.
STUF_BG_EXPIRY_MINUTES = 5


class Attributes(DjangoChoices):
    bsn = ChoiceItem("bsn", _("BSN"))
    voornamen = ChoiceItem("voornamen", _("Voornamen"))
    geslachtsnaam = ChoiceItem("geslachtsnaam", _("Geslachtsnaam"))
    straatnaam = ChoiceItem("straatnaam", _("Straatnaam"))
    huisnummer = ChoiceItem("huisnummer", _("Huisnummer"))
    huisletter = ChoiceItem("huisletter", _("Huisletter"))
    huisnummertoevoeging = ChoiceItem(
        "huisnummertoevoeging", _("Huisnummer Toevoeging")
    )
    postcode = ChoiceItem("postcode", _("Postcode"))
    woonplaatsNaam = ChoiceItem("woonplaatsNaam", _("Woonplaats Naam"))


attributes_to_stuf_bg_mapping = {
    "bsn": "inp.bsn",
    "voornaam": "voornaam",
    "geslachtsnaam": "geslachtsnaam",
    "straatnaam": "gor.straatnaam",
    "huisnummer": "aoa.huisnummer",
    "huisletter": "aoa.huisletter",
    "huisnummertoevoeging": "aoa.huisnummertoevoeging",
    "postcode": "aoa.postcode",
    "woonplaatsNaam": "wpl.woonplaatsNaam",
}
