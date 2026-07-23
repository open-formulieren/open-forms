from import_export.resources import ModelResource

from openforms.forms.models import Form
from openforms.typing import JSONObject


class BaseResource(ModelResource):
    deep_comparison_fields = ()

    def export_for_form(self, form: Form):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement export_for_form()"
        )

    def get_or_init_instance(
        self, instance_loader, row
    ) -> tuple[dict[str, JSONObject], bool]:
        """
        Search for an existing AttributeGroup with matching attributes.

        The default get_or_init_instance uses the import_id_fields. If there is no match,
        we do a deep comparison with the name, description, and attributes, and return
        the first match. If there is again no match, we create a new instance.

        The return value is a tuple of (instance, is_new).
        """
        instance, is_new = super().get_or_init_instance(instance_loader, row)

        if not is_new:
            # Return the existing instance, found using the import_id_fields.
            row["_matched_existing_instance"] = True
            return instance, is_new

        # Collect the parameters for the deep comparison.
        params = {}
        for key in self.deep_comparison_fields:
            params[key] = self.fields[key].clean(row)

        # Perform the deep comparison and return the first match.
        if (
            params
            and (new_found := self.get_queryset().filter(**params).first()) is not None
        ):
            row["_matched_existing_instance"] = True
            return new_found, False

        # No match found, return a new instance.
        return instance, is_new

    def skip_row(self, instance, original, row, import_validation_errors=None):
        if row.get("_matched_existing_instance"):
            # When we found an existing instance, we don't update it.
            return True

        return super().skip_row(instance, original, row, import_validation_errors)
