from django.db import models

from digid_eherkenning.choices import AssuranceLevels

OIDC_DIGID_IDENTIFIER = "oidc-digid"
OIDC_DIGID_MACHTIGEN_IDENTIFIER = "oidc-digid-machtigen"
OIDC_EH_IDENTIFIER = "oidc-eherkenning"
OIDC_EH_BEWINDVOERING_IDENTIFIER = "oidc-eherkenning-bewindvoering"
OIDC_EIDAS_IDENTIFIER = "oidc-eidas"
OIDC_EIDAS_COMPANY_IDENTIFIER = "oidc-eidas-company"


# ref: https://afsprakenstelsel.etoegang.nl/Startpagina/as/level-of-assurance
# LoA 1 is no-longer used. LoA 2 and LoA 2+ both translate to eIDAS LoA "Low".
# Because of the slightly worst security, we should drop LoA 2 in favor of LoA 2+.
# But, apparently LoA 2 is (in certain situations) still used, so we must support it.
class EIDASAssuranceLevels(models.TextChoices):
    low = AssuranceLevels.low
    low_plus = AssuranceLevels.low_plus
    substantial = AssuranceLevels.substantial
    high = AssuranceLevels.high
