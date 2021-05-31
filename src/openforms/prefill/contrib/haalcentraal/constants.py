from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as pg
from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    # schema: http://localhost:8021/api/schema/openapi.yaml
    # path:   /ingeschrevenpersonen/{burgerservicenummer}

    burgerservicenummer = ChoiceItem(
        "burgerservicenummer", pg("Burgerservicenummer", "Citizen service number")
    )
    datumEersteInschrijvingGBA_dag = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.dag",
        format_lazy(
            "{} > {}",
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    datumEersteInschrijvingGBA_datum = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.datum",
        format_lazy(
            "{} > {}",
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    datumEersteInschrijvingGBA_jaar = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.jaar",
        format_lazy(
            "{} > {}",
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    datumEersteInschrijvingGBA_maand = ChoiceItem(
        "_embedded.datumEersteInschrijvingGBA.maand",
        format_lazy(
            "{} > {}",
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    geboorte_datum_dag = ChoiceItem(
        "_embedded.geboorte._embedded.datum.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    geboorte_datum_datum = ChoiceItem(
        "_embedded.geboorte._embedded.datum.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    geboorte_datum_jaar = ChoiceItem(
        "_embedded.geboorte._embedded.datum.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    geboorte_datum_maand = ChoiceItem(
        "_embedded.geboorte._embedded.datum.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    geboorte_inOnderzoek_datum = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datum", "Date"),
        ),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    geboorte_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    geboorte_inOnderzoek_land = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.land",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Land", "Country"),
        ),
    )
    geboorte_inOnderzoek_plaats = ChoiceItem(
        "_embedded.geboorte._embedded.inOnderzoek.plaats",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Inonderzoek", "Under investigation"),
            pg("Plaats", "Place"),
        ),
    )
    geboorte_land_code = ChoiceItem(
        "_embedded.geboorte._embedded.land.code",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    geboorte_land_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.land.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    geboorte_plaats_code = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.code",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    geboorte_plaats_omschrijving = ChoiceItem(
        "_embedded.geboorte._embedded.plaats.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Geboorte", "Birth"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    geheimhoudingPersoonsgegevens = ChoiceItem(
        "geheimhoudingPersoonsgegevens",
        pg("Geheimhoudingpersoonsgegevens", "Confidentiality of data"),
    )
    geslachtsaanduiding = ChoiceItem(
        "geslachtsaanduiding", pg("Geslachtsaanduiding", "Gender designation")
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    gezagsverhouding_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    gezagsverhouding_inOnderzoek_indicatieCurateleRegister = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek.indicatieCurateleRegister",
        format_lazy(
            "{} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Indicatiecurateleregister", "Indication guardianship register"),
        ),
    )
    gezagsverhouding_inOnderzoek_indicatieGezagMinderjarige = ChoiceItem(
        "_embedded.gezagsverhouding._embedded.inOnderzoek.indicatieGezagMinderjarige",
        format_lazy(
            "{} > {} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Inonderzoek", "Under investigation"),
            pg("Indicatiegezagminderjarige", "Indication authority minor"),
        ),
    )
    gezagsverhouding_indicatieCurateleRegister = ChoiceItem(
        "_embedded.gezagsverhouding.indicatieCurateleRegister",
        format_lazy(
            "{} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Indicatiecurateleregister", "Indication guardianship register"),
        ),
    )
    gezagsverhouding_indicatieGezagMinderjarige = ChoiceItem(
        "_embedded.gezagsverhouding.indicatieGezagMinderjarige",
        format_lazy(
            "{} > {}",
            pg("Gezagsverhouding", "Relationship of authority"),
            pg("Indicatiegezagminderjarige", "Indication authority minor"),
        ),
    )
    inOnderzoek_burgerservicenummer = ChoiceItem(
        "_embedded.inOnderzoek.burgerservicenummer",
        format_lazy(
            "{} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Burgerservicenummer", "Citizen service number"),
        ),
    )
    inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    inOnderzoek_geslachtsaanduiding = ChoiceItem(
        "_embedded.inOnderzoek.geslachtsaanduiding",
        format_lazy(
            "{} > {}",
            pg("Inonderzoek", "Under investigation"),
            pg("Geslachtsaanduiding", "Gender designation"),
        ),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_dag = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_jaar = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    kiesrecht_einddatumUitsluitingEuropeesKiesrecht_maand = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingEuropeesKiesrecht.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_dag = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_datum = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_jaar = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    kiesrecht_einddatumUitsluitingKiesrecht_maand = ChoiceItem(
        "_embedded.kiesrecht._embedded.einddatumUitsluitingKiesrecht.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    kiesrecht_europeesKiesrecht = ChoiceItem(
        "_embedded.kiesrecht.europeesKiesrecht",
        format_lazy(
            "{} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Europeeskiesrecht", "European suffrage"),
        ),
    )
    kiesrecht_uitgeslotenVanKiesrecht = ChoiceItem(
        "_embedded.kiesrecht.uitgeslotenVanKiesrecht",
        format_lazy(
            "{} > {}",
            pg("Kiesrecht", "Right to vote"),
            pg("Uitgeslotenvankiesrecht", "Excluded from suffrage"),
        ),
    )
    leeftijd = ChoiceItem("leeftijd", pg("Leeftijd", "Age"))
    naam_aanduidingNaamgebruik = ChoiceItem(
        "_embedded.naam.aanduidingNaamgebruik",
        format_lazy(
            "{} > {}",
            pg("Naam", "Name"),
            pg("Aanduidingnaamgebruik", "Indication of name usage"),
        ),
    )
    naam_aanhef = ChoiceItem(
        "_embedded.naam.aanhef",
        format_lazy("{} > {}", pg("Naam", "Name"), pg("Aanhef", "Salutation")),
    )
    naam_aanschrijfwijze = ChoiceItem(
        "_embedded.naam.aanschrijfwijze",
        format_lazy(
            "{} > {}", pg("Naam", "Name"), pg("Aanschrijfwijze", "Notification")
        ),
    )
    naam_gebruikInLopendeTekst = ChoiceItem(
        "_embedded.naam.gebruikInLopendeTekst",
        format_lazy(
            "{} > {}", pg("Naam", "Name"), pg("Gebruikinlopendetekst", "Use in text")
        ),
    )
    naam_geslachtsnaam = ChoiceItem(
        "_embedded.naam.geslachtsnaam",
        format_lazy("{} > {}", pg("Naam", "Name"), pg("Geslachtsnaam", "Last name")),
    )
    naam_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    naam_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    naam_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    naam_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    naam_inOnderzoek_geslachtsnaam = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.geslachtsnaam",
        format_lazy(
            "{} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Geslachtsnaam", "Last name"),
        ),
    )
    naam_inOnderzoek_voornamen = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.voornamen",
        format_lazy(
            "{} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Voornamen", "First names"),
        ),
    )
    naam_inOnderzoek_voorvoegsel = ChoiceItem(
        "_embedded.naam._embedded.inOnderzoek.voorvoegsel",
        format_lazy(
            "{} > {} > {}",
            pg("Naam", "Name"),
            pg("Inonderzoek", "Under investigation"),
            pg("Voorvoegsel", "Prefix"),
        ),
    )
    naam_voorletters = ChoiceItem(
        "_embedded.naam.voorletters",
        format_lazy("{} > {}", pg("Naam", "Name"), pg("Voorletters", "Initials")),
    )
    naam_voornamen = ChoiceItem(
        "_embedded.naam.voornamen",
        format_lazy("{} > {}", pg("Naam", "Name"), pg("Voornamen", "First names")),
    )
    naam_voorvoegsel = ChoiceItem(
        "_embedded.naam.voorvoegsel",
        format_lazy("{} > {}", pg("Naam", "Name"), pg("Voorvoegsel", "Prefix")),
    )
    opschortingBijhouding_datum_dag = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Opschortingbijhouding", "Suspension Tracking"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    opschortingBijhouding_datum_datum = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Opschortingbijhouding", "Suspension Tracking"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    opschortingBijhouding_datum_jaar = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Opschortingbijhouding", "Suspension Tracking"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    opschortingBijhouding_datum_maand = ChoiceItem(
        "_embedded.opschortingBijhouding._embedded.datum.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Opschortingbijhouding", "Suspension Tracking"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    opschortingBijhouding_reden = ChoiceItem(
        "_embedded.opschortingBijhouding.reden",
        format_lazy(
            "{} > {}",
            pg("Opschortingbijhouding", "Suspension Tracking"),
            pg("Reden", "Reason"),
        ),
    )
    overlijden_datum_dag = ChoiceItem(
        "_embedded.overlijden._embedded.datum.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    overlijden_datum_datum = ChoiceItem(
        "_embedded.overlijden._embedded.datum.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    overlijden_datum_jaar = ChoiceItem(
        "_embedded.overlijden._embedded.datum.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    overlijden_datum_maand = ChoiceItem(
        "_embedded.overlijden._embedded.datum.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    overlijden_inOnderzoek_datum = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datum", "Date"),
        ),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    overlijden_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    overlijden_inOnderzoek_land = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.land",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Land", "Country"),
        ),
    )
    overlijden_inOnderzoek_plaats = ChoiceItem(
        "_embedded.overlijden._embedded.inOnderzoek.plaats",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Inonderzoek", "Under investigation"),
            pg("Plaats", "Place"),
        ),
    )
    overlijden_indicatieOverleden = ChoiceItem(
        "_embedded.overlijden.indicatieOverleden",
        format_lazy(
            "{} > {}",
            pg("Overlijden", "Passed away"),
            pg("Indicatieoverleden", "Indication deceased"),
        ),
    )
    overlijden_land_code = ChoiceItem(
        "_embedded.overlijden._embedded.land.code",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    overlijden_land_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.land.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    overlijden_plaats_code = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.code",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    overlijden_plaats_omschrijving = ChoiceItem(
        "_embedded.overlijden._embedded.plaats.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Overlijden", "Passed away"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    verblijfplaats_aanduidingBijHuisnummer = ChoiceItem(
        "_embedded.verblijfplaats.aanduidingBijHuisnummer",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Aanduidingbijhuisnummer", "Indication of house number"),
        ),
    )
    verblijfplaats_datumAanvangAdreshouding_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfplaats_datumAanvangAdreshouding_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfplaats_datumAanvangAdreshouding_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfplaats_datumAanvangAdreshouding_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumAanvangAdreshouding.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfplaats_datumIngangGeldigheid_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfplaats_datumIngangGeldigheid_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfplaats_datumIngangGeldigheid_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfplaats_datumIngangGeldigheid_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumIngangGeldigheid.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfplaats_datumInschrijvingInGemeente_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfplaats_datumInschrijvingInGemeente_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfplaats_datumInschrijvingInGemeente_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfplaats_datumInschrijvingInGemeente_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumInschrijvingInGemeente.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfplaats_datumVestigingInNederland_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfplaats_datumVestigingInNederland_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfplaats_datumVestigingInNederland_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfplaats_datumVestigingInNederland_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.datumVestigingInNederland.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfplaats_functieAdres = ChoiceItem(
        "_embedded.verblijfplaats.functieAdres",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Functieadres", "Function address"),
        ),
    )
    verblijfplaats_gemeenteVanInschrijving_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.code",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    verblijfplaats_gemeenteVanInschrijving_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.gemeenteVanInschrijving.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    verblijfplaats_huisletter = ChoiceItem(
        "_embedded.verblijfplaats.huisletter",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Huisletter", "House letter"),
        ),
    )
    verblijfplaats_huisnummer = ChoiceItem(
        "_embedded.verblijfplaats.huisnummer",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Huisnummer", "House number"),
        ),
    )
    verblijfplaats_huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats.huisnummertoevoeging",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Huisnummertoevoeging", "House number addition"),
        ),
    )
    verblijfplaats_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeAdresseerbaarObject",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Identificatiecodeadresseerbaarobject", "Identifier AddressableObject"),
        ),
    )
    verblijfplaats_identificatiecodeNummeraanduiding = ChoiceItem(
        "_embedded.verblijfplaats.identificatiecodeNummeraanduiding",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg(
                "Identificatiecodenummeraanduiding",
                "Identification code number designation",
            ),
        ),
    )
    verblijfplaats_inOnderzoek_aanduidingBijHuisnummer = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.aanduidingBijHuisnummer",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Aanduidingbijhuisnummer", "Indication of house number"),
        ),
    )
    verblijfplaats_inOnderzoek_datumAanvangAdreshouding = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumAanvangAdreshouding",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumaanvangadreshouding", "Date of commencement of address holding"),
        ),
    )
    verblijfplaats_inOnderzoek_datumIngangGeldigheid = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumIngangGeldigheid",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datuminganggeldigheid", "Date Effectiveness"),
        ),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfplaats_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfplaats_inOnderzoek_datumInschrijvingInGemeente = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumInschrijvingInGemeente",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg(
                "Datuminschrijvingingemeente",
                "Date of registration in the municipality",
            ),
        ),
    )
    verblijfplaats_inOnderzoek_datumVestigingInNederland = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.datumVestigingInNederland",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumvestiginginnederland", "Date settlement in the Netherlands"),
        ),
    )
    verblijfplaats_inOnderzoek_functieAdres = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.functieAdres",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Functieadres", "Function address"),
        ),
    )
    verblijfplaats_inOnderzoek_gemeenteVanInschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.gemeenteVanInschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Gemeentevaninschrijving", "Municipal registration"),
        ),
    )
    verblijfplaats_inOnderzoek_huisletter = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisletter",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Huisletter", "House letter"),
        ),
    )
    verblijfplaats_inOnderzoek_huisnummer = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisnummer",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Huisnummer", "House number"),
        ),
    )
    verblijfplaats_inOnderzoek_huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.huisnummertoevoeging",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Huisnummertoevoeging", "House number addition"),
        ),
    )
    verblijfplaats_inOnderzoek_identificatiecodeAdresseerbaarObject = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.identificatiecodeAdresseerbaarObject",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Identificatiecodeadresseerbaarobject", "Identifier AddressableObject"),
        ),
    )
    verblijfplaats_inOnderzoek_identificatiecodeNummeraanduiding = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.identificatiecodeNummeraanduiding",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg(
                "Identificatiecodenummeraanduiding",
                "Identification code number designation",
            ),
        ),
    )
    verblijfplaats_inOnderzoek_landVanwaarIngeschreven = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.landVanwaarIngeschreven",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Landvanwaaringeschreven", "Country of registration"),
        ),
    )
    verblijfplaats_inOnderzoek_locatiebeschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.locatiebeschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Locatiebeschrijving", "Location description"),
        ),
    )
    verblijfplaats_inOnderzoek_naamOpenbareRuimte = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.naamOpenbareRuimte",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Naamopenbareruimte", "Name public space"),
        ),
    )
    verblijfplaats_inOnderzoek_postcode = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.postcode",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Postcode", "Postal Code"),
        ),
    )
    verblijfplaats_inOnderzoek_straatnaam = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.straatnaam",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Straatnaam", "Street name"),
        ),
    )
    verblijfplaats_inOnderzoek_verblijfBuitenland = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.verblijfBuitenland",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Verblijfbuitenland", "Abroad"),
        ),
    )
    verblijfplaats_inOnderzoek_woonplaatsnaam = ChoiceItem(
        "_embedded.verblijfplaats._embedded.inOnderzoek.woonplaatsnaam",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Inonderzoek", "Under investigation"),
            pg("Woonplaatsnaam", "City name"),
        ),
    )
    verblijfplaats_indicatieVestigingVanuitBuitenland = ChoiceItem(
        "_embedded.verblijfplaats.indicatieVestigingVanuitBuitenland",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg(
                "Indicatievestigingvanuitbuitenland",
                "Indication establishment from abroad",
            ),
        ),
    )
    verblijfplaats_landVanwaarIngeschreven_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.code",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    verblijfplaats_landVanwaarIngeschreven_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.landVanwaarIngeschreven.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    verblijfplaats_locatiebeschrijving = ChoiceItem(
        "_embedded.verblijfplaats.locatiebeschrijving",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Locatiebeschrijving", "Location description"),
        ),
    )
    verblijfplaats_naamOpenbareRuimte = ChoiceItem(
        "_embedded.verblijfplaats.naamOpenbareRuimte",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Naamopenbareruimte", "Name public space"),
        ),
    )
    verblijfplaats_postcode = ChoiceItem(
        "_embedded.verblijfplaats.postcode",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Postcode", "Postal Code"),
        ),
    )
    verblijfplaats_straatnaam = ChoiceItem(
        "_embedded.verblijfplaats.straatnaam",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Straatnaam", "Street name"),
        ),
    )
    verblijfplaats_vanuitVertrokkenOnbekendWaarheen = ChoiceItem(
        "_embedded.verblijfplaats.vanuitVertrokkenOnbekendWaarheen",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Vanuitvertrokkenonbekendwaarheen", "Departed unknown destination"),
        ),
    )
    verblijfplaats_verblijfBuitenland_adresRegel1 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel1",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Adresregel1", "Address Line 1"),
        ),
    )
    verblijfplaats_verblijfBuitenland_adresRegel2 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel2",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Adresregel2", "Address Line 2"),
        ),
    )
    verblijfplaats_verblijfBuitenland_adresRegel3 = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.adresRegel3",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Adresregel3", "Address Line 3"),
        ),
    )
    verblijfplaats_verblijfBuitenland_land_code = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.code",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    verblijfplaats_verblijfBuitenland_land_omschrijving = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland._embedded.land.omschrijving",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    verblijfplaats_verblijfBuitenland_vertrokkenOnbekendWaarheen = ChoiceItem(
        "_embedded.verblijfplaats._embedded.verblijfBuitenland.vertrokkenOnbekendWaarheen",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Verblijfbuitenland", "Abroad"),
            pg("Vertrokkenonbekendwaarheen", "Departed known destination"),
        ),
    )
    verblijfplaats_woonplaatsnaam = ChoiceItem(
        "_embedded.verblijfplaats.woonplaatsnaam",
        format_lazy(
            "{} > {}",
            pg("Verblijfplaats", "Where to stay"),
            pg("Woonplaatsnaam", "City name"),
        ),
    )
    verblijfstitel_aanduiding_code = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.code",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Land", "Country"),
            pg("Code", "Code"),
        ),
    )
    verblijfstitel_aanduiding_omschrijving = ChoiceItem(
        "_embedded.verblijfstitel._embedded.aanduiding.omschrijving",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Land", "Country"),
            pg("Omschrijving", "Description"),
        ),
    )
    verblijfstitel_datumEinde_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfstitel_datumEinde_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfstitel_datumEinde_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfstitel_datumEinde_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumEinde.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfstitel_datumIngang_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.dag",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfstitel_datumIngang_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.datum",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfstitel_datumIngang_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.jaar",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfstitel_datumIngang_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.datumIngang.maand",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
    verblijfstitel_inOnderzoek_aanduiding = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.aanduiding",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Aanduiding", "Designation"),
        ),
    )
    verblijfstitel_inOnderzoek_datumEinde = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.datumEinde",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumeinde", "End date"),
        ),
    )
    verblijfstitel_inOnderzoek_datumIngang = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek.datumIngang",
        format_lazy(
            "{} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingang", "Date entry"),
        ),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_dag = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.dag",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Dag", "Day"),
        ),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_datum = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.datum",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Datum", "Date"),
        ),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_jaar = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.jaar",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Jaar", "Year"),
        ),
    )
    verblijfstitel_inOnderzoek_datumIngangOnderzoek_maand = ChoiceItem(
        "_embedded.verblijfstitel._embedded.inOnderzoek._embedded.datumIngangOnderzoek.maand",
        format_lazy(
            "{} > {} > {} > {}",
            pg("Verblijfstitel", "Residence permit"),
            pg("Inonderzoek", "Under investigation"),
            pg("Datumingangonderzoek", "Date of entry inquiry"),
            pg("Maand", "Month"),
        ),
    )
