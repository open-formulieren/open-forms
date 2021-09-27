from django.contrib import admin
from django.template.response import TemplateResponse

from solo.admin import SingletonModelAdmin
from zgw_consumers.admin import ListZaaktypenMixin

from .models import ZgwConfig, TestPlugin
from django.urls import path
from .plugin import ZGWRegistration as zwgr


@admin.register(ZgwConfig)
class ZgwConfigAdmin(ListZaaktypenMixin, SingletonModelAdmin):
    zaaktype_fields = [
        "zaaktype",
    ]
    # TODO implement informatieobjecttype suggestions similar to zaaktype


# @admin.action(description='Test id selected plugin work properly')
def test_plugin(modeladmin, request, queryset):
    test = zwgr.test_config()
    queryset.update(status=1)
    print('hallo there',test)


class TestPluginAdmin(admin.ModelAdmin):
    # list_display = ('name', 'status')
    # actions = [test_plugin]
    change_list_template = 'admin/plugin_tester.html'

    def changelist_view(self, request, extra_context=None):
        context = extra_context or {}
        context = {'plugins': [{'name': 'ZGW API', 'test': zwgr.test_config()}, ]}

        print('conntteexxtt', context)

        return super(TestPluginAdmin, self).changelist_view(request, extra_context=context)
  
admin.site.register(TestPlugin, TestPluginAdmin)