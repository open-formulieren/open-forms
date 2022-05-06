from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openforms.utils.admin import SubmitActions


class FormAdminMessageSerializer(serializers.Serializer):
    """
    Collect metadata about which (success) message to send.
    """

    submit_action = serializers.ChoiceField(
        label=_("submit action"),
        choices=SubmitActions,
        help_text=_(
            "Which submit action was clicked. This determines the success message to"
            "display."
        ),
    )
    is_create = serializers.BooleanField(
        label=_("is create"),
        help_text=_("Whether the submit action was a create operation or update."),
    )
    redirect_url = serializers.SerializerMethodField(
        label=_("redirect URL"),
        help_text=_(
            "Where the UI should redirect the user to. The exact admin URL varies "
            "with the submit action.",
        ),
        read_only=True,
    )

    @extend_schema_field(OpenApiTypes.URI)
    def get_redirect_url(self, data: dict) -> str:
        form_pk = self.context["form"].pk

        if data["submit_action"] == SubmitActions.save:
            admin_url = reverse("admin:forms_form_changelist")
        elif data["submit_action"] == SubmitActions.add_another:
            admin_url = reverse("admin:forms_form_add")
        elif data["submit_action"] == SubmitActions.edit_again:
            admin_url = reverse("admin:forms_form_change", args=(form_pk,))

        absolute_url = self.context["request"].build_absolute_uri(admin_url)
        return absolute_url
