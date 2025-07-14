from django.db import models
from django.utils.translation import gettext_lazy as _

OIDC_DIGID_IDENTIFIER = "oidc-digid"
OIDC_DIGID_MACHTIGEN_IDENTIFIER = "oidc-digid-machtigen"
OIDC_EH_IDENTIFIER = "oidc-eherkenning"
OIDC_EH_BEWINDVOERING_IDENTIFIER = "oidc-eherkenning-bewindvoering"
OIDC_EIDAS_IDENTIFIER = "oidc-eidas"
OIDC_EIDAS_COMPANY_IDENTIFIER = "oidc-eidas-company"


# ref: https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/eIDAS+Levels+of+Assurance
class EIDASAssuranceLevels(models.TextChoices):
    low = ("low", _("Laag"))
    substantial = ("substantial", _("Substantieel"))
    high = ("high", _("Hoog"))
