from django.db import models
from django.utils.translation import gettext_lazy as _

from .contrib.customer_interactions.constants import (
    PLUGIN_IDENTIFIER as CUSTOMER_INTERACTIONS_PLUGIN,
)

# list of the supported prefill plugins that allow re-triggering prefill when a submission
# is resumed and needs to update the prefilled data
PREFILL_ON_SUBMISSION_RESUME_PLUGINS = [CUSTOMER_INTERACTIONS_PLUGIN]


class IdentifierRoles(models.TextChoices):
    main = "main", _("Main")
    authorizee = "authorizee", _("Authorizee")
