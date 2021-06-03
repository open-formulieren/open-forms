from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import HaalCentraalConfig


@admin.register(HaalCentraalConfig)
class HaalCentraalConfigAdmin(SingletonModelAdmin):
    pass
