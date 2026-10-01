from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import NotRequired, TypedDict

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
class AdditionalFormConfigurationCleanup:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[type[TypedDict]], None]


@dataclass(frozen=True)
class FormConfigurationCleanup:
    option: FormConfigurationOptions
    cleanup: Callable[[type[TypedDict]], None]


class FormRegistrationExportRepresentation(TypedDict):
    key: str
    name: str
    backend: str
    options: JSONObject


class FormLogicExportRepresentation(TypedDict):
    uuid: str
    url: str
    form: str
    json_logic_trigger: JSONObject
    description: NotRequired[str]
    order: int
    actions: list[JSONObject]
    is_advanced: NotRequired[bool]


class FormVariableExportRepresentation(TypedDict):
    form: str
    form_definition: NotRequired[str]
    name: str
    key: str
    source: str
    service_fetch_configuration: JSONObject
    prefill_plugin: str
    prefill_attribute: str
    prefill_identifier_role: str
    prefill_options: NotRequired[JSONObject]
    data_type: str
    data_format: str
    is_sensitive_data: bool
    initial_value: JSONObject


class FormStepExportRepresentation(TypedDict):
    uuid: str
    index: int
    slug: str
    configuration: JSONObject
    form_definition: str
    name: str
    internal_name: NotRequired[str]
    url: str
    is_applicable: NotRequired[bool]
    login_required: NotRequired[bool]
    is_reusable: NotRequired[bool]
    translations: NotRequired[JSONObject]


class FormDefinitionExportRepresentation(TypedDict):
    url: str
    uuid: str
    name: str
    internal_name: NotRequired[str]
    slug: str
    configuration: JSONObject
    login_required: NotRequired[bool]
    is_reusable: NotRequired[bool]
    translations: NotRequired[JSONObject]


class FormExportRepresentation(TypedDict):
    uuid: str
    name: str
    internal_name: NotRequired[str]
    internal_remarks: NotRequired[str]
    slug: str
    url: str
    login_required: NotRequired[bool]
    translations_enabled: NotRequired[bool]

    registration_backends: NotRequired[list[FormRegistrationExportRepresentation]]
    auth_backends: NotRequired[list[JSONObject]]
    auto_login_authentication_backend: NotRequired[str]
    payment_required: NotRequired[bool]
    payment_backend: NotRequired[str]
    payment_backend_options: NotRequired[JSONObject]
    price_variable_key: NotRequired[str]

    appointment_options: NotRequired[JSONObject]
    product: NotRequired[str]
    type: FormTypeChoices
    category: NotRequired[str]
    theme: NotRequired[str]
    steps: list[FormStepExportRepresentation]
    show_progress_indicator: NotRequired[bool]
    show_summary_progress: NotRequired[bool]
    maintenance_mode: NotRequired[bool]
    active: NotRequired[bool]
    activate_on: NotRequired[str]
    deactivate_on: NotRequired[str]
    is_deleted: NotRequired[bool]

    submission_confirmation_template: NotRequired[str]
    introduction_page_content: NotRequired[str]
    explanation_template: NotRequired[str]
    submission_allowed: NotRequired[str]
    submission_limit: NotRequired[int]
    submission_counter: NotRequired[int]
    submission_limit_reached: NotRequired[bool]
    suspension_allowed: NotRequired[bool]

    ask_privacy_consent: NotRequired[str]
    ask_statement_of_truth: NotRequired[str]
    submissions_removal_options: NotRequired[JSONObject]
    confirmation_email_template: NotRequired[JSONObject]

    send_confirmation_email: NotRequired[bool]
    display_main_website_link: NotRequired[bool]
    include_confirmation_page_content_in_pdf: NotRequired[bool]

    required_fields_with_asterisk: NotRequired[bool]
    communication_preferences_portal_url: NotRequired[str]
    translations: NotRequired[JSONObject]
    resume_link_lifetime: NotRequired[int]
    hide_non_applicable_steps: NotRequired[bool]
    cosign_login_options: NotRequired[JSONObject]
    cosign_has_link_in_email: NotRequired[bool]
    submission_statements_configuration: NotRequired[JSONObject]
    submission_report_download_link_title: NotRequired[str]
    brp_personen_request_options: NotRequired[JSONObject]
