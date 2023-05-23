from django.contrib import admin

from solo.admin import SingletonModelAdmin
from zgw_consumers.admin import ListZaaktypenMixin

from .models import ZgwConfig


class ZgwConfigInstanceInline(ListZaaktypenMixin, admin.options.StackedInline):
    extra = 0
    model = ZgwConfig.ZgwConfigInstance
    zaaktype_fields = [
        "zaaktype",
    ]


@admin.register(ZgwConfig)
class ZgwConfigAdmin(SingletonModelAdmin):
    zaaktype_fields = [
        "zaaktype",
    ]
    inlines = [
        ZgwConfigInstanceInline,
    ]
    # TODO implement informatieobjecttype suggestions similar to zaaktype
