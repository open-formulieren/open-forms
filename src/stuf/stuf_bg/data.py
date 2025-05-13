from datetime import datetime

from pydantic import BaseModel

from .utils import get_today


class NaturalPersonDetails(BaseModel):
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
