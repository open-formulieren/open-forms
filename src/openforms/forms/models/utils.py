from dataclasses import dataclass

from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase

from openforms.config.models import GlobalConfiguration


def getter_factory(model_field: str, config_field: str, language_code: str = ""):
    # prefix as needed
    if language_code:
        model_field = f"{model_field}_{language_code}"
        config_field = f"{config_field}_{language_code}"

    def getter(instance: models.Model) -> str:
        value = getattr(instance, model_field)
        if value:
            return value

        config = GlobalConfiguration.get_solo()
        return getattr(config, config_field)

    return getter


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

        default_getter = getter_factory(self.model_field, self.config_field)

        # generate the getter function & set it on the class
        setattr(cls, name, default_getter)

        # install the language code specific getters
        for language_code, _label in settings.LANGUAGES:
            language_specific_name = f"{name}_{language_code}"
            setattr(
                cls,
                language_specific_name,
                getter_factory(self.model_field, self.config_field, language_code),
            )
