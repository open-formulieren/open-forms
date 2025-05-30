from datetime import datetime

from pydantic import BaseModel, ConfigDict

from openforms.api.utils import underscore_to_camel

from .utils import get_today


class NaturalPersonDetails(BaseModel):
    # This is needed in order to have the came case on the frontend and the snake case
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
    lastname: str = ""
    date_of_birth: str = ""
    deceased: bool | None = None

    @property
    def age(self) -> int | None:
        """Calculate age if date_of_birth is available."""
        if not self.date_of_birth:
            return None

        try:
            birth_date = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
            today = get_today()
            age = today.year - birth_date.year

            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return age
        except ValueError:
            return None
