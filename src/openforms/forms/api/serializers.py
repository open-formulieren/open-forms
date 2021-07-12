from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.prefill import apply_prefill
from openforms.products.api.serializers import ProductSerializer

from ...authentication.api.fields import LoginOptionsReadOnlyField
from ...authentication.registry import register as auth_register
from ..custom_field_types import handle_custom_types
from ..models import Form, FormDefinition, FormStep


class ButtonTextSerializer(serializers.Serializer):
    resolved = serializers.SerializerMethodField()
    value = serializers.CharField()

    def __init__(self, resolved_getter=None, raw_field=None, *args, **kwargs):
        kwargs.setdefault("source", "*")
        self.resolved_getter = resolved_getter
        self.raw_field = raw_field
        super().__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        if self.resolved_getter is None:
            self.resolved_getter = f"get_{field_name}"

        if self.raw_field is None:
            self.raw_field = field_name

        value_field = self.fields["value"]
        value_field.source = self.raw_field
        value_field.bind(value_field.field_name, self)

    def get_resolved(self, obj):
        return getattr(obj, self.resolved_getter)()


class FormStepLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text")
    save_text = ButtonTextSerializer(raw_field="save_text")
    next_text = ButtonTextSerializer(raw_field="next_text")


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
    index = serializers.IntegerField(source="order")
    slug = serializers.SlugField(source="form_definition.slug")
    literals = FormStepLiteralsSerializer(source="*")
    url = NestedHyperlinkedRelatedField(
        queryset=FormStep.objects,
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
    )

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "slug",
            "form_definition",
            "index",
            "literals",
            "url",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            }
        }


class FormLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text")
    begin_text = ButtonTextSerializer(raw_field="begin_text")
    change_text = ButtonTextSerializer(raw_field="change_text")
    confirm_text = ButtonTextSerializer(raw_field="confirm_text")


class FormSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    steps = MinimalFormStepSerializer(many=True, read_only=True, source="formstep_set")
    authentication_backends = serializers.ListField(
        child=serializers.ChoiceField(choices=[]),
        write_only=True,
        required=False,
        default=list,
    )
    login_options = LoginOptionsReadOnlyField()
    literals = FormLiteralsSerializer(source="*")

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "login_required",
            "authentication_backends",
            "login_options",
            "literals",
            "product",
            "slug",
            "url",
            "steps",
            "show_progress_indicator",
            "maintenance_mode",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
        }

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        fields["authentication_backends"].child.choices = auth_register.get_choices()
        return fields


class FormExportSerializer(FormSerializer):
    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        del fields["login_options"]
        fields["authentication_backends"].write_only = False
        return fields


class FormDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)

        _handle_custom_types = self.context.get("handle_custom_types", True)
        if _handle_custom_types:
            representation["configuration"] = handle_custom_types(
                representation["configuration"],
                request=self.context["request"],
                submission=self.context["submission"],
            )
            representation["configuration"] = apply_prefill(
                representation["configuration"],
                submission=self.context["submission"],
            )
        return representation

    class Meta:
        model = FormDefinition
        fields = (
            "url",
            "uuid",
            "name",
            "slug",
            "configuration",
            "login_required",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            }
        }


class UsedInFormSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Form
        fields = (
            "url",
            "uuid",
            "name",
            "active",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
        }


class FormDefinitionDetailSerializer(FormDefinitionSerializer):
    used_in = UsedInFormSerializer(
        many=True,
        label=_("Used in forms"),
        help_text=_(
            "The collection of forms making use of this definition. This includes both "
            "active and inactive forms."
        ),
    )

    class Meta(FormDefinitionSerializer.Meta):
        fields = FormDefinitionSerializer.Meta.fields + ("used_in",)


class FormStepSerializer(serializers.HyperlinkedModelSerializer):
    index = serializers.IntegerField(source="order")
    configuration = serializers.JSONField(
        source="form_definition.configuration", read_only=True
    )
    login_required = serializers.BooleanField(
        source="form_definition.login_required", read_only=True
    )
    name = serializers.CharField(source="form_definition.name", read_only=True)
    slug = serializers.CharField(source="form_definition.slug", read_only=True)
    literals = FormStepLiteralsSerializer(source="*")
    url = NestedHyperlinkedRelatedField(
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        read_only=True,
    )

    parent_lookup_kwargs = {
        "form_uuid_or_slug": "form__uuid",
    }

    class Meta:
        model = FormStep
        fields = (
            "index",
            "slug",
            "configuration",
            "form_definition",
            "name",
            "url",
            "login_required",
            "literals",
        )

        extra_kwargs = {
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
        }

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super(FormStepSerializer, self).to_representation(instance)
        representation["previous_text"] = instance.get_previous_text()
        representation["save_text"] = instance.get_save_text()
        representation["next_text"] = instance.get_next_text()
        return representation


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )
