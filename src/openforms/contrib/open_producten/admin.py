from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import OpenProductenConfig


@admin.register(OpenProductenConfig)
class OpenProductenConfigAdmin(SingletonModelAdmin):

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
