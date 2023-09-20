from django.db import models
from django.utils.translation import gettext_lazy as _

STUF_ZDS_EXPIRY_MINUTES = 5


class VertrouwelijkheidsAanduidingen(models.TextChoices):
    zeer_geheim = "ZEER GEHEIM", _("Zeer geheim")
    geheim = "GEHEIM", _("Geheim")
    confidentieel = "CONFIDENTIEEL", _("Confidentieel")
    vertrouwelijk = "VERTROUWELIJK", _("Vertrouwelijk")
    zaakvertrouwelijk = "ZAAKVERTROUWELIJK", _("Zaakvertrouwelijk")
    intern = "INTERN", _("Intern")
    beperkt_openbaar = "BEPERKT OPENBAAR", _("Beperkt openbaar")
    openbaar = "OPENBAAR", _("Openbaar")
