import warnings

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_array_type
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.authentication.api.serializers import CosignLoginInfoSerializer
from openforms.authentication.registry import register as auth_register
from openforms.config.api.constants import STATEMENT_CHECKBOX_SCHEMA
from openforms.config.models import GlobalConfiguration, Theme
from openforms.contrib.haal_centraal.api.serializers import (
    BRPPersonenRequestOptionsSerializer,
)
from openforms.contrib.haal_centraal.models import BRPPersonenRequestOptions
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.typing import Component
from openforms.payments.api.fields import PaymentOptionsReadOnlyField
from openforms.payments.registry import register as payment_register
from openforms.products.models import Product
from openforms.registrations.registry import register as registration_register
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ...constants import StatementCheckboxChoices
from ...models import Category, Form, FormRegistrationBackend
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


class FormRegistrationBackendSerializer(serializers.ModelSerializer):
    options = serializers.DictField(label=_("registration backend options"))

    class Meta:
        model = FormRegistrationBackend
        fields = [
            "key",
            "name",
            "backend",
            "options",
        ]

    def get_fields(self):
        # set backend choices at runtime
        fields = super().get_fields()
        fields["backend"].choices = registration_register.get_choices()
        return fields

    def to_internal_value(self, data):

        if self.context.get("is_import", False):
            if data.get("backend") == "stuf-zds-create-zaak:ext-utrecht":
                from openforms.registrations.contrib.stuf_zds.plugin import (
                    PLUGIN_IDENTIFIER,
                )

                warnings.warn(
                    "The automatic conversion from StUF-ZDS payments extension to "
                    "StUF-ZDS during import will be removed in Open Forms 3.0",
                    category=DeprecationWarning,
                )
                data["backend"] = PLUGIN_IDENTIFIER
        return super().to_internal_value(data)

    def validate(self, attrs):
        # validate config options with selected plugin
        if "backend" not in attrs:
            # performing nested PATCH
            return attrs
        plugin = registration_register[attrs["backend"]]

        if not plugin.configuration_options:  # unicorn case
            return attrs  # pragma: nocover

        serializer = plugin.configuration_options(
            data=attrs["options"], context=self.context
        )
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            detail = {"options": e.detail}
            raise serializers.ValidationError(detail) from e
        # serializer does some normalization, so make sure to update the data
        attrs["options"] = serializer.data
        return attrs


@extend_schema_serializer(
    deprecate_fields=[
        "registration_backend",
        "registration_backend_options",
        "cosign_login_info",
    ]
)
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
    authentication_backend_options = serializers.DictField(required=False, default=dict)
    login_options = LoginOptionsReadOnlyField()
    cosign_login_options = LoginOptionsReadOnlyField(is_for_cosign=True)
    # TODO: deprecated, remove in 3.0.0
    cosign_login_info = CosignLoginInfoSerializer(source="*", read_only=True)
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
    theme = serializers.HyperlinkedRelatedField(
        label=_("theme"),
        queryset=Theme.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:themes-detail",
        lookup_field="uuid",
        help_text=_("URL to the theme in the Open Forms API"),
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
    payment_backend_options = serializers.DictField(
        label=_("payment backend options"),
        required=False,
        allow_null=True,
    )
    payment_options = PaymentOptionsReadOnlyField()

    appointment_options = AppointmentOptionsSerializer(
        source="*",
        required=False,
        allow_null=True,
    )

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
    submission_report_download_link_title = serializers.SerializerMethodField()
    submission_statements_configuration = serializers.SerializerMethodField(
        label=_("submission statements configuration"),
        help_text=_(
            "A list of statements that need to be accepted by the user before they "
            "can submit a form. Returns a list of formio component definitions, all "
            "of type 'checkbox'."
        ),
    )
    brp_personen_request_options = BRPPersonenRequestOptionsSerializer(
        required=False, allow_null=True
    )

    translations = ModelTranslationsSerializer()

    registration_backends = FormRegistrationBackendSerializer(many=True, required=False)

    # deprecated fields
    registration_backend = serializers.CharField(required=False, allow_blank=True)
    registration_backend_options = serializers.JSONField(
        required=False, allow_null=True
    )

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "login_required",
            "translation_enabled",
            "registration_backends",
            "registration_backend",
            "registration_backend_options",
            "authentication_backends",
            "authentication_backend_options",
            "login_options",
            "auto_login_authentication_backend",
            "payment_required",
            "payment_backend",
            "payment_backend_options",
            "payment_options",
            "price_variable_key",
            "appointment_options",
            "literals",
            "product",
            "slug",
            "url",
            "category",
            "theme",
            "steps",
            "show_progress_indicator",
            "show_summary_progress",
            "maintenance_mode",
            "active",
            "activate_on",
            "deactivate_on",
            "is_deleted",
            "submission_confirmation_template",
            "introduction_page_content",
            "explanation_template",
            "submission_allowed",
            "suspension_allowed",
            "ask_privacy_consent",
            "ask_statement_of_truth",
            "submissions_removal_options",
            "confirmation_email_template",
            "send_confirmation_email",
            "display_main_website_link",
            "include_confirmation_page_content_in_pdf",
            "required_fields_with_asterisk",
            "translations",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
            "cosign_login_options",
            "cosign_login_info",
            "submission_statements_configuration",
            "submission_report_download_link_title",
            "brp_personen_request_options",
        )
        # allowlist for anonymous users
        public_fields = (
            "uuid",
            "name",
            "introduction_page_content",
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
            "show_summary_progress",
            "maintenance_mode",
            "translation_enabled",
            "active",
            "required_fields_with_asterisk",
            "submission_allowed",
            "suspension_allowed",
            "appointment_options",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
            "cosign_login_options",
            "cosign_login_info",
            "submission_statements_configuration",
            "submission_report_download_link_title",
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
        brp_personen_request_options = validated_data.pop(
            "brp_personen_request_options", None
        )
        registration_backends = validated_data.pop("registration_backends", [])

        registration_backend_options = (
            validated_data.pop("registration_backend_options", None) or {}
        )
        if "registration_backend" in validated_data:
            warnings.warn(
                (
                    "Form 'registration_backend' and 'registration_backend_options' "
                    "are deprecated, use 'registration_backends' instead."
                ),
                DeprecationWarning,
            )
            registration_backends.append(
                {
                    "key": "default",
                    "name": _("Default"),
                    "backend": validated_data.pop("registration_backend"),
                    "options": registration_backend_options,
                }
            )

        instance = super().create(validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        if brp_personen_request_options is not None:
            BRPPersonenRequestOptions.objects.create(
                form=instance, **brp_personen_request_options
            )
        FormRegistrationBackend.objects.bulk_create(
            FormRegistrationBackend(form=instance, **backend)
            for backend in registration_backends
        )
        return instance

    def _update_v2_registration_backend(self, form, validated_data):
        new_data = {}
        if "registration_backend" in validated_data:
            new_data["backend"] = validated_data.pop("registration_backend")
        if "registration_backend_options" in validated_data:
            new_data["options"] = validated_data.pop("registration_backend_options")
        if not any(v is not None for v in new_data.values()):
            return

        warnings.warn(
            (
                "Form 'registration_backend' and 'registration_backend_options' "
                "are deprecated, use 'registration_backends' instead."
            ),
            DeprecationWarning,
        )

        backend = form.registration_backends.first() or FormRegistrationBackend(
            form=form, name=_("Default"), key="default"
        )
        serializer = FormRegistrationBackendSerializer(
            instance=backend, data=new_data, context=self.context, partial=self.partial
        )
        # validated_data ought to be correct already
        assert serializer.is_valid()
        serializer.save()

    @transaction.atomic()
    def update(self, instance, validated_data):
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        brp_personen_request_options = validated_data.pop(
            "brp_personen_request_options", None
        )
        registration_backends = validated_data.pop("registration_backends", None)

        self._update_v2_registration_backend(instance, validated_data)

        instance = super().update(instance, validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        if brp_personen_request_options is not None:
            BRPPersonenRequestOptions.objects.update_or_create(
                form=instance, defaults=brp_personen_request_options
            )
        if registration_backends is None:
            return instance

        instance.registration_backends.all().delete()
        FormRegistrationBackend.objects.bulk_create(
            FormRegistrationBackend(form=instance, **backend)
            for backend in registration_backends
        )

        return instance

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        if "authentication_backends" in fields:
            fields["authentication_backends"].child.choices = (
                auth_register.get_choices()
            )
        if "payment_backend" in fields:
            fields["payment_backend"].choices = [
                ("", "")
            ] + payment_register.get_choices()

        # adapt fields for v2 backwards compatibility
        if "registration_backends" in fields:
            v2_backend = fields["registration_backend"]
            v3_backend = fields["registration_backends"].child.get_fields()["backend"]
            v2_backend.choices = v3_backend.choices

        return fields

    def validate(self, attrs):
        super().validate(attrs)

        if "registration_backend" in attrs and "registration_backends" in attrs:
            raise serializers.ValidationError(
                {
                    "registration_backend": ErrorDetail(
                        _(
                            "registration_backend is deprecated, please use just registration_backends",
                        ),
                        code="invalid",
                    ),
                    "registration_backend_options": ErrorDetail(
                        _(
                            "registration_backend is deprecated, please use just registration_backends",
                        ),
                        code="invalid",
                    ),
                }
            )

        if "registration_backends" not in attrs:
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

    def get_submission_report_download_link_title(self, obj) -> str:
        config = GlobalConfiguration.get_solo()
        return config.submission_report_download_link_title

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

    @extend_schema_field(field=build_array_type(STATEMENT_CHECKBOX_SCHEMA))
    def get_submission_statements_configuration(self, obj: Form) -> list[Component]:
        config = GlobalConfiguration.get_solo()

        ask_privacy_consent = (
            obj.ask_privacy_consent == StatementCheckboxChoices.required
            or (
                obj.ask_privacy_consent == StatementCheckboxChoices.global_setting
                and config.ask_privacy_consent
            )
        )
        ask_statement_of_truth = (
            obj.ask_statement_of_truth == StatementCheckboxChoices.required
            or (
                obj.ask_statement_of_truth == StatementCheckboxChoices.global_setting
                and config.ask_statement_of_truth
            )
        )

        # TODO Generalise to configurable declarations
        privacy_policy_checkbox = Component(
            key="privacyPolicyAccepted",
            label=config.render_privacy_policy_label(),
            validate={"required": ask_privacy_consent},
            type="checkbox",
        )
        truth_declaration_checkbox = Component(
            key="statementOfTruthAccepted",
            label=config.statement_of_truth_label,
            validate={"required": ask_statement_of_truth},
            type="checkbox",
        )

        return [privacy_policy_checkbox, truth_declaration_checkbox]


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
        if "registration_backend" in fields:
            del fields["registration_backend"]
        if "registration_backend_options" in fields:
            del fields["registration_backend_options"]
        return fields


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )
