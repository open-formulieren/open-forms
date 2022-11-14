from django.utils.translation import gettext_lazy as _

from rest_framework.fields import UUIDField


class ActionFormStepUUIDField(UUIDField):
    """
    UUID Field that checks the validity of the UUID but accepts empty strings (since not all rules actions need to have
    a UUID specified for the form_step field). It checks that the UUID matches the UUID of a form step related to the
    form.

    It also doesn't convert the UUID to a UUID object, since this is not JSON serializable and the action is a JSON
    field.
    """

    default_error_messages = {
        "invalid-step": _("Invalid form step specified in logic action."),
    }

    def to_internal_value(self, data: str) -> str:
        if data == "":
            return data

        value = super().to_internal_value(data)

        # Check that the form step UUID matches a UUID of a form step
        # related to the form
        related_form_steps = self.parent.context["form_steps"]
        if value not in related_form_steps:
            self.fail("invalid-step", value=value)

        return str(value)
