from typing import Literal

from django.db import models
from django.utils.translation import gettext_lazy as _


class IdentifierRoles(models.TextChoices):
    main = "main", _("Main")
    authorised_person = "authorised_person", _("Authorised person")


IdentifierRole = Literal["main", "authorised_person"]
