from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import MSGraphRegistrationConfig


@admin.register(MSGraphRegistrationConfig)
class MSGraphRegistrationConfigAdmin(SingletonModelAdmin):
    pass
