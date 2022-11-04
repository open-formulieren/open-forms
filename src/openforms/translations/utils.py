from typing import Any, Type

from django.db.models import Model

import factory
from modeltranslation.translator import translator


class FullyTranslatedMixin(factory.base.Factory):
    """
    A Factory Mixin that creates translation values for all configured languages.

    Values will have the form "{language}_{orginal value}".

    NB: When the create strategy is used, this results in extra writes to the
    database, therefore don't use the mixin unless all uses of the factory
    involve testing translation behaviour.
    """

    @factory.post_generation
    def populate_translations(
        obj: Model, create: bool, extracted: Any, **kwargs
    ) -> None:
        options = translator.get_options_for_model(type(obj))
        for field, i18n_fields in options.fields.items():
            value = getattr(obj, field)
            if isinstance(value, str):
                for i18n in i18n_fields:
                    lang = i18n.name[len(field) + 1 :]  # _suffix of base field
                    setattr(obj, i18n.name, f"{lang}_{value}")

            # TODO create valid values for all supported types
            # https://django-modeltranslation.readthedocs.io/en/latest/registration.html#supported-fields-matrix
        if create:
            obj.save()


def make_fully_translated(
    factory_class: Type[factory.django.DjangoModelFactory],
) -> Type[factory.django.DjangoModelFactory]:
    """
    Make a Factory that creates fully translated instances.

    >>> from openforms.forms.tests.factories import FormFactory
    >>> TranslatedFormFactory = make_fully_translated(FormFactory)
    >>>
    >>> translated_form = TranslatedFormFactory.create(begin_text="start")
    >>>
    >>> assert translated_form.begin_text_nl == "nl_start"
    >>> assert translated_form.begin_text_en == "en_start"
    """

    i18n_models = translator.get_registered_models()
    if factory_class._meta.model not in i18n_models:
        # Raise a warning?
        return factory_class
    return type(
        f"Translated{factory_class.__name__}",
        (factory_class, FullyTranslatedMixin),
        dict(),
    )
