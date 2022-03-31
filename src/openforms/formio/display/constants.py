from enum import Enum, auto


# TODO convert to django-choices
class OutputMode(Enum):
    summary = auto()
    pdf = auto()
    email_confirmation = auto()
    email_registration = auto()

    @classmethod
    def all(cls):
        return list(cls)
