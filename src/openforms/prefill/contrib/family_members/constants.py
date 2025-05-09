from django.db import models
from django.utils.translation import gettext as _

HC_PARTNERS_ATTRIBUTES = [
    "partners.burgerservicenummer",
    "partners.naam.voornamen",
    "partners.naam.voorletters",
    "partners.naam.voorvoegsel",
    "partners.naam.geslachtsnaam",
    "partners.geboorte.datum",
]
HC_CHILDREN_ATTRIBUTES = [
    "kinderen.burgerservicenummer",
    "kinderen.naam.voornamen",
    "kinderen.naam.voorletters",
    "kinderen.naam.voorvoegsel",
    "kinderen.naam.geslachtsnaam",
    "kinderen.geboorte.datum",
]


class FamilyMembersTypeChoices(models.TextChoices):
    partners = ("partners", _("Partners"))
    children = ("children", _("Children"))
