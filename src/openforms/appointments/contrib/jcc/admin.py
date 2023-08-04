from django.contrib import admin

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .forms import JccConfigForm
from .models import JccConfig


@admin.register(JccConfig)
class JccConfigAdmin(DynamicArrayMixin, SingletonModelAdmin):
    form = JccConfigForm
