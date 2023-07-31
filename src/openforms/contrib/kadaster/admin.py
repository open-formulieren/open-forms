from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import KadasterApiConfig


@admin.register(KadasterApiConfig)
class KadasterServiceAdmin(SingletonModelAdmin):
    pass
