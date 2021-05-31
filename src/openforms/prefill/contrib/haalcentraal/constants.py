from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

# class Attributes(DjangoChoices):
#     voornamen = ChoiceItem("_embedded.naam.voornamen", _("Voornamen"))
#     geslachtsnaam = ChoiceItem("_embedded.naam.geslachtsnaam", _("Geslachtsnaam"))
#
#     straatnaam = ChoiceItem("_embedded.verblijfplaats.straatnaam", _("Straatnaam"))
#     huisnummer = ChoiceItem("_embedded.verblijfplaats.huisnummer", _("Huisnummer"))
#     huisletter = ChoiceItem("_embedded.verblijfplaats.huisletter", _("Huisletter"))
#     huisnummertoevoeging = ChoiceItem(
#         "_embedded.verblijfplaats.huisnummertoevoeging", _("Huisnummer Toevoeging")
#     )
#     postcode = ChoiceItem("_embedded.verblijfplaats.postcode", _("Postcode"))
#     woonplaatsNaam = ChoiceItem(
#         "_embedded.verblijfplaats.woonplaatsnaam", _("Woonplaats Naam")
#     )


class Attributes(DjangoChoices):
    burgerservicenummer = ChoiceItem("burgerservicenummer", _("Burgerservicenummer"))
    datumEersteInschrijvingGBA_datum = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.datum", _("Datum")
    )
    geboorte_datum_datum = ChoiceItem(
        "_embedded.geboorte._embedded.datum.datum", _("Datum")
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
    geboorte_land_code = ChoiceItem("_embedded.geboorte._embedded.land.code", _("Code"))
    geboorte_land_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.land.omschrijving", _("Omschrijving")
    )
    geboorte_plaats_code = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.code", _("Code")
    )
    geboorte_plaats_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.omschrijving", _("Omschrijving")
    )
    geslachtsaanduiding = ChoiceItem("geslachtsaanduiding", _("Geslachtsaanduiding"))
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
    gezagsverhouding_indicatieGezagMinderjarige = ChoiceItem(
        "_embedded.gezagsverhouding.indicatieGezagMinderjarige",
        _("Indicatiegezagminderjarige"),
    )
    inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum", _("Datum")
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.datum",
        _("Datum"),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.datum", _("Datum")
    )
    naam_aanduidingNaamgebruik = ChoiceItem(
        "_embedded.naam.aanduidingNaamgebruik", _("Aanduidingnaamgebruik")
    )
    naam_aanhef = ChoiceItem("_embedded.naam.aanhef", _("Aanhef"))
    naam_aanschrijfwijze = ChoiceItem(
        "_embedded.naam.aanschrijfwijze", _("Aanschrijfwijze")
    )
    naam_gebruikInLopendeTekst = ChoiceItem(
        "_embedded.naam.gebruikInLopendeTekst", _("Gebruikinlopendetekst")
    )
    naam_geslachtsnaam = ChoiceItem("_embedded.naam.geslachtsnaam", _("Geslachtsnaam"))
    naam_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
    naam_voorletters = ChoiceItem("_embedded.naam.voorletters", _("Voorletters"))
    naam_voornamen = ChoiceItem("_embedded.naam.voornamen", _("Voornamen"))
    naam_voorvoegsel = ChoiceItem("_embedded.naam.voorvoegsel", _("Voorvoegsel"))
    opschortingBijhouding_datum_datum = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.datum", _("Datum")
    )
    opschortingBijhouding_reden = ChoiceItem(
        "_embedded.opschortingBijhouding.reden", _("Reden")
    )
    overlijden_datum_datum = ChoiceItem(
        "_embedded.overlijden._embedded.datum.datum", _("Datum")
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
    overlijden_land_code = ChoiceItem(
        "_embedded.overlijden._embedded.land.code", _("Code")
    )
    overlijden_land_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.land.omschrijving", _("Omschrijving")
    )
    overlijden_plaats_code = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.code", _("Code")
    )
    overlijden_plaats_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.omschrijving", _("Omschrijving")
    )
    verblijfplaats_aanduidingBijHuisnummer = ChoiceItem(
        "_embedded.verblijfplaats.aanduidingBijHuisnummer", _("Aanduidingbijhuisnummer")
    )
    verblijfplaats_datumAanvangAdreshouding_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.datum", _("Datum")
    )
    verblijfplaats_datumIngangGeldigheid_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.datum", _("Datum")
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.datum",
        _("Datum"),
    )
    verblijfplaats_datumVestigingInNederland_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.datum", _("Datum")
    )
    verblijfplaats_functieAdres = ChoiceItem(
        "_embedded.verblijfplaats.functieAdres", _("Functieadres")
    )
    verblijfplaats_gemeenteVanInschrijving_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.code", _("Code")
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.omschrijving",
        _("Omschrijving"),
    )
    verblijfplaats_huisletter = ChoiceItem(
        "_embedded.verblijfplaats.huisletter", _("Huisletter")
    )
    verblijfplaats_huisnummer = ChoiceItem(
        "_embedded.verblijfplaats.huisnummer", _("Huisnummer")
    )
    verblijfplaats_huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats.huisnummertoevoeging", _("Huisnummertoevoeging")
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeAdresseerbaarObject",
        _("Identificatiecodeadresseerbaarobject"),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeNummeraanduiding",
        _("Identificatiecodenummeraanduiding"),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
    verblijfplaats_landVanwaarIngeschreven_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.code", _("Code")
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.omschrijving",
        _("Omschrijving"),
    )
    verblijfplaats_locatiebeschrijving = ChoiceItem(
        "_embedded.verblijfplaats.locatiebeschrijving", _("Locatiebeschrijving")
    )
    verblijfplaats_naamOpenbareRuimte = ChoiceItem(
        "_embedded.verblijfplaats.naamOpenbareRuimte", _("Naamopenbareruimte")
    )
    verblijfplaats_postcode = ChoiceItem(
        "_embedded.verblijfplaats.postcode", _("Postcode")
    )
    verblijfplaats_straatnaam = ChoiceItem(
        "_embedded.verblijfplaats.straatnaam", _("Straatnaam")
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel1",
        _("Adresregel1"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel2",
        _("Adresregel2"),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel3",
        _("Adresregel3"),
    )
    verblijfplaats_verblijfBuitenland_land_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.code",
        _("Code"),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.omschrijving",
        _("Omschrijving"),
    )
    verblijfplaats_woonplaatsnaam = ChoiceItem(
        "_embedded.verblijfplaats.woonplaatsnaam", _("Woonplaatsnaam")
    )
    verblijfstitel_aanduiding_code = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.code", _("Code")
    )
    verblijfstitel_aanduiding_omschrijving = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.omschrijving", _("Omschrijving")
    )
    verblijfstitel_datumEinde_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.datum", _("Datum")
    )
    verblijfstitel_datumIngang_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.datum", _("Datum")
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        _("Datum"),
    )
