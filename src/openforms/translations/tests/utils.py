from typing import TypeVar

import factory
from modeltranslation.translator import translator

_F = TypeVar("_F", bound=type[factory.django.DjangoModelFactory])


class TranslatedMixin(factory.base.Factory):
    """
    A Mixin that sets the factory values on the fields that correspond
    to the requested `_language` argument passed to the factory function.
    """

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if "_language" not in kwargs:
            return kwargs
        lang = kwargs.pop("_language")
        options = translator.get_options_for_model(cls._meta.model)
        for field, i18n_fields in options.all_fields.items():
            i18n_names = {f.name for f in i18n_fields}
            i18n_field = f"{field}_{lang}"
            if field not in kwargs or i18n_field not in i18n_names:
                continue
            value = kwargs.pop(field)
            kwargs[i18n_field] = value
        return kwargs


def make_translated(factory_class: _F) -> _F:
    """
    Make a Factory that creates translated instances.

    >>> from openforms.forms.tests.factories import FormFactory
    >>> TranslatedFormFactory = make_translated(FormFactory)
    >>>
    >>> translated_form = TranslatedFormFactory.create(
    ...     _language="en",  # note the _ to prevent name clashes
    ...     begin_text="start")
    >>>
    >>> assert translated_form.begin_text_en == "start"
    >>> assert translated_form.name_en  # set from the Factory
    """

    i18n_models = translator.get_registered_models()
    if factory_class._meta.model not in i18n_models:
        return factory_class
    return type(
        f"Translated{factory_class.__name__}",
        (factory_class, TranslatedMixin),
        dict(),
    )
