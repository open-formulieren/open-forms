from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

# field name in the component configuration JSON schema
REGISTRATION_ATTRIBUTE = "registration.attribute"


class RegistrationAttribute(DjangoChoices):
    initiator_voornamen = ChoiceItem("initiator_voornamen", _("Initiator > Voornamen"))
    initiator_voorletters = ChoiceItem(
        "initiator_voorletters", _("Initiator > Voorletters")
    )
    initiator_geslachtsnaam = ChoiceItem(
        "initiator_geslachtsnaam", _("Initiator > Geslachtsnaam")
    )
    initiator_tussenvoegsel = ChoiceItem(
        "initiator_tussenvoegsel", _("Initiator > Tussenvoegsel")
    )
    initiator_geboortedatum = ChoiceItem(
        "initiator_geboortedatum", _("Initiator > Geboortedatum")
    )
    initiator_aanschrijfwijze = ChoiceItem(
        "initiator_aanschrijfwijze", _("Initiator > Aanschrijfwijze")
    )

    initiator_handelsnaam = ChoiceItem(
        "initiator_handelsnaam", _("Initiator > Handelsnaam")
    )
    initiator_kvk_nummer = ChoiceItem(
        "initiator_kvk_nummer", _("Initiator > KvK nummer")
    )
    initiator_vestigingsnummer = ChoiceItem(
        "initiator_vestigingsnummer", _("Initiator > Vestigingsnummer")
    )

    initiator_straat = ChoiceItem("initiator_straat", _("Initiator > Straat"))
    initiator_huisnummer = ChoiceItem(
        "initiator_huisnummer", _("Initiator > Huisnummer")
    )
    initiator_huisletter = ChoiceItem(
        "initiator_huisletter", _("Initiator > Huisletter")
    )
    initiator_huisnummer_toevoeging = ChoiceItem(
        "initiator_huisnummer_toevoeging", _("Initiator > Huisnummer toevoeging")
    )
    initiator_postcode = ChoiceItem("initiator_postcode", _("Initiator > Postcode"))
    initiator_woonplaats = ChoiceItem(
        "initiator_woonplaats", _("Initiator > Woonplaats")
    )
    initiator_telefoonnummer = ChoiceItem(
        "initiator_telefoonnummer", _("Initiator > Telefoonnummer")
    )
    initiator_mailadres = ChoiceItem("initiator_mailadres", _("Initiator > Mailadres"))

    # locatie
    locatie_coordinaat = ChoiceItem("locatie_coordinaat", _("Locatie > Coordinaat"))

    locatie_straat = ChoiceItem("locatie_straat", _("Locatie > Straat"))
    locatie_huisnummer = ChoiceItem("locatie_huisnummer", _("Locatie > Huisnummer"))
    locatie_huisletter = ChoiceItem("locatie_huisletter", _("Locatie > Huisletter"))
    locatie_huisnummer_toevoeging = ChoiceItem(
        "locatie_huisnummer_toevoeging", _("Locatie > Huisnummer toevoeging")
    )
    locatie_postcode = ChoiceItem("locatie_postcode", _("Locatie > Postcode"))
    locatie_stad = ChoiceItem("locatie_stad", _("Derde partij > Stad"))

    # roles

    # derdepartij
    derdepartij_voornamen = ChoiceItem(
        "derdepartij_voornamen", _("Derde partij > Voornamen")
    )
    derdepartij_voorletters = ChoiceItem(
        "derdepartij_voorletters", _("Derde partij > Voorletters")
    )
    derdepartij_tussenvoegsel = ChoiceItem(
        "derdepartij_tussenvoegsel", _("Derde partij > Tussenvoegsel")
    )
    derdepartij_geslachtsnaam = ChoiceItem(
        "derdepartij_geslachtsnaam", _("Derde partij > Geslachtsnaam")
    )
    derdepartij_straat = ChoiceItem("derdepartij_straat", _("Derde partij > Straat"))
    derdepartij_huisnummer = ChoiceItem(
        "derdepartij_huisnummer", _("Derde partij > Huisnummer")
    )
    derdepartij_huisletter = ChoiceItem(
        "derdepartij_huisletter", _("Derde partij > Huisletter")
    )
    derdepartij_huisnummer_toevoeging = ChoiceItem(
        "derdepartij_huisnummer_toevoeging", _("Derde partij > Huisnummer toevoeging")
    )
    derdepartij_postcode = ChoiceItem(
        "derdepartij_postcode", _("Derde partij > Postcode")
    )
    derdepartij_stad = ChoiceItem("derdepartij_stad", _("Derde partij > Stad"))
    derdepartij_telefoonnummer = ChoiceItem(
        "derdepartij_telefoonnummer", _("Derde partij > Telefoonnummer")
    )
    derdepartij_mailadres = ChoiceItem(
        "derdepartij_mailadres", _("Derde partij > Mailadres")
    )

    # contactpersoon
    contact_voornamen = ChoiceItem("contact_voornamen", _("Contactpersoon > Voornamen"))
    contact_voorletters = ChoiceItem(
        "contact_voorletters", _("Contactpersoon > Voorletters")
    )
    contact_tussenvoegsel = ChoiceItem(
        "contact_tussenvoegsel", _("Contactpersoon > Tussenvoegsel")
    )
    contact_geslachtsnaam = ChoiceItem(
        "contact_geslachtsnaam", _("Contactpersoon > Geslachtsnaam")
    )
    contact_straat = ChoiceItem("contact_straat", _("Contactpersoon > Straat"))
    contact_huisnummer = ChoiceItem(
        "contact_huisnummer", _("Contactpersoon > Huisnummer")
    )
    contact_huisletter = ChoiceItem(
        "contact_huisletter", _("Contactpersoon > Huisletter")
    )
    contact_huisnummer_toevoeging = ChoiceItem(
        "contact_huisnummer_toevoeging", _("Contactpersoon > Huisnummer toevoeging")
    )
    contact_postcode = ChoiceItem("contact_postcode", _("Contactpersoon > Postcode"))
    contact_stad = ChoiceItem("contact_stad", _("Contactpersoon > Stad"))
    contact_telefoonnummer = ChoiceItem(
        "contact_telefoonnummer", _("Contactpersoon > Telefoonnummer")
    )
    contact_mailadres = ChoiceItem("contact_mailadres", _("Contactpersoon > Mailadres"))

    # gemachtigde
    gemachtigde_voornamen = ChoiceItem(
        "gemachtigde_voornamen", _("Gemachtigde > Voornamen")
    )
    gemachtigde_voorletters = ChoiceItem(
        "gemachtigde_voorletters", _("Gemachtigde > Voorletters")
    )
    gemachtigde_tussenvoegsel = ChoiceItem(
        "gemachtigde_tussenvoegsel", _("Gemachtigde > Tussenvoegsel")
    )
    gemachtigde_geslachtsnaam = ChoiceItem(
        "gemachtigde_geslachtsnaam", _("Gemachtigde > Geslachtsnaam")
    )
    gemachtigde_straat = ChoiceItem("gemachtigde_straat", _("Gemachtigde > Straat"))
    gemachtigde_huisnummer = ChoiceItem(
        "gemachtigde_huisnummer", _("Gemachtigde > Huisnummer")
    )
    gemachtigde_huisletter = ChoiceItem(
        "gemachtigde_huisletter", _("Gemachtigde > Huisletter")
    )
    gemachtigde_huisnummer_toevoeging = ChoiceItem(
        "gemachtigde_huisnummer_toevoeging", _("Gemachtigde > Huisnummer toevoeging")
    )
    gemachtigde_postcode = ChoiceItem(
        "gemachtigde_postcode", _("Gemachtigde > Postcode")
    )
    gemachtigde_stad = ChoiceItem("gemachtigde_stad", _("Gemachtigde > Stad"))
    gemachtigde_telefoonnummer = ChoiceItem(
        "gemachtigde_telefoonnummer", _("Gemachtigde > Telefoonnummer")
    )
    gemachtigde_mailadres = ChoiceItem(
        "gemachtigde_mailadres", _("Gemachtigde > Mailadres")
    )

    # overige rollen
    overige_voornamen = ChoiceItem("overige_voornamen", _("Overige rollen > Voornamen"))
    overige_voorletters = ChoiceItem(
        "overige_voorletters", _("Overige rollen > Voorletters")
    )
    overige_tussenvoegsel = ChoiceItem(
        "overige_tussenvoegsel", _("Overige rollen > Tussenvoegsel")
    )
    overige_geslachtsnaam = ChoiceItem(
        "overige_geslachtsnaam", _("Overige rollen > Geslachtsnaam")
    )
    overige_straat = ChoiceItem("overige_straat", _("Overige rollen > Straat"))
    overige_huisnummer = ChoiceItem(
        "overige_huisnummer", _("Overige rollen > Huisnummer")
    )
    overige_huisletter = ChoiceItem(
        "overige_huisletter", _("Overige rollen > Huisletter")
    )
    overige_huisnummer_toevoeging = ChoiceItem(
        "overige_huisnummer_toevoeging", _("Overige rollen > Huisnummer toevoeging")
    )
    overige_postcode = ChoiceItem("overige_postcode", _("Overige rollen > Postcode"))
    overige_stad = ChoiceItem("overige_stad", _("Overige rollen > Stad"))
    overige_telefoonnummer = ChoiceItem(
        "overige_telefoonnummer", _("Overige rollen > Telefoonnummer")
    )
    overige_mailadres = ChoiceItem("overige_mailadres", _("Overige rollen > Mailadres"))
