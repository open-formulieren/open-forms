from datetime import datetime
from typing import Literal

from django.db import models

from pydantic import BaseModel

from openforms.utils.date import get_today

DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER = "BurgerZelf"

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

HC_DECEASED_ATTRIBUTES = ["burgerservicenummer", "overlijden"]

type DateOfBirthPrecisionType = Literal["date", "year_month", "year"]
DATE_OF_BIRTH_TYPE_MAPPINGS: dict[str, DateOfBirthPrecisionType] = {
    "Datum": "date",
    "JaarMaandDatum": "year_month",
    "jaarDatum": "year",
}


class NaturalPersonDetails(BaseModel):
    bsn: str | None = None
    first_names: str | None = None
    initials: str | None = None
    affixes: str | None = None
    lastname: str | None = None
    date_of_birth: str | None = None  # ISO - 8601
    date_of_birth_precision: Literal["date", "year_month", "year"] | None = None

    @property
    def age(self) -> int | None:
        """Calculate age if precision allows and date_of_birth is available."""
        if not self.date_of_birth:
            return None

        # only calculate age when full date is known.
        if self.date_of_birth_precision not in (None, "date"):
            return None

        try:
            birth_date = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
            today = datetime.strptime(get_today(), "%Y-%m-%d")
            age = today.year - birth_date.year

            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return age
        except ValueError:
            return None


Partners = list[NaturalPersonDetails]
Children = list[NaturalPersonDetails]


class BRPVersions(models.TextChoices):
    """
    Supported (and tested) versions of the Haal Centraal BRP Personen API.
    """

    v13 = "1.3", "BRP Personen Bevragen 1.3"
    v20 = "2.0", "BRP Personen Bevragen 2.0"
