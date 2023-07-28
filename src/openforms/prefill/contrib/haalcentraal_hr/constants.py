from django.db import models
from django.utils.translation import gettext_lazy as _


class Attributes(models.TextChoices):
    """
    This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
    specs: https://app.swaggerhub.com/apiproxy/schema/file/apis/DH-Sandbox/handelsregister/1.3.0?format=yaml
    schema: MaatschappelijkeActiviteitRaadplegen
    command: manage.py get_properties_from_oas --url https://app.swaggerhub.com/apiproxy/schema/file/apis/DH-Sandbox/handelsregister/1.3.0?format=yaml --schema MaatschappelijkeActiviteitRaadplegen
    """

    kvknummer = "kvkNummer", _("Kvknummer")
    naam = "naam", _("Naam")
    heeftalseigenaar_natuurlijkpersoon_burgerservicenummer = (
        "heeftAlsEigenaar.natuurlijkPersoon.burgerservicenummer",
        _("Heeftalseigenaar > Natuurlijkpersoon > Burgerservicenummer"),
    )
    heeftalseigenaar_natuurlijkpersoon_naam_geslachtsnaam = (
        "heeftAlsEigenaar.natuurlijkPersoon.naam.geslachtsnaam",
        _("Heeftalseigenaar > Natuurlijkpersoon > Naam > Geslachtsnaam"),
    )
    heeftalseigenaar_natuurlijkpersoon_naam_voornamen = (
        "heeftAlsEigenaar.natuurlijkPersoon.naam.voornamen",
        _("Heeftalseigenaar > Natuurlijkpersoon > Naam > Voornamen"),
    )
    heeftalseigenaar_natuurlijkpersoon_naam_voorvoegsel = (
        "heeftAlsEigenaar.natuurlijkPersoon.naam.voorvoegsel",
        _("Heeftalseigenaar > Natuurlijkpersoon > Naam > Voorvoegsel"),
    )
    heeftalseigenaar_natuurlijkpersoon_geboorte = (
        "heeftAlsEigenaar.natuurlijkPersoon.geboorte",
        _("Heeftalseigenaar > Natuurlijkpersoon > Geboorte"),
    )
    heeftalseigenaar_natuurlijkpersoon_geslachtsaanduiding = (
        "heeftAlsEigenaar.natuurlijkPersoon.geslachtsaanduiding",
        _("Heeftalseigenaar > Natuurlijkpersoon > Geslachtsaanduiding"),
    )
    heeftalseigenaar_nietnatuurlijkpersoon_rsin = (
        "heeftAlsEigenaar.nietNatuurlijkPersoon.rsin",
        _("Heeftalseigenaar > Nietnatuurlijkpersoon > Rsin"),
    )
    heeftalseigenaar_nietnatuurlijkpersoon_naamgeving = (
        "heeftAlsEigenaar.nietNatuurlijkPersoon.naamgeving",
        _("Heeftalseigenaar > Nietnatuurlijkpersoon > Naamgeving"),
    )
    heeftalseigenaar_rechtsvorm = "heeftAlsEigenaar.rechtsvorm", _(
        "Heeftalseigenaar > Rechtsvorm"
    )
    heeftalseigenaar_aansprakelijken = "heeftAlsEigenaar.aansprakelijken", _(
        "Heeftalseigenaar > Aansprakelijken"
    )
    heeftalseigenaar_bestuursfuncties = "heeftAlsEigenaar.bestuursfuncties", _(
        "Heeftalseigenaar > Bestuursfuncties"
    )
    heeftalseigenaar_functionarissenbijzondererechtstoestand = (
        "heeftAlsEigenaar.functionarissenBijzondereRechtstoestand",
        _("Heeftalseigenaar > Functionarissenbijzondererechtstoestand"),
    )
    heeftalseigenaar_gemachtigden = "heeftAlsEigenaar.gemachtigden", _(
        "Heeftalseigenaar > Gemachtigden"
    )
    heeftalseigenaar_publiekrechtelijkefunctionarissen = (
        "heeftAlsEigenaar.publiekrechtelijkeFunctionarissen",
        _("Heeftalseigenaar > Publiekrechtelijkefunctionarissen"),
    )
    heeftalseigenaar_overigefunctionarissen = (
        "heeftAlsEigenaar.overigeFunctionarissen",
        _("Heeftalseigenaar > Overigefunctionarissen"),
    )
    activiteiten = "activiteiten", _("Activiteiten")
    manifesteertzichals_handelsnamen = "manifesteertZichAls.handelsnamen", _(
        "Manifesteertzichals > Handelsnamen"
    )
    manifesteertzichals_activiteiten = "manifesteertZichAls.activiteiten", _(
        "Manifesteertzichals > Activiteiten"
    )
    manifesteertzichals_wordtuitgeoefendin = (
        "manifesteertZichAls.wordtUitgeoefendIn",
        _("Manifesteertzichals > Wordtuitgeoefendin"),
    )
    wordtgeleidvanuit_vestigingsnummer = "wordtGeleidVanuit.vestigingsnummer", _(
        "Wordtgeleidvanuit > Vestigingsnummer"
    )
    wordtgeleidvanuit_handelsnamen = "wordtGeleidVanuit.handelsnamen", _(
        "Wordtgeleidvanuit > Handelsnamen"
    )
    wordtgeleidvanuit_bezoeklocatie_straatnaam = (
        "wordtGeleidVanuit.bezoekLocatie.straatnaam",
        _("Wordtgeleidvanuit > Bezoeklocatie > Straatnaam"),
    )
    wordtgeleidvanuit_bezoeklocatie_huisnummer = (
        "wordtGeleidVanuit.bezoekLocatie.huisnummer",
        _("Wordtgeleidvanuit > Bezoeklocatie > Huisnummer"),
    )
    wordtgeleidvanuit_bezoeklocatie_huisletter = (
        "wordtGeleidVanuit.bezoekLocatie.huisletter",
        _("Wordtgeleidvanuit > Bezoeklocatie > Huisletter"),
    )
    wordtgeleidvanuit_bezoeklocatie_huisnummertoevoeging = (
        "wordtGeleidVanuit.bezoekLocatie.huisnummertoevoeging",
        _("Wordtgeleidvanuit > Bezoeklocatie > Huisnummertoevoeging"),
    )
    wordtgeleidvanuit_bezoeklocatie_postcode = (
        "wordtGeleidVanuit.bezoekLocatie.postcode",
        _("Wordtgeleidvanuit > Bezoeklocatie > Postcode"),
    )
    wordtgeleidvanuit_bezoeklocatie_woonplaatsnaam = (
        "wordtGeleidVanuit.bezoekLocatie.woonplaatsnaam",
        _("Wordtgeleidvanuit > Bezoeklocatie > Woonplaatsnaam"),
    )
    wordtgeleidvanuit_bezoeklocatie_buitenlandsadres_land = (
        "wordtGeleidVanuit.bezoekLocatie.buitenlandsAdres.land",
        _("Wordtgeleidvanuit > Bezoeklocatie > Buitenlandsadres > Land"),
    )
    wordtgeleidvanuit_bezoeklocatie_buitenlandsadres_straathuisnummer = (
        "wordtGeleidVanuit.bezoekLocatie.buitenlandsAdres.straatHuisnummer",
        _("Wordtgeleidvanuit > Bezoeklocatie > Buitenlandsadres > Straathuisnummer"),
    )
    wordtgeleidvanuit_bezoeklocatie_buitenlandsadres_postcodewoonplaats = (
        "wordtGeleidVanuit.bezoekLocatie.buitenlandsAdres.postcodeWoonplaats",
        _("Wordtgeleidvanuit > Bezoeklocatie > Buitenlandsadres > Postcodewoonplaats"),
    )
    wordtgeleidvanuit_bezoeklocatie_buitenlandsadres_regio = (
        "wordtGeleidVanuit.bezoekLocatie.buitenlandsAdres.regio",
        _("Wordtgeleidvanuit > Bezoeklocatie > Buitenlandsadres > Regio"),
    )
    wordtgeleidvanuit_bezoeklocatie_identificatiecodenummeraanduiding = (
        "wordtGeleidVanuit.bezoekLocatie.identificatiecodeNummeraanduiding",
        _("Wordtgeleidvanuit > Bezoeklocatie > Identificatiecodenummeraanduiding"),
    )
    wordtgeleidvanuit_postlocatie_straatnaam = (
        "wordtGeleidVanuit.postLocatie.straatnaam",
        _("Wordtgeleidvanuit > Postlocatie > Straatnaam"),
    )
    wordtgeleidvanuit_postlocatie_huisnummer = (
        "wordtGeleidVanuit.postLocatie.huisnummer",
        _("Wordtgeleidvanuit > Postlocatie > Huisnummer"),
    )
    wordtgeleidvanuit_postlocatie_huisletter = (
        "wordtGeleidVanuit.postLocatie.huisletter",
        _("Wordtgeleidvanuit > Postlocatie > Huisletter"),
    )
    wordtgeleidvanuit_postlocatie_huisnummertoevoeging = (
        "wordtGeleidVanuit.postLocatie.huisnummertoevoeging",
        _("Wordtgeleidvanuit > Postlocatie > Huisnummertoevoeging"),
    )
    wordtgeleidvanuit_postlocatie_postcode = (
        "wordtGeleidVanuit.postLocatie.postcode",
        _("Wordtgeleidvanuit > Postlocatie > Postcode"),
    )
    wordtgeleidvanuit_postlocatie_woonplaatsnaam = (
        "wordtGeleidVanuit.postLocatie.woonplaatsnaam",
        _("Wordtgeleidvanuit > Postlocatie > Woonplaatsnaam"),
    )
    wordtgeleidvanuit_postlocatie_buitenlandsadres_land = (
        "wordtGeleidVanuit.postLocatie.buitenlandsAdres.land",
        _("Wordtgeleidvanuit > Postlocatie > Buitenlandsadres > Land"),
    )
    wordtgeleidvanuit_postlocatie_buitenlandsadres_straathuisnummer = (
        "wordtGeleidVanuit.postLocatie.buitenlandsAdres.straatHuisnummer",
        _("Wordtgeleidvanuit > Postlocatie > Buitenlandsadres > Straathuisnummer"),
    )
    wordtgeleidvanuit_postlocatie_buitenlandsadres_postcodewoonplaats = (
        "wordtGeleidVanuit.postLocatie.buitenlandsAdres.postcodeWoonplaats",
        _("Wordtgeleidvanuit > Postlocatie > Buitenlandsadres > Postcodewoonplaats"),
    )
    wordtgeleidvanuit_postlocatie_buitenlandsadres_regio = (
        "wordtGeleidVanuit.postLocatie.buitenlandsAdres.regio",
        _("Wordtgeleidvanuit > Postlocatie > Buitenlandsadres > Regio"),
    )
    wordtgeleidvanuit_postlocatie_identificatiecodenummeraanduiding = (
        "wordtGeleidVanuit.postLocatie.identificatiecodeNummeraanduiding",
        _("Wordtgeleidvanuit > Postlocatie > Identificatiecodenummeraanduiding"),
    )
    wordtgeleidvanuit_postlocatie_postbusnummer = (
        "wordtGeleidVanuit.postLocatie.postbusnummer",
        _("Wordtgeleidvanuit > Postlocatie > Postbusnummer"),
    )
    wordtuitgeoefendin = "wordtUitgeoefendIn", _("Wordtuitgeoefendin")
    datumaanvang_dag = "datumAanvang.dag", _("Datumaanvang > Dag")
    datumaanvang_datum = "datumAanvang.datum", _("Datumaanvang > Datum")
    datumaanvang_jaar = "datumAanvang.jaar", _("Datumaanvang > Jaar")
    datumaanvang_maand = "datumAanvang.maand", _("Datumaanvang > Maand")
    datumeinde_dag = "datumEinde.dag", _("Datumeinde > Dag")
    datumeinde_datum = "datumEinde.datum", _("Datumeinde > Datum")
    datumeinde_jaar = "datumEinde.jaar", _("Datumeinde > Jaar")
    datumeinde_maand = "datumEinde.maand", _("Datumeinde > Maand")
    links_self_href = "_links.self.href", _("_links > Self > Href")
    links_self_templated = "_links.self.templated", _("_links > Self > Templated")
    links_self_title = "_links.self.title", _("_links > Self > Title")
    links_eigenaar_href = "_links.eigenaar.href", _("_links > Eigenaar > Href")
    links_eigenaar_templated = "_links.eigenaar.templated", _(
        "_links > Eigenaar > Templated"
    )
    links_eigenaar_title = "_links.eigenaar.title", _("_links > Eigenaar > Title")
    links_vestigingen = "_links.vestigingen", _("_links > Vestigingen")
    links_aansprakelijken = "_links.aansprakelijken", _("_links > Aansprakelijken")
    links_bestuursfuncties = "_links.bestuursfuncties", _("_links > Bestuursfuncties")
    links_functionarissenbijzondererechtstoestand = (
        "_links.functionarissenBijzondereRechtstoestand",
        _("_links > Functionarissenbijzondererechtstoestand"),
    )
    links_gemachtigden = "_links.gemachtigden", _("_links > Gemachtigden")
    links_publiekrechtelijkefunctionarissen = (
        "_links.publiekrechtelijkeFunctionarissen",
        _("_links > Publiekrechtelijkefunctionarissen"),
    )
    links_overigefunctionarissen = "_links.overigeFunctionarissen", _(
        "_links > Overigefunctionarissen"
    )
