from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from openforms.contrib.open_producten.models import OpenProductenConfig


@admin.register(OpenProductenConfig)
class OpenProductenConfig(SingletonModelAdmin):
    fieldsets = [
        (
            _("Services"),
            {
                "fields": [
                    "producten_service",
                ],
            },
        )
    ]
