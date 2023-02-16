from django.db import models
from django.utils.translation import gettext_lazy as _


class RemovalMethods(models.TextChoices):
    delete_permanently = "delete_permanently", _("Submissions will be deleted")
    make_anonymous = "make_anonymous", _(
        "Sensitive data within the submissions will be deleted"
    )
