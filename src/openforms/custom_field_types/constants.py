from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class FamilyMembersDataAPIChoices(DjangoChoices):
    haal_centraal = ChoiceItem("haal_centraal", _("Haal Centraal"))
    stuf_bg = ChoiceItem("stuf_bg", _("StufBg"))
