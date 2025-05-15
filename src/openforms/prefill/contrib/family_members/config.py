from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import FamilyMembersTypeChoices


class FamilyMembersPartnersSerializer(serializers.Serializer):
    # No need for extra fields right now, just for clarity
    pass


class FamilyMembersChildrenSerializer(serializers.Serializer):
    min_age = serializers.IntegerField(
        label=_("min age"),
        help_text=_("The minimum age (inclusive) that should be taken into account."),
        allow_null=True,
        validators=[MinValueValidator(0)],
    )
    max_age = serializers.IntegerField(
        label=_("max age"),
        help_text=_("The maximum age (inclusive) that should be taken into account."),
        allow_null=True,
        validators=[MinValueValidator(0)],
    )
    include_deceased = serializers.BooleanField(
        label=_("include deceased"),
        help_text=_("Whether to include deceased persons or not."),
        default=True,
    )


class FamilyMembersOptionsSerializer(JsonSchemaSerializerMixin, PolymorphicSerializer):
    mutable_data_form_variable = FormioVariableKeyField(
        label=_("mutable data form variable key"),
        help_text=_(
            "The 'dotted' path to a form variable key which is a copy of the initial data "
            "which has been retrieved and may change. The format should comply to how "
            "Formio handles nested component keys."
        ),
    )
    type = serializers.ChoiceField(
        choices=FamilyMembersTypeChoices.choices,
        label=_("type"),
        help_text=_("The type of the person we want to prefill/retrieve data for."),
    )
    serializer_mapping = {
        FamilyMembersTypeChoices.partners: FamilyMembersPartnersSerializer,
        FamilyMembersTypeChoices.children: FamilyMembersChildrenSerializer,
    }
    discriminator_field = "type"
