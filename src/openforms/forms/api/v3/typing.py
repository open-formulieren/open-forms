from datetime import datetime
from typing import Literal, NotRequired, TypedDict
from uuid import UUID

from openforms.appointments.base import Product
from openforms.config.models import Theme
from openforms.data_removal.constants import RemovalMethods
from openforms.emails.typing import ConfirmationEmailTemplateTranslatedData
from openforms.formio.typing import FormioConfiguration
from openforms.prefill.constants import IdentifierRoles
from openforms.variables.constants import (
    DataMappingTypes,
    FormVariableDataTypes,
    FormVariableSources,
    ServiceFetchMethods,
)
from openforms.typing import JSONValue

from ...constants import (
    FormTypeChoices,
    LogicActionTypes,
    PropertyTypes,
    StatementCheckboxChoices,
)
from ...models import Category


class AppointmentData(TypedDict):
    supports_multiple_products: bool | None


class ButtonTextData(TypedDict):
    value: str
    resolved: str


class FormLiteralData(TypedDict):
    previous_text: NotRequired[ButtonTextData]
    begin_text: NotRequired[ButtonTextData]
    change_text: NotRequired[ButtonTextData]
    confirm_text: NotRequired[ButtonTextData]


class SubmissionRemovalOptionsData(TypedDict):
    successful_submissions_removal_limit: NotRequired[int | None]
    successful_submissions_removal_method: NotRequired[RemovalMethods]
    incomplete_submissions_removal_limit: NotRequired[int | None]
    incomplete_submissions_removal_method: NotRequired[RemovalMethods]
    errored_submissions_removal_limit: NotRequired[int | None]
    errored_submissions_removal_method: NotRequired[RemovalMethods]
    all_submissions_removal_limit: NotRequired[int | None]


class FormTranslations(TypedDict):
    name: str
    internal_name: str


class FormTranslationsData(TypedDict):
    en: FormTranslations
    nl: FormTranslations


class FormDefinitionTranslations(TypedDict):
    name: str


class FormDefinitionTranslationsData(TypedDict):
    en: FormDefinitionTranslations
    nl: FormDefinitionTranslations


class FormDefinitionData(TypedDict):
    uuid: UUID
    internal_name: NotRequired[str]
    slug: NotRequired[str]
    configuration: FormioConfiguration
    login_required: NotRequired[bool]
    is_reusable: NotRequired[bool]
    translations: NotRequired[FormDefinitionTranslationsData]


class FormStepLiteralData(TypedDict):
    previous_text: NotRequired[ButtonTextData]
    save_text: NotRequired[ButtonTextData]
    next_text: NotRequired[ButtonTextData]


class FormStepTranslationData(TypedDict):
    previous_text: NotRequired[str]
    save_text: NotRequired[str]
    next_text: NotRequired[str]


class FormStepData(TypedDict):
    slug: NotRequired[str]
    form_definition: FormDefinitionData
    is_applicable: NotRequired[bool]
    literals: NotRequired[FormStepLiteralData]
    translations: NotRequired[FormStepTranslationData]


class PaymentData(TypedDict):
    payment_backend: str
    payment_backend_options: dict


class ServiceFetchConfigurationData(TypedDict):
    name: str
    service: UUID

    path: NotRequired[str]
    method: NotRequired[ServiceFetchMethods]
    headers: NotRequired[dict]
    query_params: NotRequired[dict]
    body: NotRequired[dict | None]

    data_mapping_type: NotRequired[DataMappingTypes]

    mapping_expression: NotRequired[str | None]

    cache_timeout: NotRequired[int | None]


class FormVariableData(TypedDict):
    name: str
    key: str
    source: FormVariableSources
    is_sensitive_data: NotRequired[bool]

    form_definition: NotRequired[UUID | None]

    data_type: FormVariableDataTypes
    data_subtype: NotRequired[FormVariableDataTypes]

    data_format: NotRequired[str]

    prefill_plugin: NotRequired[str]
    prefill_attribute: NotRequired[str]
    prefill_identifier_role: NotRequired[IdentifierRoles]
    prefill_options: NotRequired[dict]

    initial_value: NotRequired[dict | None]

    service_fetch_configuration: NotRequired[ServiceFetchConfigurationData | None]


class LogicActionServiceData(TypedDict):
    type: Literal[LogicActionTypes.fetch_from_service]
    value: JSONValue


type DummyActionTypes = (
    Literal[LogicActionTypes.disable_next]
    | Literal[LogicActionTypes.step_not_applicable]
    | Literal[LogicActionTypes.step_applicable]
)


class LogicActionDummyData(TypedDict):
    type: DummyActionTypes


class PropertyData(TypedDict):
    type: PropertyTypes
    value: str


class LogicActionPropertyData(TypedDict):
    type: Literal[LogicActionTypes.property]
    property: PropertyData
    state: JSONValue


class LogicValueData(TypedDict):
    type: Literal[LogicActionTypes.variable]
    value: JSONValue


class VariableMappingData(TypedDict):
    form_variable: str
    dmn_variable: str


class LogicActionDMNEvaluateConfigData(TypedDict):
    plugin_id: str
    decision_definition_id: str
    decision_definition_version: NotRequired[str]
    input_mapping: list[VariableMappingData]
    output_mapping: list[VariableMappingData]


class LogicActionDMNEvaluateData(TypedDict):
    type: Literal[LogicActionTypes.evaluate_dmn]
    config: LogicActionDMNEvaluateConfigData


class LogicActionRegistrationBackendData(TypedDict):
    type: Literal[LogicActionTypes.set_registration_backend]
    value: str


class SynchronizeDataMappingData(TypedDict):
    property: str
    component_key: str


class SynchronizeVariableConfigData(TypedDict):
    identifier_variable: str
    source_variable: str
    destination_variable: str
    data_mappings: list[SynchronizeDataMappingData]


class LogicActionSynchronizeVariableData(TypedDict):
    type: Literal[LogicActionTypes.synchronize_variables]
    config: SynchronizeVariableConfigData


type LogicActionTypeData = (
    LogicActionServiceData
    | DummyActionTypes
    | LogicActionPropertyData
    | LogicValueData
    | LogicActionDMNEvaluateData
    | LogicActionRegistrationBackendData
    | LogicActionSynchronizeVariableData
)


class FormLogicComponentActionData(TypedDict):
    component: NotRequired[str]
    variable: NotRequired[str]
    form_step_uuid: NotRequired[str]
    action: LogicActionTypeData


class FormLogicRulesData(TypedDict):
    trigger_from_step: NotRequired[str]
    json_logic_trigger: JSONValue
    description: str
    order: int
    is_advanced: NotRequired[bool]
    actions: list[FormLogicComponentActionData]
    form_steps: NotRequired[list[str]]


class FormValidatedData(TypedDict):
    uuid: UUID
    name: str
    internal_name: NotRequired[str]
    internal_remarks: NotRequired[str]
    translations_enabled: NotRequired[bool]
    appointment_options: NotRequired[AppointmentData]
    literals: NotRequired[FormLiteralData]
    product: NotRequired[Product]
    slug: str
    type: FormTypeChoices
    category: NotRequired[Category]
    theme: NotRequired[Theme]

    formstep_set: list[FormStepData]
    payment: NotRequired[PaymentData]

    formvariable_set: list[FormVariableData]

    formlogic_set: list[FormLogicRulesData]

    show_progress_indicator: NotRequired[bool]
    show_summary_progress: NotRequired[bool]
    maintenance_mode: NotRequired[bool]
    active: NotRequired[bool]
    activate_on: NotRequired[datetime]
    deactivate_on: NotRequired[datetime]
    _is_deleted: NotRequired[bool]

    submission_confirmation_template: NotRequired[str]
    introduction_page_content: NotRequired[str]
    explanation_template: NotRequired[str]

    submission_allowed: NotRequired[str]
    submission_limit: NotRequired[int | None]
    submission_counter: NotRequired[int]

    suspension_allowed: NotRequired[bool]

    ask_privacy_consent: NotRequired[StatementCheckboxChoices]
    ask_statement_of_truth: NotRequired[StatementCheckboxChoices]

    submission_removal_options: NotRequired[SubmissionRemovalOptionsData]

    confirmation_email_template: NotRequired[ConfirmationEmailTemplateTranslatedData]
    send_confirmation_email: NotRequired[bool]
    display_main_website_link: NotRequired[bool]
    include_confirmation_page_content_in_pdf: NotRequired[bool]

    new_renderer_enabled: NotRequired[bool]
    new_logic_evaluation_enabled: NotRequired[bool]

    translations: NotRequired[FormTranslationsData]
