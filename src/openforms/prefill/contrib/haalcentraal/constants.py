from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    voornamen = ChoiceItem("_embedded__naam__voornamen", _("Voornamen"))
    geslachtsnaam = ChoiceItem("_embedded__naam__geslachtsnaam", _("Geslachtsnaam"))

    straatnaam = ChoiceItem("_embedded__verblijfplaats__straatnaam", _("Straatnaam"))
    huisnummer = ChoiceItem("_embedded__verblijfplaats__huisnummer", _("Huisnummer"))
    huisletter = ChoiceItem("_embedded__verblijfplaats__huisletter", _("Huisletter"))
    huisnummertoevoeging = ChoiceItem(
        "_embedded__verblijfplaats__huisnummertoevoeging", _("Huisnummer Toevoeging")
    )
    postcode = ChoiceItem("_embedded__verblijfplaats__postcode", _("Postcode"))
    woonplaatsNaam = ChoiceItem(
        "_embedded__verblijfplaats__woonplaatsnaam", _("Woonplaats Naam")
    )
