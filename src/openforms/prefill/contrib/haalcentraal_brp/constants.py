from django.db import models
from django.utils.translation import gettext_lazy as _


class AttributesV1(models.TextChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://op.open-forms.test.maykin.opengem.nl/api/schema/openapi.yaml
    path:    /ingeschrevenpersonen/{burgerservicenummer}
    """

    burgerservicenummer = "burgerservicenummer", _("Burgerservicenummer")
    datumEersteInschrijvingGBA_dag = (
        "datumEersteInschrijvingGBA.dag",
        _("DatumEersteInschrijvingGBA > Dag"),
    )
    datumEersteInschrijvingGBA_datum = (
        "datumEersteInschrijvingGBA.datum",
        _("DatumEersteInschrijvingGBA > Datum"),
    )
    datumEersteInschrijvingGBA_jaar = (
        "datumEersteInschrijvingGBA.jaar",
        _("DatumEersteInschrijvingGBA > Jaar"),
    )
    datumEersteInschrijvingGBA_maand = (
        "datumEersteInschrijvingGBA.maand",
        _("DatumEersteInschrijvingGBA > Maand"),
    )
    geboorte_datum_dag = "geboorte.datum.dag", _("Geboorte > Datum > Dag")
    geboorte_datum_datum = "geboorte.datum.datum", _("Geboorte > Datum > Datum")
    geboorte_datum_jaar = "geboorte.datum.jaar", _("Geboorte > Datum > Jaar")
    geboorte_datum_maand = "geboorte.datum.maand", _("Geboorte > Datum > Maand")
    geboorte_inOnderzoek_datum = (
        "geboorte.inOnderzoek.datum",
        _("Geboorte > InOnderzoek > Datum"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.dag",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.datum",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.maand",
        _("Geboorte > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    geboorte_inOnderzoek_land = (
        "geboorte.inOnderzoek.land",
        _("Geboorte > InOnderzoek > Land"),
    )
    geboorte_inOnderzoek_plaats = (
        "geboorte.inOnderzoek.plaats",
        _("Geboorte > InOnderzoek > Plaats"),
    )
    geboorte_land_code = "geboorte.land.code", _("Geboorte > Land > Code")
    geboorte_land_omschrijving = (
        "geboorte.land.omschrijving",
        _("Geboorte > Land > Omschrijving"),
    )
    geboorte_plaats_code = "geboorte.plaats.code", _("Geboorte > Land > Code")
    geboorte_plaats_omschrijving = (
        "geboorte.plaats.omschrijving",
        _("Geboorte > Land > Omschrijving"),
    )
    geheimhoudingPersoonsgegevens = (
        "geheimhoudingPersoonsgegevens",
        _("GeheimhoudingPersoonsgegevens"),
    )
    geslachtsaanduiding = "geslachtsaanduiding", _("Geslachtsaanduiding")
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.dag",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.datum",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.maand",
        _("Gezagsverhouding > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = (
        "gezagsverhouding.inOnderzoek.indicatieCurateleRegister",
        _("Gezagsverhouding > InOnderzoek > IndicatieCurateleRegister"),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = (
        "gezagsverhouding.inOnderzoek.indicatieGezagMinderjarige",
        _("Gezagsverhouding > InOnderzoek > IndicatieGezagMinderjarige"),
    )
    gezagsverhouding_indicatieCurateleRegister = (
        "gezagsverhouding.indicatieCurateleRegister",
        _("Gezagsverhouding > IndicatieCurateleRegister"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = (
        "gezagsverhouding.indicatieGezagMinderjarige",
        _("Gezagsverhouding > IndicatieGezagMinderjarige"),
    )
    inOnderzoek_burgerservicenummer = (
        "inOnderzoek.burgerservicenummer",
        _("InOnderzoek > Burgerservicenummer"),
    )
    inOnderzoek_datumIngangOnderzoek_dag = (
        "inOnderzoek.datumIngangOnderzoek.dag",
        _("InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = (
        "inOnderzoek.datumIngangOnderzoek.datum",
        _("InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = (
        "inOnderzoek.datumIngangOnderzoek.jaar",
        _("InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    inOnderzoek_datumIngangOnderzoek_maand = (
        "inOnderzoek.datumIngangOnderzoek.maand",
        _("InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    inOnderzoek_geslachtsaanduiding = (
        "inOnderzoek.geslachtsaanduiding",
        _("InOnderzoek > Geslachtsaanduiding"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.dag",
        _("Kiesrecht > DatumIngangOnderzoek > Dag"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Datum"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.jaar",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Jaar"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.maand",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Maand"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = (
        "kiesrecht.einddatumUitsluitingKiesrecht.dag",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Dag"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = (
        "kiesrecht.einddatumUitsluitingKiesrecht.datum",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Datum"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = (
        "kiesrecht.einddatumUitsluitingKiesrecht.jaar",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Jaar"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = (
        "kiesrecht.einddatumUitsluitingKiesrecht.maand",
        _("Kiesrecht > EinddatumUitsluitingEuropeesKiesrecht > Maand"),
    )
    kiesrecht_europeesKiesrecht = (
        "kiesrecht.europeesKiesrecht",
        _("Kiesrecht > EuropeesKiesrecht"),
    )
    kiesrecht_uitgeslotenVanKiesrecht = (
        "kiesrecht.uitgeslotenVanKiesrecht",
        _("Kiesrecht > UitgeslotenVanKiesrecht"),
    )
    leeftijd = "leeftijd", _("Leeftijd")
    naam_aanduidingNaamgebruik = (
        "naam.aanduidingNaamgebruik",
        _("Naam > AanduidingNaamgebruik"),
    )
    naam_aanhef = "naam.aanhef", _("Naam > Aanhef")
    naam_aanschrijfwijze = "naam.aanschrijfwijze", _("Naam > Aanschrijfwijze")
    naam_gebruikInLopendeTekst = (
        "naam.gebruikInLopendeTekst",
        _("Naam > GebruikInLopendeTekst"),
    )
    naam_geslachtsnaam = "naam.geslachtsnaam", _("Naam > Geslachtsnaam")
    naam_inOnderzoek_datumIngangOnderzoek_dag = (
        "naam.inOnderzoek.datumIngangOnderzoek.dag",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = (
        "naam.inOnderzoek.datumIngangOnderzoek.datum",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = (
        "naam.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = (
        "naam.inOnderzoek.datumIngangOnderzoek.maand",
        _("Naam > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    naam_inOnderzoek_geslachtsnaam = (
        "naam.inOnderzoek.geslachtsnaam",
        _("Naam > InOnderzoek > Geslachtsnaam"),
    )
    naam_inOnderzoek_voornamen = (
        "naam.inOnderzoek.voornamen",
        _("Naam > InOnderzoek > Voornamen"),
    )
    naam_inOnderzoek_voorvoegsel = (
        "naam.inOnderzoek.voorvoegsel",
        _("Naam > InOnderzoek > Voorvoegsel"),
    )
    naam_voorletters = "naam.voorletters", _("Naam > Voorletters")
    naam_voornamen = "naam.voornamen", _("Naam > Voornamen")
    naam_voorvoegsel = "naam.voorvoegsel", _("Naam > Voorvoegsel")
    opschortingBijhouding_datum_dag = (
        "opschortingBijhouding.datum.dag",
        _("OpschortingBijhouding > Datum > Dag"),
    )
    opschortingBijhouding_datum_datum = (
        "opschortingBijhouding.datum.datum",
        _("OpschortingBijhouding > Datum > Datum"),
    )
    opschortingBijhouding_datum_jaar = (
        "opschortingBijhouding.datum.jaar",
        _("OpschortingBijhouding > Datum > Jaar"),
    )
    opschortingBijhouding_datum_maand = (
        "opschortingBijhouding.datum.maand",
        _("OpschortingBijhouding > Datum > Maand"),
    )
    opschortingBijhouding_reden = (
        "opschortingBijhouding.reden",
        _("OpschortingBijhouding > Reden"),
    )
    overlijden_datum_dag = "overlijden.datum.dag", _("Overlijden > Datum > Dag")
    overlijden_datum_datum = "overlijden.datum.datum", _("Overlijden > Datum > Datum")
    overlijden_datum_jaar = "overlijden.datum.jaar", _("Overlijden > Datum > Jaar")
    overlijden_datum_maand = "overlijden.datum.maand", _("Overlijden > Datum > Maand")
    overlijden_inOnderzoek_datum = (
        "overlijden.inOnderzoek.datum",
        _("Overlijden > InOnderzoek > Datum"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.dag",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.datum",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.maand",
        _("Overlijden > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    overlijden_inOnderzoek_land = (
        "overlijden.inOnderzoek.land",
        _("Overlijden > InOnderzoek > Land"),
    )
    overlijden_inOnderzoek_plaats = (
        "overlijden.inOnderzoek.plaats",
        _("Overlijden > InOnderzoek > Plaats"),
    )
    overlijden_indicatieOverleden = (
        "overlijden.indicatieOverleden",
        _("Overlijden > IndicatieOverleden"),
    )
    overlijden_land_code = "overlijden.land.code", _("Overlijden > Land > Code")
    overlijden_land_omschrijving = (
        "overlijden.land.omschrijving",
        _("Overlijden > Land > Omschrijving"),
    )
    overlijden_plaats_code = "overlijden.plaats.code", _("Overlijden > Land > Code")
    overlijden_plaats_omschrijving = (
        "overlijden.plaats.omschrijving",
        _("Overlijden > Land > Omschrijving"),
    )
    verblijfplaats_aanduidingBijHuisnummer = (
        "verblijfplaats.aanduidingBijHuisnummer",
        _("Verblijfplaats > AanduidingBijHuisnummer"),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = (
        "verblijfplaats.datumAanvangAdreshouding.dag",
        _("Verblijfplaats > DatumAanvangAdreshouding > Dag"),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = (
        "verblijfplaats.datumAanvangAdreshouding.datum",
        _("Verblijfplaats > DatumAanvangAdreshouding > Datum"),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = (
        "verblijfplaats.datumAanvangAdreshouding.jaar",
        _("Verblijfplaats > DatumAanvangAdreshouding > Jaar"),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = (
        "verblijfplaats.datumAanvangAdreshouding.maand",
        _("Verblijfplaats > DatumAanvangAdreshouding > Maand"),
    )
    verblijfplaats_datumIngangGeldigheid_dag = (
        "verblijfplaats.datumIngangGeldigheid.dag",
        _("Verblijfplaats > DatumIngangGeldigheid > Dag"),
    )
    verblijfplaats_datumIngangGeldigheid_datum = (
        "verblijfplaats.datumIngangGeldigheid.datum",
        _("Verblijfplaats > DatumIngangGeldigheid > Datum"),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = (
        "verblijfplaats.datumIngangGeldigheid.jaar",
        _("Verblijfplaats > DatumIngangGeldigheid > Jaar"),
    )
    verblijfplaats_datumIngangGeldigheid_maand = (
        "verblijfplaats.datumIngangGeldigheid.maand",
        _("Verblijfplaats > DatumIngangGeldigheid > Maand"),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = (
        "verblijfplaats.datumInschrijvingInGemeente.dag",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Dag"),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = (
        "verblijfplaats.datumInschrijvingInGemeente.datum",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Datum"),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = (
        "verblijfplaats.datumInschrijvingInGemeente.jaar",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Jaar"),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = (
        "verblijfplaats.datumInschrijvingInGemeente.maand",
        _("Verblijfplaats > DatumInschrijvingInGemeente > Maand"),
    )
    verblijfplaats_datumVestigingInNederland_dag = (
        "verblijfplaats.datumVestigingInNederland.dag",
        _("Verblijfplaats > DatumIngangOnderzoek > Dag"),
    )
    verblijfplaats_datumVestigingInNederland_datum = (
        "verblijfplaats.datumVestigingInNederland.datum",
        _("Verblijfplaats > DatumVestigingInNederland > Datum"),
    )
    verblijfplaats_datumVestigingInNederland_jaar = (
        "verblijfplaats.datumVestigingInNederland.jaar",
        _("Verblijfplaats > DatumVestigingInNederland > Jaar"),
    )
    verblijfplaats_datumVestigingInNederland_maand = (
        "verblijfplaats.datumVestigingInNederland.maand",
        _("Verblijfplaats > DatumVestigingInNederland > Maand"),
    )
    verblijfplaats_functieAdres = (
        "verblijfplaats.functieAdres",
        _("Verblijfplaats > FunctieAdres"),
    )
    verblijfplaats_gemeenteVanInschrijving_code = (
        "verblijfplaats.gemeenteVanInschrijving.code",
        _("Verblijfplaats > GemeenteVanInschrijving > Code"),
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = (
        "verblijfplaats.gemeenteVanInschrijving.omschrijving",
        _("Verblijfplaats > GemeenteVanInschrijving > Omschrijving"),
    )
    verblijfplaats_huisletter = (
        "verblijfplaats.huisletter",
        _("Verblijfplaats > Huisletter"),
    )
    verblijfplaats_huisnummer = (
        "verblijfplaats.huisnummer",
        _("Verblijfplaats > Huisnummer"),
    )
    verblijfplaats_huisnummertoevoeging = (
        "verblijfplaats.huisnummertoevoeging",
        _("Verblijfplaats > Huisnummertoevoeging"),
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = (
        "verblijfplaats.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > IdentificatiecodeAdresseerbaarObject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = (
        "verblijfplaats.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > IdentificatiecodeNummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = (
        "verblijfplaats.inOnderzoek.aanduidingBijHuisnummer",
        _("Verblijfplaats > InOnderzoek > AanduidingBijHuisnummer"),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = (
        "verblijfplaats.inOnderzoek.datumAanvangAdreshouding",
        _("Verblijfplaats > InOnderzoek > DatumAanvangAdreshouding"),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = (
        "verblijfplaats.inOnderzoek.datumIngangGeldigheid",
        _("Verblijfplaats > InOnderzoek > DatumIngangGeldigheid"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfplaats > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = (
        "verblijfplaats.inOnderzoek.datumInschrijvingInGemeente",
        _("Verblijfplaats > InOnderzoek > DatumInschrijvingInGemeente"),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = (
        "verblijfplaats.inOnderzoek.datumVestigingInNederland",
        _("Verblijfplaats > InOnderzoek > DatumVestigingInNederland"),
    )
    verblijfplaats_inOnderzoek_functieAdres = (
        "verblijfplaats.inOnderzoek.functieAdres",
        _("Verblijfplaats > InOnderzoek > Functieadres"),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = (
        "verblijfplaats.inOnderzoek.gemeenteVanInschrijving",
        _("Verblijfplaats > InOnderzoek > GemeenteVanInschrijving"),
    )
    verblijfplaats_inOnderzoek_huisletter = (
        "verblijfplaats.inOnderzoek.huisletter",
        _("Verblijfplaats > InOnderzoek > Huisletter"),
    )
    verblijfplaats_inOnderzoek_huisnummer = (
        "verblijfplaats.inOnderzoek.huisnummer",
        _("Verblijfplaats > InOnderzoek > Huisnummer"),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = (
        "verblijfplaats.inOnderzoek.huisnummertoevoeging",
        _("Verblijfplaats > InOnderzoek > Huisnummertoevoeging"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = (
        "verblijfplaats.inOnderzoek.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > InOnderzoek > Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = (
        "verblijfplaats.inOnderzoek.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > InOnderzoek > IdentificatiecodeAdresseerbaarObject"),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = (
        "verblijfplaats.inOnderzoek.landVanwaarIngeschreven",
        _("Verblijfplaats > InOnderzoek > LandVanwaarIngeschreven"),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = (
        "verblijfplaats.inOnderzoek.locatiebeschrijving",
        _("Verblijfplaats > InOnderzoek > Locatiebeschrijving"),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = (
        "verblijfplaats.inOnderzoek.naamOpenbareRuimte",
        _("Verblijfplaats > InOnderzoek > NaamOpenbareRuimte"),
    )
    verblijfplaats_inOnderzoek_postcode = (
        "verblijfplaats.inOnderzoek.postcode",
        _("Verblijfplaats > InOnderzoek > Postcode"),
    )
    verblijfplaats_inOnderzoek_straat = (
        "verblijfplaats.inOnderzoek.straat",
        _("Verblijfplaats > InOnderzoek > Straat"),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = (
        "verblijfplaats.inOnderzoek.verblijfBuitenland",
        _("Verblijfplaats > InOnderzoek > VerblijfBuitenland"),
    )
    verblijfplaats_inOnderzoek_woonplaats = (
        "verblijfplaats.inOnderzoek.woonplaats",
        _("Verblijfplaats > InOnderzoek > Woonplaats"),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = (
        "verblijfplaats.indicatieVestigingVanuitBuitenland",
        _("Verblijfplaats > IndicatieVestigingVanuitBuitenland"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = (
        "verblijfplaats.landVanwaarIngeschreven.code",
        _("Verblijfplaats > LandVanwaarIngeschreven > Code"),
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = (
        "verblijfplaats.landVanwaarIngeschreven.omschrijving",
        _("Verblijfplaats > LandVanwaarIngeschreven > Omschrijving"),
    )
    verblijfplaats_locatiebeschrijving = (
        "verblijfplaats.locatiebeschrijving",
        _("Verblijfplaats > Locatiebeschrijving"),
    )
    verblijfplaats_naamOpenbareRuimte = (
        "verblijfplaats.naamOpenbareRuimte",
        _("Verblijfplaats > NaamOpenbareRuimte"),
    )
    verblijfplaats_postcode = "verblijfplaats.postcode", _("Verblijfplaats > Postcode")
    verblijfplaats_straat = "verblijfplaats.straat", _("Verblijfplaats > Straat")
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = (
        "verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        _("Verblijfplaats > VanuitVertrokkenOnbekendWaarheen"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = (
        "verblijfplaats.verblijfBuitenland.adresRegel1",
        _("Verblijfplaats > VerblijfBuitenland > Adresregel1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = (
        "verblijfplaats.verblijfBuitenland.adresRegel2",
        _("Verblijfplaats > VerblijfBuitenland > Adresregel2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = (
        "verblijfplaats.verblijfBuitenland.adresRegel3",
        _("Verblijfplaats > VerblijfBuitenland > Adresregel3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = (
        "verblijfplaats.verblijfBuitenland.land.code",
        _("Verblijfplaats > VerblijfBuitenland > Land > Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = (
        "verblijfplaats.verblijfBuitenland.land.omschrijving",
        _("Verblijfplaats > VerblijfBuitenland > Land > Omschrijving"),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = (
        "verblijfplaats.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        _("Verblijfplaats > VerblijfBuitenland > VertrokkenOnbekendWaarheen"),
    )
    verblijfplaats_woonplaats = (
        "verblijfplaats.woonplaats",
        _("Verblijfplaats > Woonplaats"),
    )
    verblijfstitel_aanduiding_code = (
        "verblijfstitel.aanduiding.code",
        _("Verblijfstitel > Land > Code"),
    )
    verblijfstitel_aanduiding_omschrijving = (
        "verblijfstitel.aanduiding.omschrijving",
        _("Verblijfstitel > Land > Omschrijving"),
    )
    verblijfstitel_datumEinde_dag = (
        "verblijfstitel.datumEinde.dag",
        _("Verblijfstitel > DatumEinde > Dag"),
    )
    verblijfstitel_datumEinde_datum = (
        "verblijfstitel.datumEinde.datum",
        _("Verblijfstitel > DatumEinde > Datum"),
    )
    verblijfstitel_datumEinde_jaar = (
        "verblijfstitel.datumEinde.jaar",
        _("Verblijfstitel > DatumEinde > Jaar"),
    )
    verblijfstitel_datumEinde_maand = (
        "verblijfstitel.datumEinde.maand",
        _("Verblijfstitel > DatumEinde > Maand"),
    )
    verblijfstitel_datumIngang_dag = (
        "verblijfstitel.datumIngang.dag",
        _("Verblijfstitel > DatumIngang > Dag"),
    )
    verblijfstitel_datumIngang_datum = (
        "verblijfstitel.datumIngang.datum",
        _("Verblijfstitel > DatumIngang > Datum"),
    )
    verblijfstitel_datumIngang_jaar = (
        "verblijfstitel.datumIngang.jaar",
        _("Verblijfstitel > DatumIngang > Jaar"),
    )
    verblijfstitel_datumIngang_maand = (
        "verblijfstitel.datumIngang.maand",
        _("Verblijfstitel > DatumIngang > Maand"),
    )
    verblijfstitel_inOnderzoek_aanduiding = (
        "verblijfstitel.inOnderzoek.aanduiding",
        _("Verblijfstitel > InOnderzoek > Aanduiding"),
    )
    verblijfstitel_inOnderzoek_datumEinde = (
        "verblijfstitel.inOnderzoek.datumEinde",
        _("Verblijfstitel > InOnderzoek > DatumEinde"),
    )
    verblijfstitel_inOnderzoek_datumIngang = (
        "verblijfstitel.inOnderzoek.datumIngang",
        _("Verblijfstitel > InOnderzoek > DatumIngang"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Dag"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Datum"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Jaar"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfstitel > InOnderzoek > DatumIngangOnderzoek > Maand"),
    )


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
