from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import BAGConfig


@admin.register(BAGConfig)
class BAGConfigAdmin(SingletonModelAdmin):
    pass
