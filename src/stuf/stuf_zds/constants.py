from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class VertrouwelijkheidsAanduidingen(DjangoChoices):
    zeer_geheim = ChoiceItem("ZEER GEHEIM", _("Zeer geheim"))
    geheim = ChoiceItem("GEHEIM", _("Geheim"))
    confidentieel = ChoiceItem("CONFIDENTIEEL", _("Confidentieel"))
    vertrouwelijk = ChoiceItem("VERTROUWELIJK", _("Vertrouwelijk"))
    zaakvertrouwelijk = ChoiceItem("ZAAKVERTROUWELIJK", _("Zaakvertrouwelijk"))
    intern = ChoiceItem("INTERN", _("Intern"))
    beperkt_openbaar = ChoiceItem("BEPERKT OPENBAAR", _("Beperkt openbaar"))
    openbaar = ChoiceItem("OPENBAAR", _("Openbaar"))
