from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import FamilyMembersTypeConfig


@admin.register(FamilyMembersTypeConfig)
class FamilyMembersTypeConfigAdmin(SingletonModelAdmin):
    pass
