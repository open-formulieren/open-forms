from django.db import models
from django.utils.translation import gettext_lazy as _


class AttributesV2(models.TextChoices):
    # A-nummer
    anummer = (
        "aNummer",
        _("A-nummer"),
    )

    # Burgerservicenummer
    burgerservicenummer = (
        "burgerservicenummer",
        _("Burgerservicenummer"),
    )

    # Datum Eerste Inschrijving GBA
    datumeersteinschrijvinggba_type = (
        "datumEersteInschrijvingGBA.type",
        _("Datum Eerste Inschrijving GBA > Type"),
    )
    datumeersteinschrijvinggba_langformaat = (
        "datumEersteInschrijvingGBA.langFormaat",
        _("Datum Eerste Inschrijving GBA > Lang Formaat"),
    )
    datumeersteinschrijvinggba_datum = (
        "datumEersteInschrijvingGBA.datum",
        _("Datum Eerste Inschrijving GBA > Datum"),
    )
    datumeersteinschrijvinggba_onbekend = (
        "datumEersteInschrijvingGBA.onbekend",
        _("Datum Eerste Inschrijving GBA > Onbekend"),
    )
    datumeersteinschrijvinggba_jaar = (
        "datumEersteInschrijvingGBA.jaar",
        _("Datum Eerste Inschrijving GBA > Jaar"),
    )
    datumeersteinschrijvinggba_maand = (
        "datumEersteInschrijvingGBA.maand",
        _("Datum Eerste Inschrijving GBA > Maand"),
    )

    # Geslacht
    geslacht_code = (
        "geslacht.code",
        _("Geslacht > Code"),
    )
    geslacht_omschrijving = (
        "geslacht.omschrijving",
        _("Geslacht > Omschrijving"),
    )

    # Uitsluiting Kiesrecht
    uitsluitingkiesrecht_uitgeslotenvankiesrecht = (
        "uitsluitingKiesrecht.uitgeslotenVanKiesrecht",
        _("Uitsluiting Kiesrecht > Uitgesloten Van Kiesrecht"),
    )
    uitsluitingkiesrecht_einddatum_type = (
        "uitsluitingKiesrecht.einddatum.type",
        _("Uitsluiting Kiesrecht > Einddatum > Type"),
    )
    uitsluitingkiesrecht_einddatum_langformaat = (
        "uitsluitingKiesrecht.einddatum.langFormaat",
        _("Uitsluiting Kiesrecht > Einddatum > Lang Formaat"),
    )
    uitsluitingkiesrecht_einddatum_datum = (
        "uitsluitingKiesrecht.einddatum.datum",
        _("Uitsluiting Kiesrecht > Einddatum > Datum"),
    )
    uitsluitingkiesrecht_einddatum_onbekend = (
        "uitsluitingKiesrecht.einddatum.onbekend",
        _("Uitsluiting Kiesrecht > Einddatum > Onbekend"),
    )
    uitsluitingkiesrecht_einddatum_jaar = (
        "uitsluitingKiesrecht.einddatum.jaar",
        _("Uitsluiting Kiesrecht > Einddatum > Jaar"),
    )
    uitsluitingkiesrecht_einddatum_maand = (
        "uitsluitingKiesrecht.einddatum.maand",
        _("Uitsluiting Kiesrecht > Einddatum > Maand"),
    )

    # Europees Kiesrecht
    europeeskiesrecht_aanduiding_code = (
        "europeesKiesrecht.aanduiding.code",
        _("Europees Kiesrecht > Aanduiding > Code"),
    )
    europeeskiesrecht_aanduiding_omschrijving = (
        "europeesKiesrecht.aanduiding.omschrijving",
        _("Europees Kiesrecht > Aanduiding > Omschrijving"),
    )
    europeeskiesrecht_einddatumuitsluiting_type = (
        "europeesKiesrecht.einddatumUitsluiting.type",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Type"),
    )
    europeeskiesrecht_einddatumuitsluiting_langformaat = (
        "europeesKiesrecht.einddatumUitsluiting.langFormaat",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Lang Formaat"),
    )
    europeeskiesrecht_einddatumuitsluiting_datum = (
        "europeesKiesrecht.einddatumUitsluiting.datum",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Datum"),
    )
    europeeskiesrecht_einddatumuitsluiting_onbekend = (
        "europeesKiesrecht.einddatumUitsluiting.onbekend",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Onbekend"),
    )
    europeeskiesrecht_einddatumuitsluiting_jaar = (
        "europeesKiesrecht.einddatumUitsluiting.jaar",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Jaar"),
    )
    europeeskiesrecht_einddatumuitsluiting_maand = (
        "europeesKiesrecht.einddatumUitsluiting.maand",
        _("Europees Kiesrecht > Einddatum Uitsluiting > Maand"),
    )

    # Leeftijd
    leeftijd = (
        "leeftijd",
        _("Leeftijd"),
    )

    # Naam
    naam_voornamen = (
        "naam.voornamen",
        _("Naam > Voornamen"),
    )
    naam_adellijketitelpredicaat_code = (
        "naam.adellijkeTitelPredicaat.code",
        _("Naam > Adellijke Titel/Predicaat > Code"),
    )
    naam_adellijketitelpredicaat_omschrijving = (
        "naam.adellijkeTitelPredicaat.omschrijving",
        _("Naam > Adellijke Titel/Predicaat > Omschrijving"),
    )
    naam_adellijketitelpredicaat_soort = (
        "naam.adellijkeTitelPredicaat.soort",
        _("Naam > Adellijke Titel/Predicaat > Soort"),
    )
    naam_voorvoegsel = (
        "naam.voorvoegsel",
        _("Naam > Voorvoegsel"),
    )
    naam_geslachtsnaam = (
        "naam.geslachtsnaam",
        _("Naam > Geslachtsnaam"),
    )
    naam_voorletters = (
        "naam.voorletters",
        _("Naam > Voorletters"),
    )
    naam_volledigenaam = (
        "naam.volledigeNaam",
        _("Naam > Volledige Naam"),
    )
    naam_aanduidingnaamgebruik_code = (
        "naam.aanduidingNaamgebruik.code",
        _("Naam > Aanduiding Naamgebruik > Code"),
    )
    naam_aanduidingnaamgebruik_omschrijving = (
        "naam.aanduidingNaamgebruik.omschrijving",
        _("Naam > Aanduiding Naamgebruik > Omschrijving"),
    )

    # Nationaliteiten
    nationaliteiten_type = (
        "nationaliteiten.type",
        _("Nationaliteiten > Type"),
    )
    nationaliteiten_redenopname_code = (
        "nationaliteiten.redenOpname.code",
        _("Nationaliteiten > Reden Opname > Code"),
    )
    nationaliteiten_redenopname_omschrijving = (
        "nationaliteiten.redenOpname.omschrijving",
        _("Nationaliteiten > Reden Opname > Omschrijving"),
    )
    nationaliteiten_datuminganggeldigheid_type = (
        "nationaliteiten.datumIngangGeldigheid.type",
        _("Nationaliteiten > Datum Ingang Geldigheid > Type"),
    )
    nationaliteiten_datuminganggeldigheid_langformaat = (
        "nationaliteiten.datumIngangGeldigheid.langFormaat",
        _("Nationaliteiten > Datum Ingang Geldigheid > Lang Formaat"),
    )
    nationaliteiten_datuminganggeldigheid_datum = (
        "nationaliteiten.datumIngangGeldigheid.datum",
        _("Nationaliteiten > Datum Ingang Geldigheid > Datum"),
    )
    nationaliteiten_datuminganggeldigheid_onbekend = (
        "nationaliteiten.datumIngangGeldigheid.onbekend",
        _("Nationaliteiten > Datum Ingang Geldigheid > Onbekend"),
    )
    nationaliteiten_datuminganggeldigheid_jaar = (
        "nationaliteiten.datumIngangGeldigheid.jaar",
        _("Nationaliteiten > Datum Ingang Geldigheid > Jaar"),
    )
    nationaliteiten_datuminganggeldigheid_maand = (
        "nationaliteiten.datumIngangGeldigheid.maand",
        _("Nationaliteiten > Datum Ingang Geldigheid > Maand"),
    )
    nationaliteiten_nationaliteit_code = (
        "nationaliteiten.nationaliteit.code",
        _("Nationaliteiten > Nationaliteit > Code"),
    )
    nationaliteiten_nationaliteit_omschrijving = (
        "nationaliteiten.nationaliteit.omschrijving",
        _("Nationaliteiten > Nationaliteit > Omschrijving"),
    )

    # Geboorte
    geboorte_datum_type = (
        "geboorte.datum.type",
        _("Geboorte > Datum > Type"),
    )
    geboorte_datum_langformaat = (
        "geboorte.datum.langFormaat",
        _("Geboorte > Datum > Lang Formaat"),
    )
    geboorte_datum_datum = (
        "geboorte.datum.datum",
        _("Geboorte > Datum > Datum"),
    )
    geboorte_datum_onbekend = (
        "geboorte.datum.onbekend",
        _("Geboorte > Datum > Onbekend"),
    )
    geboorte_datum_jaar = (
        "geboorte.datum.jaar",
        _("Geboorte > Datum > Jaar"),
    )
    geboorte_datum_maand = (
        "geboorte.datum.maand",
        _("Geboorte > Datum > Maand"),
    )
    geboorte_land_code = (
        "geboorte.land.code",
        _("Geboorte > Land > Code"),
    )
    geboorte_land_omschrijving = (
        "geboorte.land.omschrijving",
        _("Geboorte > Land > Omschrijving"),
    )
    geboorte_plaats_code = (
        "geboorte.plaats.code",
        _("Geboorte > Plaats > Code"),
    )
    geboorte_plaats_omschrijving = (
        "geboorte.plaats.omschrijving",
        _("Geboorte > Plaats > Omschrijving"),
    )

    # Overlijden
    overlijden_land_code = (
        "overlijden.land.code",
        _("Overlijden > Land > Code"),
    )
    overlijden_land_omschrijving = (
        "overlijden.land.omschrijving",
        _("Overlijden > Land > Omschrijving"),
    )
    overlijden_plaats_code = (
        "overlijden.plaats.code",
        _("Overlijden > Plaats > Code"),
    )
    overlijden_plaats_omschrijving = (
        "overlijden.plaats.omschrijving",
        _("Overlijden > Plaats > Omschrijving"),
    )
    overlijden_datum_type = (
        "overlijden.datum.type",
        _("Overlijden > Datum > Type"),
    )
    overlijden_datum_langformaat = (
        "overlijden.datum.langFormaat",
        _("Overlijden > Datum > Lang Formaat"),
    )
    overlijden_datum_datum = (
        "overlijden.datum.datum",
        _("Overlijden > Datum > Datum"),
    )
    overlijden_datum_onbekend = (
        "overlijden.datum.onbekend",
        _("Overlijden > Datum > Onbekend"),
    )
    overlijden_datum_jaar = (
        "overlijden.datum.jaar",
        _("Overlijden > Datum > Jaar"),
    )
    overlijden_datum_maand = (
        "overlijden.datum.maand",
        _("Overlijden > Datum > Maand"),
    )

    # Verblijfplaats
    verblijfplaats_type = (
        "verblijfplaats.type",
        _("Verblijfplaats > Type"),
    )
    verblijfplaats_verblijfadres_locatiebeschrijving = (
        "verblijfplaats.verblijfadres.locatiebeschrijving",
        _("Verblijfplaats > Verblijfadres > Locatiebeschrijving"),
    )
    verblijfplaats_datumvan_type = (
        "verblijfplaats.datumVan.type",
        _("Verblijfplaats > Datum Van > Type"),
    )
    verblijfplaats_datumvan_langformaat = (
        "verblijfplaats.datumVan.langFormaat",
        _("Verblijfplaats > Datum Van > Lang Formaat"),
    )
    verblijfplaats_datumvan_datum = (
        "verblijfplaats.datumVan.datum",
        _("Verblijfplaats > Datum Van > Datum"),
    )
    verblijfplaats_datumvan_onbekend = (
        "verblijfplaats.datumVan.onbekend",
        _("Verblijfplaats > Datum Van > Onbekend"),
    )
    verblijfplaats_datumvan_jaar = (
        "verblijfplaats.datumVan.jaar",
        _("Verblijfplaats > Datum Van > Jaar"),
    )
    verblijfplaats_datumvan_maand = (
        "verblijfplaats.datumVan.maand",
        _("Verblijfplaats > Datum Van > Maand"),
    )
    verblijfplaats_functieadres_code = (
        "verblijfplaats.functieAdres.code",
        _("Verblijfplaats > Functie Adres > Code"),
    )
    verblijfplaats_functieadres_omschrijving = (
        "verblijfplaats.functieAdres.omschrijving",
        _("Verblijfplaats > Functie Adres > Omschrijving"),
    )
    verblijfplaats_adresseerbaarobjectidentificatie = (
        "verblijfplaats.adresseerbaarObjectIdentificatie",
        _("Verblijfplaats > Adresseerbaar Object Identificatie"),
    )
    verblijfplaats_nummeraanduidingidentificatie = (
        "verblijfplaats.nummeraanduidingIdentificatie",
        _("Verblijfplaats > Nummeraanduiding Identificatie"),
    )
    verblijfplaats_indicatievastgesteldverblijftnietopadres = (
        "verblijfplaats.indicatieVastgesteldVerblijftNietOpAdres",
        _("Verblijfplaats > Indicatie Vastgesteld Verblijft Niet Op Adres"),
    )
    verblijfplaats_verblijfadres_regel1 = (
        "verblijfplaats.verblijfadres.regel1",
        _("Verblijfplaats > Verblijfadres > Regel 1"),
    )
    verblijfplaats_verblijfadres_regel2 = (
        "verblijfplaats.verblijfadres.regel2",
        _("Verblijfplaats > Verblijfadres > Regel 2"),
    )
    verblijfplaats_verblijfadres_regel3 = (
        "verblijfplaats.verblijfadres.regel3",
        _("Verblijfplaats > Verblijfadres > Regel 3"),
    )
    verblijfplaats_verblijfadres_land_code = (
        "verblijfplaats.verblijfadres.land.code",
        _("Verblijfplaats > Verblijfadres > Land > Code"),
    )
    verblijfplaats_verblijfadres_land_omschrijving = (
        "verblijfplaats.verblijfadres.land.omschrijving",
        _("Verblijfplaats > Verblijfadres > Land > Omschrijving"),
    )
    verblijfplaats_verblijfadres_officielestraatnaam = (
        "verblijfplaats.verblijfadres.officieleStraatnaam",
        _("Verblijfplaats > Verblijfadres > Officiële Straatnaam"),
    )
    verblijfplaats_verblijfadres_kortestraatnaam = (
        "verblijfplaats.verblijfadres.korteStraatnaam",
        _("Verblijfplaats > Verblijfadres > Korte Straatnaam"),
    )
    verblijfplaats_verblijfadres_huisnummer = (
        "verblijfplaats.verblijfadres.huisnummer",
        _("Verblijfplaats > Verblijfadres > Huisnummer"),
    )
    verblijfplaats_verblijfadres_huisletter = (
        "verblijfplaats.verblijfadres.huisletter",
        _("Verblijfplaats > Verblijfadres > Huisletter"),
    )
    verblijfplaats_verblijfadres_huisnummertoevoeging = (
        "verblijfplaats.verblijfadres.huisnummertoevoeging",
        _("Verblijfplaats > Verblijfadres > Huisnummertoevoeging"),
    )
    verblijfplaats_verblijfadres_aanduidingbijhuisnummer_code = (
        "verblijfplaats.verblijfadres.aanduidingBijHuisnummer.code",
        _("Verblijfplaats > Verblijfadres > Aanduiding Bij Huisnummer > Code"),
    )
    verblijfplaats_verblijfadres_aanduidingbijhuisnummer_omschrijving = (
        "verblijfplaats.verblijfadres.aanduidingBijHuisnummer.omschrijving",
        _("Verblijfplaats > Verblijfadres > Aanduiding Bij Huisnummer > Omschrijving"),
    )
    verblijfplaats_verblijfadres_postcode = (
        "verblijfplaats.verblijfadres.postcode",
        _("Verblijfplaats > Verblijfadres > Postcode"),
    )
    verblijfplaats_verblijfadres_woonplaats = (
        "verblijfplaats.verblijfadres.woonplaats",
        _("Verblijfplaats > Verblijfadres > Woonplaats"),
    )

    # Immigratie
    immigratie_landvanwaaringeschreven_code = (
        "immigratie.landVanwaarIngeschreven.code",
        _("Immigratie > Land Vanwaar Ingeschreven > Code"),
    )
    immigratie_landvanwaaringeschreven_omschrijving = (
        "immigratie.landVanwaarIngeschreven.omschrijving",
        _("Immigratie > Land Vanwaar Ingeschreven > Omschrijving"),
    )
    immigratie_datumvestiginginnederland_type = (
        "immigratie.datumVestigingInNederland.type",
        _("Immigratie > Datum Vestiging In Nederland > Type"),
    )
    immigratie_datumvestiginginnederland_langformaat = (
        "immigratie.datumVestigingInNederland.langFormaat",
        _("Immigratie > Datum Vestiging In Nederland > Lang Formaat"),
    )
    immigratie_datumvestiginginnederland_datum = (
        "immigratie.datumVestigingInNederland.datum",
        _("Immigratie > Datum Vestiging In Nederland > Datum"),
    )
    immigratie_datumvestiginginnederland_onbekend = (
        "immigratie.datumVestigingInNederland.onbekend",
        _("Immigratie > Datum Vestiging In Nederland > Onbekend"),
    )
    immigratie_datumvestiginginnederland_jaar = (
        "immigratie.datumVestigingInNederland.jaar",
        _("Immigratie > Datum Vestiging In Nederland > Jaar"),
    )
    immigratie_datumvestiginginnederland_maand = (
        "immigratie.datumVestigingInNederland.maand",
        _("Immigratie > Datum Vestiging In Nederland > Maand"),
    )
    immigratie_vanuitverblijfplaatsonbekend = (
        "immigratie.vanuitVerblijfplaatsOnbekend",
        _("Immigratie > Vanuit Verblijfplaats Onbekend"),
    )
    immigratie_indicatievestigingvanuitbuitenland = (
        "immigratie.indicatieVestigingVanuitBuitenland",
        _("Immigratie > Indicatie Vestiging Vanuit Buitenland"),
    )

    # Gemeente Van Inschrijving
    gemeentevaninschrijving_code = (
        "gemeenteVanInschrijving.code",
        _("Gemeente Van Inschrijving > Code"),
    )
    gemeentevaninschrijving_omschrijving = (
        "gemeenteVanInschrijving.omschrijving",
        _("Gemeente Van Inschrijving > Omschrijving"),
    )

    # Datum Inschrijving In Gemeente
    datuminschrijvingingemeente_type = (
        "datumInschrijvingInGemeente.type",
        _("Datum Inschrijving In Gemeente > Type"),
    )
    datuminschrijvingingemeente_langformaat = (
        "datumInschrijvingInGemeente.langFormaat",
        _("Datum Inschrijving In Gemeente > Lang Formaat"),
    )
    datuminschrijvingingemeente_datum = (
        "datumInschrijvingInGemeente.datum",
        _("Datum Inschrijving In Gemeente > Datum"),
    )
    datuminschrijvingingemeente_onbekend = (
        "datumInschrijvingInGemeente.onbekend",
        _("Datum Inschrijving In Gemeente > Onbekend"),
    )
    datuminschrijvingingemeente_jaar = (
        "datumInschrijvingInGemeente.jaar",
        _("Datum Inschrijving In Gemeente > Jaar"),
    )
    datuminschrijvingingemeente_maand = (
        "datumInschrijvingInGemeente.maand",
        _("Datum Inschrijving In Gemeente > Maand"),
    )

    # Adressering
    adressering_adresregel1 = (
        "adressering.adresregel1",
        _("Adressering > Adresregel 1"),
    )
    adressering_adresregel2 = (
        "adressering.adresregel2",
        _("Adressering > Adresregel 2"),
    )
    adressering_adresregel3 = (
        "adressering.adresregel3",
        _("Adressering > Adresregel 3"),
    )
    adressering_land_code = (
        "adressering.land.code",
        _("Adressering > Land > Code"),
    )
    adressering_land_omschrijving = (
        "adressering.land.omschrijving",
        _("Adressering > Land > Omschrijving"),
    )
    adressering_indicatievastgesteldverblijftnietopadres = (
        "adressering.indicatieVastgesteldVerblijftNietOpAdres",
        _("Adressering > Indicatie Vastgesteld Verblijft Niet Op Adres"),
    )
    adressering_aanhef = (
        "adressering.aanhef",
        _("Adressering > Aanhef"),
    )
    adressering_aanschrijfwijze_naam = (
        "adressering.aanschrijfwijze.naam",
        _("Adressering > Aanschrijfwijze > Naam"),
    )
    adressering_aanschrijfwijze_aanspreekvorm = (
        "adressering.aanschrijfwijze.aanspreekvorm",
        _("Adressering > Aanschrijfwijze > Aanspreekvorm"),
    )
    adressering_gebruikinlopendetekst = (
        "adressering.gebruikInLopendeTekst",
        _("Adressering > Gebruik In Lopende Tekst"),
    )

    # Indicatie Curatele Register
    indicatiecurateleregister = (
        "indicatieCurateleRegister",
        _("Indicatie Curatele Register"),
    )

    # Gezag
    gezag_type = (
        "gezag.type",
        _("Gezag > Type"),
    )
    gezag_minderjarige_burgerservicenummer = (
        "gezag.minderjarige.burgerservicenummer",
        _("Gezag > Minderjarige > Burgerservicenummer"),
    )
    gezag_minderjarige_naam_volledigenaam = (
        "gezag.minderjarige.naam.volledigeNaam",
        _("Gezag > Minderjarige > Naam > Volledige Naam"),
    )
    gezag_minderjarige_leeftijd = (
        "gezag.minderjarige.leeftijd",
        _("Gezag > Minderjarige > Leeftijd"),
    )
    gezag_ouders_burgerservicenummer = (
        "gezag.ouders.burgerservicenummer",
        _("Gezag > Ouders > Burgerservicenummer"),
    )
    gezag_ouders_naam_volledigenaam = (
        "gezag.ouders.naam.volledigeNaam",
        _("Gezag > Ouders > Naam > Volledige Naam"),
    )
    gezag_ouder_burgerservicenummer = (
        "gezag.ouder.burgerservicenummer",
        _("Gezag > Ouder > Burgerservicenummer"),
    )
    gezag_ouder_naam_volledigenaam = (
        "gezag.ouder.naam.volledigeNaam",
        _("Gezag > Ouder > Naam > Volledige Naam"),
    )
    gezag_derde_type = (
        "gezag.derde.type",
        _("Gezag > Derde > Type"),
    )
    gezag_derde_burgerservicenummer = (
        "gezag.derde.burgerservicenummer",
        _("Gezag > Derde > Burgerservicenummer"),
    )
    gezag_derde_naam_volledigenaam = (
        "gezag.derde.naam.volledigeNaam",
        _("Gezag > Derde > Naam > Volledige Naam"),
    )
    gezag_derden_type = (
        "gezag.derden.type",
        _("Gezag > Derden > Type"),
    )
    gezag_derden_burgerservicenummer = (
        "gezag.derden.burgerservicenummer",
        _("Gezag > Derden > Burgerservicenummer"),
    )
    gezag_derden_naam_volledigenaam = (
        "gezag.derden.naam.volledigeNaam",
        _("Gezag > Derden > Naam > Volledige Naam"),
    )
    gezag_toelichting = (
        "gezag.toelichting",
        _("Gezag > Toelichting"),
    )

    # Verblijfstitel
    verblijfstitel_aanduiding_code = (
        "verblijfstitel.aanduiding.code",
        _("Verblijfstitel > Aanduiding > Code"),
    )
    verblijfstitel_aanduiding_omschrijving = (
        "verblijfstitel.aanduiding.omschrijving",
        _("Verblijfstitel > Aanduiding > Omschrijving"),
    )
    verblijfstitel_datumeinde_type = (
        "verblijfstitel.datumEinde.type",
        _("Verblijfstitel > Datum Einde > Type"),
    )
    verblijfstitel_datumeinde_langformaat = (
        "verblijfstitel.datumEinde.langFormaat",
        _("Verblijfstitel > Datum Einde > Lang Formaat"),
    )
    verblijfstitel_datumeinde_datum = (
        "verblijfstitel.datumEinde.datum",
        _("Verblijfstitel > Datum Einde > Datum"),
    )
    verblijfstitel_datumeinde_onbekend = (
        "verblijfstitel.datumEinde.onbekend",
        _("Verblijfstitel > Datum Einde > Onbekend"),
    )
    verblijfstitel_datumeinde_jaar = (
        "verblijfstitel.datumEinde.jaar",
        _("Verblijfstitel > Datum Einde > Jaar"),
    )
    verblijfstitel_datumeinde_maand = (
        "verblijfstitel.datumEinde.maand",
        _("Verblijfstitel > Datum Einde > Maand"),
    )
    verblijfstitel_datumingang_type = (
        "verblijfstitel.datumIngang.type",
        _("Verblijfstitel > Datum Ingang > Type"),
    )
    verblijfstitel_datumingang_langformaat = (
        "verblijfstitel.datumIngang.langFormaat",
        _("Verblijfstitel > Datum Ingang > Lang Formaat"),
    )
    verblijfstitel_datumingang_datum = (
        "verblijfstitel.datumIngang.datum",
        _("Verblijfstitel > Datum Ingang > Datum"),
    )
    verblijfstitel_datumingang_onbekend = (
        "verblijfstitel.datumIngang.onbekend",
        _("Verblijfstitel > Datum Ingang > Onbekend"),
    )
    verblijfstitel_datumingang_jaar = (
        "verblijfstitel.datumIngang.jaar",
        _("Verblijfstitel > Datum Ingang > Jaar"),
    )
    verblijfstitel_datumingang_maand = (
        "verblijfstitel.datumIngang.maand",
        _("Verblijfstitel > Datum Ingang > Maand"),
    )

    # Kinderen
    kinderen_burgerservicenummer = (
        "kinderen.burgerservicenummer",
        _("Kinderen > Burgerservicenummer"),
    )
    kinderen_naam_voornamen = (
        "kinderen.naam.voornamen",
        _("Kinderen > Naam > Voornamen"),
    )
    kinderen_naam_adellijketitelpredicaat_code = (
        "kinderen.naam.adellijkeTitelPredicaat.code",
        _("Kinderen > Naam > Adellijke Titel/Predicaat > Code"),
    )
    kinderen_naam_adellijketitelpredicaat_omschrijving = (
        "kinderen.naam.adellijkeTitelPredicaat.omschrijving",
        _("Kinderen > Naam > Adellijke Titel/Predicaat > Omschrijving"),
    )
    kinderen_naam_adellijketitelpredicaat_soort = (
        "kinderen.naam.adellijkeTitelPredicaat.soort",
        _("Kinderen > Naam > Adellijke Titel/Predicaat > Soort"),
    )
    kinderen_naam_voorvoegsel = (
        "kinderen.naam.voorvoegsel",
        _("Kinderen > Naam > Voorvoegsel"),
    )
    kinderen_naam_geslachtsnaam = (
        "kinderen.naam.geslachtsnaam",
        _("Kinderen > Naam > Geslachtsnaam"),
    )
    kinderen_naam_voorletters = (
        "kinderen.naam.voorletters",
        _("Kinderen > Naam > Voorletters"),
    )
    kinderen_geboorte_datum_type = (
        "kinderen.geboorte.datum.type",
        _("Kinderen > Geboorte > Datum > Type"),
    )
    kinderen_geboorte_datum_langformaat = (
        "kinderen.geboorte.datum.langFormaat",
        _("Kinderen > Geboorte > Datum > Lang Formaat"),
    )
    kinderen_geboorte_datum_datum = (
        "kinderen.geboorte.datum.datum",
        _("Kinderen > Geboorte > Datum > Datum"),
    )
    kinderen_geboorte_datum_onbekend = (
        "kinderen.geboorte.datum.onbekend",
        _("Kinderen > Geboorte > Datum > Onbekend"),
    )
    kinderen_geboorte_datum_jaar = (
        "kinderen.geboorte.datum.jaar",
        _("Kinderen > Geboorte > Datum > Jaar"),
    )
    kinderen_geboorte_datum_maand = (
        "kinderen.geboorte.datum.maand",
        _("Kinderen > Geboorte > Datum > Maand"),
    )
    kinderen_geboorte_land_code = (
        "kinderen.geboorte.land.code",
        _("Kinderen > Geboorte > Land > Code"),
    )
    kinderen_geboorte_land_omschrijving = (
        "kinderen.geboorte.land.omschrijving",
        _("Kinderen > Geboorte > Land > Omschrijving"),
    )
    kinderen_geboorte_plaats_code = (
        "kinderen.geboorte.plaats.code",
        _("Kinderen > Geboorte > Plaats > Code"),
    )
    kinderen_geboorte_plaats_omschrijving = (
        "kinderen.geboorte.plaats.omschrijving",
        _("Kinderen > Geboorte > Plaats > Omschrijving"),
    )

    # Ouders
    ouders_burgerservicenummer = (
        "ouders.burgerservicenummer",
        _("Ouders > Burgerservicenummer"),
    )
    ouders_geslacht_code = (
        "ouders.geslacht.code",
        _("Ouders > Geslacht > Code"),
    )
    ouders_geslacht_omschrijving = (
        "ouders.geslacht.omschrijving",
        _("Ouders > Geslacht > Omschrijving"),
    )
    ouders_ouderaanduiding = (
        "ouders.ouderAanduiding",
        _("Ouders > Ouderaanduiding"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_type = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.type",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Type"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_langformaat = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.langFormaat",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Lang Formaat"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_datum = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.datum",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Datum"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_onbekend = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.onbekend",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Onbekend"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_jaar = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.jaar",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Jaar"),
    )
    ouders_datumingangfamilierechtelijkebetrekking_maand = (
        "ouders.datumIngangFamilierechtelijkeBetrekking.maand",
        _("Ouders > Datum Ingang Familierechtelijke Betrekking > Maand"),
    )
    ouders_naam_voornamen = (
        "ouders.naam.voornamen",
        _("Ouders > Naam > Voornamen"),
    )
    ouders_naam_adellijketitelpredicaat_code = (
        "ouders.naam.adellijkeTitelPredicaat.code",
        _("Ouders > Naam > Adellijke Titel/Predicaat > Code"),
    )
    ouders_naam_adellijketitelpredicaat_omschrijving = (
        "ouders.naam.adellijkeTitelPredicaat.omschrijving",
        _("Ouders > Naam > Adellijke Titel/Predicaat > Omschrijving"),
    )
    ouders_naam_adellijketitelpredicaat_soort = (
        "ouders.naam.adellijkeTitelPredicaat.soort",
        _("Ouders > Naam > Adellijke Titel/Predicaat > Soort"),
    )
    ouders_naam_voorvoegsel = (
        "ouders.naam.voorvoegsel",
        _("Ouders > Naam > Voorvoegsel"),
    )
    ouders_naam_geslachtsnaam = (
        "ouders.naam.geslachtsnaam",
        _("Ouders > Naam > Geslachtsnaam"),
    )
    ouders_naam_voorletters = (
        "ouders.naam.voorletters",
        _("Ouders > Naam > Voorletters"),
    )
    ouders_geboorte_datum_type = (
        "ouders.geboorte.datum.type",
        _("Ouders > Geboorte > Datum > Type"),
    )
    ouders_geboorte_datum_langformaat = (
        "ouders.geboorte.datum.langFormaat",
        _("Ouders > Geboorte > Datum > Lang Formaat"),
    )
    ouders_geboorte_datum_datum = (
        "ouders.geboorte.datum.datum",
        _("Ouders > Geboorte > Datum > Datum"),
    )
    ouders_geboorte_datum_onbekend = (
        "ouders.geboorte.datum.onbekend",
        _("Ouders > Geboorte > Datum > Onbekend"),
    )
    ouders_geboorte_datum_jaar = (
        "ouders.geboorte.datum.jaar",
        _("Ouders > Geboorte > Datum > Jaar"),
    )
    ouders_geboorte_datum_maand = (
        "ouders.geboorte.datum.maand",
        _("Ouders > Geboorte > Datum > Maand"),
    )
    ouders_geboorte_land_code = (
        "ouders.geboorte.land.code",
        _("Ouders > Geboorte > Land > Code"),
    )
    ouders_geboorte_land_omschrijving = (
        "ouders.geboorte.land.omschrijving",
        _("Ouders > Geboorte > Land > Omschrijving"),
    )
    ouders_geboorte_plaats_code = (
        "ouders.geboorte.plaats.code",
        _("Ouders > Geboorte > Plaats > Code"),
    )
    ouders_geboorte_plaats_omschrijving = (
        "ouders.geboorte.plaats.omschrijving",
        _("Ouders > Geboorte > Plaats > Omschrijving"),
    )

    # Partners
    partners_burgerservicenummer = (
        "partners.burgerservicenummer",
        _("Partners > Burgerservicenummer"),
    )
    partners_geslacht_code = (
        "partners.geslacht.code",
        _("Partners > Geslacht > Code"),
    )
    partners_geslacht_omschrijving = (
        "partners.geslacht.omschrijving",
        _("Partners > Geslacht > Omschrijving"),
    )
    partners_soortverbintenis_code = (
        "partners.soortVerbintenis.code",
        _("Partners > Soort Verbintenis > Code"),
    )
    partners_soortverbintenis_omschrijving = (
        "partners.soortVerbintenis.omschrijving",
        _("Partners > Soort Verbintenis > Omschrijving"),
    )
    partners_naam_voornamen = (
        "partners.naam.voornamen",
        _("Partners > Naam > Voornamen"),
    )
    partners_naam_adellijketitelpredicaat_code = (
        "partners.naam.adellijkeTitelPredicaat.code",
        _("Partners > Naam > Adellijke Titel/Predicaat > Code"),
    )
    partners_naam_adellijketitelpredicaat_omschrijving = (
        "partners.naam.adellijkeTitelPredicaat.omschrijving",
        _("Partners > Naam > Adellijke Titel/Predicaat > Omschrijving"),
    )
    partners_naam_adellijketitelpredicaat_soort = (
        "partners.naam.adellijkeTitelPredicaat.soort",
        _("Partners > Naam > Adellijke Titel/Predicaat > Soort"),
    )
    partners_naam_voorvoegsel = (
        "partners.naam.voorvoegsel",
        _("Partners > Naam > Voorvoegsel"),
    )
    partners_naam_geslachtsnaam = (
        "partners.naam.geslachtsnaam",
        _("Partners > Naam > Geslachtsnaam"),
    )
    partners_naam_voorletters = (
        "partners.naam.voorletters",
        _("Partners > Naam > Voorletters"),
    )
    partners_geboorte_datum_type = (
        "partners.geboorte.datum.type",
        _("Partners > Geboorte > Datum > Type"),
    )
    partners_geboorte_datum_langformaat = (
        "partners.geboorte.datum.langFormaat",
        _("Partners > Geboorte > Datum > Lang Formaat"),
    )
    partners_geboorte_datum_datum = (
        "partners.geboorte.datum.datum",
        _("Partners > Geboorte > Datum > Datum"),
    )
    partners_geboorte_datum_onbekend = (
        "partners.geboorte.datum.onbekend",
        _("Partners > Geboorte > Datum > Onbekend"),
    )
    partners_geboorte_datum_jaar = (
        "partners.geboorte.datum.jaar",
        _("Partners > Geboorte > Datum > Jaar"),
    )
    partners_geboorte_datum_maand = (
        "partners.geboorte.datum.maand",
        _("Partners > Geboorte > Datum > Maand"),
    )
    partners_geboorte_land_code = (
        "partners.geboorte.land.code",
        _("Partners > Geboorte > Land > Code"),
    )
    partners_geboorte_land_omschrijving = (
        "partners.geboorte.land.omschrijving",
        _("Partners > Geboorte > Land > Omschrijving"),
    )
    partners_geboorte_plaats_code = (
        "partners.geboorte.plaats.code",
        _("Partners > Geboorte > Plaats > Code"),
    )
    partners_geboorte_plaats_omschrijving = (
        "partners.geboorte.plaats.omschrijving",
        _("Partners > Geboorte > Plaats > Omschrijving"),
    )
    partners_aangaanhuwelijkpartnerschap_land_code = (
        "partners.aangaanHuwelijkPartnerschap.land.code",
        _("Partners > Aangaan Huwelijk/Partnerschap > Land > Code"),
    )
    partners_aangaanhuwelijkpartnerschap_land_omschrijving = (
        "partners.aangaanHuwelijkPartnerschap.land.omschrijving",
        _("Partners > Aangaan Huwelijk/Partnerschap > Land > Omschrijving"),
    )
    partners_aangaanhuwelijkpartnerschap_plaats_code = (
        "partners.aangaanHuwelijkPartnerschap.plaats.code",
        _("Partners > Aangaan Huwelijk/Partnerschap > Plaats > Code"),
    )
    partners_aangaanhuwelijkpartnerschap_plaats_omschrijving = (
        "partners.aangaanHuwelijkPartnerschap.plaats.omschrijving",
        _("Partners > Aangaan Huwelijk/Partnerschap > Plaats > Omschrijving"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_type = (
        "partners.aangaanHuwelijkPartnerschap.datum.type",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Type"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_langformaat = (
        "partners.aangaanHuwelijkPartnerschap.datum.langFormaat",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Lang Formaat"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_datum = (
        "partners.aangaanHuwelijkPartnerschap.datum.datum",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Datum"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_onbekend = (
        "partners.aangaanHuwelijkPartnerschap.datum.onbekend",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Onbekend"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_jaar = (
        "partners.aangaanHuwelijkPartnerschap.datum.jaar",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Jaar"),
    )
    partners_aangaanhuwelijkpartnerschap_datum_maand = (
        "partners.aangaanHuwelijkPartnerschap.datum.maand",
        _("Partners > Aangaan Huwelijk/Partnerschap > Datum > Maand"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_type = (
        "partners.ontbindingHuwelijkPartnerschap.datum.type",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Type"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_langformaat = (
        "partners.ontbindingHuwelijkPartnerschap.datum.langFormaat",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Lang Formaat"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_datum = (
        "partners.ontbindingHuwelijkPartnerschap.datum.datum",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Datum"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_onbekend = (
        "partners.ontbindingHuwelijkPartnerschap.datum.onbekend",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Onbekend"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_jaar = (
        "partners.ontbindingHuwelijkPartnerschap.datum.jaar",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Jaar"),
    )
    partners_ontbindinghuwelijkpartnerschap_datum_maand = (
        "partners.ontbindingHuwelijkPartnerschap.datum.maand",
        _("Partners > Ontbinding Huwelijk/Partnerschap > Datum > Maand"),
    )
