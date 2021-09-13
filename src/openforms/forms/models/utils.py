from dataclasses import dataclass

from django.db import models
from django.db.models import F, Value
from django.db.models.base import ModelBase
from django.db.models.functions import Coalesce, NullIf

from openforms.config.models import GlobalConfiguration


@dataclass
class literal_getter:
    """
    'Descriptor' to access a model field with a :class:`GlobalConfiguration` default.
    """

    model_field: str
    config_field: str

    def contribute_to_class(self, cls: ModelBase, name: str) -> None:
        # validate the existing fields were passed in - raises django.core.exceptions.FieldDoesNotExist
        assert cls._meta.get_field(self.model_field)
        assert GlobalConfiguration._meta.get_field(self.config_field)

        # generate the getter function & set it on the class
        def getter(instance: models.Model) -> str:
            value = getattr(instance, self.model_field)
            if value:
                return value

            config = GlobalConfiguration.get_solo()
            return getattr(config, self.config_field)

        setattr(cls, name, getter)


def FirstNotBlank(*fields):
    # note: we could support any expression but lets assume F() field names for now
    assert len(fields) >= 2, "pass at least two field names"
    fields = list(fields)
    last = fields.pop()
    args = [NullIf(F(f), Value("")) for f in fields] + [F(last)]
    return Coalesce(*args)
