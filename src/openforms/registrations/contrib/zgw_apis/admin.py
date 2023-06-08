from django.contrib import admin

from solo.admin import SingletonModelAdmin
from zgw_consumers.admin import ListZaaktypenMixin

from .models import ZGWApiGroupConfig, ZgwConfig


@admin.register(ZgwConfig)
class ZgwConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(ZGWApiGroupConfig)
class ZGWApiGroupConfigAdmin(ListZaaktypenMixin, admin.ModelAdmin):
    zaaktype_fields = [
        "zaaktype",
    ]
    # TODO implement informatieobjecttype suggestions similar to zaaktype
