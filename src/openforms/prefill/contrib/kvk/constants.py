from django.db import models
from django.utils.translation import gettext_lazy as _


class Attributes(models.TextChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://developers.kvk.nl/cms/api/uploads/api_basisprofiel_widget_aa888449ed.yaml
    schema:  Basisprofiel

    Post-processed by hand by commenting out all the array items and deleting all the
    HAL 'links' constructs.
    """

    # NOTE the plugin manipulates the data to finds and attach the 'bezoekadres' and
    # 'correspondentieadres' from 'adressen' list so to make these 'bezoekadres_xx'
    # and 'correspondentieadres_xx' attributes we did some manual copy/paste/replace on the generated attrutes
    bezoekadres_aanduidingBijHuisnummer = (
        "bezoekadres.aanduidingBijHuisnummer",
        _("bezoekadres > aanduidingBijHuisnummer"),
    )
    bezoekadres_geoData_addresseerbaarObjectId = (
        "bezoekadres.geoData.addresseerbaarObjectId",
        _("bezoekadres > geoData > addresseerbaarObjectId"),
    )
    bezoekadres_geoData_gpsLatitude = (
        "bezoekadres.geoData.gpsLatitude",
        _("bezoekadres > geoData > gpsLatitude"),
    )
    bezoekadres_geoData_gpsLongitude = (
        "bezoekadres.geoData.gpsLongitude",
        _("bezoekadres > geoData > gpsLongitude"),
    )
    bezoekadres_geoData_nummerAanduidingId = (
        "bezoekadres.geoData.nummerAanduidingId",
        _("bezoekadres > geoData > nummerAanduidingId"),
    )
    bezoekadres_geoData_rijksdriehoekX = (
        "bezoekadres.geoData.rijksdriehoekX",
        _("bezoekadres > geoData > rijksdriehoekX"),
    )
    bezoekadres_geoData_rijksdriehoekY = (
        "bezoekadres.geoData.rijksdriehoekY",
        _("bezoekadres > geoData > rijksdriehoekY"),
    )
    bezoekadres_geoData_rijksdriehoekZ = (
        "bezoekadres.geoData.rijksdriehoekZ",
        _("bezoekadres > geoData > rijksdriehoekZ"),
    )
    bezoekadres_huisletter = "bezoekadres.huisletter", _("bezoekadres > huisletter")
    bezoekadres_huisnummer = "bezoekadres.huisnummer", _("bezoekadres > huisnummer")
    bezoekadres_huisnummerToevoeging = (
        "bezoekadres.huisnummerToevoeging",
        _("bezoekadres > huisnummerToevoeging"),
    )
    bezoekadres_indAfgeschermd = (
        "bezoekadres.indAfgeschermd",
        _("bezoekadres > indAfgeschermd"),
    )
    bezoekadres_land = ("bezoekadres.land", _("bezoekadres > land"))
    bezoekadres_plaats = ("bezoekadres.plaats", _("bezoekadres > plaats"))
    bezoekadres_postbusnummer = (
        "bezoekadres.postbusnummer",
        _("bezoekadres > postbusnummer"),
    )
    bezoekadres_postcode = "bezoekadres.postcode", _("bezoekadres > postcode")
    bezoekadres_postcodeWoonplaats = (
        "bezoekadres.postcodeWoonplaats",
        _("bezoekadres > postcodeWoonplaats"),
    )
    bezoekadres_regio = ("bezoekadres.regio", _("bezoekadres > regio"))
    bezoekadres_straatHuisnummer = (
        "bezoekadres.straatHuisnummer",
        _("bezoekadres > straatHuisnummer"),
    )
    bezoekadres_straatnaam = "bezoekadres.straatnaam", _("bezoekadres > straatnaam")
    bezoekadres_toevoegingAdres = (
        "bezoekadres.toevoegingAdres",
        _("bezoekadres > toevoegingAdres"),
    )
    bezoekadres_type = ("bezoekadres.type", _("bezoekadres > type"))

    correspondentieadres_aanduidingBijHuisnummer = (
        "correspondentieadres.aanduidingBijHuisnummer",
        _("correspondentieadres > aanduidingBijHuisnummer"),
    )
    correspondentieadres_geoData_addresseerbaarObjectId = (
        "correspondentieadres.geoData.addresseerbaarObjectId",
        _("correspondentieadres > geoData > addresseerbaarObjectId"),
    )
    correspondentieadres_geoData_gpsLatitude = (
        "correspondentieadres.geoData.gpsLatitude",
        _("correspondentieadres > geoData > gpsLatitude"),
    )
    correspondentieadres_geoData_gpsLongitude = (
        "correspondentieadres.geoData.gpsLongitude",
        _("correspondentieadres > geoData > gpsLongitude"),
    )
    correspondentieadres_geoData_nummerAanduidingId = (
        "correspondentieadres.geoData.nummerAanduidingId",
        _("correspondentieadres > geoData > nummerAanduidingId"),
    )
    correspondentieadres_geoData_rijksdriehoekX = (
        "correspondentieadres.geoData.rijksdriehoekX",
        _("correspondentieadres > geoData > rijksdriehoekX"),
    )
    correspondentieadres_geoData_rijksdriehoekY = (
        "correspondentieadres.geoData.rijksdriehoekY",
        _("correspondentieadres > geoData > rijksdriehoekY"),
    )
    correspondentieadres_geoData_rijksdriehoekZ = (
        "correspondentieadres.geoData.rijksdriehoekZ",
        _("correspondentieadres > geoData > rijksdriehoekZ"),
    )
    correspondentieadres_huisletter = (
        "correspondentieadres.huisletter",
        _("correspondentieadres > huisletter"),
    )
    correspondentieadres_huisnummer = (
        "correspondentieadres.huisnummer",
        _("correspondentieadres > huisnummer"),
    )
    correspondentieadres_huisnummerToevoeging = (
        "correspondentieadres.huisnummerToevoeging",
        _("correspondentieadres > huisnummerToevoeging"),
    )
    correspondentieadres_indAfgeschermd = (
        "correspondentieadres.indAfgeschermd",
        _("correspondentieadres > indAfgeschermd"),
    )
    correspondentieadres_land = (
        "correspondentieadres.land",
        _("correspondentieadres > land"),
    )
    correspondentieadres_plaats = (
        "correspondentieadres.plaats",
        _("correspondentieadres > plaats"),
    )
    correspondentieadres_postbusnummer = (
        "correspondentieadres.postbusnummer",
        _("correspondentieadres > postbusnummer"),
    )
    correspondentieadres_postcode = (
        "correspondentieadres.postcode",
        _("correspondentieadres > postcode"),
    )
    correspondentieadres_postcodeWoonplaats = (
        "correspondentieadres.postcodeWoonplaats",
        _("correspondentieadres > postcodeWoonplaats"),
    )
    correspondentieadres_regio = (
        "correspondentieadres.regio",
        _("correspondentieadres > regio"),
    )
    correspondentieadres_straatHuisnummer = (
        "correspondentieadres.straatHuisnummer",
        _("correspondentieadres > straatHuisnummer"),
    )
    correspondentieadres_straatnaam = (
        "correspondentieadres.straatnaam",
        _("correspondentieadres > straatnaam"),
    )
    correspondentieadres_toevoegingAdres = (
        "correspondentieadres.toevoegingAdres",
        _("correspondentieadres > toevoegingAdres"),
    )
    correspondentieadres_type = (
        "correspondentieadres.type",
        _("correspondentieadres > type"),
    )
    eigenaar_rechtsvorm = (
        "_embedded.eigenaar.rechtsvorm",
        _("_embedded > eigenaar > rechtsvorm"),
    )
    eigenaar_rsin = "_embedded.eigenaar.rsin", _("_embedded > eigenaar > rsin")
    eigenaar_uitgebreideRechtsvorm = (
        "_embedded.eigenaar.uitgebreideRechtsvorm",
        _("_embedded > eigenaar > uitgebreideRechtsvorm"),
    )
    formeleRegistratiedatum = "formeleRegistratiedatum", _("formeleRegistratiedatum")
    # handelsnamen_i_naam = (
    #     "handelsnamen[].naam", _("handelsnamen > [] > naam")
    # )
    # handelsnamen_i_volgorde = (
    #     "handelsnamen[].volgorde", _("handelsnamen > [] > volgorde")
    # )
    hoofdvestiging_deeltijdWerkzamePersonen = (
        "_embedded.hoofdvestiging.deeltijdWerkzamePersonen",
        _("_embedded > hoofdvestiging > deeltijdWerkzamePersonen"),
    )
    hoofdvestiging_eersteHandelsnaam = (
        "_embedded.hoofdvestiging.eersteHandelsnaam",
        _("_embedded > hoofdvestiging > eersteHandelsnaam"),
    )
    hoofdvestiging_formeleRegistratiedatum = (
        "_embedded.hoofdvestiging.formeleRegistratiedatum",
        _("_embedded > hoofdvestiging > formeleRegistratiedatum"),
    )
    hoofdvestiging_indCommercieleVestiging = (
        "_embedded.hoofdvestiging.indCommercieleVestiging",
        _("_embedded > hoofdvestiging > indCommercieleVestiging"),
    )
    hoofdvestiging_indHoofdvestiging = (
        "_embedded.hoofdvestiging.indHoofdvestiging",
        _("_embedded > hoofdvestiging > indHoofdvestiging"),
    )
    hoofdvestiging_indNonMailing = (
        "_embedded.hoofdvestiging.indNonMailing",
        _("_embedded > hoofdvestiging > indNonMailing"),
    )
    hoofdvestiging_kvkNummer = (
        "_embedded.hoofdvestiging.kvkNummer",
        _("_embedded > hoofdvestiging > kvkNummer"),
    )
    hoofdvestiging_materieleRegistratie_datumAanvang = (
        "_embedded.hoofdvestiging.materieleRegistratie.datumAanvang",
        _("_embedded > hoofdvestiging > materieleRegistratie > datumAanvang"),
    )
    hoofdvestiging_materieleRegistratie_datumEinde = (
        "_embedded.hoofdvestiging.materieleRegistratie.datumEinde",
        _("_embedded > hoofdvestiging > materieleRegistratie > datumEinde"),
    )
    hoofdvestiging_rsin = (
        "_embedded.hoofdvestiging.rsin",
        _("_embedded > hoofdvestiging > rsin"),
    )
    # hoofdvestiging_sbiActiviteiten_i_indHoofdactiviteit = (
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].indHoofdactiviteit",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > indHoofdactiviteit"),
    # )
    # hoofdvestiging_sbiActiviteiten_i_sbiCode = (
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].sbiCode",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > sbiCode"),
    # )
    # hoofdvestiging_sbiActiviteiten_i_sbiOmschrijving = (
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].sbiOmschrijving",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > sbiOmschrijving"),
    # )
    hoofdvestiging_totaalWerkzamePersonen = (
        "_embedded.hoofdvestiging.totaalWerkzamePersonen",
        _("_embedded > hoofdvestiging > totaalWerkzamePersonen"),
    )
    hoofdvestiging_vestigingsnummer = (
        "_embedded.hoofdvestiging.vestigingsnummer",
        _("_embedded > hoofdvestiging > vestigingsnummer"),
    )
    hoofdvestiging_voltijdWerkzamePersonen = (
        "_embedded.hoofdvestiging.voltijdWerkzamePersonen",
        _("_embedded > hoofdvestiging > voltijdWerkzamePersonen"),
    )
    # hoofdvestiging_websites_i = (
    #     "_embedded.hoofdvestiging.websites[]",
    #     _("_embedded > hoofdvestiging > websites > []"),
    # )
    indNonMailing = ("indNonMailing", _("indNonMailing"))
    kvkNummer = ("kvkNummer", _("kvkNummer"))
    vestigingsnummer = ("vestigingsnummer", _("vestigingsnummer"))
    materieleRegistratie_datumAanvang = (
        "materieleRegistratie.datumAanvang",
        _("materieleRegistratie > datumAanvang"),
    )
    materieleRegistratie_datumEinde = (
        "materieleRegistratie.datumEinde",
        _("materieleRegistratie > datumEinde"),
    )
    naam = ("naam", _("naam"))
    # sbiActiviteiten_i_indHoofdactiviteit = (
    #     "sbiActiviteiten[].indHoofdactiviteit",
    #     _("sbiActiviteiten > [] > indHoofdactiviteit"),
    # )
    # sbiActiviteiten_i_sbiCode = (
    #     "sbiActiviteiten[].sbiCode", _("sbiActiviteiten > [] > sbiCode")
    # )
    # sbiActiviteiten_i_sbiOmschrijving = (
    #     "sbiActiviteiten[].sbiOmschrijving", _("sbiActiviteiten > [] > sbiOmschrijving")
    # )
    statutaireNaam = ("statutaireNaam", _("statutaireNaam"))
    totaalWerkzamePersonen = "totaalWerkzamePersonen", _("totaalWerkzamePersonen")
