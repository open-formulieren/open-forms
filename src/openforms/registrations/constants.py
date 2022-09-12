from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

# field name in the component configuration JSON schema
REGISTRATION_ATTRIBUTE = "registration.attribute"


class RegistrationAttribute(DjangoChoices):
    # Initiator
    # Natuurlijk Persoon
    initiator_voorletters = ChoiceItem(
        "initiator_voorletters", _("Initiator > Voorletters")
    )
    initiator_voornamen = ChoiceItem("initiator_voornamen", _("Initiator > Voornamen"))
    initiator_geslachtsnaam = ChoiceItem(
        "initiator_geslachtsnaam", _("Initiator > Geslachtsnaam")
    )
    initiator_tussenvoegsel = ChoiceItem(
        "initiator_tussenvoegsel", _("Initiator > Tussenvoegsel")
    )
    initiator_geslachtsaanduiding = ChoiceItem(
        "initiator_geslachtsaanduiding", _("Initiator > Geslachtsaanduiding")
    )
    initiator_geboortedatum = ChoiceItem(
        "initiator_geboortedatum", _("Initiator > Geboortedatum")
    )
    initiator_aanschrijfwijze = ChoiceItem(
        "initiator_aanschrijfwijze", _("Initiator > Aanschrijfwijze")
    )

    # Verblijfsadres for both Natuurlijk Persoon and Vestiging
    initiator_straat = ChoiceItem("Strainitiator_straatat", _("Initiator > Straat"))
    initiator_huisnummer = ChoiceItem(
        "initiator_huisnummer", _("Initiator > Huisnummer")
    )
    initiator_huisletter = ChoiceItem(
        "initiator_huisletter", _("Initiator > Huisletter")
    )
    initiator_huisnummer_toevoeging = ChoiceItem(
        "initiator_huisnummer_toevoeging", _("Initiator > Huisnummertoevoeging")
    )
    initiator_postcode = ChoiceItem("initiator_postcode", _("Initiator > Postcode"))
    initiator_woonplaats = ChoiceItem(
        "initiator_woonplaats", _("Initiator > Woonplaats")
    )

    # Contactpersoon
    initiator_telefoonnummer = ChoiceItem(
        "initiator_telefoonnummer", _("Initiator > Telefoonnummer")
    )
    initiator_emailadres = ChoiceItem("initiator_emailadres", _("Initiator > E-mail"))

    # Vestiging
    initiator_handelsnaam = ChoiceItem(
        "initiator_handelsnaam", _("Initiator > Handelsnaam")
    )
    initiator_kvk_nummer = ChoiceItem(
        "initiator_kvk_nummer", _("Initiator > KvK-nummer")
    )
    initiator_vestigingsnummer = ChoiceItem(
        "initiator_vestigingsnummer", _("Initiator > Vestigingsnummer")
    )

    # Location
    locatie_coordinaat = ChoiceItem("locatie_coordinaat", _("Location > Coordinate"))
