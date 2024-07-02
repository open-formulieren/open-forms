from django.db import models
from django.utils.translation import gettext_lazy as _


class IdentifierRoles(models.TextChoices):
    main = "main", _("Main")
    authorizee = "authorizee", _("Authorizee")
