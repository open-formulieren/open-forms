from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import QmaticConfig


@admin.register(QmaticConfig)
class QmaticConfigAdmin(SingletonModelAdmin):
    pass
