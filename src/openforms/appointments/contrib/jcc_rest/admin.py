from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import JccRestConfig


@admin.register(JccRestConfig)
class JccRestConfigAdmin(SingletonModelAdmin):
    pass
