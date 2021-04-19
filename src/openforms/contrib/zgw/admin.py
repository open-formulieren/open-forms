from django.contrib import admin

from solo.admin import SingletonModelAdmin

from openforms.forms.admin.registry import register_inline

from .models import ZgwConfig, ZGWFormConfig


@register_inline(backend_name="create_zaak_backend")
class ZGWFormConfigInline(admin.StackedInline):
    model = ZGWFormConfig


@admin.register(ZgwConfig)
class ZgwConfigAdmin(SingletonModelAdmin):
    #  todo display zaaktype and informatieobjecttype fields as choice fields would be nice
    pass
