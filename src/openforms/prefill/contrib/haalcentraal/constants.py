from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://op.open-forms.test.maykin.opengem.nl/api/schema/openapi.yaml
    path:    /ingeschrevenpersonen/{burgerservicenummer}
    command: manage.py generate_prefill_from_spec --path /ingeschrevenpersonen/{burgerservicenummer} --url https://op.open-forms.test.maykin.opengem.nl/api/schema/openapi.yaml
    """

    burgerservicenummer = ChoiceItem("burgerservicenummer", _("Burgerservicenummer"))
    datumEersteInschrijvingGBA_dag = ChoiceItem(
        "datumEersteInschrijvingGBA.dag", _("DatumEersteInschrijvingGBA > Dag")
    )
    datumEersteInschrijvingGBA_datum = ChoiceItem(
        "datumEersteInschrijvingGBA.datum", _("DatumEersteInschrijvingGBA > Datum")
    )
    datumEersteInschrijvingGBA_jaar = ChoiceItem(
        "datumEersteInschrijvingGBA.jaar", _("DatumEersteInschrijvingGBA > Jaar")
    )
    datumEersteInschrijvingGBA_maand = ChoiceItem(
        "datumEersteInschrijvingGBA.maand", _("DatumEersteInschrijvingGBA > Maand")
    )
    geboorte_datum_dag = ChoiceItem("geboorte.datum.dag", _("Geboorte > Datum > Dag"))
    geboorte_datum_datum = ChoiceItem(
        "geboorte.datum.datum", _("Geboorte > Datum > Datum")
    )
    geboorte_datum_jaar = ChoiceItem(
        "geboorte.datum.jaar", _("Geboorte > Datum > Jaar")
    )
    geboorte_datum_maand = ChoiceItem(
        "geboorte.datum.maand", _("Geboorte > Datum > Maand")
    )
    geboorte_inOnderzoek_datum = ChoiceItem(
        "geboorte.inOnderzoek.datum", _("Geboorte > InOnderzoek > Datum")
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.dag",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.datum",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.maand",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    geboorte_inOnderzoek_land = ChoiceItem(
        "geboorte.inOnderzoek.land", _("Geboorte > InOnderzoek > Land")
    )
    geboorte_inOnderzoek_plaats = ChoiceItem(
        "geboorte.inOnderzoek.plaats", _("Geboorte > InOnderzoek > Plaats")
    )
    geboorte_land_code = ChoiceItem("geboorte.land.code", _("Geboorte > Land > Code"))
    geboorte_land_omschrijving = ChoiceItem(
        "geboorte.land.omschrijving", _("Geboorte > Land > Omschrijving")
    )
    geboorte_plaats_code = ChoiceItem(
        "geboorte.plaats.code", _("Geboorte > Land > Code")
    )
    geboorte_plaats_omschrijving = ChoiceItem(
        "geboorte.plaats.omschrijving", _("Geboorte > Land > Omschrijving")
    )
    geheimhoudingPersoonsgegevens = ChoiceItem(
        "geheimhoudingPersoonsgegevens", _("GeheimhoudingPersoonsgegevens")
    )
    geslachtsaanduiding = ChoiceItem("geslachtsaanduiding", _("Geslachtsaanduiding"))
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.dag",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.datum",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.maand",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = ChoiceItem(
        "gezagsverhouding.inOnderzoek.indicatieCurateleRegister",
        _("Gezagsverhouding > InOnderzoek > IndicatieCurateleRegister"),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = ChoiceItem(
        "gezagsverhouding.inOnderzoek.indicatieGezagMinderjarige",
        _("Gezagsverhouding > InOnderzoek > IndicatieGezagMinderjarige"),
    )
    gezagsverhouding_indicatieCurateleRegister = ChoiceItem(
        "gezagsverhouding.indicatieCurateleRegister",
        _("Gezagsverhouding > IndicatieCurateleRegister"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = ChoiceItem(
        "gezagsverhouding.indicatieGezagMinderjarige",
        _("Gezagsverhouding > IndicatieGezagMinderjarige"),
    )
    inOnderzoek_burgerservicenummer = ChoiceItem(
        "inOnderzoek.burgerservicenummer", _("InOnderzoek > Burgerservicenummer")
    )
    inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.dag",
        _("InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.datum",
        _("InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.jaar",
        _("InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.maand",
        _("InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    inOnderzoek_geslachtsaanduiding = ChoiceItem(
        "inOnderzoek.geslachtsaanduiding", _("InOnderzoek > Geslachtsaanduiding")
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.dag",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Dag"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Datum"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.jaar",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Jaar"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.maand",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Maand"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.dag",
        _("Kiesrecht > EinddatumUitsluitingKiesrecht > Dag"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.datum",
        _("Kiesrecht > EinddatumUitsluitingKiesrecht > Datum"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.jaar",
        _("Kiesrecht > EinddatumUitsluitingKiesrecht > Jaar"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.maand",
        _("Kiesrecht > EinddatumUitsluitingKiesrecht > Maand"),
    )
    kiesrecht_europeesKiesrecht = ChoiceItem(
        "kiesrecht.europeesKiesrecht", _("Kiesrecht > EuropeesKiesrecht")
    )
    kiesrecht_uitgeslotenVanKiesrecht = ChoiceItem(
        "kiesrecht.uitgeslotenVanKiesrecht", _("Kiesrecht > UitgeslotenVanKiesrecht")
    )
    leeftijd = ChoiceItem("leeftijd", _("Leeftijd"))
    naam_aanduidingNaamgebruik = ChoiceItem(
        "naam.aanduidingNaamgebruik", _("Naam > AanduidingNaamgebruik")
    )
    naam_aanhef = ChoiceItem("naam.aanhef", _("Naam > Aanhef"))
    naam_aanschrijfwijze = ChoiceItem(
        "naam.aanschrijfwijze", _("Naam > Aanschrijfwijze")
    )
    naam_gebruikInLopendeTekst = ChoiceItem(
        "naam.gebruikInLopendeTekst", _("Naam > GebruikInLopendeTekst")
    )
    naam_geslachtsnaam = ChoiceItem("naam.geslachtsnaam", _("Naam > Geslachtsnaam"))
    naam_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.dag",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.datum",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.maand",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    naam_inOnderzoek_geslachtsnaam = ChoiceItem(
        "naam.inOnderzoek.geslachtsnaam", _("Naam > InOnderzoek > Geslachtsnaam")
    )
    naam_inOnderzoek_voornamen = ChoiceItem(
        "naam.inOnderzoek.voornamen", _("Naam > InOnderzoek > Voornamen")
    )
    naam_inOnderzoek_voorvoegsel = ChoiceItem(
        "naam.inOnderzoek.voorvoegsel", _("Naam > InOnderzoek > Voorvoegsel")
    )
    naam_voorletters = ChoiceItem("naam.voorletters", _("Naam > Voorletters"))
    naam_voornamen = ChoiceItem("naam.voornamen", _("Naam > Voornamen"))
    naam_voorvoegsel = ChoiceItem("naam.voorvoegsel", _("Naam > Voorvoegsel"))
    opschortingBijhouding_datum_dag = ChoiceItem(
        "opschortingBijhouding.datum.dag",
        _("OpschortingBijhouding > Datum > Dag"),
    )
    opschortingBijhouding_datum_datum = ChoiceItem(
        "opschortingBijhouding.datum.datum",
        _("OpschortingBijhouding > Datum > Datum"),
    )
    opschortingBijhouding_datum_jaar = ChoiceItem(
        "opschortingBijhouding.datum.jaar",
        _("OpschortingBijhouding > Datum > Jaar"),
    )
    opschortingBijhouding_datum_maand = ChoiceItem(
        "opschortingBijhouding.datum.maand",
        _("OpschortingBijhouding > Datum > Maand"),
    )
    opschortingBijhouding_reden = ChoiceItem(
        "opschortingBijhouding.reden", _("OpschortingBijhouding > Reden")
    )
    overlijden_datum_dag = ChoiceItem(
        "overlijden.datum.dag", _("Overlijden > Datum > Dag")
    )
    overlijden_datum_datum = ChoiceItem(
        "overlijden.datum.datum", _("Overlijden > Datum > Datum")
    )
    overlijden_datum_jaar = ChoiceItem(
        "overlijden.datum.jaar", _("Overlijden > Datum > Jaar")
    )
    overlijden_datum_maand = ChoiceItem(
        "overlijden.datum.maand", _("Overlijden > Datum > Maand")
    )
    overlijden_inOnderzoek_datum = ChoiceItem(
        "overlijden.inOnderzoek.datum", _("Overlijden > InOnderzoek > Datum")
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.dag",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.datum",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.maand",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    overlijden_inOnderzoek_land = ChoiceItem(
        "overlijden.inOnderzoek.land", _("Overlijden > InOnderzoek > Land")
    )
    overlijden_inOnderzoek_plaats = ChoiceItem(
        "overlijden.inOnderzoek.plaats", _("Overlijden > InOnderzoek > Plaats")
    )
    overlijden_indicatieOverleden = ChoiceItem(
        "overlijden.indicatieOverleden", _("Overlijden > Indicatieoverleden")
    )
    overlijden_land_code = ChoiceItem(
        "overlijden.land.code", _("Overlijden > Land > Code")
    )
    overlijden_land_omschrijving = ChoiceItem(
        "overlijden.land.omschrijving", _("Overlijden > Land > Omschrijving")
    )
    overlijden_plaats_code = ChoiceItem(
        "overlijden.plaats.code", _("Overlijden > Land > Code")
    )
    overlijden_plaats_omschrijving = ChoiceItem(
        "overlijden.plaats.omschrijving", _("Overlijden > Land > Omschrijving")
    )
    verblijfplaats_aanduidingBijHuisnummer = ChoiceItem(
        "verblijfplaats.aanduidingBijHuisnummer",
        _("Verblijfplaats > AanduidingBijHuisnummer"),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.dag",
        _("Verblijfplaats > DatumAanvangAdreshouding > Dag"),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.datum",
        _("Verblijfplaats > DatumAanvangAdreshouding > Datum"),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.jaar",
        _("Verblijfplaats > DatumAanvangAdreshouding > Jaar"),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.maand",
        _("Verblijfplaats > DatumAanvangAdreshouding > Maand"),
    )
    verblijfplaats_datumIngangGeldigheid_dag = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.dag",
        _("Verblijfplaats > DatumIngangGeldigheid > Dag"),
    )
    verblijfplaats_datumIngangGeldigheid_datum = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.datum",
        _("Verblijfplaats > DatumIngangGeldigheid > Datum"),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.jaar",
        _("Verblijfplaats > DatumIngangGeldigheid > Jaar"),
    )
    verblijfplaats_datumIngangGeldigheid_maand = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.maand",
        _("Verblijfplaats > DatumIngangGeldigheid > Maand"),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.dag",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Dag"),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.datum",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Datum"),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.jaar",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Jaar"),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.maand",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Maand"),
    )
    verblijfplaats_datumVestigingInNederland_dag = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.dag",
        _("Verblijfplaats > DatumVestigingInNederland > Dag"),
    )
    verblijfplaats_datumVestigingInNederland_datum = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.datum",
        _("Verblijfplaats > DatumVestigingInNederland > Datum"),
    )
    verblijfplaats_datumVestigingInNederland_jaar = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.jaar",
        _("Verblijfplaats > DatumVestigingInNederland > Jaar"),
    )
    verblijfplaats_datumVestigingInNederland_maand = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.maand",
        _("Verblijfplaats > DatumVestigingInNederland > Maand"),
    )
    verblijfplaats_functieAdres = ChoiceItem(
        "verblijfplaats.functieAdres", _("Verblijfplaats > Functieadres")
    )
    verblijfplaats_gemeenteVanInschrijving_code = ChoiceItem(
        "verblijfplaats.gemeenteVanInschrijving.code",
        _("Verblijfplaats > GemeenteVanInschrijving > Code"),
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = ChoiceItem(
        "verblijfplaats.gemeenteVanInschrijving.omschrijving",
        _("Verblijfplaats > GemeenteVanInschrijving > Omschrijving"),
    )
    verblijfplaats_huisletter = ChoiceItem(
        "verblijfplaats.huisletter", _("Verblijfplaats > Huisletter")
    )
    verblijfplaats_huisnummer = ChoiceItem(
        "verblijfplaats.huisnummer", _("Verblijfplaats > Huisnummer")
    )
    verblijfplaats_huisnummertoevoeging = ChoiceItem(
        "verblijfplaats.huisnummertoevoeging",
        _("Verblijfplaats > Huisnummertoevoeging"),
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "verblijfplaats.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > IdentificatiecodeAdresseerbaarObject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = ChoiceItem(
        "verblijfplaats.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > IdentificatiecodeNummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = ChoiceItem(
        "verblijfplaats.inOnderzoek.aanduidingBijHuisnummer",
        _("Verblijfplaats > InOnderzoek > AanduidingBijHuisnummer"),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumAanvangAdreshouding",
        _("Verblijfplaats > InOnderzoek > DatumAanvangAdreshouding"),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangGeldigheid",
        _("Verblijfplaats > InOnderzoek > DatumIngangGeldigheid"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumInschrijvingInGemeente",
        _("Verblijfplaats > InOnderzoek > DatumInschrijvingInGemeente"),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumVestigingInNederland",
        _("Verblijfplaats > InOnderzoek > DatumVestigingInNederland"),
    )
    verblijfplaats_inOnderzoek_functieAdres = ChoiceItem(
        "verblijfplaats.inOnderzoek.functieAdres",
        _("Verblijfplaats > InOnderzoek > FunctieAdres"),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = ChoiceItem(
        "verblijfplaats.inOnderzoek.gemeenteVanInschrijving",
        _("Verblijfplaats > InOnderzoek > GemeenteVanInschrijving"),
    )
    verblijfplaats_inOnderzoek_huisletter = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisletter",
        _("Verblijfplaats > InOnderzoek > Huisletter"),
    )
    verblijfplaats_inOnderzoek_huisnummer = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisnummer",
        _("Verblijfplaats > InOnderzoek > Huisnummer"),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisnummertoevoeging",
        _("Verblijfplaats > InOnderzoek > Huisnummertoevoeging"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "verblijfplaats.inOnderzoek.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > InOnderzoek > IdentificatiecodeAdresseerbaarObject"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = ChoiceItem(
        "verblijfplaats.inOnderzoek.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > InOnderzoek > IdentificatiecodeNummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = ChoiceItem(
        "verblijfplaats.inOnderzoek.landVanwaarIngeschreven",
        _("Verblijfplaats > InOnderzoek > LandVanwaarIngeschreven"),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = ChoiceItem(
        "verblijfplaats.inOnderzoek.locatiebeschrijving",
        _("Verblijfplaats > InOnderzoek > Locatiebeschrijving"),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = ChoiceItem(
        "verblijfplaats.inOnderzoek.naamOpenbareRuimte",
        _("Verblijfplaats > InOnderzoek > NaamOpenbareRuimte"),
    )
    verblijfplaats_inOnderzoek_postcode = ChoiceItem(
        "verblijfplaats.inOnderzoek.postcode",
        _("Verblijfplaats > InOnderzoek > Postcode"),
    )
    verblijfplaats_inOnderzoek_straat = ChoiceItem(
        "verblijfplaats.inOnderzoek.straat",
        _("Verblijfplaats > InOnderzoek > Straat"),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = ChoiceItem(
        "verblijfplaats.inOnderzoek.verblijfBuitenland",
        _("Verblijfplaats > InOnderzoek > VerblijfBuitenland"),
    )
    verblijfplaats_inOnderzoek_woonplaats = ChoiceItem(
        "verblijfplaats.inOnderzoek.woonplaats",
        _("Verblijfplaats > InOnderzoek > Woonplaats"),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = ChoiceItem(
        "verblijfplaats.indicatieVestigingVanuitBuitenland",
        _("Verblijfplaats > IndicatieVestigingVanuitBuitenland"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = ChoiceItem(
        "verblijfplaats.landVanwaarIngeschreven.code",
        _("Verblijfplaats > LandVanwaarIngeschreven > Code"),
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = ChoiceItem(
        "verblijfplaats.landVanwaarIngeschreven.omschrijving",
        _("Verblijfplaats > LandVanwaarIngeschreven > Omschrijving"),
    )
    verblijfplaats_locatiebeschrijving = ChoiceItem(
        "verblijfplaats.locatiebeschrijving", _("Verblijfplaats > Locatiebeschrijving")
    )
    verblijfplaats_naamOpenbareRuimte = ChoiceItem(
        "verblijfplaats.naamOpenbareRuimte", _("Verblijfplaats > NaamOpenbareRuimte")
    )
    verblijfplaats_postcode = ChoiceItem(
        "verblijfplaats.postcode", _("Verblijfplaats > Postcode")
    )
    verblijfplaats_straat = ChoiceItem(
        "verblijfplaats.straat", _("Verblijfplaats > Straat")
    )
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = ChoiceItem(
        "verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        _("Verblijfplaats > VanuitVertrokkenOnbekendWaarheen"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel1",
        _("Verblijfplaats > VerblijfBuitenland > AdresRegel1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel2",
        _("Verblijfplaats > VerblijfBuitenland > AdresRegel2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel3",
        _("Verblijfplaats > VerblijfBuitenland > AdresRegel3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.land.code",
        _("Verblijfplaats > VerblijfBuitenland > Land > Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.land.omschrijving",
        _("Verblijfplaats > VerblijfBuitenland > Land > Omschrijving"),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        _("Verblijfplaats > VerblijfBuitenland > VertrokkenOnbekendWaarheen"),
    )
    verblijfplaats_woonplaats = ChoiceItem(
        "verblijfplaats.woonplaats", _("Verblijfplaats > Woonplaats")
    )
    verblijfstitel_aanduiding_code = ChoiceItem(
        "verblijfstitel.aanduiding.code", _("Verblijfstitel > Aanduiding > Code")
    )
    verblijfstitel_aanduiding_omschrijving = ChoiceItem(
        "verblijfstitel.aanduiding.omschrijving",
        _("Verblijfstitel > Aanduiding > Omschrijving"),
    )
    verblijfstitel_datumEinde_dag = ChoiceItem(
        "verblijfstitel.datumEinde.dag",
        _("Verblijfstitel > DatumEinde > Dag"),
    )
    verblijfstitel_datumEinde_datum = ChoiceItem(
        "verblijfstitel.datumEinde.datum",
        _("Verblijfstitel > DatumEinde > Datum"),
    )
    verblijfstitel_datumEinde_jaar = ChoiceItem(
        "verblijfstitel.datumEinde.jaar",
        _("Verblijfstitel > DatumEinde > Jaar"),
    )
    verblijfstitel_datumEinde_maand = ChoiceItem(
        "verblijfstitel.datumEinde.maand",
        _("Verblijfstitel > DatumEinde > Maand"),
    )
    verblijfstitel_datumIngang_dag = ChoiceItem(
        "verblijfstitel.datumIngang.dag",
        _("Verblijfstitel > DatumIngang > Dag"),
    )
    verblijfstitel_datumIngang_datum = ChoiceItem(
        "verblijfstitel.datumIngang.datum",
        _("Verblijfstitel > DatumIngang > Datum"),
    )
    verblijfstitel_datumIngang_jaar = ChoiceItem(
        "verblijfstitel.datumIngang.jaar",
        _("Verblijfstitel > DatumIngang > Jaar"),
    )
    verblijfstitel_datumIngang_maand = ChoiceItem(
        "verblijfstitel.datumIngang.maand",
        _("Verblijfstitel > DatumIngang > Maand"),
    )
    verblijfstitel_inOnderzoek_aanduiding = ChoiceItem(
        "verblijfstitel.inOnderzoek.aanduiding",
        _("Verblijfstitel > InOnderzoek > Aanduiding"),
    )
    verblijfstitel_inOnderzoek_datumEinde = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumEinde",
        _("Verblijfstitel > InOnderzoek > DatumEinde"),
    )
    verblijfstitel_inOnderzoek_datumIngang = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngang",
        _("Verblijfstitel > InOnderzoek > DatumIngang"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
