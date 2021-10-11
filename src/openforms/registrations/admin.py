from .fields import RegistrationBackendChoiceField
from django.contrib import admin
from django.views.generic import TemplateView

from openforms.registrations.registry import register


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


class TestPluginAdminView(TemplateView):
    template_name = 'admin/plugin_tester.html'
    title = "Plugin Tester"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plugins = []

        for plugin in register.items():
            context = {'name': plugin[0], 'test': plugin[1].test_config()}
            # exclude email plugin from plugins[], since email plugin is test on another page
            plugins.append(context) if context['name'] != 'email' else None

        return {'plugins': plugins}
