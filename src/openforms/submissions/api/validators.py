from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import JSONField

from ..models import SubmissionStep


class ValidatePrefillData:
    code = "invalidPrefilledField"
    default_message = _("The prefill data may not be altered.")
    requires_context = True

    def __call__(self, data: dict, field: JSONField):
        instance: SubmissionStep = field.parent.instance
        prefill_data = instance.submission.get_prefilled_data()

        errors = {}
        for component in instance.form_step.iter_components():
            if "prefill" not in component or component["prefill"]["plugin"] == "":
                continue

            if not component["disabled"]:
                continue

            # match on key
            if not (component_key := component.get("key")):
                continue

            prefilled_value = prefill_data.get(component_key)
            if prefilled_value is None:
                # the value will be `None` if there is no actual prefill data available, so there is nothing to compare to. This
                # especially applies to test-environments without real prefill-connections.
                continue

            new_value = data.get(component_key)
            if new_value != prefilled_value:
                errors[component_key] = serializers.ErrorDetail(
                    self.default_message, code=self.code
                )

        if errors:
            raise serializers.ValidationError(errors)
