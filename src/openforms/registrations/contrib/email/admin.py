from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import EmailConfig


@admin.register(EmailConfig)
class EmailConfigAdmin(SingletonModelAdmin):
    pass
