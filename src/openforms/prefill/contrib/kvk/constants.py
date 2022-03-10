from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://developers.kvk.nl/cms/api/uploads/api_basisprofiel_widget_aa888449ed.yaml
    schema:  Basisprofiel
    command: manage.py generate_prefill_from_spec --schema Basisprofiel \
        --url https://developers.kvk.nl/cms/api/uploads/api_basisprofiel_widget_aa888449ed.yaml

    Post-processed by hand by commenting out all the array items and deleting all the
    HAL 'links' constructs.
    """

    # NOTE the plugin manipulates the data to finds and attach the 'bezoekadres' and
    # 'correspondentieadres' from 'adressen' list so to make these 'bezoekadres_xx'
    # and 'correspondentieadres_xx' attributes we did some manual copy/paste/replace on the generated attrutes
    bezoekadres_aanduidingBijHuisnummer = ChoiceItem(
        "bezoekadres.aanduidingBijHuisnummer",
        _("bezoekadres > aanduidingBijHuisnummer"),
    )
    bezoekadres_geoData_addresseerbaarObjectId = ChoiceItem(
        "bezoekadres.geoData.addresseerbaarObjectId",
        _("bezoekadres > geoData > addresseerbaarObjectId"),
    )
    bezoekadres_geoData_gpsLatitude = ChoiceItem(
        "bezoekadres.geoData.gpsLatitude", _("bezoekadres > geoData > gpsLatitude")
    )
    bezoekadres_geoData_gpsLongitude = ChoiceItem(
        "bezoekadres.geoData.gpsLongitude", _("bezoekadres > geoData > gpsLongitude")
    )
    bezoekadres_geoData_nummerAanduidingId = ChoiceItem(
        "bezoekadres.geoData.nummerAanduidingId",
        _("bezoekadres > geoData > nummerAanduidingId"),
    )
    bezoekadres_geoData_rijksdriehoekX = ChoiceItem(
        "bezoekadres.geoData.rijksdriehoekX",
        _("bezoekadres > geoData > rijksdriehoekX"),
    )
    bezoekadres_geoData_rijksdriehoekY = ChoiceItem(
        "bezoekadres.geoData.rijksdriehoekY",
        _("bezoekadres > geoData > rijksdriehoekY"),
    )
    bezoekadres_geoData_rijksdriehoekZ = ChoiceItem(
        "bezoekadres.geoData.rijksdriehoekZ",
        _("bezoekadres > geoData > rijksdriehoekZ"),
    )
    bezoekadres_huisletter = ChoiceItem(
        "bezoekadres.huisletter", _("bezoekadres > huisletter")
    )
    bezoekadres_huisnummer = ChoiceItem(
        "bezoekadres.huisnummer", _("bezoekadres > huisnummer")
    )
    bezoekadres_huisnummerToevoeging = ChoiceItem(
        "bezoekadres.huisnummerToevoeging", _("bezoekadres > huisnummerToevoeging")
    )
    bezoekadres_indAfgeschermd = ChoiceItem(
        "bezoekadres.indAfgeschermd", _("bezoekadres > indAfgeschermd")
    )
    bezoekadres_land = ChoiceItem("bezoekadres.land", _("bezoekadres > land"))
    bezoekadres_plaats = ChoiceItem("bezoekadres.plaats", _("bezoekadres > plaats"))
    bezoekadres_postbusnummer = ChoiceItem(
        "bezoekadres.postbusnummer", _("bezoekadres > postbusnummer")
    )
    bezoekadres_postcode = ChoiceItem(
        "bezoekadres.postcode", _("bezoekadres > postcode")
    )
    bezoekadres_postcodeWoonplaats = ChoiceItem(
        "bezoekadres.postcodeWoonplaats", _("bezoekadres > postcodeWoonplaats")
    )
    bezoekadres_regio = ChoiceItem("bezoekadres.regio", _("bezoekadres > regio"))
    bezoekadres_straatHuisnummer = ChoiceItem(
        "bezoekadres.straatHuisnummer", _("bezoekadres > straatHuisnummer")
    )
    bezoekadres_straatnaam = ChoiceItem(
        "bezoekadres.straatnaam", _("bezoekadres > straatnaam")
    )
    bezoekadres_toevoegingAdres = ChoiceItem(
        "bezoekadres.toevoegingAdres", _("bezoekadres > toevoegingAdres")
    )
    bezoekadres_type = ChoiceItem("bezoekadres.type", _("bezoekadres > type"))

    correspondentieadres_aanduidingBijHuisnummer = ChoiceItem(
        "correspondentieadres.aanduidingBijHuisnummer",
        _("correspondentieadres > aanduidingBijHuisnummer"),
    )
    correspondentieadres_geoData_addresseerbaarObjectId = ChoiceItem(
        "correspondentieadres.geoData.addresseerbaarObjectId",
        _("correspondentieadres > geoData > addresseerbaarObjectId"),
    )
    correspondentieadres_geoData_gpsLatitude = ChoiceItem(
        "correspondentieadres.geoData.gpsLatitude",
        _("correspondentieadres > geoData > gpsLatitude"),
    )
    correspondentieadres_geoData_gpsLongitude = ChoiceItem(
        "correspondentieadres.geoData.gpsLongitude",
        _("correspondentieadres > geoData > gpsLongitude"),
    )
    correspondentieadres_geoData_nummerAanduidingId = ChoiceItem(
        "correspondentieadres.geoData.nummerAanduidingId",
        _("correspondentieadres > geoData > nummerAanduidingId"),
    )
    correspondentieadres_geoData_rijksdriehoekX = ChoiceItem(
        "correspondentieadres.geoData.rijksdriehoekX",
        _("correspondentieadres > geoData > rijksdriehoekX"),
    )
    correspondentieadres_geoData_rijksdriehoekY = ChoiceItem(
        "correspondentieadres.geoData.rijksdriehoekY",
        _("correspondentieadres > geoData > rijksdriehoekY"),
    )
    correspondentieadres_geoData_rijksdriehoekZ = ChoiceItem(
        "correspondentieadres.geoData.rijksdriehoekZ",
        _("correspondentieadres > geoData > rijksdriehoekZ"),
    )
    correspondentieadres_huisletter = ChoiceItem(
        "correspondentieadres.huisletter", _("correspondentieadres > huisletter")
    )
    correspondentieadres_huisnummer = ChoiceItem(
        "correspondentieadres.huisnummer", _("correspondentieadres > huisnummer")
    )
    correspondentieadres_huisnummerToevoeging = ChoiceItem(
        "correspondentieadres.huisnummerToevoeging",
        _("correspondentieadres > huisnummerToevoeging"),
    )
    correspondentieadres_indAfgeschermd = ChoiceItem(
        "correspondentieadres.indAfgeschermd",
        _("correspondentieadres > indAfgeschermd"),
    )
    correspondentieadres_land = ChoiceItem(
        "correspondentieadres.land", _("correspondentieadres > land")
    )
    correspondentieadres_plaats = ChoiceItem(
        "correspondentieadres.plaats", _("correspondentieadres > plaats")
    )
    correspondentieadres_postbusnummer = ChoiceItem(
        "correspondentieadres.postbusnummer", _("correspondentieadres > postbusnummer")
    )
    correspondentieadres_postcode = ChoiceItem(
        "correspondentieadres.postcode", _("correspondentieadres > postcode")
    )
    correspondentieadres_postcodeWoonplaats = ChoiceItem(
        "correspondentieadres.postcodeWoonplaats",
        _("correspondentieadres > postcodeWoonplaats"),
    )
    correspondentieadres_regio = ChoiceItem(
        "correspondentieadres.regio", _("correspondentieadres > regio")
    )
    correspondentieadres_straatHuisnummer = ChoiceItem(
        "correspondentieadres.straatHuisnummer",
        _("correspondentieadres > straatHuisnummer"),
    )
    correspondentieadres_straatnaam = ChoiceItem(
        "correspondentieadres.straatnaam", _("correspondentieadres > straatnaam")
    )
    correspondentieadres_toevoegingAdres = ChoiceItem(
        "correspondentieadres.toevoegingAdres",
        _("correspondentieadres > toevoegingAdres"),
    )
    correspondentieadres_type = ChoiceItem(
        "correspondentieadres.type", _("correspondentieadres > type")
    )
    eigenaar_rechtsvorm = ChoiceItem(
        "_embedded.eigenaar.rechtsvorm", _("_embedded > eigenaar > rechtsvorm")
    )
    eigenaar_rsin = ChoiceItem(
        "_embedded.eigenaar.rsin", _("_embedded > eigenaar > rsin")
    )
    eigenaar_uitgebreideRechtsvorm = ChoiceItem(
        "_embedded.eigenaar.uitgebreideRechtsvorm",
        _("_embedded > eigenaar > uitgebreideRechtsvorm"),
    )
    formeleRegistratiedatum = ChoiceItem(
        "formeleRegistratiedatum", _("formeleRegistratiedatum")
    )
    # handelsnamen_i_naam = ChoiceItem(
    #     "handelsnamen[].naam", _("handelsnamen > [] > naam")
    # )
    # handelsnamen_i_volgorde = ChoiceItem(
    #     "handelsnamen[].volgorde", _("handelsnamen > [] > volgorde")
    # )
    hoofdvestiging_deeltijdWerkzamePersonen = ChoiceItem(
        "_embedded.hoofdvestiging.deeltijdWerkzamePersonen",
        _("_embedded > hoofdvestiging > deeltijdWerkzamePersonen"),
    )
    hoofdvestiging_eersteHandelsnaam = ChoiceItem(
        "_embedded.hoofdvestiging.eersteHandelsnaam",
        _("_embedded > hoofdvestiging > eersteHandelsnaam"),
    )
    hoofdvestiging_formeleRegistratiedatum = ChoiceItem(
        "_embedded.hoofdvestiging.formeleRegistratiedatum",
        _("_embedded > hoofdvestiging > formeleRegistratiedatum"),
    )
    hoofdvestiging_indCommercieleVestiging = ChoiceItem(
        "_embedded.hoofdvestiging.indCommercieleVestiging",
        _("_embedded > hoofdvestiging > indCommercieleVestiging"),
    )
    hoofdvestiging_indHoofdvestiging = ChoiceItem(
        "_embedded.hoofdvestiging.indHoofdvestiging",
        _("_embedded > hoofdvestiging > indHoofdvestiging"),
    )
    hoofdvestiging_indNonMailing = ChoiceItem(
        "_embedded.hoofdvestiging.indNonMailing",
        _("_embedded > hoofdvestiging > indNonMailing"),
    )
    hoofdvestiging_kvkNummer = ChoiceItem(
        "_embedded.hoofdvestiging.kvkNummer",
        _("_embedded > hoofdvestiging > kvkNummer"),
    )
    hoofdvestiging_materieleRegistratie_datumAanvang = ChoiceItem(
        "_embedded.hoofdvestiging.materieleRegistratie.datumAanvang",
        _("_embedded > hoofdvestiging > materieleRegistratie > datumAanvang"),
    )
    hoofdvestiging_materieleRegistratie_datumEinde = ChoiceItem(
        "_embedded.hoofdvestiging.materieleRegistratie.datumEinde",
        _("_embedded > hoofdvestiging > materieleRegistratie > datumEinde"),
    )
    hoofdvestiging_rsin = ChoiceItem(
        "_embedded.hoofdvestiging.rsin", _("_embedded > hoofdvestiging > rsin")
    )
    # hoofdvestiging_sbiActiviteiten_i_indHoofdactiviteit = ChoiceItem(
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].indHoofdactiviteit",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > indHoofdactiviteit"),
    # )
    # hoofdvestiging_sbiActiviteiten_i_sbiCode = ChoiceItem(
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].sbiCode",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > sbiCode"),
    # )
    # hoofdvestiging_sbiActiviteiten_i_sbiOmschrijving = ChoiceItem(
    #     "_embedded.hoofdvestiging.sbiActiviteiten[].sbiOmschrijving",
    #     _("_embedded > hoofdvestiging > sbiActiviteiten > [] > sbiOmschrijving"),
    # )
    hoofdvestiging_totaalWerkzamePersonen = ChoiceItem(
        "_embedded.hoofdvestiging.totaalWerkzamePersonen",
        _("_embedded > hoofdvestiging > totaalWerkzamePersonen"),
    )
    hoofdvestiging_vestigingsnummer = ChoiceItem(
        "_embedded.hoofdvestiging.vestigingsnummer",
        _("_embedded > hoofdvestiging > vestigingsnummer"),
    )
    hoofdvestiging_voltijdWerkzamePersonen = ChoiceItem(
        "_embedded.hoofdvestiging.voltijdWerkzamePersonen",
        _("_embedded > hoofdvestiging > voltijdWerkzamePersonen"),
    )
    # hoofdvestiging_websites_i = ChoiceItem(
    #     "_embedded.hoofdvestiging.websites[]",
    #     _("_embedded > hoofdvestiging > websites > []"),
    # )
    indNonMailing = ChoiceItem("indNonMailing", _("indNonMailing"))
    kvkNummer = ChoiceItem("kvkNummer", _("kvkNummer"))
    materieleRegistratie_datumAanvang = ChoiceItem(
        "materieleRegistratie.datumAanvang", _("materieleRegistratie > datumAanvang")
    )
    materieleRegistratie_datumEinde = ChoiceItem(
        "materieleRegistratie.datumEinde", _("materieleRegistratie > datumEinde")
    )
    naam = ChoiceItem("naam", _("naam"))
    # sbiActiviteiten_i_indHoofdactiviteit = ChoiceItem(
    #     "sbiActiviteiten[].indHoofdactiviteit",
    #     _("sbiActiviteiten > [] > indHoofdactiviteit"),
    # )
    # sbiActiviteiten_i_sbiCode = ChoiceItem(
    #     "sbiActiviteiten[].sbiCode", _("sbiActiviteiten > [] > sbiCode")
    # )
    # sbiActiviteiten_i_sbiOmschrijving = ChoiceItem(
    #     "sbiActiviteiten[].sbiOmschrijving", _("sbiActiviteiten > [] > sbiOmschrijving")
    # )
    statutaireNaam = ChoiceItem("statutaireNaam", _("statutaireNaam"))
    totaalWerkzamePersonen = ChoiceItem(
        "totaalWerkzamePersonen", _("totaalWerkzamePersonen")
    )
