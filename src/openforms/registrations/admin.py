from .fields import RegistrationBackendChoiceField
from django.contrib import admin
from .contrib.zgw_apis.models import TestPlugin
from .contrib.zgw_apis.plugin import ZGWRegistration as zwgr
from .contrib.stuf_zds.plugin import StufZDSRegistration as szr
from .contrib.objects_api.plugin import ObjectsAPIRegistration as oar
from .contrib.email.plugin import EmailRegistration as er 
from .contrib.demo.plugin import DemoFailRegistration as dfr


class RegistrationBackendFieldMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, RegistrationBackendChoiceField):
            assert not db_field.choices
            _old = db_field.choices
            db_field.choices = db_field._get_plugin_choices()
            field = super().formfield_for_dbfield(db_field, request, **kwargs)
            db_field.choices = _old
            return field

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class TestPluginAdmin(admin.ModelAdmin):
    # list_display = ('name', 'status')
    # actions = [test_plugin]
    change_list_template = 'admin/plugin_tester.html'

    def changelist_view(self, request, extra_context=None):
        context = extra_context or {}
        context = {'plugins': [
            {'name': 'ZGW API', 'test': zwgr.test_config()},
            {'name': 'StUF-ZDS', 'test': szr.test_config()},
            {'name': 'Objects API', 'test': oar.test_config()},
            # {'name': 'Local', 'test': dfr.test_config()},
        ], 'email': {'name': 'Email', 'test': er.test_config()},}

        return super(TestPluginAdmin, self).changelist_view(request, extra_context=context)
  
admin.site.register(TestPlugin, TestPluginAdmin)
