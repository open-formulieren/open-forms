from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import FamilyMembersDataAPIChoices


class FamilyMembersTypeConfig(SingletonModel):
    data_api = models.CharField(
        _("data api"),
        help_text=_("Which API to use to retrieve the data of the family members."),
        choices=FamilyMembersDataAPIChoices,
        max_length=100,
    )

    class Meta:
        verbose_name = _("Family members type configuration")
