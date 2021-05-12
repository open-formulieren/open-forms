from django.contrib import admin

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .models import ConfirmationEmailConfig


@admin.register(ConfirmationEmailConfig)
class ConfirmationEmailConfig(SingletonModelAdmin, DynamicArrayMixin):
    pass
