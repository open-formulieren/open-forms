from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    # schema: http://localhost:8021/api/schema/openapi.yaml
    # path:   /ingeschrevenpersonen/{burgerservicenummer}

    burgerservicenummer = ChoiceItem("burgerservicenummer", _("Citizen service number"))
    datumEersteInschrijvingGBA_dag = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.dag",
        _("Date of entry inquiryingang > Day"),
    )
    datumEersteInschrijvingGBA_datum = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.datum",
        _("Date of entry inquiryingang > Date"),
    )
    datumEersteInschrijvingGBA_jaar = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.jaar",
        _("Date of entry inquiryingang > Year"),
    )
    datumEersteInschrijvingGBA_maand = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.maand",
        _("Date of entry inquiryingang > Month"),
    )
    geboorte_datum_dag = ChoiceItem(
        "_embedded.geboorte._embedded.datum.dag",
        _("Birth > Date of entry inquiryingang > Day"),
    )
    geboorte_datum_datum = ChoiceItem(
        "_embedded.geboorte._embedded.datum.datum",
        _("Birth > Date of entry inquiryingang > Date"),
    )
    geboorte_datum_jaar = ChoiceItem(
        "_embedded.geboorte._embedded.datum.jaar",
        _("Birth > Date of entry inquiryingang > Year"),
    )
    geboorte_datum_maand = ChoiceItem(
        "_embedded.geboorte._embedded.datum.maand",
        _("Birth > Date of entry inquiryingang > Month"),
    )
    geboorte_inOnderzoek_datum = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.datum",
        _("Birth > In research > Date"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("Birth > In research > Date of entry inquiryingang > Day"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Birth > In research > Date of entry inquiryingang > Date"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("Birth > In research > Date of entry inquiryingang > Year"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("Birth > In research > Date of entry inquiryingang > Month"),
    )
    geboorte_inOnderzoek_land = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.land",
        _("Birth > In research > Country"),
    )
    geboorte_inOnderzoek_plaats = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.plaats",
        _("Birth > In research > Place"),
    )
    geboorte_land_code = ChoiceItem(
        "_embedded.geboorte._embedded.land.code", _("Birth > Country > Code")
    )
    geboorte_land_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.land.omschrijving",
        _("Birth > Country > Description"),
    )
    geboorte_plaats_code = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.code", _("Birth > Country > Code")
    )
    geboorte_plaats_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.omschrijving",
        _("Birth > Country > Description"),
    )
    geheimhoudingPersoonsgegevens = ChoiceItem(
        "geheimhoudingPersoonsgegevens", _("Confidentiality of data")
    )
    geslachtsaanduiding = ChoiceItem("geslachtsaanduiding", _("Gender designation"))
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _(
            "Relationship of authority > In research > Date of entry inquiryingang > Day"
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _(
            "Relationship of authority > In research > Date of entry inquiryingang > Date"
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _(
            "Relationship of authority > In research > Date of entry inquiryingang > Year"
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _(
            "Relationship of authority > In research > Date of entry inquiryingang > Month"
        ),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek.indicatieCurateleRegister",
        _("Relationship of authority > In research > Indication guardianship register"),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek.indicatieGezagMinderjarige",
        _("Relationship of authority > In research > Indication authority minor"),
    )
    gezagsverhouding_indicatieCurateleRegister = ChoiceItem(
        "_embedded.gezagsverhouding.indicatieCurateleRegister",
        _("Relationship of authority > Indication guardianship register"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = ChoiceItem(
        "_embedded.gezagsverhouding.indicatieGezagMinderjarige",
        _("Relationship of authority > Indication authority minor"),
    )
    inOnderzoek_burgerservicenummer = ChoiceItem(
        "_embedded.inOnderzoek.burgerservicenummer",
        _("In research > Citizen service number"),
    )
    inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("In research > Date of entry inquiryingang > Day"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("In research > Date of entry inquiryingang > Date"),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("In research > Date of entry inquiryingang > Year"),
    )
    inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("In research > Date of entry inquiryingang > Month"),
    )
    inOnderzoek_geslachtsaanduiding = ChoiceItem(
        "_embedded.inOnderzoek.geslachtsaanduiding",
        _("In research > Gender designation"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.dag",
        _("Right to vote > Date of entry inquiryingang > Day"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Right to vote > Date of entry inquiryingang > Date"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.jaar",
        _("Right to vote > Date of entry inquiryingang > Year"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.maand",
        _("Right to vote > Date of entry inquiryingang > Month"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.dag",
        _("Right to vote > Date of entry inquiryingang > Day"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.datum",
        _("Right to vote > Date of entry inquiryingang > Date"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.jaar",
        _("Right to vote > Date of entry inquiryingang > Year"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.maand",
        _("Right to vote > Date of entry inquiryingang > Month"),
    )
    kiesrecht_europeesKiesrecht = ChoiceItem(
        "_embedded.kiesrecht.europeesKiesrecht", _("Right to vote > European suffrage")
    )
    kiesrecht_uitgeslotenVanKiesrecht = ChoiceItem(
        "_embedded.kiesrecht.uitgeslotenVanKiesrecht",
        _("Right to vote > Excluded from suffrage"),
    )
    leeftijd = ChoiceItem("leeftijd", _("Age"))
    naam_aanduidingNaamgebruik = ChoiceItem(
        "_embedded.naam.aanduidingNaamgebruik", _("Name > Indication of name usage")
    )
    naam_aanhef = ChoiceItem("_embedded.naam.aanhef", _("Name > Salutation"))
    naam_aanschrijfwijze = ChoiceItem(
        "_embedded.naam.aanschrijfwijze", _("Name > Notification")
    )
    naam_gebruikInLopendeTekst = ChoiceItem(
        "_embedded.naam.gebruikInLopendeTekst", _("Name > Use in text")
    )
    naam_geslachtsnaam = ChoiceItem(
        "_embedded.naam.geslachtsnaam", _("Name > Last name")
    )
    naam_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("Name > In research > Date of entry inquiryingang > Day"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Name > In research > Date of entry inquiryingang > Date"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("Name > In research > Date of entry inquiryingang > Year"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("Name > In research > Date of entry inquiryingang > Month"),
    )
    naam_inOnderzoek_geslachtsnaam = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.geslachtsnaam",
        _("Name > In research > Last name"),
    )
    naam_inOnderzoek_voornamen = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.voornamen",
        _("Name > In research > First names"),
    )
    naam_inOnderzoek_voorvoegsel = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.voorvoegsel",
        _("Name > In research > Prefix"),
    )
    naam_voorletters = ChoiceItem("_embedded.naam.voorletters", _("Name > Initials"))
    naam_voornamen = ChoiceItem("_embedded.naam.voornamen", _("Name > First names"))
    naam_voorvoegsel = ChoiceItem("_embedded.naam.voorvoegsel", _("Name > Prefix"))
    opschortingBijhouding_datum_dag = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.dag",
        _("Suspension Tracking > Date of entry inquiryingang > Day"),
    )
    opschortingBijhouding_datum_datum = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.datum",
        _("Suspension Tracking > Date of entry inquiryingang > Date"),
    )
    opschortingBijhouding_datum_jaar = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.jaar",
        _("Suspension Tracking > Date of entry inquiryingang > Year"),
    )
    opschortingBijhouding_datum_maand = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.maand",
        _("Suspension Tracking > Date of entry inquiryingang > Month"),
    )
    opschortingBijhouding_reden = ChoiceItem(
        "_embedded.opschortingBijhouding.reden", _("Suspension Tracking > Reason")
    )
    overlijden_datum_dag = ChoiceItem(
        "_embedded.overlijden._embedded.datum.dag",
        _("Passed away > Date of entry inquiryingang > Day"),
    )
    overlijden_datum_datum = ChoiceItem(
        "_embedded.overlijden._embedded.datum.datum",
        _("Passed away > Date of entry inquiryingang > Date"),
    )
    overlijden_datum_jaar = ChoiceItem(
        "_embedded.overlijden._embedded.datum.jaar",
        _("Passed away > Date of entry inquiryingang > Year"),
    )
    overlijden_datum_maand = ChoiceItem(
        "_embedded.overlijden._embedded.datum.maand",
        _("Passed away > Date of entry inquiryingang > Month"),
    )
    overlijden_inOnderzoek_datum = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.datum",
        _("Passed away > In research > Date"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("Passed away > In research > Date of entry inquiryingang > Day"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Passed away > In research > Date of entry inquiryingang > Date"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("Passed away > In research > Date of entry inquiryingang > Year"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("Passed away > In research > Date of entry inquiryingang > Month"),
    )
    overlijden_inOnderzoek_land = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.land",
        _("Passed away > In research > Country"),
    )
    overlijden_inOnderzoek_plaats = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.plaats",
        _("Passed away > In research > Place"),
    )
    overlijden_indicatieOverleden = ChoiceItem(
        "_embedded.overlijden.indicatieOverleden",
        _("Passed away > Indication deceased"),
    )
    overlijden_land_code = ChoiceItem(
        "_embedded.overlijden._embedded.land.code", _("Passed away > Country > Code")
    )
    overlijden_land_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.land.omschrijving",
        _("Passed away > Country > Description"),
    )
    overlijden_plaats_code = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.code", _("Passed away > Country > Code")
    )
    overlijden_plaats_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.omschrijving",
        _("Passed away > Country > Description"),
    )
    verblijfplaats_aanduidingBijHuisnummer = ChoiceItem(
        "_embedded.verblijfplaats.aanduidingBijHuisnummer",
        _("Where to stay > Indication of house number"),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.dag",
        _("Where to stay > Date of entry inquiryingang > Day"),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.datum",
        _("Where to stay > Date of entry inquiryingang > Date"),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.jaar",
        _("Where to stay > Date of entry inquiryingang > Year"),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.maand",
        _("Where to stay > Date of entry inquiryingang > Month"),
    )
    verblijfplaats_datumIngangGeldigheid_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.dag",
        _("Where to stay > Date of entry inquiryingang > Day"),
    )
    verblijfplaats_datumIngangGeldigheid_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.datum",
        _("Where to stay > Date of entry inquiryingang > Date"),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.jaar",
        _("Where to stay > Date of entry inquiryingang > Year"),
    )
    verblijfplaats_datumIngangGeldigheid_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.maand",
        _("Where to stay > Date of entry inquiryingang > Month"),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.dag",
        _("Where to stay > Date of entry inquiryingang > Day"),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.datum",
        _("Where to stay > Date of entry inquiryingang > Date"),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.jaar",
        _("Where to stay > Date of entry inquiryingang > Year"),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.maand",
        _("Where to stay > Date of entry inquiryingang > Month"),
    )
    verblijfplaats_datumVestigingInNederland_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.dag",
        _("Where to stay > Date of entry inquiryingang > Day"),
    )
    verblijfplaats_datumVestigingInNederland_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.datum",
        _("Where to stay > Date of entry inquiryingang > Date"),
    )
    verblijfplaats_datumVestigingInNederland_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.jaar",
        _("Where to stay > Date of entry inquiryingang > Year"),
    )
    verblijfplaats_datumVestigingInNederland_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.maand",
        _("Where to stay > Date of entry inquiryingang > Month"),
    )
    verblijfplaats_functieAdres = ChoiceItem(
        "_embedded.verblijfplaats.functieAdres", _("Where to stay > Function address")
    )
    verblijfplaats_gemeenteVanInschrijving_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.code",
        _("Where to stay > Country > Code"),
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.omschrijving",
        _("Where to stay > Country > Description"),
    )
    verblijfplaats_huisletter = ChoiceItem(
        "_embedded.verblijfplaats.huisletter", _("Where to stay > House letter")
    )
    verblijfplaats_huisnummer = ChoiceItem(
        "_embedded.verblijfplaats.huisnummer", _("Where to stay > House number")
    )
    verblijfplaats_huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats.huisnummertoevoeging",
        _("Where to stay > House number addition"),
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeAdresseerbaarObject",
        _("Where to stay > Identifier AddressableObject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeNummeraanduiding",
        _("Where to stay > Identification code number designation"),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.aanduidingBijHuisnummer",
        _("Where to stay > In research > Indication of house number"),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumAanvangAdreshouding",
        _("Where to stay > In research > Date of commencement of address holding"),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumIngangGeldigheid",
        _("Where to stay > In research > Date Effectiveness"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("Where to stay > In research > Date of entry inquiryingang > Day"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Where to stay > In research > Date of entry inquiryingang > Date"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("Where to stay > In research > Date of entry inquiryingang > Year"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("Where to stay > In research > Date of entry inquiryingang > Month"),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumInschrijvingInGemeente",
        _("Where to stay > In research > Date of registration in the municipality"),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumVestigingInNederland",
        _("Where to stay > In research > Date settlement in the Netherlands"),
    )
    verblijfplaats_inOnderzoek_functieAdres = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.functieAdres",
        _("Where to stay > In research > Function address"),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.gemeenteVanInschrijving",
        _("Where to stay > In research > Municipal registration"),
    )
    verblijfplaats_inOnderzoek_huisletter = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisletter",
        _("Where to stay > In research > House letter"),
    )
    verblijfplaats_inOnderzoek_huisnummer = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisnummer",
        _("Where to stay > In research > House number"),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisnummertoevoeging",
        _("Where to stay > In research > House number addition"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.identificatiecodeAdresseerbaarObject",
        _("Where to stay > In research > Identifier AddressableObject"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.identificatiecodeNummeraanduiding",
        _("Where to stay > In research > Identification code number designation"),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.landVanwaarIngeschreven",
        _("Where to stay > In research > Country of registration"),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.locatiebeschrijving",
        _("Where to stay > In research > Location description"),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.naamOpenbareRuimte",
        _("Where to stay > In research > Name public space"),
    )
    verblijfplaats_inOnderzoek_postcode = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.postcode",
        _("Where to stay > In research > Postal Code"),
    )
    verblijfplaats_inOnderzoek_straatnaam = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.straatnaam",
        _("Where to stay > In research > Street name"),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.verblijfBuitenland",
        _("Where to stay > In research > Abroad"),
    )
    verblijfplaats_inOnderzoek_woonplaatsnaam = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.woonplaatsnaam",
        _("Where to stay > In research > City name"),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = ChoiceItem(
        "_embedded.verblijfplaats.indicatieVestigingVanuitBuitenland",
        _("Where to stay > Indication establishment from abroad"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.code",
        _("Where to stay > Country > Code"),
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.omschrijving",
        _("Where to stay > Country > Description"),
    )
    verblijfplaats_locatiebeschrijving = ChoiceItem(
        "_embedded.verblijfplaats.locatiebeschrijving",
        _("Where to stay > Location description"),
    )
    verblijfplaats_naamOpenbareRuimte = ChoiceItem(
        "_embedded.verblijfplaats.naamOpenbareRuimte",
        _("Where to stay > Name public space"),
    )
    verblijfplaats_postcode = ChoiceItem(
        "_embedded.verblijfplaats.postcode", _("Where to stay > Postal Code")
    )
    verblijfplaats_straatnaam = ChoiceItem(
        "_embedded.verblijfplaats.straatnaam", _("Where to stay > Street name")
    )
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = ChoiceItem(
        "_embedded.verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        _("Where to stay > Departed unknown destination"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel1",
        _("Where to stay > Abroad > Address Line 1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel2",
        _("Where to stay > Abroad > Address Line 2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel3",
        _("Where to stay > Abroad > Address Line 3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.code",
        _("Where to stay > Abroad > Country > Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.omschrijving",
        _("Where to stay > Abroad > Country > Description"),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        _("Where to stay > Abroad > Departed known destination"),
    )
    verblijfplaats_woonplaatsnaam = ChoiceItem(
        "_embedded.verblijfplaats.woonplaatsnaam", _("Where to stay > City name")
    )
    verblijfstitel_aanduiding_code = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.code",
        _("Residence permit > Country > Code"),
    )
    verblijfstitel_aanduiding_omschrijving = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.omschrijving",
        _("Residence permit > Country > Description"),
    )
    verblijfstitel_datumEinde_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.dag",
        _("Residence permit > Date of entry inquiryingang > Day"),
    )
    verblijfstitel_datumEinde_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.datum",
        _("Residence permit > Date of entry inquiryingang > Date"),
    )
    verblijfstitel_datumEinde_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.jaar",
        _("Residence permit > Date of entry inquiryingang > Year"),
    )
    verblijfstitel_datumEinde_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.maand",
        _("Residence permit > Date of entry inquiryingang > Month"),
    )
    verblijfstitel_datumIngang_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.dag",
        _("Residence permit > Date of entry inquiryingang > Day"),
    )
    verblijfstitel_datumIngang_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.datum",
        _("Residence permit > Date of entry inquiryingang > Date"),
    )
    verblijfstitel_datumIngang_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.jaar",
        _("Residence permit > Date of entry inquiryingang > Year"),
    )
    verblijfstitel_datumIngang_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.maand",
        _("Residence permit > Date of entry inquiryingang > Month"),
    )
    verblijfstitel_inOnderzoek_aanduiding = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.aanduiding",
        _("Residence permit > In research > Designation"),
    )
    verblijfstitel_inOnderzoek_datumEinde = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.datumEinde",
        _("Residence permit > In research > End date"),
    )
    verblijfstitel_inOnderzoek_datumIngang = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.datumIngang",
        _("Residence permit > In research > Date entry"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        _("Residence permit > In research > Date of entry inquiryingang > Day"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Residence permit > In research > Date of entry inquiryingang > Date"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        _("Residence permit > In research > Date of entry inquiryingang > Year"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        _("Residence permit > In research > Date of entry inquiryingang > Month"),
    )
