from typing import List

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.utils import (
    get_from_serializer_data_or_instance,
    underscore_to_camel,
)
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.authentication.registry import register as auth_register
from openforms.config.models import GlobalConfiguration
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.payments.api.fields import PaymentOptionsReadOnlyField
from openforms.payments.registry import register as payment_register
from openforms.products.models import Product
from openforms.registrations.registry import register as registration_register

from ...constants import ConfirmationEmailOptions
from ...models import Form
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


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )
