from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    voornamen = ChoiceItem("_embedded.naam.voornamen", _("Voornamen"))
    geslachtsnaam = ChoiceItem("_embedded.naam.geslachtsnaam", _("Geslachtsnaam"))

    straatnaam = ChoiceItem("_embedded.verblijfplaats.straatnaam", _("Straatnaam"))
    huisnummer = ChoiceItem("_embedded.verblijfplaats.huisnummer", _("Huisnummer"))
    huisletter = ChoiceItem("_embedded.verblijfplaats.huisletter", _("Huisletter"))
    huisnummertoevoeging = ChoiceItem(
        "_embedded.verblijfplaats.huisnummertoevoeging", _("Huisnummer Toevoeging")
    )
    postcode = ChoiceItem("_embedded.verblijfplaats.postcode", _("Postcode"))
    woonplaatsNaam = ChoiceItem(
        "_embedded.verblijfplaats.woonplaatsnaam", _("Woonplaats Naam")
    )
