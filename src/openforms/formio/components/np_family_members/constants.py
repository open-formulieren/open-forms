from django.db import models
from django.utils.translation import gettext_lazy as _


class FamilyMembersDataAPIChoices(models.TextChoices):
    haal_centraal = "haal_centraal", _("Haal Centraal")
    stuf_bg = "stuf_bg", _("StufBg")
