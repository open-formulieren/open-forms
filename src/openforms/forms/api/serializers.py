from django.utils.translation import ugettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.prefill import apply_prefill
from openforms.products.models import Product
from openforms.utils.json_logic import JsonLogicTest

from ...authentication.api.fields import LoginOptionsReadOnlyField
from ...authentication.registry import register as auth_register
from ...payments.api.fields import PaymentOptionsReadOnlyField
from ...payments.registry import register as payment_register
from ...submissions.api.fields import URLRelatedField
from ..constants import LogicActionTypes, PropertyTypes
from ..custom_field_types import handle_custom_types
from ..models import Form, FormDefinition, FormStep, FormVersion
from ..models.form import FormLogic
from .validators import JsonLogicValidator


class ButtonTextSerializer(serializers.Serializer):
    resolved = serializers.SerializerMethodField()
    value = serializers.CharField(allow_blank=True)

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

    def get_resolved(self, obj) -> str:
        return getattr(obj, self.resolved_getter)()


class FormStepLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text", required=False)
    save_text = ButtonTextSerializer(raw_field="save_text", required=False)
    next_text = ButtonTextSerializer(raw_field="next_text", required=False)


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(
        read_only=True, slug_field="public_name"
    )
    index = serializers.IntegerField(source="order")
    slug = serializers.SlugField(source="form_definition.slug")
    literals = FormStepLiteralsSerializer(source="*", required=False)
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
    previous_text = ButtonTextSerializer(raw_field="previous_text", required=False)
    begin_text = ButtonTextSerializer(raw_field="begin_text", required=False)
    change_text = ButtonTextSerializer(raw_field="change_text", required=False)
    confirm_text = ButtonTextSerializer(raw_field="confirm_text", required=False)


class SubmissionsRemovalOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = (
            "successful_submissions_removal_limit",
            "successful_submissions_removal_method",
            "incomplete_submissions_removal_limit",
            "incomplete_submissions_removal_method",
            "errored_submissions_removal_limit",
            "errored_submissions_removal_method",
            "all_submissions_removal_limit",
        )


class FormSerializer(serializers.ModelSerializer):
    steps = MinimalFormStepSerializer(many=True, read_only=True, source="formstep_set")

    authentication_backends = serializers.ListField(
        child=serializers.ChoiceField(choices=[]),
        write_only=True,
        required=False,
        default=list,
    )
    login_options = LoginOptionsReadOnlyField()

    product = serializers.HyperlinkedRelatedField(
        label=_("product"),
        queryset=Product.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:product-detail",
        lookup_field="uuid",
        help_text=_("URL to the product in the Open Forms API"),
    )
    payment_backend = serializers.ChoiceField(
        choices=[],
        required=False,
        default="",
    )
    payment_options = PaymentOptionsReadOnlyField()

    literals = FormLiteralsSerializer(source="*", required=False)
    submissions_removal_options = SubmissionsRemovalOptionsSerializer(
        source="*", required=False
    )
    is_deleted = serializers.BooleanField(source="_is_deleted", required=False)

    class Meta:
        model = Form
        fields = (
            "uuid",
            "public_name",
            "internal_name",
            "login_required",
            "registration_backend",
            "registration_backend_options",
            "authentication_backends",
            "login_options",
            "payment_required",
            "payment_backend",
            "payment_backend_options",
            "payment_options",
            "literals",
            "product",
            "slug",
            "url",
            "steps",
            "show_progress_indicator",
            "maintenance_mode",
            "active",
            "is_deleted",
            "submission_confirmation_template",
            "can_submit",
            "submissions_removal_options",
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
        fields["payment_backend"].choices = [("", "")] + payment_register.get_choices()
        return fields


class FormExportSerializer(FormSerializer):
    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        del fields["login_options"]
        del fields["payment_options"]
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
            "public_name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
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
            "public_name",
            "internal_name",
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
    is_reusable = serializers.BooleanField(
        source="form_definition.is_reusable", read_only=True
    )
    public_name = serializers.CharField(
        source="form_definition.public_name", read_only=True
    )
    internal_name = serializers.CharField(
        source="form_definition.internal_name", read_only=True
    )
    slug = serializers.CharField(source="form_definition.slug", read_only=True)
    literals = FormStepLiteralsSerializer(source="*", required=False)
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
            "uuid",
            "index",
            "slug",
            "configuration",
            "form_definition",
            "public_name",
            "internal_name",
            "url",
            "login_required",
            "is_reusable",
            "literals",
        )

        extra_kwargs = {
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "uuid": {
                "read_only": True,
            },
        }

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        return super().create(validated_data)


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )


class FormVersionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FormVersion
        fields = (
            "uuid",
            "created",
        )


class ComponentPropertySerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("property key"),
        help_text=_(
            "The Form.io component property to alter, identified by `component.key`"
        ),
    )
    type = serializers.ChoiceField(
        label=_("type"),
        help_text=_("The type of the value field"),
        choices=PropertyTypes,
    )


class LogicPropertyActionSerializer(serializers.Serializer):
    property = ComponentPropertySerializer()
    state = serializers.JSONField(
        label=_("value of the property"),
        help_text=_(
            "Valid JSON determining the new value of the specified property. For example: `true` or `false`."
        ),
    )


class LogicValueActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("Value"),
        help_text=_(
            "A valid JsonLogic expression describing the value. This may refer to "
            "(other) Form.io components."
        ),
        validators=[JsonLogicValidator()],
    )


class LogicActionPolymorphicSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(
        choices=LogicActionTypes,
        label=_("Type"),
        help_text=_("Action type for this particular action"),
    )

    discriminator_field = "type"
    serializer_mapping = {
        LogicActionTypes.disable_next: serializers.Serializer,
        LogicActionTypes.property: LogicPropertyActionSerializer,
        LogicActionTypes.value: LogicValueActionSerializer,
        LogicActionTypes.step_not_applicable: serializers.Serializer,
    }


class LogicComponentActionSerializer(serializers.Serializer):
    # TODO: validate that the component is present on the form
    component = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Form.io component"),
        help_text=_(
            "Key of the Form.io component that the action applies to. This field is "
            "optional if the action type is `{action_type}`, otherwise required."
        ).format(action_type=LogicActionTypes.disable_next),
    )
    form_step = URLRelatedField(
        required=False,  # validated against the action.type
        queryset=FormStep.objects,
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        label=_("form step"),
        help_text=_(
            "The form step that will be affected by the action. This field is "
            "optional if the action type is `%(action_type)s`, otherwise required."
        )
        % {"action_type": LogicActionTypes.step_not_applicable},
    )
    action = LogicActionPolymorphicSerializer()

    def validate(self, data: dict) -> dict:
        """
        Check that the component is supplied depending on the action type.
        """
        action_type = data.get("action", {}).get("type")
        component = data.get("component")
        form_step = data.get("form_step")

        if (
            action_type
            and action_type in LogicActionTypes.requires_component
            and not component
        ):
            # raises validation error
            self.fields["component"].fail("blank")

        if (
            action_type
            and action_type in LogicActionTypes.step_not_applicable
            and not form_step
        ):
            # raises validation error
            self.fields["form_step"].fail("blank")

        return data


class FormLogicSerializer(serializers.HyperlinkedModelSerializer):
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("Actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    class Meta:
        model = FormLogic
        fields = (
            "uuid",
            "form",
            "json_logic_trigger",
            "actions",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "json_logic_trigger": {
                "help_text": _(
                    "The trigger expression to determine if the actions should execute "
                    "or not. Note that this must be a valid JsonLogic expression, and "
                    "the first operand must be a reference to a component in the form."
                ),
                "validators": [JsonLogicValidator()],
            },
        }

    def validate_json_logic_trigger(self, trigger_logic: dict) -> dict:
        """
        Validate that the first operand of the trigger is a reference to a component.
        """
        # at first instance, we don't support nested logic. Once we do, this will need
        # to be adapted so that we only check primitives.
        logic_test = JsonLogicTest.from_expression(trigger_logic)

        first_operand = logic_test.values[0]
        is_date_operand = (
            first_operand.operator == "date"
            and isinstance(first_operand.values[0], JsonLogicTest)
            and first_operand.values[0].operator == "var"
        )
        if not isinstance(first_operand, JsonLogicTest) or (
            first_operand.operator != "var" and not is_date_operand
        ):
            raise serializers.ValidationError(
                _('The first operand must be a `{"var": "<componentKey>"}` expression.')
            )

        return trigger_logic

    def validate(self, data: dict) -> dict:
        # test that the component is present in the form definition
        form = data.get("form") or self.instance.form
        trigger_logic = (
            data.get("json_logic_trigger") or self.instance.json_logic_trigger
        )

        if form and trigger_logic:
            logic_test = JsonLogicTest.from_expression(trigger_logic)
            first_operand = logic_test.values[0]
            if (
                first_operand.operator == "date"
                and isinstance(first_operand.values[0], JsonLogicTest)
                and first_operand.values[0].operator == "var"
            ):
                needle = first_operand.values[0].values[0]
            else:
                needle = first_operand.values[0]
            for component in form.iter_components(recursive=True):
                if (key := component.get("key")) and key == needle:
                    break
            # executes if the break was not hit
            else:
                raise serializers.ValidationError(
                    {
                        "json_logic_trigger": serializers.ValidationError(
                            _(
                                "The specified component is not present in the form definition"
                            ),
                            code="invalid",
                        )
                    }
                )

        return data
