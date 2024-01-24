from django.core.exceptions import ImproperlyConfigured
from django.db import migrations

from openforms.formio.migration_converters import CONVERTERS
from openforms.formio.utils import iter_components


class ApplyConverter:
    def __init__(self, component_type: str, identifier: str):
        self.component_type = component_type

        try:
            self.apply_conversion = CONVERTERS[component_type][identifier]
        except KeyError:  # pragma: no cover
            raise ImproperlyConfigured(
                f"Could not find the converter '{identifier}' for component type "
                f"'{component_type}'."
            )

    def __call__(self, apps, _):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        form_definitions = FormDefinition.objects.all()

        form_definitions_to_update = []
        for form_definition in form_definitions:
            updated_form_definition = False
            for comp in iter_components(configuration=form_definition.configuration):
                assert "type" in comp
                if comp["type"] != self.component_type:
                    continue

                is_modified = self.apply_conversion(comp)
                if is_modified:
                    updated_form_definition = True

            if updated_form_definition:
                form_definitions_to_update.append(form_definition)

        if form_definitions_to_update:
            FormDefinition.objects.bulk_update(
                form_definitions_to_update, fields=["configuration"]
            )


class ConvertComponentsOperation(migrations.RunPython):
    """
    Generate a data migration to apply component conversion.

    :arg component_type: The form.io component type, e.g. "textfield". Only
      components of this type will be targeted.
    :arg identifier: identifier of the conversion operation, as defined in
      ``CONVERTERS``.
    """

    def __init__(self, component_type: str, identifier: str):
        apply_converter = ApplyConverter(component_type, identifier)
        super().__init__(code=apply_converter, reverse_code=migrations.RunPython.noop)

    def deconstruct(self):  # pragma: no cover
        # Same as migrations.Operation base class
        return (
            self.__class__.__name__,
            self._constructor_args[0],
            self._constructor_args[1],
        )
