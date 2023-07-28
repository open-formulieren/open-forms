from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import HaalCentraalHRConfig


@admin.register(HaalCentraalHRConfig)
class HaalCentraalHRConfigAdmin(SingletonModelAdmin):
    pass
