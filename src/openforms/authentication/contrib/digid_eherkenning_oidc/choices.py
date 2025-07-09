from django.db import models
from django.utils.translation import gettext_lazy as _


# ref: https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/eIDAS+Levels+of+Assurance
class EIDASAssuranceLevels(models.TextChoices):
    low = ("low", _("Laag"))
    substantial = ("substantial", _("Substantieel"))
    high = ("high", _("Hoog"))
