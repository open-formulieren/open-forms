from django.db import transaction
from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.plumbing import build_array_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.api.utils import (
    get_from_serializer_data_or_instance,
    underscore_to_camel,
)
from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.authentication.registry import register as auth_register
from openforms.config.api.constants import STATEMENT_CHECKBOX_SCHEMA
from openforms.config.models import GlobalConfiguration, Theme
from openforms.contrib.haal_centraal.api.serializers import (
    BRPPersonenRequestOptionsSerializer,
)
from openforms.contrib.haal_centraal.models import BRPPersonenRequestOptions
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.typing import Component
from openforms.payments.api.fields import PaymentOptionsReadOnlyField
from openforms.payments.registry import register as payment_register
from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH
from openforms.products.models import Product
from openforms.registrations.registry import register as registration_register
from openforms.registrations.service import plugin_allows_json_schema_generation
from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import RegistrationBackendKey

from ...constants import StatementCheckboxChoices
from ...models import Category, Form, FormAuthenticationBackend, FormRegistrationBackend
from .button_text import ButtonTextSerializer
from .form_step import MinimalFormStepSerializer

logger = structlog.stdlib.get_logger(__name__)


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


class FormAuthenticationBackendSerializer(serializers.ModelSerializer):
    options = serializers.JSONField(
        label=_("authentication backend options"), allow_null=True, required=False
    )

    class Meta:
        model = FormAuthenticationBackend
        fields = ("backend", "options")

    def validate(self, attrs):
        plugin = auth_register[attrs["backend"]]

        if not plugin.configuration_options:
            return attrs

        options = get_from_serializer_data_or_instance("options", attrs, self)
        serializer = plugin.configuration_options(
            data=options, context=self.context, required=False, allow_null=True
        )
        if not serializer.is_valid():
            raise serializers.ValidationError({"options": serializer.errors})
        # serializer does some normalization, so make sure to update the data
        attrs["options"] = serializer.data
        return attrs


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

    login_options = LoginOptionsReadOnlyField()
    cosign_login_options = LoginOptionsReadOnlyField(is_for_cosign=True)
    cosign_has_link_in_email = serializers.SerializerMethodField(
        label=_("cosign request has links in email"),
        help_text=_(
            "Indicates whether deep links are included in the cosign request emails "
            "or not."
        ),
    )
    auto_login_authentication_backend = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "The authentication backend to which the user will be automatically "
            "redirected upon starting the form. The chosen backend must be present in "
            "`auth_backends`"
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
    communication_preferences_portal_url = serializers.SerializerMethodField(
        read_only=True
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
    submission_limit_reached = serializers.SerializerMethodField()
    brp_personen_request_options = BRPPersonenRequestOptionsSerializer(
        required=False, allow_null=True
    )

    translations = ModelTranslationsSerializer()

    registration_backends = FormRegistrationBackendSerializer(many=True, required=False)
    auth_backends = FormAuthenticationBackendSerializer(many=True, required=False)

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "internal_remarks",
            "login_required",
            "translation_enabled",
            "registration_backends",
            "auth_backends",
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
            "submission_limit",
            "submission_counter",
            "submission_limit_reached",
            "suspension_allowed",
            "ask_privacy_consent",
            "ask_statement_of_truth",
            "submissions_removal_options",
            "confirmation_email_template",
            "send_confirmation_email",
            "display_main_website_link",
            "include_confirmation_page_content_in_pdf",
            "required_fields_with_asterisk",
            "communication_preferences_portal_url",
            "translations",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
            "cosign_login_options",
            "cosign_has_link_in_email",
            "submission_statements_configuration",
            "submission_report_download_link_title",
            "brp_personen_request_options",
            "new_renderer_enabled",
            "new_logic_evaluation_enabled",
        )
        # allowlist for anonymous users
        public_fields = (
            "uuid",
            "name",
            "introduction_page_content",
            "explanation_template",
            "login_required",
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
            "communication_preferences_portal_url",
            "submission_allowed",
            "submission_limit_reached",
            "suspension_allowed",
            "send_confirmation_email",
            "appointment_options",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
            "cosign_login_options",
            "cosign_has_link_in_email",
            "submission_statements_configuration",
            "submission_report_download_link_title",
            "new_renderer_enabled",
            "new_logic_evaluation_enabled",
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
        auth_backends = validated_data.pop("auth_backends", [])

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
        FormAuthenticationBackend.objects.bulk_create(
            FormAuthenticationBackend(form=instance, **backend)
            for backend in auth_backends
        )
        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        brp_personen_request_options = validated_data.pop(
            "brp_personen_request_options", None
        )
        registration_backends = validated_data.pop("registration_backends", None)
        auth_backends = validated_data.pop("auth_backends", None)

        instance = super().update(instance, validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        if brp_personen_request_options is not None:
            BRPPersonenRequestOptions.objects.update_or_create(
                form=instance, defaults=brp_personen_request_options
            )
        if registration_backends is not None:
            instance.registration_backends.all().delete()
            FormRegistrationBackend.objects.bulk_create(
                FormRegistrationBackend(form=instance, **backend)
                for backend in registration_backends
            )
        if auth_backends is not None:
            instance.auth_backends.all().delete()
            FormAuthenticationBackend.objects.bulk_create(
                FormAuthenticationBackend(form=instance, **backend_config)
                for backend_config in auth_backends
            )

        return instance

    def get_fields(self):
        fields = super().get_fields()
        # lazy set choices
        if "payment_backend" in fields:
            fields["payment_backend"].choices = [
                ("", "")
            ] + payment_register.get_choices()

        return fields

    def convert_objects_api_group(self, attrs) -> None:
        """
        backwards compatibility for using objects_api_group as pk in the form registration backends
        see GH issue #5384
        """
        if not self.context.get("is_import", False):
            return

        if "registration_backends" not in attrs:
            return

        objects_api_pk_to_slug = {
            group.pk: group.identifier for group in ObjectsAPIGroupConfig.objects.all()
        }
        for plugin in attrs["registration_backends"]:
            options = plugin["options"]
            if not (api_group_id := options.get("objects_api_group")):
                continue

            if isinstance(api_group_id, int):
                api_group_slug = objects_api_pk_to_slug[api_group_id]
                options["objects_api_group"] = api_group_slug
                logger.info(
                    "objects_api_group_reference_converted",
                    from_pk=api_group_id,
                    to_identifier=api_group_slug,
                )

    def to_internal_value(self, attrs):
        self.convert_objects_api_group(attrs)
        return super().to_internal_value(attrs)

    def _handle_import(self, attrs) -> None:
        # we're not importing, nothing to do
        if not self.context.get("is_import", False) or not hasattr(
            self, "initial_data"
        ):
            return

        if (
            "authentication_backends" not in self.initial_data
            and "authentication_backend_options" not in self.initial_data
        ):
            return

        # Make sure `auth_backends` exists
        attrs["auth_backends"] = attrs.get("auth_backends", [])
        auth_backends_map = {}

        # Pre-fill the map with the `auth_backends` values
        for auth_backend in attrs["auth_backends"]:
            auth_backends_map[auth_backend["backend"]] = auth_backend

        # Collect all the backends that should be transformed to `auth_backends`
        if "authentication_backends" in self.initial_data:
            for plugin in self.initial_data["authentication_backends"]:
                # Add plugin if it's not already in the map
                if plugin not in auth_backends_map:
                    auth_backends_map[plugin] = {
                        "backend": plugin,
                        "options": None,
                    }

        if "authentication_backend_options" in self.initial_data:
            for plugin, options in self.initial_data[
                "authentication_backend_options"
            ].items():
                if plugin not in auth_backends_map:
                    auth_backends_map[plugin] = {
                        "backend": plugin,
                        "options": options,
                    }
                    continue

                if auth_backends_map[plugin]["options"] is None:
                    auth_backends_map[plugin]["options"] = options

        validated_auth_backends = []
        for config in auth_backends_map.values():
            validated_auth_backends.append(
                FormAuthenticationBackendSerializer().validate(config)
            )
        attrs["auth_backends"] = validated_auth_backends

    def validate(self, attrs):
        super().validate(attrs)
        self._handle_import(attrs)

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
            # like registrationBackends.0.options.toEmails.0 if the first email was invalid
            detail = {options_field: e.detail}
            raise serializers.ValidationError(detail) from e
        # serializer does some normalization, so make sure to update the data
        attrs[options_field] = serializer.data

    def validate_auto_login_backend(self, attrs):
        field_name = "auto_login_authentication_backend"

        auto_login_backend = get_from_serializer_data_or_instance(
            field_name, attrs, self
        )
        auth_backends = get_from_serializer_data_or_instance(
            "auth_backends", attrs, self
        )

        # If an auto login backend is supplied, it must be present in
        # `auth_backends`
        if auto_login_backend and not any(
            auth_backend["backend"] == auto_login_backend
            for auth_backend in auth_backends
        ):
            raise serializers.ValidationError(
                {
                    field_name: ErrorDetail(
                        _(
                            "The `auto_login_authentication_backend` must be one of "
                            "the selected backends from `auth_backends`"
                        ),
                        code="invalid",
                    )
                }
            )

    def get_required_fields_with_asterisk(self, obj) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.form_display_required_with_asterisk

    def get_communication_preferences_portal_url(self, obj) -> str:
        config = GlobalConfiguration.get_solo()
        return config.communication_preferences_portal_url

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

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_cosign_has_link_in_email(self, obj: Form) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.cosign_request_template_has_link

    def get_submission_limit_reached(self, obj: Form) -> bool:
        return obj.submissions_limit_reached


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
        return fields


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )


class FormImportResponseSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(help_text=_("The uuid of the imported form."))


class FormJsonSchemaOptionsSerializer(serializers.Serializer):
    registration_backend_key: RegistrationBackendKey = serializers.CharField(
        label=_("Registration backend key"),
        max_length=50,
        help_text=_("The registration backend key for which to generate the schema."),
        required=True,
        allow_null=False,
    )
    backend = serializers.CharField(
        label=_("Registration backend identifier"),
        max_length=UNIQUE_ID_MAX_LENGTH,
        read_only=True,
    )
    options = serializers.JSONField(
        label=_("Registration backend options"),
        read_only=True,
    )

    def validate_registration_backend_key(self, value):
        form = self.context["form"]

        # Note that a backend is unique by its key for each form
        try:
            backend = form.registration_backends.get(key=value)
        except FormRegistrationBackend.DoesNotExist as exc:
            raise ValidationError(
                _("Backend with key '{key}' does not exist for form '{form}'").format(
                    key=value, form=form
                )
            ) from exc

        plugin = registration_register[backend.backend]
        options_serializer = plugin.configuration_options(
            data=backend.options,
            context={"validate_business_logic": False},
        )
        # the options are expected to be valid since the form must be saved before you
        # can call this endpoint
        options_serializer.is_valid(raise_exception=True)
        backend_options = options_serializer.validated_data
        if not plugin_allows_json_schema_generation(backend.backend, backend_options):
            raise ValidationError(
                _(
                    "Backend with id '{backend}' does not allow JSON schema generation"
                ).format(backend=backend.backend)
            )

        self.context["_backend"] = {
            "plugin": backend.backend,
            "options": backend_options,
        }

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        _backend = self.context["_backend"]
        attrs["backend"] = _backend["plugin"]
        attrs["options"] = _backend["options"]

        return attrs

    @classmethod
    def as_openapi_params(cls):
        instance = cls()
        field = instance.fields["registration_backend_key"]
        return [
            OpenApiParameter(
                underscore_to_camel(str(field.field_name)),
                OpenApiTypes.STR,
                description=str(field.help_text),
            )
        ]
