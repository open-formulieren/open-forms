from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    bsn = ChoiceItem("bsn", _("BSN"))
    voornamen = ChoiceItem("voornamen", _("Voornamen"))
    geslachtsnaam = ChoiceItem("geslachtsnaam", _("Geslachtsnaam"))
    straatnaam = ChoiceItem("straatnaam", _("Straatnaam"))
    huisnummer = ChoiceItem("huisnummer", _("Huisnummer"))
    huisletter = ChoiceItem("huisletter", _("Huisletter"))
    huisnummertoevoeging = ChoiceItem("huisnummertoevoeging", _("Huisnummer Toevoeging"))
    postcode = ChoiceItem("postcode", _("Postcode"))
    woonplaatsNaam = ChoiceItem("woonplaatsNaam", _("Woonplaats Naam"))
