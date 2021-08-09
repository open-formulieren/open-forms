from django import forms

from openforms.registrations.contrib.demo.config import DemoOptionsSerializer


# TODO This file needs to be moved somewhere more generic
class RegistrationBackendOptionsWidget(forms.Widget):
    template_name = "admin/forms/form/registration_backend_options.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        json_schemas = {
            name: DemoOptionsSerializer.display_as_jsonschema()
        }
        context.update({"json_schemas": json_schemas})
        return context
