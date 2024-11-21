import functools
from collections.abc import Sequence

from django.conf import settings
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.utils import translation
from django.utils.translation import gettext

import openforms.utils.translations


class FixDefaultTranslations:
    """
    Set the properly translated default translatable field values.

    Workaround for https://github.com/open-formulieren/open-forms/issues/4826
    """

    def __init__(self, app_label: str, model: str, fields: Sequence[str]):
        self.app_label = app_label
        self.model = model
        self.fields = fields

    def __call__(self, apps: StateApps, schema_editor: BaseDatabaseSchemaEditor):
        Model = apps.get_model(self.app_label, self.model)
        for obj in Model.objects.all():
            for field in self.fields:
                for lang, _ in settings.LANGUAGES:
                    with translation.override(lang):
                        default_callback = Model._meta.get_field(field).default
                        assert isinstance(default_callback, functools.partial)
                        if (
                            default_callback.func
                            is openforms.utils.translations.get_default
                        ):
                            default_callback = functools.partial(
                                gettext,
                                *default_callback.args,
                            )
                        setattr(obj, f"{field}_{lang}", default_callback())
            obj.save()
