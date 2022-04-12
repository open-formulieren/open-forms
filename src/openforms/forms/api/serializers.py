from typing import List

from django.db import transaction
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.accounts.api.serializers import UserSerializer
from openforms.api.utils import (
    get_from_serializer_data_or_instance,
    underscore_to_camel,
)
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.authentication.registry import register as auth_register
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.service import (
    get_dynamic_configuration,
    update_configuration_for_request,
)
from openforms.payments.api.fields import PaymentOptionsReadOnlyField
from openforms.payments.registry import register as payment_register
from openforms.products.models import Product
from openforms.registrations.registry import register as registration_register
from openforms.submissions.api.fields import URLRelatedField
from openforms.utils.admin import SubmitActions

from ...config.models import GlobalConfiguration
from ..constants import ConfirmationEmailOptions, LogicActionTypes, PropertyTypes
from ..models import (
    Form,
    FormDefinition,
    FormLogic,
    FormPriceLogic,
    FormStep,
    FormVersion,
)
from .validators import (
    FormIOComponentsValidator,
    JsonLogicActionValueValidator,
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)


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
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
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
    """
    Represent a single `Form` definition.

    Contains all the relevant metadata and configuration from the form design. Form
    renderers should use this as starting point.

    Note that this schema is used for both non-admin users filling out forms and
    admin users designing forms. The fields that are only relevant for admin users are:
    {admin_fields}.
    """

    steps = MinimalFormStepSerializer(many=True, read_only=True, source="formstep_set")

    authentication_backends = serializers.ListField(
        child=serializers.ChoiceField(choices=[]),
        write_only=True,
        required=False,
        default=list,
    )
    login_options = LoginOptionsReadOnlyField()
    auto_login_authentication_backend = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "The authentication backend to which the user will be automatically "
            "redirected upon starting the form. The chosen backend must be present in "
            "`authentication_backends`"
        ),
    )

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
    confirmation_email_template = ConfirmationEmailTemplateSerializer(
        required=False, allow_null=True
    )
    is_deleted = serializers.BooleanField(source="_is_deleted", required=False)
    required_fields_with_asterisk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "login_required",
            "registration_backend",
            "registration_backend_options",
            "authentication_backends",
            "login_options",
            "auto_login_authentication_backend",
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
            "explanation_template",
            "submission_allowed",
            "submissions_removal_options",
            "confirmation_email_template",
            "confirmation_email_option",
            "display_main_website_link",
            "required_fields_with_asterisk",
        )
        # allowlist for anonymous users
        public_fields = (
            "uuid",
            "name",
            "explanation_template",
            "login_required",
            "authentication_backends",
            "auto_login_authentication_backend",
            "login_options",
            "payment_required",
            "payment_options",
            "literals",
            "slug",
            "url",
            "steps",
            "show_progress_indicator",
            "maintenance_mode",
            "active",
            "required_fields_with_asterisk",
            "submission_allowed",
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

    @classmethod
    def _get_admin_field_names(cls, camelize=True) -> List[str]:
        formatter = underscore_to_camel if camelize else lambda x: x
        return [
            formatter(name)
            for name in cls.Meta.fields
            if name not in cls.Meta.public_fields
        ]

    @transaction.atomic()
    def create(self, validated_data):
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        instance = super().create(validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        instance = super().update(instance, validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        return instance

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        fields["authentication_backends"].child.choices = auth_register.get_choices()
        fields["payment_backend"].choices = [("", "")] + payment_register.get_choices()

        request = self.context.get("request")
        view = self.context.get("view")
        is_api_schema_generation = (
            getattr(view, "swagger_fake_view", False) if view else False
        )
        is_mock_request = request and getattr(
            request, "is_mock_request", is_api_schema_generation
        )

        admin_only_fields = self._get_admin_field_names(camelize=False)

        # filter public fields if not staff and not exporting or schema generating
        # request.is_mock_request is set by the export serializers (possibly from management command etc)
        # also this can be called from schema generator without request
        if request and not is_mock_request:
            if not request.user.is_staff:
                for admin_field in admin_only_fields:
                    del fields[admin_field]

        return fields

    def validate(self, attrs):
        super().validate(attrs)
        self.validate_backend_options(
            attrs,
            "registration_backend",
            "registration_backend_options",
            registration_register,
        )
        self.validate_backend_options(
            attrs, "payment_backend", "payment_backend_options", payment_register
        )

        self.validate_auto_login_backend(attrs)

        confirmation_email_option = get_from_serializer_data_or_instance(
            "confirmation_email_option", attrs, self
        )
        confirmation_email_template = (
            get_from_serializer_data_or_instance(
                "confirmation_email_template", attrs, self
            )
            or {}
        )
        if confirmation_email_option == ConfirmationEmailOptions.form_specific_email:
            if isinstance(confirmation_email_template, ConfirmationEmailTemplate):
                _template = confirmation_email_template
            else:
                _template = ConfirmationEmailTemplate(**confirmation_email_template)
            if not _template.is_usable:
                raise serializers.ValidationError(
                    {
                        "confirmation_email_option": ErrorDetail(
                            _(
                                "The form specific confirmation email template is not set up correctly and "
                                "can therefore not be selected."
                            ),
                            code="invalid",
                        )
                    }
                )

        return attrs

    def validate_backend_options(self, attrs, backend_field, options_field, registry):
        plugin_id = get_from_serializer_data_or_instance(
            backend_field, data=attrs, serializer=self
        )
        options = get_from_serializer_data_or_instance(
            options_field, data=attrs, serializer=self
        )
        if not plugin_id:
            return
        plugin = registry[plugin_id]
        if not plugin.configuration_options:
            return

        serializer = plugin.configuration_options(data=options)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # wrap detail in dict so we can attach it to the field
            # DRF will create the .invalidParams with a dotted path to nested fields
            # like registrationBackendOptions.toEmails.0 if the first email was invalid
            detail = {options_field: e.detail}
            raise serializers.ValidationError(detail) from e
        # serializer does some normalization, so make sure to update the data
        attrs[options_field] = serializer.data

    def validate_auto_login_backend(self, attrs):
        field_name = "auto_login_authentication_backend"

        auto_login_backend = get_from_serializer_data_or_instance(
            field_name, attrs, self
        )
        authentication_backends = get_from_serializer_data_or_instance(
            "authentication_backends", attrs, self
        )

        # If an auto login backend is supplied, it must be present in
        # `authentication_backends`
        if auto_login_backend and auto_login_backend not in authentication_backends:
            raise serializers.ValidationError(
                {
                    field_name: ErrorDetail(
                        _(
                            "The `auto_login_authentication_backend` must be one of "
                            "the selected backends from `authentication_backends`"
                        ),
                        code="invalid",
                    )
                }
            )

    def get_required_fields_with_asterisk(self, obj) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.form_display_required_with_asterisk


FormSerializer.__doc__ = FormSerializer.__doc__.format(
    admin_fields=", ".join(
        [f"`{field}`" for field in FormSerializer._get_admin_field_names()]
    )
)


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

        # set upload urls etc
        update_configuration_for_request(
            representation["configuration"],
            request=self.context["request"],
        )

        _handle_custom_types = self.context.get("handle_custom_types", True)
        if _handle_custom_types:
            representation["configuration"] = get_dynamic_configuration(
                representation["configuration"],
                request=self.context["request"],
                submission=self.context["submission"],
            )
        return representation

    class Meta:
        model = FormDefinition
        fields = (
            "url",
            "uuid",
            "name",
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
            },
            "configuration": {
                "validators": [FormIOComponentsValidator()],
            },
        }


class UsedInFormSerializer(serializers.HyperlinkedModelSerializer):
    admin_url = serializers.SerializerMethodField(
        label=_("admin URL"),
        help_text=_("Link to the change/view page in the admin interface"),
    )

    class Meta:
        model = Form
        fields = (
            "url",
            "uuid",
            "name",
            "active",
            "admin_url",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "name": {
                "source": "admin_name",
            },
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_admin_url(self, obj: Form) -> str:
        admin_url = reverse("admin:forms_form_change", args=(obj.pk,))
        request = self.context.get("request")
        if not request:
            return admin_url
        return request.build_absolute_uri(admin_url)


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
    name = serializers.CharField(source="form_definition.name", read_only=True)
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
            "name",
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
    user = UserSerializer(required=False, read_only=True)

    class Meta:
        model = FormVersion
        fields = (
            "uuid",
            "created",
            "user",
            "description",
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
        validators=[JsonLogicActionValueValidator()],
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
        allow_null=True,
        required=False,  # validated against the action.type
        queryset=FormStep.objects,
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        label=_("form step"),
        help_text=_(
            "The form step that will be affected by the action. This field is "
            "required if the action type is `%(action_type)s`, otherwise optional."
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
            raise serializers.ValidationError(
                {"component": self.fields["component"].error_messages["blank"]},
                code="blank",
            )

        if (
            action_type
            and action_type == LogicActionTypes.step_not_applicable
            and not form_step
        ):
            raise serializers.ValidationError(
                {"form_step": self.fields["form_step"].error_messages["blank"]},
                code="blank",
            )

        return data


class FormLogicBaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        fields = (
            "uuid",
            "url",
            "form",
            "json_logic_trigger",
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
        validators = [
            JsonLogicTriggerValidator("json_logic_trigger"),
        ]


class FormLogicSerializer(FormLogicBaseSerializer):
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("Actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    class Meta(FormLogicBaseSerializer.Meta):
        model = FormLogic
        fields = FormLogicBaseSerializer.Meta.fields + ("actions", "is_advanced")
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:form-logics-detail",
                "lookup_field": "uuid",
            },
        }


class FormPriceLogicSerializer(FormLogicBaseSerializer):
    class Meta(FormLogicBaseSerializer.Meta):
        model = FormPriceLogic
        fields = FormLogicBaseSerializer.Meta.fields + ("price",)
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:price-logics-detail",
                "lookup_field": "uuid",
            },
        }


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
