from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.authentication.registry import register as auth_register
from openforms.config.models import GlobalConfiguration
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.payments.api.fields import PaymentOptionsReadOnlyField
from openforms.payments.registry import register as payment_register
from openforms.products.models import Product
from openforms.registrations.registry import register as registration_register
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ...models import Category, Form
from .button_text import ButtonTextSerializer
from .form_step import MinimalFormStepSerializer


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


class FormLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text", required=False)
    begin_text = ButtonTextSerializer(raw_field="begin_text", required=False)
    change_text = ButtonTextSerializer(raw_field="change_text", required=False)
    confirm_text = ButtonTextSerializer(raw_field="confirm_text", required=False)


class FormSerializer(PublicFieldsSerializerMixin, serializers.ModelSerializer):
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

    category = serializers.HyperlinkedRelatedField(
        label=_("category"),
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:categories-detail",
        lookup_field="uuid",
        help_text=_("URL to the category in the Open Forms API"),
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
    resume_link_lifetime = serializers.SerializerMethodField(
        label=_("Resume link lifetime"),
        read_only=True,
        help_text=_("The number of days that the resume link is valid for."),
    )
    hide_non_applicable_steps = serializers.SerializerMethodField(read_only=True)

    translations = ModelTranslationsSerializer()

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "login_required",
            "translation_enabled",
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
            "category",
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
            "send_confirmation_email",
            "display_main_website_link",
            "include_confirmation_page_content_in_pdf",
            "required_fields_with_asterisk",
            "translations",
            "appointment_enabled",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
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
            "translation_enabled",
            "active",
            "required_fields_with_asterisk",
            "submission_allowed",
            "appointment_enabled",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
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
        if "authentication_backends" in fields:
            fields[
                "authentication_backends"
            ].child.choices = auth_register.get_choices()
        if "payment_backend" in fields:
            fields["payment_backend"].choices = [
                ("", "")
            ] + payment_register.get_choices()
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

    def get_hide_non_applicable_steps(self, obj) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.hide_non_applicable_steps

    def get_resume_link_lifetime(self, obj) -> int:
        config = GlobalConfiguration.get_solo()
        lifetime = (
            obj.incomplete_submissions_removal_limit
            or config.incomplete_submissions_removal_limit
        )
        lifetime_all = (
            obj.all_submissions_removal_limit or config.all_submissions_removal_limit
        )
        lifetime = min(lifetime, lifetime_all)

        return lifetime


FormSerializer.__doc__ = FormSerializer.__doc__.format(
    admin_fields=", ".join(
        [f"`{field}`" for field in FormSerializer._get_admin_field_names()]
    )
)


class FormExportSerializer(FormSerializer):
    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        if "login_options" in fields:
            del fields["login_options"]
        if "payment_options" in fields:
            del fields["payment_options"]
        if "authentication_backends" in fields:
            fields["authentication_backends"].write_only = False
        return fields


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )
