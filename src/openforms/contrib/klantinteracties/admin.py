from django.contrib import admin
from .models import KlantinteractiesConfig
from solo.admin import SingletonModelAdmin


@admin.register(KlantinteractiesConfig)
class KlantinteractiesConfigAdmin(SingletonModelAdmin):
    pass
