from django.contrib import admin

from solo.admin import SingletonModelAdmin
from zgw_consumers.admin import ListZaaktypenMixin

from .models import ZgwConfig


@admin.register(ZgwConfig)
class ZgwConfigAdmin(ListZaaktypenMixin, SingletonModelAdmin):
    zaaktype_fields = [
        "zaaktype",
    ]
    # TODO implement informatieobjecttype suggestions similar to zaaktype
