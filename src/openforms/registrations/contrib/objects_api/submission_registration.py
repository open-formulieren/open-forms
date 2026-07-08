from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import (
    Any,
    Literal,
    assert_never,
    override,
)

import structlog

from openforms.contrib.objects_api.clients import (
    DocumentenClient,
    get_catalogi_client,
    get_documents_client,
)
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.objects_api.typing import Record
from openforms.contrib.zgw.service import (
    DocumentOptions,
    DocumentTypeResolver,
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.formio.service import FormioData
from openforms.formio.typing import Component
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import FieldConf, apply_data_mapping
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
)
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import VariableValue
from openforms.utils.date import datetime_in_amsterdam
from openforms.variables.constants import FormVariableSources
from openforms.variables.utils import get_variables_for_context

from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from .handlers.v1 import get_payment_context_data, render_template
from .handlers.v2 import AssignmentSpec, OutputSpec, process_mapped_variable
from .models import ObjectsAPIRegistrationData, ObjectsAPISubmissionAttachment
from .registration_variables import (
    PAYMENT_VARIABLE_NAMES,
    register as variables_registry,
)
from .typing import (
    ConfigVersion,
    FileComponentOptions,
    RegistrationOptions,
    RegistrationOptionsV1,
    RegistrationOptionsV2,
)

logger = structlog.stdlib.get_logger(__name__)


def _resolve_documenttype(
    resolver: DocumentTypeResolver,
    field: Literal["submission_report", "submission_csv", "attachment"],
    options: RegistrationOptions,
    submission: Submission,
) -> str:
    """
    Given the registration options, resolve the documenttype URL to use.

    :param field: for which kind of upload the document type must be resolved.
    :return: the resolved document type URL, if any. Empty string means that the upload
      should be skipped.
    """
    catalogue = options["catalogue"]
    # validation ensures both are empty or not empty at the same time
    if not (catalogue["domain"] and catalogue["domain"]):
        return ""

    match field:
        case "submission_report":
            description = options["iot_submission_report"]
        case "submission_csv":
            description = options["iot_submission_csv"]
        case "attachment":
            description = options["iot_attachment"]
        case _:  # pragma: no cover
            assert_never(field)

    if not description:
        return ""

    assert submission.completed_on is not None

    version_valid_on = datetime_in_amsterdam(submission.completed_on).date()
    version = resolver.resolve(
        catalogue=catalogue,
        description=description,
        on_date=version_valid_on,
    )
    return version["url"]


def register_submission_pdf(
    resolver: DocumentTypeResolver,
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
) -> str:
    document_type = _resolve_documenttype(
        resolver, "submission_report", options, submission
    )
    if not document_type:
        return ""

    submission_report = SubmissionReport.objects.get(submission=submission)
    report_document = create_report_document(
        client=documents_client,
        name=submission.form.name,
        submission_report=submission_report,
        options={
            "informatieobjecttype": document_type,
            "organisatie_rsin": options.get("organisatie_rsin", ""),
        },
        language=submission_report.submission.language_code,
    )
    return report_document["url"]


def register_submission_csv(
    resolver: DocumentTypeResolver,
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
) -> str:
    if not options.get("upload_submission_csv", False):
        return ""

    document_type = _resolve_documenttype(
        resolver, "submission_csv", options, submission
    )
    if not document_type:
        return ""

    qs = Submission.objects.filter(pk=submission.pk).select_related("auth_info")
    submission_csv = create_submission_export(qs).export("csv")

    submission_csv_document = create_csv_document(
        client=documents_client,
        name=f"{submission.form.name} (csv)",
        csv_data=submission_csv,
        options={
            "informatieobjecttype": document_type,
            "organisatie_rsin": options.get("organisatie_rsin", ""),
        },
        language=submission.language_code,
    )

    return submission_csv_document["url"]


def register_submission_attachment(
    resolver: DocumentTypeResolver,
    submission: Submission,
    attachment: SubmissionFileAttachment,
    options: RegistrationOptions,
    file_options: Mapping[str, FileComponentOptions],
    documents_client: DocumentenClient,
) -> str:
    default_document_type = _resolve_documenttype(
        resolver, "attachment", options, submission
    )
    assert default_document_type, "Registration should have been skipped"

    # registration for submissions that aren't completed does not make sense and the
    # assert helps with type narrowing
    assert submission.completed_on is not None

    document_options: DocumentOptions = {
        "informatieobjecttype": default_document_type,
        "organisatie_rsin": options.get("organisatie_rsin", ""),
        "ontvangstdatum": datetime_in_amsterdam(submission.completed_on)
        .date()
        .isoformat(),
    }

    # look up registration overrides for the component that this file was
    # uploaded for
    if (overrides := file_options.get(attachment.component_key)) is not None:
        if _document_type_description := overrides.get("document_type_description"):
            _options = options.copy()
            _options["iot_attachment"] = _document_type_description
            document_options["informatieobjecttype"] = _resolve_documenttype(
                resolver, "attachment", _options, submission
            )
        if _bronorganisatie := overrides.get("organization_rsin"):
            document_options["organisatie_rsin"] = _bronorganisatie
        if _cl := overrides.get("confidentiality_level"):
            document_options["doc_vertrouwelijkheidaanduiding"] = _cl
        if _title := overrides.get("title"):
            document_options["titel"] = _title

    attachment_document = create_attachment_document(
        client=documents_client,
        name=submission.form.name,
        submission_attachment=attachment,
        options=document_options,
        language=attachment.submission_step.submission.language_code,  # assume same as submission
    )

    return attachment_document["url"]


@contextmanager
def save_and_raise(
    registration_data: ObjectsAPIRegistrationData,
    submission_attachments: list[ObjectsAPISubmissionAttachment],
) -> Iterator[None]:
    """Save the registration data before raising a :class:`~openforms.registrations.exceptions.RegistrationFailed` exception."""

    try:
        yield
    except Exception as e:
        raise RegistrationFailed() from e
    finally:
        registration_data.save()
        ObjectsAPISubmissionAttachment.objects.bulk_create(submission_attachments)


class ObjectsAPIRegistrationHandler[
    OptionsT: RegistrationOptionsV1 | RegistrationOptionsV2
](ABC):
    """Provide the registration data to be sent to the Objects API.

    When registering a submission to the Objects API, the following happens:
    - Depending on the version (v1 or v2) of the options, the correct handler is instantiated.
    - ``save_registration_data`` is called, creating an instance of ``ObjectsAPIRegistrationData``.
    - ``get_record_data`` is called, and should make use of the saved registration data to build
      the record data to be sent to the Objects API.
    - Similarly, ``get_update_payment_status_data`` is called to get the PATCH payload to be sent
      to the Objects API.
    """

    def save_registration_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> None:
        """Save the registration data.

        The creation of submission documents (report, attachment, csv) makes use of ZGW
        service functions (e.g. :func:`create_report_document`) and involves a mapping
        (and in some cases renaming) of variables which would otherwise not be
        accessible from here. For example, 'vertrouwelijkheidaanduiding' must be named
        'doc_vertrouwelijkheidaanduiding' because this is what the ZGW service functions
        use.
        """
        registration_data, _ = ObjectsAPIRegistrationData.objects.get_or_create(
            submission=submission
        )
        submission_attachments: list[ObjectsAPISubmissionAttachment] = []

        _is_catalogue_empty = not (
            options["catalogue"]["domain"] and options["catalogue"]["rsin"]
        )
        _is_attachment_document_type_configured = (not _is_catalogue_empty) and options[
            "iot_attachment"
        ]

        api_group = options["objects_api_group"]
        file_options = {item["key"]: item for item in options.get("files", [])}

        with (
            get_documents_client(api_group) as documents_client,
            get_catalogi_client(api_group) as catalogi_client,
            save_and_raise(registration_data, submission_attachments),
        ):
            doc_type_resolver = DocumentTypeResolver(catalogi_client)
            if not registration_data.pdf_url:
                registration_data.pdf_url = register_submission_pdf(
                    doc_type_resolver,
                    submission,
                    options,
                    documents_client,
                )

            if not registration_data.csv_url:
                registration_data.csv_url = register_submission_csv(
                    doc_type_resolver,
                    submission,
                    options,
                    documents_client,
                )

            if _is_attachment_document_type_configured:
                existing = [
                    o.submission_file_attachment
                    for o in ObjectsAPISubmissionAttachment.objects.filter(
                        submission_file_attachment__submission_step__submission=submission
                    )
                ]

                for attachment in submission.attachments:
                    if attachment not in existing:
                        document_url = register_submission_attachment(
                            doc_type_resolver,
                            submission,
                            attachment,
                            options,
                            file_options,
                            documents_client,
                        )
                        submission_attachments.append(
                            ObjectsAPISubmissionAttachment(
                                submission_file_attachment=attachment,
                                document_url=document_url,
                            )
                        )

    @abstractmethod
    def get_record_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> Record:
        """Get the record data to be sent to the Objects API."""
        pass

    @abstractmethod
    def get_update_payment_status_data(
        self, submission: Submission, options: OptionsT
    ) -> Record | None:
        """Get the object data payload to be sent (either as a PATCH or PUT request) to the Objects API."""
        pass


class ObjectsAPIV1Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV1]):
    """Provide the registration data for legacy (v1) registration options, using JSON templates."""

    @override
    def get_record_data(
        self, submission: Submission, options: RegistrationOptionsV1
    ) -> Record:
        """Get the record data to be sent to the Objects API."""

        # help the type checker a little, our 'apply_defaults_to' does some heavy
        # lifting.
        assert "productaanvraag_type" in options
        assert "content_json" in options

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        attachment_urls = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment__submission_step__submission=submission
        ).values_list("document_url", flat=True)

        data = render_template(
            submission=submission,
            template=options["content_json"],
            product_request_type=options["productaanvraag_type"],
            uploaded_attachment_urls=list(attachment_urls),
            pdf_url=registration_data.pdf_url,
            csv_url=registration_data.csv_url,
        )

        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )
        record_data = apply_data_mapping(
            submission,
            {"geometry": FieldConf(RegistrationAttribute.locatie_coordinaat)},
            REGISTRATION_ATTRIBUTE,
            record_data,  # pyright: ignore[reportArgumentType]
        )
        return record_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV1
    ) -> Record | None:
        assert "payment_status_update_json" in options

        if not options["payment_status_update_json"]:
            logger.warning(
                "skip_payment_status_update", reason="no_template_configured"
            )
            return

        context = {
            "variables": get_variables_for_context(submission),
            "payment": get_payment_context_data(submission),
        }

        data = render_to_json(options["payment_status_update_json"], context)
        assert isinstance(data, dict)
        return prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )


def _lookup_component(variable: SubmissionValueVariable) -> Component:
    assert variable.form_variable is not None
    config_wrapper = variable.form_variable.form_definition.configuration_wrapper
    component = config_wrapper.component_map[variable.key]
    return component


class ObjectsAPIV2Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV2]):
    @staticmethod
    def get_attachment_urls_by_key(submission: Submission) -> dict[str, list[str]]:
        urls_map = defaultdict[str, list[str]](list)
        attachments = ObjectsAPISubmissionAttachment.objects.select_related(
            "submission_file_attachment"
        ).filter(submission_file_attachment__submission_variable__submission=submission)
        for attachment_meta in attachments:
            key: str = attachment_meta.submission_file_attachment.data_path
            urls_map[key].append(attachment_meta.document_url)
        return urls_map

    @override
    def get_record_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> Record:
        log = logger.bind(submission_uuid=str(submission.uuid))
        state = submission.variables_state

        all_values = state.get_data(
            include_static_variables=True,
            include_unsaved=True,
        )
        # update with the registration static values - a special subtype of static
        # variables. They're possibly derived from user input.
        registration_vars = state.get_static_data(other_registry=variables_registry)
        all_values.update(registration_vars)

        # For every file upload component, we alter the value of the variable to be
        # the Document API URL(s).
        urls_map = self.get_attachment_urls_by_key(submission)

        variables_mapping = options["variables_mapping"]
        transform_to_list = options["transform_to_list"]

        # collect all the assignments to be done to the object
        assignment_specs: list[AssignmentSpec] = []
        for mapping in variables_mapping:
            key = mapping["variable_key"]
            log = log.bind(action="process_variable_mapping", key=key, mapping=mapping)

            try:
                variable = state.variables[key]
            except KeyError:
                # this is normal for registration variables
                log.debug(
                    "variable_definition_not_found",
                    is_registration_var=key in registration_vars,
                )
                variable = None

            value: VariableValue
            try:
                value = all_values[key]
            except KeyError:
                log.info("variable_not_found", outcome="ignore_mapping")
                continue

            # Look up if the key points to a form component that provides additional
            # context for how to process the value.
            component: Component | None = None
            if (
                variable
                and variable.form_variable is not None
                and variable.form_variable.source == FormVariableSources.component
            ):
                component = _lookup_component(variable)

            # process the value so that we can assign it to the record data as requested
            assignment_spec = process_mapped_variable(
                mapping=mapping,
                value=value,
                variable=variable,
                component=component,
                attachment_urls=urls_map,
                transform_to_list=transform_to_list,
            )
            if isinstance(assignment_spec, AssignmentSpec):
                assignment_specs.append(assignment_spec)
            else:
                assignment_specs.extend(assignment_spec)

        log = log.unbind("action", "key", "mapping")

        output_spec = OutputSpec(assignments=assignment_specs)
        data = output_spec.create_output_data()

        # turn the data into a proper record for the objects API
        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )

        # special treatment for the geometry key, as that one sits outside of the data
        # nested inside the record
        if key := options.get("geometry_variable_key"):
            variable = state.variables[key]
            component = _lookup_component(variable)
            # piggy-back on the value processing
            assignment_spec = process_mapped_variable(
                mapping={"variable_key": key, "target_path": ["geometry"]},
                value=all_values[key],
                variable=variable,
                component=component,
            )
            assert isinstance(assignment_spec, AssignmentSpec)
            geometry = assignment_spec.value
            assert isinstance(geometry, dict)
            record_data["geometry"] = geometry

        return record_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> Record:
        state = submission.variables_state
        # we only consider the payment variables for payment update status data
        registration_values = FormioData(
            state.get_static_data(other_registry=variables_registry)
        )

        # collect all the assignments to be done to the object
        assignment_specs: list[AssignmentSpec] = []
        for mapping in options["variables_mapping"]:
            key = mapping["variable_key"]
            if key not in PAYMENT_VARIABLE_NAMES:
                continue

            # process the value so that we can assign it to the record data as requested
            assignment_spec = process_mapped_variable(
                mapping=mapping,
                value=registration_values[key],
            )
            if isinstance(assignment_spec, AssignmentSpec):
                assignment_specs.append(assignment_spec)
            else:
                assignment_specs.extend(assignment_spec)

        output_spec = OutputSpec(assignments=assignment_specs)
        data = output_spec.create_output_data()

        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )
        return record_data


HANDLER_MAPPING: dict[ConfigVersion, ObjectsAPIRegistrationHandler[Any]] = {
    1: ObjectsAPIV1Handler(),
    2: ObjectsAPIV2Handler(),
}
