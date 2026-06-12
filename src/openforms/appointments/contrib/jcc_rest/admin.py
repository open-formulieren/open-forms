from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .forms import JccRestConfigForm
from .models import JccRestConfig


@admin.register(JccRestConfig)
class JccRestConfigAdmin(SingletonModelAdmin):
    form = JccRestConfigForm
    change_form_template = "admin/jcc_rest/jccrestconfig/change_form.html"
