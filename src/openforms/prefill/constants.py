from django.db import models
from django.utils.translation import gettext_lazy as _


class IdentifierRoles(models.TextChoices):
    main = "main", _("Main")
    # TODO: this value is wrongly named:
    # 1. authorised person only applies for DigiD machtigen
    # 2. with eHerkenning (bewindvoering), the authorizee is de *company* (legal
    #    subject). For the acting subject, we only get an opaque, encrypted identifier
    #    that cannot be used to prefill information (this is by design).
    authorizee = "authorizee", _("Authorizee")
