from django.db.models.fields import CharField

UNIQUE_ID_MAX_LENGTH = 100


class BackendChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", UNIQUE_ID_MAX_LENGTH)
        if kwargs["max_length"] > UNIQUE_ID_MAX_LENGTH:
            raise ValueError("'max_length' is capped at {UNIQUE_ID_MAX_LENGTH}")
        super().__init__(*args, **kwargs)
