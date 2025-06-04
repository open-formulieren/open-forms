from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from openforms.api.utils import underscore_to_camel
from openforms.utils.date import get_today


class NaturalPersonDetails(BaseModel):
    # This is needed in order to have the camel case names on the frontend and snake case
    # on the backend
    model_config = ConfigDict(
        alias_generator=underscore_to_camel,
        populate_by_name=True,  # Allow using snake_case names when creating model
        from_attributes=True,
    )

    bsn: str = ""
    first_names: str = ""
    initials: str = ""
    affixes: str = ""
    last_name: str = ""
    date_of_birth: str = ""
    date_of_birth_precision: Literal["date", "year_month", "year"] | None = None

    @property
    def age(self) -> int | None:
        """Calculate age if precision allows and date_of_birth is available."""
        if not self.date_of_birth:
            return None

        # only calculate age when full date is known.
        if self.date_of_birth_precision not in (None, "date"):
            return None

        birth_date = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
        today = get_today()
        age = today.year - birth_date.year

        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age


type Partners = list[NaturalPersonDetails]
type Children = list[NaturalPersonDetails]
