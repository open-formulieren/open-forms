from dataclasses import dataclass

from django.db import models

from modeltranslation.utils import fallbacks

from openforms.config.models import GlobalConfiguration


@dataclass
class literal_getter:
    """
    'Descriptor' to access a model field with a :class:`GlobalConfiguration` default.
    """

    model_field: str
    config_field: str

    def contribute_to_class(self, cls: type[models.Model], name: str) -> None:
        # validate the existing fields were passed in - raises django.core.exceptions.FieldDoesNotExist
        assert cls._meta.get_field(self.model_field)
        assert GlobalConfiguration._meta.get_field(self.config_field)

        def getter(instance: models.Model) -> str:
            with fallbacks(False):
                value = getattr(instance, self.model_field)
            if value:
                return value

            config = GlobalConfiguration.get_solo()
            return getattr(config, self.config_field)

        # generate the getter function & set it on the class
        setattr(cls, name, getter)
