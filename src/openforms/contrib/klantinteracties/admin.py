from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import KlantinteractiesConfig


@admin.register(KlantinteractiesConfig)
class KlantinteractiesConfigAdmin(SingletonModelAdmin):
    pass
