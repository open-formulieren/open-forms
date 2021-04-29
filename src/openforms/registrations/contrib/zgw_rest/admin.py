from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import ZgwConfig


@admin.register(ZgwConfig)
class ZgwConfigAdmin(SingletonModelAdmin):
    # TODO display zaaktype and informatieobjecttype fields as choice fields would be nice
    pass
