from django.db import models
from django.utils.translation import gettext_lazy as _


class Attributes(models.TextChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://op.open-forms.test.maykin.opengem.nl/api/schema/openapi.yaml
    path:    /ingeschrevenpersonen/{burgerservicenummer}
    command: manage.py generate_prefill_from_spec --path /ingeschrevenpersonen/{burgerservicenummer} --url https://op.open-forms.test.maykin.opengem.nl/api/schema/openapi.yaml
    """

    burgerservicenummer = "burgerservicenummer", _("Burgerservicenummer")
    datumEersteInschrijvingGBA_dag = "datumEersteInschrijvingGBA.dag", _(
        "Datumingangonderzoek > Dag"
    )
    datumEersteInschrijvingGBA_datum = "datumEersteInschrijvingGBA.datum", _(
        "Datumingangonderzoek > Datum"
    )
    datumEersteInschrijvingGBA_jaar = "datumEersteInschrijvingGBA.jaar", _(
        "Datumingangonderzoek > Jaar"
    )
    datumEersteInschrijvingGBA_maand = "datumEersteInschrijvingGBA.maand", _(
        "Datumingangonderzoek > Maand"
    )
    geboorte_datum_dag = "geboorte.datum.dag", _(
        "Geboorte > Datumingangonderzoek > Dag"
    )
    geboorte_datum_datum = "geboorte.datum.datum", _(
        "Geboorte > Datumingangonderzoek > Datum"
    )
    geboorte_datum_jaar = "geboorte.datum.jaar", _(
        "Geboorte > Datumingangonderzoek > Jaar"
    )
    geboorte_datum_maand = "geboorte.datum.maand", _(
        "Geboorte > Datumingangonderzoek > Maand"
    )
    geboorte_inOnderzoek_datum = "geboorte.inOnderzoek.datum", _(
        "Geboorte > Inonderzoek > Datum"
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.dag",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.datum",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = (
        "geboorte.inOnderzoek.datumIngangOnderzoek.maand",
        _("Geboorte > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    geboorte_inOnderzoek_land = "geboorte.inOnderzoek.land", _(
        "Geboorte > Inonderzoek > Land"
    )
    geboorte_inOnderzoek_plaats = "geboorte.inOnderzoek.plaats", _(
        "Geboorte > Inonderzoek > Plaats"
    )
    geboorte_land_code = "geboorte.land.code", _("Geboorte > Land > Code")
    geboorte_land_omschrijving = "geboorte.land.omschrijving", _(
        "Geboorte > Land > Omschrijving"
    )
    geboorte_plaats_code = "geboorte.plaats.code", _("Geboorte > Land > Code")
    geboorte_plaats_omschrijving = "geboorte.plaats.omschrijving", _(
        "Geboorte > Land > Omschrijving"
    )
    geheimhoudingPersoonsgegevens = "geheimhoudingPersoonsgegevens", _(
        "Geheimhoudingpersoonsgegevens"
    )
    geslachtsaanduiding = "geslachtsaanduiding", _("Geslachtsaanduiding")
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.dag",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.datum",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = (
        "gezagsverhouding.inOnderzoek.datumIngangOnderzoek.maand",
        _("Gezagsverhouding > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = (
        "gezagsverhouding.inOnderzoek.indicatieCurateleRegister",
        _("Gezagsverhouding > Inonderzoek > Indicatiecurateleregister"),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = (
        "gezagsverhouding.inOnderzoek.indicatieGezagMinderjarige",
        _("Gezagsverhouding > Inonderzoek > Indicatiegezagminderjarige"),
    )
    gezagsverhouding_indicatieCurateleRegister = (
        "gezagsverhouding.indicatieCurateleRegister",
        _("Gezagsverhouding > Indicatiecurateleregister"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = (
        "gezagsverhouding.indicatieGezagMinderjarige",
        _("Gezagsverhouding > Indicatiegezagminderjarige"),
    )
    inOnderzoek_burgerservicenummer = "inOnderzoek.burgerservicenummer", _(
        "Inonderzoek > Burgerservicenummer"
    )
    inOnderzoek_datumIngangOnderzoek_dag = (
        "inOnderzoek.datumIngangOnderzoek.dag",
        _("Inonderzoek > Datumingangonderzoek > Dag"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = (
        "inOnderzoek.datumIngangOnderzoek.datum",
        _("Inonderzoek > Datumingangonderzoek > Datum"),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = (
        "inOnderzoek.datumIngangOnderzoek.jaar",
        _("Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    inOnderzoek_datumIngangOnderzoek_maand = (
        "inOnderzoek.datumIngangOnderzoek.maand",
        _("Inonderzoek > Datumingangonderzoek > Maand"),
    )
    inOnderzoek_geslachtsaanduiding = "inOnderzoek.geslachtsaanduiding", _(
        "Inonderzoek > Geslachtsaanduiding"
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.dag",
        _("Kiesrecht > Datumingangonderzoek > Dag"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Kiesrecht > Datumingangonderzoek > Datum"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.jaar",
        _("Kiesrecht > Datumingangonderzoek > Jaar"),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = (
        "kiesrecht.einddatumUitsluitingEuropeesKiesrecht.maand",
        _("Kiesrecht > Datumingangonderzoek > Maand"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = (
        "kiesrecht.einddatumUitsluitingKiesrecht.dag",
        _("Kiesrecht > Datumingangonderzoek > Dag"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = (
        "kiesrecht.einddatumUitsluitingKiesrecht.datum",
        _("Kiesrecht > Datumingangonderzoek > Datum"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = (
        "kiesrecht.einddatumUitsluitingKiesrecht.jaar",
        _("Kiesrecht > Datumingangonderzoek > Jaar"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = (
        "kiesrecht.einddatumUitsluitingKiesrecht.maand",
        _("Kiesrecht > Datumingangonderzoek > Maand"),
    )
    kiesrecht_europeesKiesrecht = "kiesrecht.europeesKiesrecht", _(
        "Kiesrecht > Europeeskiesrecht"
    )
    kiesrecht_uitgeslotenVanKiesrecht = "kiesrecht.uitgeslotenVanKiesrecht", _(
        "Kiesrecht > Uitgeslotenvankiesrecht"
    )
    leeftijd = "leeftijd", _("Leeftijd")
    naam_aanduidingNaamgebruik = "naam.aanduidingNaamgebruik", _(
        "Naam > Aanduidingnaamgebruik"
    )
    naam_aanhef = "naam.aanhef", _("Naam > Aanhef")
    naam_aanschrijfwijze = "naam.aanschrijfwijze", _("Naam > Aanschrijfwijze")
    naam_gebruikInLopendeTekst = "naam.gebruikInLopendeTekst", _(
        "Naam > Gebruikinlopendetekst"
    )
    naam_geslachtsnaam = "naam.geslachtsnaam", _("Naam > Geslachtsnaam")
    naam_inOnderzoek_datumIngangOnderzoek_dag = (
        "naam.inOnderzoek.datumIngangOnderzoek.dag",
        _("Naam > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = (
        "naam.inOnderzoek.datumIngangOnderzoek.datum",
        _("Naam > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = (
        "naam.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Naam > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = (
        "naam.inOnderzoek.datumIngangOnderzoek.maand",
        _("Naam > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    naam_inOnderzoek_geslachtsnaam = "naam.inOnderzoek.geslachtsnaam", _(
        "Naam > Inonderzoek > Geslachtsnaam"
    )
    naam_inOnderzoek_voornamen = "naam.inOnderzoek.voornamen", _(
        "Naam > Inonderzoek > Voornamen"
    )
    naam_inOnderzoek_voorvoegsel = "naam.inOnderzoek.voorvoegsel", _(
        "Naam > Inonderzoek > Voorvoegsel"
    )
    naam_voorletters = "naam.voorletters", _("Naam > Voorletters")
    naam_voornamen = "naam.voornamen", _("Naam > Voornamen")
    naam_voorvoegsel = "naam.voorvoegsel", _("Naam > Voorvoegsel")
    opschortingBijhouding_datum_dag = (
        "opschortingBijhouding.datum.dag",
        _("Opschortingbijhouding > Datumingangonderzoek > Dag"),
    )
    opschortingBijhouding_datum_datum = (
        "opschortingBijhouding.datum.datum",
        _("Opschortingbijhouding > Datumingangonderzoek > Datum"),
    )
    opschortingBijhouding_datum_jaar = (
        "opschortingBijhouding.datum.jaar",
        _("Opschortingbijhouding > Datumingangonderzoek > Jaar"),
    )
    opschortingBijhouding_datum_maand = (
        "opschortingBijhouding.datum.maand",
        _("Opschortingbijhouding > Datumingangonderzoek > Maand"),
    )
    opschortingBijhouding_reden = "opschortingBijhouding.reden", _(
        "Opschortingbijhouding > Reden"
    )
    overlijden_datum_dag = "overlijden.datum.dag", _(
        "Overlijden > Datumingangonderzoek > Dag"
    )
    overlijden_datum_datum = "overlijden.datum.datum", _(
        "Overlijden > Datumingangonderzoek > Datum"
    )
    overlijden_datum_jaar = "overlijden.datum.jaar", _(
        "Overlijden > Datumingangonderzoek > Jaar"
    )
    overlijden_datum_maand = "overlijden.datum.maand", _(
        "Overlijden > Datumingangonderzoek > Maand"
    )
    overlijden_inOnderzoek_datum = "overlijden.inOnderzoek.datum", _(
        "Overlijden > Inonderzoek > Datum"
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.dag",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.datum",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = (
        "overlijden.inOnderzoek.datumIngangOnderzoek.maand",
        _("Overlijden > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    overlijden_inOnderzoek_land = "overlijden.inOnderzoek.land", _(
        "Overlijden > Inonderzoek > Land"
    )
    overlijden_inOnderzoek_plaats = "overlijden.inOnderzoek.plaats", _(
        "Overlijden > Inonderzoek > Plaats"
    )
    overlijden_indicatieOverleden = "overlijden.indicatieOverleden", _(
        "Overlijden > Indicatieoverleden"
    )
    overlijden_land_code = "overlijden.land.code", _("Overlijden > Land > Code")
    overlijden_land_omschrijving = "overlijden.land.omschrijving", _(
        "Overlijden > Land > Omschrijving"
    )
    overlijden_plaats_code = "overlijden.plaats.code", _("Overlijden > Land > Code")
    overlijden_plaats_omschrijving = "overlijden.plaats.omschrijving", _(
        "Overlijden > Land > Omschrijving"
    )
    verblijfplaats_aanduidingBijHuisnummer = (
        "verblijfplaats.aanduidingBijHuisnummer",
        _("Verblijfplaats > Aanduidingbijhuisnummer"),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = (
        "verblijfplaats.datumAanvangAdreshouding.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = (
        "verblijfplaats.datumAanvangAdreshouding.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = (
        "verblijfplaats.datumAanvangAdreshouding.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = (
        "verblijfplaats.datumAanvangAdreshouding.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumIngangGeldigheid_dag = (
        "verblijfplaats.datumIngangGeldigheid.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumIngangGeldigheid_datum = (
        "verblijfplaats.datumIngangGeldigheid.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = (
        "verblijfplaats.datumIngangGeldigheid.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumIngangGeldigheid_maand = (
        "verblijfplaats.datumIngangGeldigheid.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = (
        "verblijfplaats.datumInschrijvingInGemeente.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = (
        "verblijfplaats.datumInschrijvingInGemeente.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = (
        "verblijfplaats.datumInschrijvingInGemeente.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = (
        "verblijfplaats.datumInschrijvingInGemeente.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_datumVestigingInNederland_dag = (
        "verblijfplaats.datumVestigingInNederland.dag",
        _("Verblijfplaats > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_datumVestigingInNederland_datum = (
        "verblijfplaats.datumVestigingInNederland.datum",
        _("Verblijfplaats > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_datumVestigingInNederland_jaar = (
        "verblijfplaats.datumVestigingInNederland.jaar",
        _("Verblijfplaats > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_datumVestigingInNederland_maand = (
        "verblijfplaats.datumVestigingInNederland.maand",
        _("Verblijfplaats > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_functieAdres = "verblijfplaats.functieAdres", _(
        "Verblijfplaats > Functieadres"
    )
    verblijfplaats_gemeenteVanInschrijving_code = (
        "verblijfplaats.gemeenteVanInschrijving.code",
        _("Verblijfplaats > Land > Code"),
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = (
        "verblijfplaats.gemeenteVanInschrijving.omschrijving",
        _("Verblijfplaats > Land > Omschrijving"),
    )
    verblijfplaats_huisletter = "verblijfplaats.huisletter", _(
        "Verblijfplaats > Huisletter"
    )
    verblijfplaats_huisnummer = "verblijfplaats.huisnummer", _(
        "Verblijfplaats > Huisnummer"
    )
    verblijfplaats_huisnummertoevoeging = (
        "verblijfplaats.huisnummertoevoeging",
        _("Verblijfplaats > Huisnummertoevoeging"),
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = (
        "verblijfplaats.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = (
        "verblijfplaats.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > Identificatiecodenummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = (
        "verblijfplaats.inOnderzoek.aanduidingBijHuisnummer",
        _("Verblijfplaats > Inonderzoek > Aanduidingbijhuisnummer"),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = (
        "verblijfplaats.inOnderzoek.datumAanvangAdreshouding",
        _("Verblijfplaats > Inonderzoek > Datumaanvangadreshouding"),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = (
        "verblijfplaats.inOnderzoek.datumIngangGeldigheid",
        _("Verblijfplaats > Inonderzoek > Datuminganggeldigheid"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = (
        "verblijfplaats.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfplaats > Inonderzoek > Datumingangonderzoek > Maand"),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = (
        "verblijfplaats.inOnderzoek.datumInschrijvingInGemeente",
        _("Verblijfplaats > Inonderzoek > Datuminschrijvingingemeente"),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = (
        "verblijfplaats.inOnderzoek.datumVestigingInNederland",
        _("Verblijfplaats > Inonderzoek > Datumvestiginginnederland"),
    )
    verblijfplaats_inOnderzoek_functieAdres = (
        "verblijfplaats.inOnderzoek.functieAdres",
        _("Verblijfplaats > Inonderzoek > Functieadres"),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = (
        "verblijfplaats.inOnderzoek.gemeenteVanInschrijving",
        _("Verblijfplaats > Inonderzoek > Gemeentevaninschrijving"),
    )
    verblijfplaats_inOnderzoek_huisletter = (
        "verblijfplaats.inOnderzoek.huisletter",
        _("Verblijfplaats > Inonderzoek > Huisletter"),
    )
    verblijfplaats_inOnderzoek_huisnummer = (
        "verblijfplaats.inOnderzoek.huisnummer",
        _("Verblijfplaats > Inonderzoek > Huisnummer"),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = (
        "verblijfplaats.inOnderzoek.huisnummertoevoeging",
        _("Verblijfplaats > Inonderzoek > Huisnummertoevoeging"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = (
        "verblijfplaats.inOnderzoek.identificatiecodeAdresseerbaarObject",
        _("Verblijfplaats > Inonderzoek > Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = (
        "verblijfplaats.inOnderzoek.identificatiecodeNummeraanduiding",
        _("Verblijfplaats > Inonderzoek > Identificatiecodenummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = (
        "verblijfplaats.inOnderzoek.landVanwaarIngeschreven",
        _("Verblijfplaats > Inonderzoek > Landvanwaaringeschreven"),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = (
        "verblijfplaats.inOnderzoek.locatiebeschrijving",
        _("Verblijfplaats > Inonderzoek > Locatiebeschrijving"),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = (
        "verblijfplaats.inOnderzoek.naamOpenbareRuimte",
        _("Verblijfplaats > Inonderzoek > Naamopenbareruimte"),
    )
    verblijfplaats_inOnderzoek_postcode = (
        "verblijfplaats.inOnderzoek.postcode",
        _("Verblijfplaats > Inonderzoek > Postcode"),
    )
    verblijfplaats_inOnderzoek_straat = (
        "verblijfplaats.inOnderzoek.straat",
        _("Verblijfplaats > Inonderzoek > Straat"),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = (
        "verblijfplaats.inOnderzoek.verblijfBuitenland",
        _("Verblijfplaats > Inonderzoek > Verblijfbuitenland"),
    )
    verblijfplaats_inOnderzoek_woonplaats = (
        "verblijfplaats.inOnderzoek.woonplaats",
        _("Verblijfplaats > Inonderzoek > Woonplaats"),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = (
        "verblijfplaats.indicatieVestigingVanuitBuitenland",
        _("Verblijfplaats > Indicatievestigingvanuitbuitenland"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = (
        "verblijfplaats.landVanwaarIngeschreven.code",
        _("Verblijfplaats > Land > Code"),
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = (
        "verblijfplaats.landVanwaarIngeschreven.omschrijving",
        _("Verblijfplaats > Land > Omschrijving"),
    )
    verblijfplaats_locatiebeschrijving = "verblijfplaats.locatiebeschrijving", _(
        "Verblijfplaats > Locatiebeschrijving"
    )
    verblijfplaats_naamOpenbareRuimte = "verblijfplaats.naamOpenbareRuimte", _(
        "Verblijfplaats > Naamopenbareruimte"
    )
    verblijfplaats_postcode = "verblijfplaats.postcode", _("Verblijfplaats > Postcode")
    verblijfplaats_straat = "verblijfplaats.straat", _("Verblijfplaats > Straat")
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = (
        "verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        _("Verblijfplaats > Vanuitvertrokkenonbekendwaarheen"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = (
        "verblijfplaats.verblijfBuitenland.adresRegel1",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = (
        "verblijfplaats.verblijfBuitenland.adresRegel2",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = (
        "verblijfplaats.verblijfBuitenland.adresRegel3",
        _("Verblijfplaats > Verblijfbuitenland > Adresregel3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = (
        "verblijfplaats.verblijfBuitenland.land.code",
        _("Verblijfplaats > Verblijfbuitenland > Land > Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = (
        "verblijfplaats.verblijfBuitenland.land.omschrijving",
        _("Verblijfplaats > Verblijfbuitenland > Land > Omschrijving"),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = (
        "verblijfplaats.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        _("Verblijfplaats > Verblijfbuitenland > Vertrokkenonbekendwaarheen"),
    )
    verblijfplaats_woonplaats = "verblijfplaats.woonplaats", _(
        "Verblijfplaats > Woonplaats"
    )
    verblijfstitel_aanduiding_code = "verblijfstitel.aanduiding.code", _(
        "Verblijfstitel > Land > Code"
    )
    verblijfstitel_aanduiding_omschrijving = (
        "verblijfstitel.aanduiding.omschrijving",
        _("Verblijfstitel > Land > Omschrijving"),
    )
    verblijfstitel_datumEinde_dag = (
        "verblijfstitel.datumEinde.dag",
        _("Verblijfstitel > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_datumEinde_datum = (
        "verblijfstitel.datumEinde.datum",
        _("Verblijfstitel > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_datumEinde_jaar = (
        "verblijfstitel.datumEinde.jaar",
        _("Verblijfstitel > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_datumEinde_maand = (
        "verblijfstitel.datumEinde.maand",
        _("Verblijfstitel > Datumingangonderzoek > Maand"),
    )
    verblijfstitel_datumIngang_dag = (
        "verblijfstitel.datumIngang.dag",
        _("Verblijfstitel > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_datumIngang_datum = (
        "verblijfstitel.datumIngang.datum",
        _("Verblijfstitel > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_datumIngang_jaar = (
        "verblijfstitel.datumIngang.jaar",
        _("Verblijfstitel > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_datumIngang_maand = (
        "verblijfstitel.datumIngang.maand",
        _("Verblijfstitel > Datumingangonderzoek > Maand"),
    )
    verblijfstitel_inOnderzoek_aanduiding = (
        "verblijfstitel.inOnderzoek.aanduiding",
        _("Verblijfstitel > Inonderzoek > Aanduiding"),
    )
    verblijfstitel_inOnderzoek_datumEinde = (
        "verblijfstitel.inOnderzoek.datumEinde",
        _("Verblijfstitel > Inonderzoek > Datumeinde"),
    )
    verblijfstitel_inOnderzoek_datumIngang = (
        "verblijfstitel.inOnderzoek.datumIngang",
        _("Verblijfstitel > Inonderzoek > Datumingang"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.dag",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Dag"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.datum",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Datum"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.jaar",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Jaar"),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = (
        "verblijfstitel.inOnderzoek.datumIngangOnderzoek.maand",
        _("Verblijfstitel > Inonderzoek > Datumingangonderzoek > Maand"),
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
    verblijfplaats_verblijfadres_postcode = "verblijfplaats.verblijfadres.postcode", _(
        "Verblijfplaats > Verblijf Adres > Postcode"
    )
    verblijfplaats_verblijfadres_woonplaats = (
        "verblijfplaats.verblijfadres.woonplaats",
        _("Verblijfplaats > Verblijf Adres > Woonplaats"),
    )
    gemeentevaninschrijving_code = "gemeenteVanInschrijving.code", _(
        "Gemeentevaninschrijving > Code"
    )
    gemeentevaninschrijving_omschrijving = "gemeenteVanInschrijving.omschrijving", _(
        "Gemeentevaninschrijving > Omschrijving"
    )
    adressering_adresregel1 = "adressering.adresregel1", _(
        "Adressering > Adres Regel 1"
    )
    adressering_adresregel2 = "adressering.adresregel2", _(
        "Adressering > Adres Regel 2"
    )
    adressering_adresregel3 = "adressering.adresregel3", _(
        "Adressering > Adres Regel 3"
    )
    adressering_land = "adressering.land", _("Adressering > Land")
    geboorte_land = "geboorte.land", _("Geboorte > Land")
    geboorte_land_code = "geboorte.land.code", _("Geboorte > Land > Code")
    geboorte_land_omschrijving = "geboorte.land.omschrijving", _(
        "Geboorte > Land > Omschrijving"
    )
    geboorte_plaats = "geboorte.plaats", _("Geboorte > Plaats")
    geboorte_plaats_code = "geboorte.plaats.code", _("Geboorte > Plaats > Code")
    geboorte_plaats_omschrijving = "geboorte.plaats.omschrijving", _(
        "Geboorte > Plaats > Omschrijving"
    )
    geboorte_datum_langformaat = "geboorte.datum.langFormaat", _(
        "Geboorte > Datum > Lang Formaat"
    )
    geboorte_datum_type = "geboorte.datum.type", _("Geboorte > Datum > Type")
    geboorte_datum_datum = "geboorte.datum.datum", _("Geboorte > Datum > Datum")
    geboorte_datum_onbekend = "geboorte.datum.onbekend", _(
        "Geboorte > Datum > Onbekend"
    )
    geboorte_datum_jaar = "geboorte.datum.jaar", _("Geboorte > Datum > Jaar")
    geboorte_datum_maand = "geboorte.datum.maand", _("Geboorte > Datum > Maand")
    geslacht_code = "geslacht.code", _("Geslacht > Code")
    geslacht_omschrijving = "geslacht.omschrijving", _("Geslacht > Omschrijving")
    overlijden_datum_langformaat = "overlijden.datum.langFormaat", _(
        "Overlijden > Datum > Lang Formaat"
    )
    overlijden_datum_type = "overlijden.datum.type", _("Overlijden > Datum > Type")
    overlijden_datum_datum = "overlijden.datum.datum", _("Overlijden > Datum > Datum")
    overlijden_datum_onbekend = "overlijden.datum.onbekend", _(
        "Overlijden > Datum > Onbekend"
    )
    overlijden_datum_jaar = "overlijden.datum.jaar", _("Overlijden > Datum > Jaar")
    overlijden_datum_maand = "overlijden.datum.maand", _("Overlijden > Datum > Maand")


class HaalCentraalVersion(models.TextChoices):
    haalcentraal13 = "1.3", "BRP Bevragen Personen 1.3"
    haalcentraal20 = "2.0", "BRP Bevragen Personen 2.0"
