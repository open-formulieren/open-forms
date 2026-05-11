from django.db import models
from django.utils.translation import gettext_lazy as _


class AttributesV2(models.TextChoices):
    burgerservicenummer = "burgerservicenummer", _("Burgerservicenummer")
    naam_geslachtsnaam = "naam.geslachtsnaam", _("Naam > Geslachtsnaam")
    naam_volledigenaam = "naam.volledigeNaam", _("Naam > Volledigenaam")
    naam_voorletters = "naam.voorletters", _("Naam > Voorletters")
    naam_voornamen = "naam.voornamen", _("Naam > Voornamen")
    naam_voorvoegsel = "naam.voorvoegsel", _("Naam > Voorvoegsel")
    verblijfplaats_verblijfadres_huisletter = (
        "verblijfplaats.verblijfadres.huisletter",
        _("Verblijfplaats > Verblijf Adres > Huisletter"),
    )
    verblijfplaats_verblijfadres_huisnummer = (
        "verblijfplaats.verblijfadres.huisnummer",
        _("Verblijfplaats > Verblijf Adres > Huisnummer"),
    )
    verblijfplaats_verblijfadres_huisnummertoevoeging = (
        "verblijfplaats.verblijfadres.huisnummertoevoeging",
        _("Verblijfplaats > Verblijf Adres > Huisnummertoevoeging"),
    )
    verblijfplaats_verblijfadres_kortestraatnaam = (
        "verblijfplaats.verblijfadres.korteStraatnaam",
        _("Verblijfplaats > Verblijf Adres > Kortestraatnaam"),
    )
    verblijfplaats_verblijfadres_officielestraatnaam = (
        "verblijfplaats.verblijfadres.officieleStraatnaam",
        _("Verblijfplaats > Verblijf Adres > Officiele Straatnaam"),
    )
    verblijfplaats_verblijfadres_postcode = (
        "verblijfplaats.verblijfadres.postcode",
        _("Verblijfplaats > Verblijf Adres > Postcode"),
    )
    verblijfplaats_verblijfadres_woonplaats = (
        "verblijfplaats.verblijfadres.woonplaats",
        _("Verblijfplaats > Verblijf Adres > Woonplaats"),
    )
    gemeentevaninschrijving_code = (
        "gemeenteVanInschrijving.code",
        _("Gemeentevaninschrijving > Code"),
    )
    gemeentevaninschrijving_omschrijving = (
        "gemeenteVanInschrijving.omschrijving",
        _("Gemeentevaninschrijving > Omschrijving"),
    )
    adressering_adresregel1 = (
        "adressering.adresregel1",
        _("Adressering > Adres Regel 1"),
    )
    adressering_adresregel2 = (
        "adressering.adresregel2",
        _("Adressering > Adres Regel 2"),
    )
    adressering_adresregel3 = (
        "adressering.adresregel3",
        _("Adressering > Adres Regel 3"),
    )
    adressering_land = "adressering.land", _("Adressering > Land")
    geboorte_land = "geboorte.land", _("Geboorte > Land")
    geboorte_land_code = "geboorte.land.code", _("Geboorte > Land > Code")
    geboorte_land_omschrijving = (
        "geboorte.land.omschrijving",
        _("Geboorte > Land > Omschrijving"),
    )
    geboorte_plaats = "geboorte.plaats", _("Geboorte > Plaats")
    geboorte_plaats_code = "geboorte.plaats.code", _("Geboorte > Plaats > Code")
    geboorte_plaats_omschrijving = (
        "geboorte.plaats.omschrijving",
        _("Geboorte > Plaats > Omschrijving"),
    )
    geboorte_datum_langformaat = (
        "geboorte.datum.langFormaat",
        _("Geboorte > Datum > Lang Formaat"),
    )
    geboorte_datum_type = "geboorte.datum.type", _("Geboorte > Datum > Type")
    geboorte_datum_datum = "geboorte.datum.datum", _("Geboorte > Datum > Datum")
    geboorte_datum_onbekend = (
        "geboorte.datum.onbekend",
        _("Geboorte > Datum > Onbekend"),
    )
    geboorte_datum_jaar = "geboorte.datum.jaar", _("Geboorte > Datum > Jaar")
    geboorte_datum_maand = "geboorte.datum.maand", _("Geboorte > Datum > Maand")
    geslacht_code = "geslacht.code", _("Geslacht > Code")
    geslacht_omschrijving = "geslacht.omschrijving", _("Geslacht > Omschrijving")
    overlijden_datum_langformaat = (
        "overlijden.datum.langFormaat",
        _("Overlijden > Datum > Lang Formaat"),
    )
    overlijden_datum_type = "overlijden.datum.type", _("Overlijden > Datum > Type")
    overlijden_datum_datum = "overlijden.datum.datum", _("Overlijden > Datum > Datum")
    overlijden_datum_onbekend = (
        "overlijden.datum.onbekend",
        _("Overlijden > Datum > Onbekend"),
    )
    overlijden_datum_jaar = "overlijden.datum.jaar", _("Overlijden > Datum > Jaar")
    overlijden_datum_maand = "overlijden.datum.maand", _("Overlijden > Datum > Maand")
