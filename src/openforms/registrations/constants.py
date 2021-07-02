from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

UNIQUE_ID_MAX_LENGTH = 100


class RegistrationAttribute(DjangoChoices):
    initiator_voornamen = ChoiceItem("initiator_voornamen", _("Initiator > Voornamen"))
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
