from .fields import RegistrationBackendChoiceField
from django.contrib import admin
from django.views.generic import TemplateView

from openforms.registrations.registry import register
from openforms.prefill.registry import register as pr


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
        plugins = [
            {'pname': 'Prefills Plugins', 'data': [{'name': p[0], 'test': p[1].test_config()} for p in pr.items()]},
            # exclude email plugin from plugins[], since email plugin is test on another page
            {'pname': 'registrations Plugins', 'data': [{'name': p[0], 'test': p[1].test_config()} for p in register.items() if p[0] != 'email']}            # }
        ]

        return {'plugins': plugins}
