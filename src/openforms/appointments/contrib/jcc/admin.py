from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import JccConfig


@admin.register(JccConfig)
class JccConfigAdmin(SingletonModelAdmin):
    pass
