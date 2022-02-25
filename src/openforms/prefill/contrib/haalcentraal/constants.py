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
        "datumEersteInschrijvingGBA.dag", _("Datumingangonderzoek > Dag")
    )
    datumEersteInschrijvingGBA_datum = ChoiceItem(
        "datumEersteInschrijvingGBA.datum", _("Datumingangonderzoek > Datum")
    )
    datumEersteInschrijvingGBA_jaar = ChoiceItem(
        "datumEersteInschrijvingGBA.jaar", _("Datumingangonderzoek > Jaar")
    )
    datumEersteInschrijvingGBA_maand = ChoiceItem(
        "datumEersteInschrijvingGBA.maand", _("Datumingangonderzoek > Maand")
    )
    geboorte_datum_dag = ChoiceItem(
        "geboorte.datum.dag", _("Geboorte > Datumingangonderzoek > Dag")
    )
    geboorte_datum_datum = ChoiceItem(
        "geboorte.datum.datum", _("Geboorte > Datumingangonderzoek > Datum")
    )
    geboorte_datum_jaar = ChoiceItem(
        "geboorte.datum.jaar", _("Geboorte > Datumingangonderzoek > Jaar")
    )
    geboorte_datum_maand = ChoiceItem(
        "geboorte.datum.maand", _("Geboorte > Datumingangonderzoek > Maand")
    )
    geboorte_inOnderzoek_datum = ChoiceItem(
        "geboorte.inOnderzoek.datum", _("Geboorte > Inonderzoek > Datum")
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.dag",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.datum",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "geboorte.inOnderzoek.datumIngangOnderzoek.maand",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    geboorte_inOnderzoek_land = ChoiceItem(
        "geboorte.inOnderzoek.land", _("Geboorte > Inonderzoek > Land")
    )
    geboorte_inOnderzoek_plaats = ChoiceItem(
        "geboorte.inOnderzoek.plaats", _("Geboorte > Inonderzoek > Plaats")
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
        "geheimhoudingPersoonsgegevens", _("Geheimhoudingpersoonsgegevens")
    )
    geslachtsaanduiding = ChoiceItem("geslachtsaanduiding", _("Geslachtsaanduiding"))
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.dag",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.datum",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.maand",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = ChoiceItem(
        "gezagsverhouding.inOnderzoek.indicatieCurateleRegister",
        _("Gezagsverhouding > Inonderzoek > Indicatiecurateleregister"),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = ChoiceItem(
        "gezagsverhouding.inOnderzoek.indicatieGezagMinderjarige",
        _("Gezagsverhouding > Inonderzoek > Indicatiegezagminderjarige"),
    )
    gezagsverhouding_indicatieCurateleRegister = ChoiceItem(
        "gezagsverhouding.indicatieCurateleRegister",
        _("Gezagsverhouding > Indicatiecurateleregister"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = ChoiceItem(
        "gezagsverhouding.indicatieGezagMinderjarige",
        _("Gezagsverhouding > Indicatiegezagminderjarige"),
    )
    inOnderzoek_burgerservicenummer = ChoiceItem(
        "inOnderzoek.burgerservicenummer", _("Inonderzoek > Burgerservicenummer")
    )
    inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.dag",
        _("Inonderzoek > Datumingangonderzoek > Dag"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.datum",
        _("Inonderzoek > Datumingangonderzoek > Datum"),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.jaar",
        _("Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "inOnderzoek.datumIngangOnderzoek.maand",
        _("Inonderzoek > Datumingangonderzoek > Maand"),
    )
    inOnderzoek_geslachtsaanduiding = ChoiceItem(
        "inOnderzoek.geslachtsaanduiding", _("Inonderzoek > Geslachtsaanduiding")
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.dag",
        _("Kiesrecht > Datumingangonderzoek > Dag"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Kiesrecht > Datumingangonderzoek > Datum"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.jaar",
        _("Kiesrecht > Datumingangonderzoek > Jaar"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = ChoiceItem(
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.maand",
        _("Kiesrecht > Datumingangonderzoek > Maand"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.dag",
        _("Kiesrecht > Datumingangonderzoek > Dag"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.datum",
        _("Kiesrecht > Datumingangonderzoek > Datum"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.jaar",
        _("Kiesrecht > Datumingangonderzoek > Jaar"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = ChoiceItem(
        "kiesrecht.einddatumUitsluitingKiesrecht.maand",
        _("Kiesrecht > Datumingangonderzoek > Maand"),
    )
    kiesrecht_europeesKiesrecht = ChoiceItem(
        "kiesrecht.europeesKiesrecht", _("Kiesrecht > Europeeskiesrecht")
    )
    kiesrecht_uitgeslotenVanKiesrecht = ChoiceItem(
        "kiesrecht.uitgeslotenVanKiesrecht", _("Kiesrecht > Uitgeslotenvankiesrecht")
    )
    leeftijd = ChoiceItem("leeftijd", _("Leeftijd"))
    naam_aanduidingNaamgebruik = ChoiceItem(
        "naam.aanduidingNaamgebruik", _("Naam > Aanduidingnaamgebruik")
    )
    naam_aanhef = ChoiceItem("naam.aanhef", _("Naam > Aanhef"))
    naam_aanschrijfwijze = ChoiceItem(
        "naam.aanschrijfwijze", _("Naam > Aanschrijfwijze")
    )
    naam_gebruikInLopendeTekst = ChoiceItem(
        "naam.gebruikInLopendeTekst", _("Naam > Gebruikinlopendetekst")
    )
    naam_geslachtsnaam = ChoiceItem("naam.geslachtsnaam", _("Naam > Geslachtsnaam"))
    naam_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.dag",
        _("Naam > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.datum",
        _("Naam > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Naam > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "naam.inOnderzoek.datumIngangOnderzoek.maand",
        _("Naam > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    naam_inOnderzoek_geslachtsnaam = ChoiceItem(
        "naam.inOnderzoek.geslachtsnaam", _("Naam > Inonderzoek > Geslachtsnaam")
    )
    naam_inOnderzoek_voornamen = ChoiceItem(
        "naam.inOnderzoek.voornamen", _("Naam > Inonderzoek > Voornamen")
    )
    naam_inOnderzoek_voorvoegsel = ChoiceItem(
        "naam.inOnderzoek.voorvoegsel", _("Naam > Inonderzoek > Voorvoegsel")
    )
    naam_voorletters = ChoiceItem("naam.voorletters", _("Naam > Voorletters"))
    naam_voornamen = ChoiceItem("naam.voornamen", _("Naam > Voornamen"))
    naam_voorvoegsel = ChoiceItem("naam.voorvoegsel", _("Naam > Voorvoegsel"))
    opschortingBijhouding_datum_dag = ChoiceItem(
        "opschortingBijhouding.datum.dag",
        _("Opschortingbijhouding > Datumingangonderzoek > Dag"),
    )
    opschortingBijhouding_datum_datum = ChoiceItem(
        "opschortingBijhouding.datum.datum",
        _("Opschortingbijhouding > Datumingangonderzoek > Datum"),
    )
    opschortingBijhouding_datum_jaar = ChoiceItem(
        "opschortingBijhouding.datum.jaar",
        _("Opschortingbijhouding > Datumingangonderzoek > Jaar"),
    )
    opschortingBijhouding_datum_maand = ChoiceItem(
        "opschortingBijhouding.datum.maand",
        _("Opschortingbijhouding > Datumingangonderzoek > Maand"),
    )
    opschortingBijhouding_reden = ChoiceItem(
        "opschortingBijhouding.reden", _("Opschortingbijhouding > Reden")
    )
    overlijden_datum_dag = ChoiceItem(
        "overlijden.datum.dag", _("Overlijden > Datumingangonderzoek > Dag")
    )
    overlijden_datum_datum = ChoiceItem(
        "overlijden.datum.datum", _("Overlijden > Datumingangonderzoek > Datum")
    )
    overlijden_datum_jaar = ChoiceItem(
        "overlijden.datum.jaar", _("Overlijden > Datumingangonderzoek > Jaar")
    )
    overlijden_datum_maand = ChoiceItem(
        "overlijden.datum.maand", _("Overlijden > Datumingangonderzoek > Maand")
    )
    overlijden_inOnderzoek_datum = ChoiceItem(
        "overlijden.inOnderzoek.datum", _("Overlijden > Inonderzoek > Datum")
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.dag",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.datum",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "overlijden.inOnderzoek.datumIngangOnderzoek.maand",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    overlijden_inOnderzoek_land = ChoiceItem(
        "overlijden.inOnderzoek.land", _("Overlijden > Inonderzoek > Land")
    )
    overlijden_inOnderzoek_plaats = ChoiceItem(
        "overlijden.inOnderzoek.plaats", _("Overlijden > Inonderzoek > Plaats")
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
        _("Verblijfplaats > Aanduidingbijhuisnummer"),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = ChoiceItem(
        "verblijfplaats.datumAanvangAdreshouding.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumIngangGeldigheid_dag = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumIngangGeldigheid_datum = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumIngangGeldigheid_maand = ChoiceItem(
        "verblijfplaats.datumIngangGeldigheid.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = ChoiceItem(
        "verblijfplaats.datumInschrijvingInGemeente.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumVestigingInNederland_dag = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumVestigingInNederland_datum = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumVestigingInNederland_jaar = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumVestigingInNederland_maand = ChoiceItem(
        "verblijfplaats.datumVestigingInNederland.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_functieAdres = ChoiceItem(
        "verblijfplaats.functieAdres", _("Verblijfplaats > Functieadres")
    )
    verblijfplaats_gemeenteVanInschrijving_code = ChoiceItem(
        "verblijfplaats.gemeenteVanInschrijving.code", _("Verblijfplaats > Land > Code")
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = ChoiceItem(
        "verblijfplaats.gemeenteVanInschrijving.omschrijving",
        _("Verblijfplaats > Land > Omschrijving"),
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
        _("Verblijfplaats > Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = ChoiceItem(
        "verblijfplaats.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > Identificatiecodenummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = ChoiceItem(
        "verblijfplaats.inOnderzoek.aanduidingBijHuisnummer",
        _("Verblijfplaats > Inonderzoek > Aanduidingbijhuisnummer"),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumAanvangAdreshouding",
        _("Verblijfplaats > Inonderzoek > Datumaanvangadreshouding"),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangGeldigheid",
        _("Verblijfplaats > Inonderzoek > Datuminganggeldigheid"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumInschrijvingInGemeente",
        _("Verblijfplaats > Inonderzoek > Datuminschrijvingingemeente"),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = ChoiceItem(
        "verblijfplaats.inOnderzoek.datumVestigingInNederland",
        _("Verblijfplaats > Inonderzoek > Datumvestiginginnederland"),
    )
    verblijfplaats_inOnderzoek_functieAdres = ChoiceItem(
        "verblijfplaats.inOnderzoek.functieAdres",
        _("Verblijfplaats > Inonderzoek > Functieadres"),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = ChoiceItem(
        "verblijfplaats.inOnderzoek.gemeenteVanInschrijving",
        _("Verblijfplaats > Inonderzoek > Gemeentevaninschrijving"),
    )
    verblijfplaats_inOnderzoek_huisletter = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisletter",
        _("Verblijfplaats > Inonderzoek > Huisletter"),
    )
    verblijfplaats_inOnderzoek_huisnummer = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisnummer",
        _("Verblijfplaats > Inonderzoek > Huisnummer"),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = ChoiceItem(
        "verblijfplaats.inOnderzoek.huisnummertoevoeging",
        _("Verblijfplaats > Inonderzoek > Huisnummertoevoeging"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "verblijfplaats.inOnderzoek.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > Inonderzoek > Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = ChoiceItem(
        "verblijfplaats.inOnderzoek.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > Inonderzoek > Identificatiecodenummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = ChoiceItem(
        "verblijfplaats.inOnderzoek.landVanwaarIngeschreven",
        _("Verblijfplaats > Inonderzoek > Landvanwaaringeschreven"),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = ChoiceItem(
        "verblijfplaats.inOnderzoek.locatiebeschrijving",
        _("Verblijfplaats > Inonderzoek > Locatiebeschrijving"),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = ChoiceItem(
        "verblijfplaats.inOnderzoek.naamOpenbareRuimte",
        _("Verblijfplaats > Inonderzoek > Naamopenbareruimte"),
    )
    verblijfplaats_inOnderzoek_postcode = ChoiceItem(
        "verblijfplaats.inOnderzoek.postcode",
        _("Verblijfplaats > Inonderzoek > Postcode"),
    )
    verblijfplaats_inOnderzoek_straat = ChoiceItem(
        "verblijfplaats.inOnderzoek.straat",
        _("Verblijfplaats > Inonderzoek > Straat"),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = ChoiceItem(
        "verblijfplaats.inOnderzoek.verblijfBuitenland",
        _("Verblijfplaats > Inonderzoek > Verblijfbuitenland"),
    )
    verblijfplaats_inOnderzoek_woonplaats = ChoiceItem(
        "verblijfplaats.inOnderzoek.woonplaats",
        _("Verblijfplaats > Inonderzoek > Woonplaats"),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = ChoiceItem(
        "verblijfplaats.indicatieVestigingVanuitBuitenland",
        _("Verblijfplaats > Indicatievestigingvanuitbuitenland"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = ChoiceItem(
        "verblijfplaats.landVanwaarIngeschreven.code", _("Verblijfplaats > Land > Code")
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = ChoiceItem(
        "verblijfplaats.landVanwaarIngeschreven.omschrijving",
        _("Verblijfplaats > Land > Omschrijving"),
    )
    verblijfplaats_locatiebeschrijving = ChoiceItem(
        "verblijfplaats.locatiebeschrijving", _("Verblijfplaats > Locatiebeschrijving")
    )
    verblijfplaats_naamOpenbareRuimte = ChoiceItem(
        "verblijfplaats.naamOpenbareRuimte", _("Verblijfplaats > Naamopenbareruimte")
    )
    verblijfplaats_postcode = ChoiceItem(
        "verblijfplaats.postcode", _("Verblijfplaats > Postcode")
    )
    verblijfplaats_straat = ChoiceItem(
        "verblijfplaats.straat", _("Verblijfplaats > Straat")
    )
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = ChoiceItem(
        "verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        _("Verblijfplaats > Vanuitvertrokkenonbekendwaarheen"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel1",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel2",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.adresRegel3",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.land.code",
        _("Verblijfplaats > Verblijfbuitenland > Land > Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.land.omschrijving",
        _("Verblijfplaats > Verblijfbuitenland > Land > Omschrijving"),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = ChoiceItem(
        "verblijfplaats.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        _("Verblijfplaats > Verblijfbuitenland > Vertrokkenonbekendwaarheen"),
    )
    verblijfplaats_woonplaats = ChoiceItem(
        "verblijfplaats.woonplaats", _("Verblijfplaats > Woonplaats")
    )
    verblijfstitel_aanduiding_code = ChoiceItem(
        "verblijfstitel.aanduiding.code", _("Verblijfstitel > Land > Code")
    )
    verblijfstitel_aanduiding_omschrijving = ChoiceItem(
        "verblijfstitel.aanduiding.omschrijving",
        _("Verblijfstitel > Land > Omschrijving"),
    )
    verblijfstitel_datumEinde_dag = ChoiceItem(
        "verblijfstitel.datumEinde.dag",
        _("Verblijfstitel > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_datumEinde_datum = ChoiceItem(
        "verblijfstitel.datumEinde.datum",
        _("Verblijfstitel > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_datumEinde_jaar = ChoiceItem(
        "verblijfstitel.datumEinde.jaar",
        _("Verblijfstitel > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_datumEinde_maand = ChoiceItem(
        "verblijfstitel.datumEinde.maand",
        _("Verblijfstitel > Datumingangonderzoek > Maand"),
    )
    verblijfstitel_datumIngang_dag = ChoiceItem(
        "verblijfstitel.datumIngang.dag",
        _("Verblijfstitel > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_datumIngang_datum = ChoiceItem(
        "verblijfstitel.datumIngang.datum",
        _("Verblijfstitel > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_datumIngang_jaar = ChoiceItem(
        "verblijfstitel.datumIngang.jaar",
        _("Verblijfstitel > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_datumIngang_maand = ChoiceItem(
        "verblijfstitel.datumIngang.maand",
        _("Verblijfstitel > Datumingangonderzoek > Maand"),
    )
    verblijfstitel_inOnderzoek_aanduiding = ChoiceItem(
        "verblijfstitel.inOnderzoek.aanduiding",
        _("Verblijfstitel > Inonderzoek > Aanduiding"),
    )
    verblijfstitel_inOnderzoek_datumEinde = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumEinde",
        _("Verblijfstitel > Inonderzoek > Datumeinde"),
    )
    verblijfstitel_inOnderzoek_datumIngang = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngang",
        _("Verblijfstitel > Inonderzoek > Datumingang"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Maand"),
    )
