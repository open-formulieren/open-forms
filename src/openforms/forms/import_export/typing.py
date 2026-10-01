from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TypedDict

from openforms.typing import JSONObject

from ..constants import FormTypeChoices
from .constants import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)


# This is needed for the form bulk export Celery task.
# Any other place where export options are needed should use FormExportOptions.
class FormExportOptionsData(TypedDict, total=False):
    remove_sensitive_content: bool
    form_configuration: Sequence[FormConfigurationOptions]
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions]


@dataclass(slots=True)
class FormExportOptions:
    remove_sensitive_content: bool = True
    form_configuration: Sequence[FormConfigurationOptions] = field(
        default_factory=lambda: [
            FormConfigurationOptions.registration_backends,
            FormConfigurationOptions.prefill,
            FormConfigurationOptions.payment_backend,
            FormConfigurationOptions.auth_backends,
        ]
    )
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class AdditionalFormConfigurationCleanup[RT]:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[RT], None]


@dataclass(frozen=True)
class FormConfigurationCleanup[RT]:
    option: FormConfigurationOptions
    cleanup: Callable[[RT], None]


class FormRegistrationExportRepresentation(TypedDict, total=False):
    key: str
    name: str
    backend: str
    options: JSONObject


class FormLogicExportRepresentation(TypedDict, total=False):
    uuid: str
    url: str
    form: str
    json_logic_trigger: JSONObject
    description: str
    order: int
    actions: list[JSONObject]
    is_advanced: bool


class FormVariableExportRepresentation(TypedDict, total=False):
    form: str
    form_definition: str
    name: str
    key: str
    source: str
    service_fetch_configuration: JSONObject
    prefill_plugin: str
    prefill_attribute: str
    prefill_identifier_role: str
    prefill_options: JSONObject
    data_type: str
    data_format: str
    is_sensitive_data: bool
    initial_value: JSONObject


class FormStepExportRepresentation(TypedDict, total=False):
    uuid: str
    index: int
    slug: str
    configuration: JSONObject
    form_definition: str
    name: str
    internal_name: str
    url: str
    is_applicable: bool
    login_required: bool
    is_reusable: bool
    translations: JSONObject


class FormDefinitionExportRepresentation(TypedDict, total=False):
    url: str
    uuid: str
    name: str
    internal_name: str
    slug: str
    configuration: JSONObject
    login_required: bool
    is_reusable: bool
    translations: JSONObject


class FormExportRepresentation(TypedDict, total=False):
    uuid: str
    name: str
    internal_name: str
    internal_remarks: str
    slug: str
    url: str
    login_required: bool
    translations_enabled: bool

    registration_backends: list[FormRegistrationExportRepresentation]
    auth_backends: list[JSONObject]
    auto_login_authentication_backend: str
    payment_required: bool
    payment_backend: str
    payment_backend_options: JSONObject
    price_variable_key: str

    appointment_options: JSONObject
    product: str
    type: FormTypeChoices
    category: str
    theme: str
    steps: list[FormStepExportRepresentation]
    show_progress_indicator: bool
    show_summary_progress: bool
    maintenance_mode: bool
    active: bool
    activate_on: str
    deactivate_on: str
    is_deleted: bool

    submission_confirmation_template: str
    introduction_page_content: str
    explanation_template: str
    submission_allowed: str
    submission_limit: int
    submission_counter: int
    submission_limit_reached: bool
    suspension_allowed: bool

    ask_privacy_consent: str
    ask_statement_of_truth: str
    submissions_removal_options: JSONObject
    confirmation_email_template: JSONObject

    send_confirmation_email: bool
    display_main_website_link: bool
    include_confirmation_page_content_in_pdf: bool

    required_fields_with_asterisk: bool
    communication_preferences_portal_url: str
    translations: JSONObject
    resume_link_lifetime: int
    hide_non_applicable_steps: bool
    cosign_login_options: JSONObject
    cosign_has_link_in_email: bool
    submission_statements_configuration: JSONObject
    submission_report_download_link_title: str
    brp_personen_request_options: JSONObject
