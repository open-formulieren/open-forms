from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .fields import PrefillPluginChoiceField
from .models import PrefillConfig


@admin.register(PrefillConfig)
class PrefillConfigAdmin(SingletonModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, PrefillPluginChoiceField):
            assert not db_field.choices
            _old = db_field.choices
            db_field.choices = db_field._get_plugin_choices()
            field = super().formfield_for_dbfield(db_field, request, **kwargs)
            db_field.choices = _old
            return field

        return super().formfield_for_dbfield(db_field, request, **kwargs)
