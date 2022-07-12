from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class VertrouwelijkheidsAanduidingen(DjangoChoices):
    zeer_geheim = ChoiceItem("ZEER GEHEIM", _("Very secret"))
    geheim = ChoiceItem("GEHEIM", _("Secret"))
    confidentieel = ChoiceItem("CONFIDENTIEEL", _("Confidential"))
    vertrouwelijk = ChoiceItem("VERTROUWELIJK", _("Public"))
    zaakvertrouwelijk = ChoiceItem("ZAAKVERTROUWELIJK", _("Case confidential"))
    intern = ChoiceItem("INTERN", _("Internal"))
    beperkt_openbaar = ChoiceItem("BEPERKT OPENBAAR", _("Limited public"))
    openbaar = ChoiceItem("OPENBAAR", _("Public"))
