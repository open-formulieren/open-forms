from django.contrib import admin
from django.utils.decorators import method_decorator

import requests
import zds_client
from solo.admin import SingletonModelAdmin
from zgw_consumers.admin import ListZaaktypenMixin

from openforms.utils.decorators import dbfields_exception_handler

from .models import ZGWApiGroupConfig, ZgwConfig


@admin.register(ZgwConfig)
class ZgwConfigAdmin(SingletonModelAdmin):
    pass


@method_decorator(
    dbfields_exception_handler(
        exceptions=(requests.exceptions.RequestException, zds_client.ClientError),
    ),
    name="formfield_for_dbfield",
)
@admin.register(ZGWApiGroupConfig)
class ZGWApiGroupConfigAdmin(ListZaaktypenMixin, admin.ModelAdmin):
    zaaktype_fields = [
        "zaaktype",
    ]
    # TODO implement informatieobjecttype suggestions similar to zaaktype
