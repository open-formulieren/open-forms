from django.db import models
from django.utils.translation import gettext as _


class FamilyMembersTypeChoices(models.TextChoices):
    partners = "partners", _("Partners")
    children = "children", _("Children")
