from django.db import models
from django.utils.translation import gettext_lazy as _

# field name in the component configuration JSON schema
REGISTRATION_ATTRIBUTE = "registration.attribute"


class RegistrationAttribute(models.TextChoices):
    # Initiator
    # Medewerker
    initiator_medewerker_nummer = "medewerker_nummer", _("Employee > Employee number")
    # Natuurlijk Persoon
    initiator_voorletters = "initiator_voorletters", _("Initiator > Voorletters")
    initiator_voornamen = "initiator_voornamen", _("Initiator > Voornamen")
    initiator_geslachtsnaam = "initiator_geslachtsnaam", _("Initiator > Geslachtsnaam")
    initiator_tussenvoegsel = "initiator_tussenvoegsel", _("Initiator > Tussenvoegsel")
    initiator_geslachtsaanduiding = (
        "initiator_geslachtsaanduiding",
        _("Initiator > Geslachtsaanduiding"),
    )
    initiator_geboortedatum = "initiator_geboortedatum", _("Initiator > Geboortedatum")
    initiator_aanschrijfwijze = (
        "initiator_aanschrijfwijze",
        _("Initiator > Aanschrijfwijze"),
    )

    # Verblijfsadres for both Natuurlijk Persoon and Vestiging
    initiator_straat = "initiator_straat", _("Initiator > Straat")
    initiator_huisnummer = "initiator_huisnummer", _("Initiator > Huisnummer")
    initiator_huisletter = "initiator_huisletter", _("Initiator > Huisletter")
    initiator_huisnummer_toevoeging = (
        "initiator_huisnummer_toevoeging",
        _("Initiator > Huisnummertoevoeging"),
    )
    initiator_postcode = "initiator_postcode", _("Initiator > Postcode")
    initiator_woonplaats = "initiator_woonplaats", _("Initiator > Woonplaats")

    # Vestiging
    initiator_handelsnaam = "initiator_handelsnaam", _("Initiator > Handelsnaam")
    initiator_vestigingsnummer = (
        "initiator_vestigingsnummer",
        _("Initiator > Vestigingsnummer"),
    )

    # Location
    locatie_coordinaat = "locatie_coordinaat", _("Location > Coordinate")

    # Partners
    partners = "partners", _("Partners")
