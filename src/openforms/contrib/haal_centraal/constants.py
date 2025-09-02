from typing import Literal

from django.db import models

DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER = "BurgerZelf"

# needed attributes for the requests to the API
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

# extra needed attributes for the deceased children
HC_DECEASED_ATTRIBUTES = ["burgerservicenummer", "overlijden"]

# properties/data which can be populated by the already retreived data (in a second form step)
HC_CHILDREN_EXTRA_STEP_ALLOWED_PROPERTIES = {
    "bsn": "id_bsn",
    "first_names": "id_firstNames",
}

type DateOfBirthPrecisionType = Literal["date", "year_month", "year"]
DATE_OF_BIRTH_TYPE_MAPPINGS: dict[str, DateOfBirthPrecisionType] = {
    "Datum": "date",
    "JaarMaandDatum": "year_month",
    "jaarDatum": "year",
}


class BRPVersions(models.TextChoices):
    """
    Supported (and tested) versions of the Haal Centraal BRP Personen API.
    """

    v13 = "1.3", "BRP Personen Bevragen 1.3"
    v20 = "2.0", "BRP Personen Bevragen 2.0"
